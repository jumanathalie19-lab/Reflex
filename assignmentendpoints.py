import secrets
from flask import Blueprint, jsonify, request
from db import get_connection

assignment_bp = Blueprint("assignment", __name__)


@assignment_bp.route("/deliveries", methods=["POST"])
def create_delivery():
    """
    Retailer logs a new delivery request. This was missing entirely —
    Nathalie's original doc covered assignment (OPEN -> ASSIGNED), but
    nothing covered how a delivery becomes OPEN in the first place.
    Added here since it's the same Deliveries table she already owns.

    Body: { retailer_id, customer_name, customer_phone,
            delivery_address, item_description }
    New deliveries always start as status = OPEN (the table default).
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    required = ["retailer_id", "customer_name", "customer_phone",
                "delivery_address", "item_description"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Confirm retailer_id actually refers to a Retailer.
    cur.execute("SELECT role FROM Users WHERE user_id = %s", (body["retailer_id"],))
    retailer = cur.fetchone()
    if retailer is None or retailer["role"] != "Retailer":
        cur.close()
        conn.close()
        return jsonify({"error": f"User {body['retailer_id']} is not a valid Retailer"}), 400

    cur.execute(
        """
        INSERT INTO Deliveries
            (retailer_id, customer_name, customer_phone, delivery_address, item_description)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (body["retailer_id"], body["customer_name"], body["customer_phone"],
         body["delivery_address"], body["item_description"]),
    )
    delivery_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "delivery_id": delivery_id,
        "status": "OPEN"
    }), 201


@assignment_bp.route("/deliveries", methods=["GET"])
def list_open_deliveries():
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
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    rider_id = body.get("rider_id")
    dispatcher_id = body.get("dispatcher_id")

    if not rider_id or not dispatcher_id:
        return jsonify({"error": "rider_id and dispatcher_id are required"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

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

    cur.execute(
        "SELECT role FROM Users WHERE user_id = %s", (rider_id,)
    )
    rider = cur.fetchone()
    if rider is None or rider["role"] != "Rider":
        cur.close()
        conn.close()
        return jsonify({"error": f"User {rider_id} is not a valid Rider"}), 400

    # QR code generated here, at ASSIGNED, per George's scan/confirmation
    # doc: "Trigger: when a delivery moves ASSIGNED. At that point, the
    # backend generates a short unique code, stores it on the Deliveries
    # row..." That's this transition, so it's generated here rather than
    # in George's qr-confirm endpoint, which only ever checks a code that
    # must already exist.
    qr_code = secrets.token_hex(8)

    cur.execute(
        """
        UPDATE Deliveries
        SET rider_id = %s, status = 'ASSIGNED', qr_code = %s
        WHERE delivery_id = %s
        """,
        (rider_id, qr_code, delivery_id),
    )

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
        "status": "ASSIGNED",
        "qr_code": qr_code
    }), 200