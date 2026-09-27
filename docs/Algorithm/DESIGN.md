# SmartBay Parking System — Design Notes

Web-based modern parking system for a client in Kenya. Built in Python (Flask) +
SQLite. Run with `python app.py`, open `http://localhost:5000`.

## Modules (one file each, matches project scope)

| Module | File | Responsibility |
|---|---|---|
| Entry lane control | `entry_module.py` | Record plate, time, allocated bay on arrival; blocks duplicate check-ins |
| Slot monitoring & display | `slot_manager.py` | Live board data, hash-map + heap slot allocation |
| Slot allocation | `slot_manager.py` (`allocate_slot`) | Nearest-free-bay assignment |
| Duration & fee computation | `fee_calculator.py` | Reads dynamic rate tiers, computes minutes parked and amount due |
| Payment collection | `payment_module.py` | M-Pesa / card / cash confirmation |
| Exit & barrier control | `exit_module.py` | Quote fee, verify confirmed payment, open barrier, free bay |
| Exception handling | `exception_handler.py` | Custom exceptions, audit logging, JSON error responses |
| Administrative reporting | `reporting.py` | Revenue/VAT summary, CSV export, rate editor |
| Data containers | `models.py` | Dataclasses shared across modules |
| Persistence | `database.py` | SQLite schema + connection |

## Algorithms

**Slot allocation (best-fit / nearest bay):** free slot IDs are kept in a
min-heap. `allocate_slot()` pops the smallest ID in O(log n) — always the
nearest bay to the entry lane — instead of scanning every bay (O(n)) on each
arrival. `release_slot()` pushes the freed ID back, O(log n).

**Duration & fee computation:** `duration = exit_time - entry_time` in
minutes; fee tiers are stored in DB order and scanned once (≤5 tiers, so
O(1) in practice) until `duration <= tier.max_minutes`.

**Exit/payment/barrier sequencing:** a state machine — `ACTIVE → (quote) →
PENDING payment → CONFIRMED/FAILED → (if CONFIRMED) barrier opens → slot
released → vehicle COMPLETED`. The barrier module re-verifies a CONFIRMED
transaction exists before opening, so no other code path can bypass payment.

**Exception handling:** every failure (full park, duplicate entry, unknown
plate, failed payment, barrier fault) is a typed exception caught by one
Flask error handler, written to `audit_log`, and returned as JSON — nothing
fails silently, and attendants get a specific reason.

## Data structures & why

- **Hash map** (`_slot_cache`, dict keyed by `slot_id`): O(1) status
  lookup/update for the live board, which is polled every few seconds.
- **Min-heap** (`_free_heap`): O(log n) nearest-free-bay allocation/release
  instead of a linear scan.
- **Relational tables** (SQLite) for everything that must persist and be
  queried/joined: vehicles, transactions, rates, audit log.
- **Dataclasses** (`models.py`): typed, dependency-free containers passed
  between modules.

## Dynamic database design

```
slots(slot_id PK, bay_number, status)
vehicles(entry_id PK, plate_number, slot_id FK, entry_time, exit_time, status)
rates(rate_id PK, tier_order, max_minutes NULL=open-ended, amount)
transactions(txn_id PK, entry_id FK, amount, method, status, receipt_no, timestamp)
audit_log(log_id PK, event_type, details, timestamp)
```

`rates` is the "dynamic" part: management edits tier amounts via
`/admin/rates` — no code change or redeploy (Objective 5). Every confirmed
transaction is queryable by method/date for VAT and reconciliation
(Objective 6) via `/admin` and the CSV export.

## In scope / out of scope

In scope: entry lane control, slot monitoring & display, slot allocation,
duration/fee computation, payment collection, exit barrier control,
exception handling, administrative reporting.

Out of scope (this phase): online pre-booking, valet operations, loyalty
scheme integration, automated number-plate blacklisting.
