"""
Duration & Fee Computation Module
Rates are read from the `rates` table every time (Objective 5: management
can edit tiers via /admin/rates with no code change or redeploy).
Tiers are stored sorted by tier_order; a linear scan over <=5 tiers is
cheap, so no need for a fancier search structure here.
"""
from datetime import datetime
from database import get_connection


def get_rate_tiers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM rates ORDER BY tier_order ASC").fetchall()
    conn.close()
    return rows


def compute_duration_minutes(entry_time_iso, exit_time_iso=None):
    entry_dt = datetime.fromisoformat(entry_time_iso)
    exit_dt = datetime.fromisoformat(exit_time_iso) if exit_time_iso else datetime.now()
    return max(0, int((exit_dt - entry_dt).total_seconds() // 60))


def calculate_fee(duration_minutes):
    tiers = get_rate_tiers()
    for tier in tiers:
        if tier["max_minutes"] is None or duration_minutes <= tier["max_minutes"]:
            return tier["amount"]
    return tiers[-1]["amount"] if tiers else 0
