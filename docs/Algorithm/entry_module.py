"""
Entry Lane Control Module (Objective 2)
Records plate number, entry time and allocated bay; rejects a plate
that is already parked (DuplicateEntryError) before touching a slot.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from database import get_connection
from slot_manager import allocate_slot
from exception_handler import DuplicateEntryError, log_event

entry_bp = Blueprint("entry", __name__)


def _plate_already_active(plate_number):
    conn = get_connection()
    row = conn.execute(
        "SELECT entry_id FROM vehicles WHERE plate_number=? AND status='ACTIVE'", (plate_number,)
    ).fetchone()
    conn.close()
    return row is not None


def register_arrival(plate_number):
    plate_number = plate_number.strip().upper()
    if _plate_already_active(plate_number):
        raise DuplicateEntryError(f"{plate_number} is already checked in.")

    slot_id, bay_number = allocate_slot()          # raises SlotUnavailableError if full
    entry_time = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO vehicles (plate_number, slot_id, entry_time, status) VALUES (?, ?, ?, 'ACTIVE')",
        (plate_number, slot_id, entry_time),
    )
    conn.commit()
    entry_id = cur.lastrowid
    conn.close()

    log_event("VEHICLE_ENTRY", f"{plate_number} -> bay {bay_number} at {entry_time}")
    return {"entry_id": entry_id, "plate_number": plate_number, "bay_number": bay_number, "entry_time": entry_time}


@entry_bp.route("/entry", methods=["GET", "POST"])
def entry_view():
    if request.method == "GET":
        return render_template("entry.html")
    plate_number = request.form.get("plate_number", "")
    ticket = register_arrival(plate_number)
    return render_template("entry.html", ticket=ticket)


@entry_bp.route("/api/entry", methods=["POST"])
def api_entry():
    data = request.get_json(force=True)
    ticket = register_arrival(data.get("plate_number", ""))
    return jsonify(ticket), 201
