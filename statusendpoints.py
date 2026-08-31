from flask import Blueprint, jsonify, request
from db import get_connection

status_bp = Blueprint("status", __name__)


# Forward-only transition map. No skipping, no reversing — matches the
# status flow doc: the backend only ever validates "is this the next step,"
# not an arbitrary state machine.
VALID_TRANSITIONS = {
    "ASSIGNED": ["PICKED_UP"],
    "PICKED_UP": ["DELIVERED"],
    "DELIVERED": [],
}


@status_bp.route("/deliveries", methods=["GET"])
def list_rider_deliveries():
    """
    Rider's own delivery list.

    GET /deliveries?rider_id=<id>&status=active

    "active" per the doc means anything not yet DELIVERED, i.e. what a
    rider currently has on their plate (ASSIGNED or PICKED_UP). This is a
    different view from Nathalie's GET /deliveries (the dispatcher's view
    of OPEN deliveries) — same table, same endpoint path, different query
    params, so it lives on this blueprint rather than duplicating hers.
    """
    rider_id = request.args.get("rider_id")
    status_filter = request.args.get("status")

    if not rider_id:
        return jsonify({"error": "rider_id is required"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if status_filter == "active":
        cur.execute(
            """
            SELECT delivery_id, retailer_id, customer_name, customer_phone,
                   delivery_address, item_description, status,
                   created_at, updated_at
            FROM Deliveries
            WHERE rider_id = %s AND status IN ('ASSIGNED', 'PICKED_UP')
            ORDER BY updated_at ASC
            """,
            (rider_id,),
        )
    else:
        cur.execute(
            """
            SELECT delivery_id, retailer_id, customer_name, customer_phone,
                   delivery_address, item_description, status,
                   created_at, updated_at
            FROM Deliveries
            WHERE rider_id = %s
            ORDER BY updated_at DESC
            """,
            (rider_id,),
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200


@status_bp.route("/deliveries/<int:delivery_id>/status", methods=["PATCH"])
def update_status(delivery_id):
    """
    Body: { "rider_id": <int>, "status": "PICKED_UP" | "DELIVERED" }

    rider_id is who's making the change — checked against the delivery's
    assigned rider, and recorded as changed_by in Status_history, same
    pattern Nathalie used for dispatcher_id on the assign endpoint.

    DELIVERED is hard-gated behind a successful QR_confirmations row for
    this delivery, per the status flow doc and George's scan/confirmation
    piece. That check lives here — not just in the frontend or in George's
    future qr-confirm endpoint — so DELIVERED can never be reached by
    calling this endpoint directly, regardless of what calls it.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    rider_id = body.get("rider_id")
    new_status = body.get("status")

    if not rider_id or not new_status:
        return jsonify({"error": "rider_id and status are required"}), 400

    if new_status not in ("PICKED_UP", "DELIVERED"):
        return jsonify({
            "error": f"'{new_status}' is not a status a rider can set directly"
        }), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Confirm the delivery exists and is assigned to this rider.
    cur.execute(
        "SELECT status, rider_id FROM Deliveries WHERE delivery_id = %s",
        (delivery_id,),
    )
    delivery = cur.fetchone()
    if delivery is None:
        cur.close()
        conn.close()
        return jsonify({"error": f"No delivery found with id {delivery_id}"}), 404

    if str(delivery["rider_id"]) != str(rider_id):
        cur.close()
        conn.close()
        return jsonify({
            "error": f"Delivery {delivery_id} is not assigned to rider {rider_id}"
        }), 403

    current_status = delivery["status"]
    allowed_next = VALID_TRANSITIONS.get(current_status, [])

    if new_status not in allowed_next:
        cur.close()
        conn.close()
        return jsonify({
            "error": f"Cannot change status from {current_status} to {new_status}"
        }), 409

    # Hard gate: DELIVERED requires a prior successful scan.
    if new_status == "DELIVERED":
        cur.execute(
            """
            SELECT confirmation_id
            FROM QR_confirmations
            WHERE delivery_id = %s AND result = 'Successful'
            ORDER BY scanned_at DESC
            LIMIT 1
            """,
            (delivery_id,),
        )
        confirmation = cur.fetchone()
        if confirmation is None:
            cur.close()
            conn.close()
            return jsonify({
                "error": "DELIVERED requires a successful QR scan first",
                "delivery_id": delivery_id
            }), 409

    # Apply the transition.
    cur.execute(
        """
        UPDATE Deliveries
        SET status = %s
        WHERE delivery_id = %s
        """,
        (new_status, delivery_id),
    )

    # Log it — changed_by is the rider making the update.
    cur.execute(
        """
        INSERT INTO Status_history (delivery_id, changed_by, status)
        VALUES (%s, %s, %s)
        """,
        (delivery_id, rider_id, new_status),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "delivery_id": delivery_id,
        "previous_status": current_status,
        "status": new_status
    }), 200
