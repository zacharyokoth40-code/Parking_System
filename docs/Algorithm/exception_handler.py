"""
Exception Handling Module
Central place for every failure case the parking system can hit.
Every exception is logged to audit_log before being turned into a
JSON response, so nothing fails silently.
"""
from datetime import datetime
from flask import jsonify
from database import get_connection


class ParkingSystemError(Exception):
    status_code = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class SlotUnavailableError(ParkingSystemError):
    status_code = 409


class VehicleNotFoundError(ParkingSystemError):
    status_code = 404


class DuplicateEntryError(ParkingSystemError):
    status_code = 409


class PaymentFailedError(ParkingSystemError):
    status_code = 402


class BarrierFaultError(ParkingSystemError):
    status_code = 503


def log_event(event_type, details):
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (event_type, details, timestamp) VALUES (?, ?, ?)",
        (event_type, details, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def register_error_handlers(app):
    @app.errorhandler(ParkingSystemError)
    def handle_parking_error(err):
        log_event(err.__class__.__name__, err.message)
        return jsonify({"error": err.__class__.__name__, "message": err.message}), err.status_code

    @app.errorhandler(500)
    def handle_generic_error(err):
        log_event("UnhandledError", str(err))
        return jsonify({"error": "InternalError", "message": "Something went wrong. Attendant notified."}), 500
