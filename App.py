from flask import Flask, render_template
from assignmentendpoints import assignment_bp
from statusendpoint import status_bp
from qr import qr_bp

app = Flask(__name__)
app.register_blueprint(assignment_bp)
app.register_blueprint(status_bp)
app.register_blueprint(qr_bp)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/retailer")
def retailer_page():
    return render_template("retailer.html")


@app.route("/rider")
def rider_page():
    return render_template("rider.html")


@app.route("/dispatcher")
def dispatcher_page():
    return render_template("dispatcher.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)