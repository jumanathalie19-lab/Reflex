from flask import Flask, render_template

from assignmentendpoints import assignment_bp
from statusendpoint import status_bp
from qr import qr_bp
from deliveryendpoint import delivery_bp


app = Flask(__name__)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app.config["JSON_SORT_KEYS"] = False


# ============================================================
# REGISTER API BLUEPRINTS
# ============================================================
#
# All API endpoints will start with:
#
#     /api
#
# Examples:
#     POST  /api/deliveries
#     GET   /api/deliveries/open
#     GET   /api/riders
#     POST  /api/deliveries/1/assign
#     GET   /api/deliveries/mine
#     PATCH /api/deliveries/1/status
#     POST  /api/deliveries/1/qr-confirm
#
# ============================================================

app.register_blueprint(
    delivery_bp,
    url_prefix="/api"
)

app.register_blueprint(
    assignment_bp,
    url_prefix="/api"
)

app.register_blueprint(
    status_bp,
    url_prefix="/api"
)

app.register_blueprint(
    qr_bp,
    url_prefix="/api"
)


# ============================================================
# FRONTEND PAGES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/retailer")
def retailer_page():
    return render_template("retailer.html")


@app.route("/dispatcher")
def dispatcher_page():
    return render_template("dispatcher.html")


@app.route("/rider")
def rider_page():
    return render_template("rider.html")


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )