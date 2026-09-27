"""
Slot Monitoring, Display & Allocation Module
Data structures:
- Hash map (dict) slot_id -> Slot: O(1) status lookup/update for the
  live display board, which polls this on every refresh.
- Min-heap of free slot_ids: allocate_slot() always returns the
  lowest-numbered free bay (nearest to the entry lane) in O(log n),
  instead of scanning every bay (O(n)) on each car arrival.
"""
import heapq
from flask import Blueprint, jsonify, render_template
from database import get_connection
from exception_handler import SlotUnavailableError

slot_bp = Blueprint("slot", __name__)

_free_heap = []          # min-heap of free slot_ids
_slot_cache = {}         # slot_id -> dict(bay_number, status)  -- the hash map
_loaded = False


def _load_cache():
    global _loaded
    conn = get_connection()
    rows = conn.execute("SELECT * FROM slots ORDER BY slot_id").fetchall()
    conn.close()
    _slot_cache.clear()
    _free_heap.clear()
    for row in rows:
        _slot_cache[row["slot_id"]] = {"bay_number": row["bay_number"], "status": row["status"]}
        if row["status"] == "FREE":
            heapq.heappush(_free_heap, row["slot_id"])
    _loaded = True


def _ensure_loaded():
    if not _loaded:
        _load_cache()


def allocate_slot():
    """Pop the nearest free bay. Raises if the park is full."""
    _ensure_loaded()
    while _free_heap:
        slot_id = heapq.heappop(_free_heap)
        if _slot_cache[slot_id]["status"] == "FREE":
            _slot_cache[slot_id]["status"] = "OCCUPIED"
            conn = get_connection()
            conn.execute("UPDATE slots SET status='OCCUPIED' WHERE slot_id=?", (slot_id,))
            conn.commit()
            conn.close()
            return slot_id, _slot_cache[slot_id]["bay_number"]
    raise SlotUnavailableError("No free bay available. Parking is full.")


def release_slot(slot_id):
    _ensure_loaded()
    _slot_cache[slot_id]["status"] = "FREE"
    heapq.heappush(_free_heap, slot_id)
    conn = get_connection()
    conn.execute("UPDATE slots SET status='FREE' WHERE slot_id=?", (slot_id,))
    conn.commit()
    conn.close()


def get_all_slots():
    _ensure_loaded()
    return [{"slot_id": sid, **data} for sid, data in sorted(_slot_cache.items())]


def get_counts():
    slots = get_all_slots()
    free = sum(1 for s in slots if s["status"] == "FREE")
    return {"total": len(slots), "free": free, "occupied": len(slots) - free}


# ---- routes: the live display board (Objective 1) ----

@slot_bp.route("/display")
def display_board():
    return render_template("display_board.html")


@slot_bp.route("/api/slots")
def api_slots():
    return jsonify({"slots": get_all_slots(), "counts": get_counts()})
