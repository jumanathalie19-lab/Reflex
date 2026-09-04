from flask import Blueprint, jsonify, request
from db import get_connection
from statusendpoint import apply_transition

qr_bp = Blueprint("qr", __name__)


@qr_bp.route("/deliveries/<int:delivery_id>/qr-confirm", methods=["POST"])
def qr_confirm(delivery_id):
    """
    Body: { "rider_id": <int>, "qr_code": <string> }

    Matches George's own scan/confirmation doc exactly:
    1. Confirm the requesting user is the rider assigned to this delivery.
    2. Check the submitted qr_code against the one stored on the
       Deliveries row (set by Nathalie's assign endpoint).
    3. ALWAYS insert a row into QR_confirmations — success or fail — this
       is the audit trail his doc specifies, not just a success log.
    4. On success: apply the existing status-transition flow to move to
       DELIVERED (reusing Mark's apply_transition, not reimplementing it).
    5. On failure: status stays at PICKED_UP, caller is told to rescan.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    rider_id = body.get("rider_id")
    submitted_code = body.get("qr_code")

    if not rider_id or not submitted_code:
        return jsonify({"error": "rider_id and qr_code are required"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT status, rider_id, qr_code FROM Deliveries WHERE delivery_id = %s",
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

    if delivery["status"] != "PICKED_UP":
        cur.close()
        conn.close()
        return jsonify({
            "error": f"Cannot QR-confirm a delivery with status '{delivery['status']}'. "
                     f"Delivery must be PICKED_UP first."
        }), 409

    is_match = (delivery["qr_code"] is not None and submitted_code == delivery["qr_code"])
    result = "Successful" if is_match else "Failed"

    # Log the attempt regardless of outcome — this is the audit trail,
    # not just a success record.
    cur.execute(
        """
        INSERT INTO QR_confirmations (delivery_id, qr_code, scanned_by, result)
        VALUES (%s, %s, %s, %s)
        """,
        (delivery_id, submitted_code, rider_id, result),
    )

    if not is_match:
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            "error": "QR code does not match this delivery",
            "result": "fail"
        }), 409

    apply_transition(cur, delivery_id, rider_id, "DELIVERED")

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "delivery_id": delivery_id,
        "previous_status": "PICKED_UP",
        "status": "DELIVERED",
        "result": "success"
    }), 200