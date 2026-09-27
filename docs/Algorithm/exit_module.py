"""
Exit & Barrier Control Module (Objectives 3 & 4)
Barrier only opens once a CONFIRMED transaction exists for the entry_id -
open_barrier() re-checks this itself so nothing else in the codebase can
open it on an unpaid ticket by mistake.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from database import get_connection
from fee_calculator import compute_duration_minutes, calculate_fee
from slot_manager import release_slot
from exception_handler import VehicleNotFoundError, PaymentFailedError, log_event

exit_bp = Blueprint("exit", __name__)


def find_active_vehicle(plate_number):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM vehicles WHERE plate_number=? AND status='ACTIVE'", (plate_number.strip().upper(),)
    ).fetchone()
    conn.close()
    if not row:
        raise VehicleNotFoundError(f"No active entry found for {plate_number.upper()}.")
    return row


def quote_exit(plate_number):
    """Duration + fee due, shown to the driver before payment."""
    vehicle = find_active_vehicle(plate_number)
    duration = compute_duration_minutes(vehicle["entry_time"])
    fee = calculate_fee(duration)
    return {"entry_id": vehicle["entry_id"], "plate_number": vehicle["plate_number"],
            "slot_id": vehicle["slot_id"], "duration_minutes": duration, "amount_due": fee}


def _latest_confirmed_transaction(entry_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM transactions WHERE entry_id=? AND status='CONFIRMED' ORDER BY txn_id DESC LIMIT 1",
        (entry_id,),
    ).fetchone()
    conn.close()
    return row


def open_barrier(entry_id):
    """Only opens if a confirmed payment exists. Then frees the bay."""
    txn = _latest_confirmed_transaction(entry_id)
    if not txn:
        raise PaymentFailedError("Cannot open barrier: payment not confirmed.")

    conn = get_connection()
    vehicle = conn.execute("SELECT * FROM vehicles WHERE entry_id=?", (entry_id,)).fetchone()
    exit_time = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE vehicles SET exit_time=?, status='COMPLETED' WHERE entry_id=?", (exit_time, entry_id)
    )
    conn.commit()
    conn.close()

    release_slot(vehicle["slot_id"])
    log_event("BARRIER_OPEN", f"entry_id={entry_id} plate={vehicle['plate_number']} receipt={txn['receipt_no']}")
    return {"barrier": "OPEN", "exit_time": exit_time, "receipt_no": txn["receipt_no"]}


@exit_bp.route("/exit", methods=["GET", "POST"])
def exit_view():
    quote = None
    if request.method == "POST":
        quote = quote_exit(request.form.get("plate_number", ""))
    return render_template("exit.html", quote=quote)


@exit_bp.route("/api/exit/quote", methods=["POST"])
def api_quote():
    data = request.get_json(force=True)
    return jsonify(quote_exit(data.get("plate_number", "")))


@exit_bp.route("/api/exit/open-barrier", methods=["POST"])
def api_open_barrier():
    data = request.get_json(force=True)
    return jsonify(open_barrier(data["entry_id"]))
