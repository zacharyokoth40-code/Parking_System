"""
Database Module
Owns the SQLite connection and schema. Rates live in a table (not code)
so management can change fees without a software change (Objective 5).
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "parking.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(total_bays=20):
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS slots (
        slot_id INTEGER PRIMARY KEY,
        bay_number TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'FREE'   -- FREE | OCCUPIED | OUT_OF_SERVICE
    );

    CREATE TABLE IF NOT EXISTS vehicles (
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL,
        slot_id INTEGER NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE | COMPLETED
        FOREIGN KEY (slot_id) REFERENCES slots(slot_id)
    );

    CREATE TABLE IF NOT EXISTS rates (
        rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tier_order INTEGER NOT NULL,   -- ordering for tier lookup
        max_minutes INTEGER,           -- NULL = "and above" (open-ended tier)
        amount REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transactions (
        txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        method TEXT NOT NULL,          -- MPESA | CARD | CASH
        status TEXT NOT NULL,          -- PENDING | CONFIRMED | FAILED
        receipt_no TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (entry_id) REFERENCES vehicles(entry_id)
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    # Seed bays only once
    cur.execute("SELECT COUNT(*) FROM slots")
    if cur.fetchone()[0] == 0:
        for i in range(1, total_bays + 1):
            cur.execute("INSERT INTO slots (bay_number, status) VALUES (?, 'FREE')", (f"B{i:02d}",))

    # Seed default rate card (from the brief) only once
    cur.execute("SELECT COUNT(*) FROM rates")
    if cur.fetchone()[0] == 0:
        default_tiers = [
            (1, 30, 0),
            (2, 120, 50),
            (3, 240, 100),
            (4, 360, 300),
            (5, None, 500),   # over 6 hours
        ]
        cur.executemany(
            "INSERT INTO rates (tier_order, max_minutes, amount) VALUES (?, ?, ?)",
            default_tiers,
        )

    conn.commit()
    conn.close()
