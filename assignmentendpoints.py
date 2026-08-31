
from flask import Blueprint, jsonify, request
from db import get_connection

assignment_bp = Blueprint("assignment", __name__)


@assignment_bp.route("/deliveries", methods=["GET"])
def list_open_deliveries():
    """Dispatcher's view: every delivery still waiting for a rider."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT delivery_id, retailer_id, customer_name, customer_phone,
               delivery_address, item_description, status, created_at
        FROM Deliveries
        WHERE status = 'OPEN'
        ORDER BY created_at ASC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200


@assignment_bp.route("/riders", methods=["GET"])
def list_riders():
    """Everyone the Dispatcher is allowed to assign a delivery to."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT user_id, name, phone FROM Users WHERE role = 'Rider'"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200


@assignment_bp.route("/deliveries/<int:delivery_id>/assign", methods=["POST"])
def assign_delivery(delivery_id):
    """
    Body: { "rider_id": <int>, "dispatcher_id": <int> }

    dispatcher_id is who's making the assignment — it's who gets recorded
    as changed_by in Status_history, per Nathalie's doc (the audit trail
    needs to show WHO assigned it, not just that it happened).
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    rider_id = body.get("rider_id")
    dispatcher_id = body.get("dispatcher_id")

    if not rider_id or not dispatcher_id:
        return jsonify({"error": "rider_id and dispatcher_id are required"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Confirm the delivery exists and is still OPEN — can't assign
    # something already assigned, picked up, or delivered.
    cur.execute(
        "SELECT status FROM Deliveries WHERE delivery_id = %s", (delivery_id,)
    )
    delivery = cur.fetchone()
    if delivery is None:
        cur.close()
        conn.close()
        return jsonify({"error": f"No delivery found with id {delivery_id}"}), 404
    if delivery["status"] != "OPEN":
        cur.close()
        conn.close()
        return jsonify({
            "error": f"Delivery {delivery_id} is already {delivery['status']}, cannot assign"
        }), 409

    # Confirm the chosen user is actually a Rider.
    cur.execute(
        "SELECT role FROM Users WHERE user_id = %s", (rider_id,)
    )
    rider = cur.fetchone()
    if rider is None or rider["role"] != "Rider":
        cur.close()
        conn.close()
        return jsonify({"error": f"User {rider_id} is not a valid Rider"}), 400

    # Update the delivery: assign the rider, move status to ASSIGNED.
    cur.execute(
        """
        UPDATE Deliveries
        SET rider_id = %s, status = 'ASSIGNED'
        WHERE delivery_id = %s
        """,
        (rider_id, delivery_id),
    )

    # Log the change to Status_history — changed_by is the dispatcher.
    cur.execute(
        """
        INSERT INTO Status_history (delivery_id, changed_by, status)
        VALUES (%s, %s, 'ASSIGNED')
        """,
        (delivery_id, dispatcher_id),
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "delivery_id": delivery_id,
        "rider_id": rider_id,
        "status": "ASSIGNED"
    }), 200