import secrets
from flask import Flask, jsonify, request, render_template
import mysql.connector
from mysql.connector import Error
from config import Config
from sms_service import send_sms


app = Flask(__name__)


# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------

def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )


# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    connection = None

    try:
        connection = get_db_connection()

        if connection.is_connected():
            return jsonify({
                "status": "success",
                "message": "Reflex API and MySQL connection are working"
            })

    except Error as error:
        return jsonify({
            "status": "error",
            "message": "Database connection failed",
            "error": str(error)
        }), 500

    finally:
        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# GET ALL RIDERS
# ---------------------------------------------------

@app.route("/api/riders", methods=["GET"])
def get_riders():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM riders
            ORDER BY rider_id DESC
        """)

        riders = cursor.fetchall()

        return jsonify(riders)

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# CREATE RIDER
# ---------------------------------------------------

@app.route("/api/riders", methods=["POST"])
def create_rider():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    phone = data.get("phone")

    if not name or not phone:
        return jsonify({
            "error": "name and phone are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO riders (name, phone)
            VALUES (%s, %s)
        """, (name, phone))

        connection.commit()

        rider_id = cursor.lastrowid

        return jsonify({
            "message": "Rider created successfully",
            "rider_id": rider_id
        }), 201

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# GET ALL RETAILERS
# ---------------------------------------------------

@app.route("/api/retailers", methods=["GET"])
def get_retailers():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM retailers
            ORDER BY retailer_id DESC
        """)

        retailers = cursor.fetchall()

        return jsonify(retailers)

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# CREATE RETAILER
# ---------------------------------------------------

@app.route("/api/retailers", methods=["POST"])
def create_retailer():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    phone = data.get("phone")

    if not name or not phone:
        return jsonify({
            "error": "name and phone are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO retailers (name, phone)
            VALUES (%s, %s)
        """, (name, phone))

        connection.commit()

        retailer_id = cursor.lastrowid

        return jsonify({
            "message": "Retailer created successfully",
            "retailer_id": retailer_id
        }), 201

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# GET ALL DELIVERIES
# ---------------------------------------------------

@app.route("/api/deliveries", methods=["GET"])
def get_deliveries():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                d.delivery_id,
                d.customer_name,
                d.customer_phone,
                d.delivery_address,
                d.item_description,
                d.status,
                d.created_at,
                d.updated_at,
                r.name AS retailer_name,
                rd.name AS rider_name
            FROM deliveries d
            JOIN retailers r
                ON d.retailer_id = r.retailer_id
            LEFT JOIN riders rd
                ON d.rider_id = rd.rider_id
            ORDER BY d.delivery_id DESC
        """)

        deliveries = cursor.fetchall()

        return jsonify(deliveries)

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# CREATE DELIVERY
# ---------------------------------------------------

@app.route("/api/deliveries", methods=["POST"])
def create_delivery():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    required_fields = [
        "retailer_id",
        "customer_name",
        "customer_phone",
        "delivery_address",
        "item_description"
    ]

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO deliveries (
                retailer_id,
                customer_name,
                customer_phone,
                delivery_address,
                item_description
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data["retailer_id"],
            data["customer_name"],
            data["customer_phone"],
            data["delivery_address"],
            data["item_description"]
        ))

        connection.commit()

        delivery_id = cursor.lastrowid

        return jsonify({
            "message": "Delivery request created successfully",
            "delivery_id": delivery_id,
            "status": "Pending"
        }), 201

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# ASSIGN DELIVERY TO RIDER
# (generates the QR code for this delivery at the same time)
# ---------------------------------------------------

@app.route("/api/deliveries/<int:delivery_id>/assign", methods=["PUT"])
def assign_delivery(delivery_id):
    data = request.get_json()

    if not data or not data.get("rider_id"):
        return jsonify({
            "error": "rider_id is required"
        }), 400

    rider_id = data["rider_id"]

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check delivery exists
        cursor.execute("""
            SELECT delivery_id, status, customer_phone, customer_name
            FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        delivery = cursor.fetchone()

        if not delivery:
            return jsonify({
                "error": "Delivery not found"
            }), 404

        # Check rider exists
        cursor.execute("""
            SELECT rider_id
            FROM riders
            WHERE rider_id = %s
        """, (rider_id,))

        rider = cursor.fetchone()

        if not rider:
            return jsonify({
                "error": "Rider not found"
            }), 404

        # Generate a unique QR code for this delivery
        qr_code = secrets.token_hex(8)  # e.g. "a13f9c2e8b7d4f10"

        # Assign rider and attach QR code
        cursor.execute("""
            UPDATE deliveries
            SET rider_id = %s,
                status = 'Assigned',
                qr_code = %s
            WHERE delivery_id = %s
        """, (rider_id, qr_code, delivery_id))

        connection.commit()

        # Notify the customer via SMS (stub - see sms_service.py)
        send_sms(
            delivery["customer_phone"],
            f"Hi {delivery['customer_name']}, your Reflex delivery has "
            f"been assigned to a rider and is on its way."
        )

        return jsonify({
            "message": "Delivery assigned successfully",
            "delivery_id": delivery_id,
            "rider_id": rider_id,
            "status": "Assigned",
            "qr_code": qr_code
        })

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# UPDATE DELIVERY STATUS
# ---------------------------------------------------

@app.route("/api/deliveries/<int:delivery_id>/status", methods=["PUT"])
def update_delivery_status(delivery_id):
    data = request.get_json()

    if not data or not data.get("status"):
        return jsonify({
            "error": "status is required"
        }), 400

    new_status = data["status"]

    allowed_statuses = [
        "Pending",
        "Assigned",
        "Picked Up",
        "Delivered"
    ]

    if new_status not in allowed_statuses:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": allowed_statuses
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT delivery_id, status
            FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        delivery = cursor.fetchone()

        if not delivery:
            return jsonify({
                "error": "Delivery not found"
            }), 404

        current_status = delivery["status"]

        valid_transitions = {
            "Pending": ["Assigned"],
            "Assigned": ["Picked Up"],
            "Picked Up": ["Delivered"],
            "Delivered": []
        }

        if new_status not in valid_transitions[current_status]:
            return jsonify({
                "error": f"Cannot change status from {current_status} to {new_status}"
            }), 400

        cursor.execute("""
            UPDATE deliveries
            SET status = %s
            WHERE delivery_id = %s
        """, (new_status, delivery_id))

        connection.commit()

        return jsonify({
            "message": "Delivery status updated successfully",
            "delivery_id": delivery_id,
            "previous_status": current_status,
            "status": new_status
        })

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# QR CONFIRM DELIVERY
# ---------------------------------------------------

@app.route("/api/deliveries/<int:delivery_id>/qr-confirm", methods=["POST"])
def qr_confirm_delivery(delivery_id):
    data = request.get_json()

    if not data or not data.get("qr_code") or not data.get("rider_id"):
        return jsonify({
            "error": "qr_code and rider_id are required"
        }), 400

    submitted_code = data["qr_code"]
    rider_id = data["rider_id"]

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT delivery_id, status, rider_id, qr_code,
                   customer_phone, customer_name
            FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        delivery = cursor.fetchone()

        if not delivery:
            return jsonify({
                "error": "Delivery not found"
            }), 404

        # Confirm this rider is actually the one assigned
        if delivery["rider_id"] != rider_id:
            return jsonify({
                "error": "This rider is not assigned to this delivery"
            }), 403

        current_status = delivery["status"]

        # Only a delivery sitting at 'Picked Up' can be QR-confirmed
        if current_status != "Picked Up":
            return jsonify({
                "error": f"Cannot QR-confirm a delivery with status '{current_status}'. "
                         f"Delivery must be 'Picked Up' first."
            }), 400

        # Check the code matches
        if not delivery["qr_code"] or submitted_code != delivery["qr_code"]:
            return jsonify({
                "error": "QR code does not match this delivery",
                "result": "fail"
            }), 409

        # Success — advance status to Delivered
        cursor.execute("""
            UPDATE deliveries
            SET status = 'Delivered',
                qr_scanned_at = NOW()
            WHERE delivery_id = %s
        """, (delivery_id,))

        connection.commit()

        # Notify the customer via SMS (stub - see sms_service.py)
        send_sms(
            delivery["customer_phone"],
            f"Hi {delivery['customer_name']}, your Reflex delivery has "
            f"been confirmed as delivered. Thank you!"
        )

        return jsonify({
            "message": "Delivery confirmed via QR scan",
            "delivery_id": delivery_id,
            "previous_status": current_status,
            "status": "Delivered",
            "result": "success"
        })

    except Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
