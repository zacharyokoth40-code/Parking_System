"""
Payment Collection Module (Objective 4)
One process_payment() entry point for all three channels. Real deployments
swap _confirm_mpesa/_confirm_card for a live STK Push / card-terminal
callback; the rest of the system only depends on the CONFIRMED/FAILED
outcome, not on how it was obtained.
"""
import random
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import get_connection
from exception_handler import PaymentFailedError

payment_bp = Blueprint("payment", __name__)

VALID_METHODS = {"MPESA", "CARD", "CASH"}


def _confirm_mpesa(phone_number):
    # Simulated STK push confirmation (90% success rate)
    return random.random() < 0.9


def _confirm_card():
    return random.random() < 0.95


def process_payment(entry_id, amount, method, phone_number=None):
    method = method.upper()
    if method not in VALID_METHODS:
        raise PaymentFailedError(f"Unsupported payment method: {method}")

    if method == "MPESA":
        confirmed = _confirm_mpesa(phone_number)
    elif method == "CARD":
        confirmed = _confirm_card()
    else:  # CASH is confirmed by the attendant at point of collection
        confirmed = True

    status = "CONFIRMED" if confirmed else "FAILED"
    receipt_no = f"RCPT-{uuid.uuid4().hex[:8].upper()}" if confirmed else None
    timestamp = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (entry_id, amount, method, status, receipt_no, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (entry_id, amount, method, status, receipt_no, timestamp),
    )
    conn.commit()
    conn.close()

    if not confirmed:
        raise PaymentFailedError(f"{method} payment could not be confirmed. Please retry.")

    return {"status": status, "receipt_no": receipt_no, "amount": amount, "method": method}


@payment_bp.route("/api/pay", methods=["POST"])
def api_pay():
    data = request.get_json(force=True)
    result = process_payment(
        entry_id=data["entry_id"],
        amount=data["amount"],
        method=data["method"],
        phone_number=data.get("phone_number"),
    )
    return jsonify(result), 200
