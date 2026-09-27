"""
Modern Parking System - Main Application
Name: SmartBay Parking System

Run with: python app.py
Then open: http://localhost:5000
"""
from flask import Flask, render_template
from database import init_db
from exception_handler import register_error_handlers
from slot_manager import slot_bp
from entry_module import entry_bp
from exit_module import exit_bp
from payment_module import payment_bp
from reporting import report_bp

app = Flask(__name__)
app.secret_key = "smartbay-dev-key"

register_error_handlers(app)
app.register_blueprint(slot_bp)
app.register_blueprint(entry_bp)
app.register_blueprint(exit_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(report_bp)


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    init_db(total_bays=20)
    app.run(debug=True, host="0.0.0.0", port=5000)
