"""
Administrative Reporting Module (Objective 6 + Objective 5's rate editor)
VAT_RATE is the only "config in code" left; everything money-related that
management needs to change day-to-day (the rate card) lives in the DB.
"""
import csv
import io
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, Response
from database import get_connection

report_bp = Blueprint("report", __name__)
VAT_RATE = 0.16  # Kenya standard VAT, inclusive


def revenue_summary():
    conn = get_connection()
    rows = conn.execute("""
        SELECT method,
               COUNT(*) AS txn_count,
               SUM(amount) AS gross
        FROM transactions
        WHERE status='CONFIRMED'
        GROUP BY method
    """).fetchall()
    conn.close()

    summary = []
    total_gross = 0
    for row in rows:
        gross = row["gross"] or 0
        vat = round(gross * VAT_RATE / (1 + VAT_RATE), 2)  # VAT portion of an inclusive price
        summary.append({"method": row["method"], "txn_count": row["txn_count"], "gross": gross, "vat": vat})
        total_gross += gross

    return {"by_method": summary, "total_gross": total_gross,
            "total_vat": round(total_gross * VAT_RATE / (1 + VAT_RATE), 2)}


def audit_trail(limit=100):
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.receipt_no, t.amount, t.method, t.status, t.timestamp, v.plate_number
        FROM transactions t JOIN vehicles v ON t.entry_id = v.entry_id
        ORDER BY t.txn_id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


@report_bp.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", summary=revenue_summary(), trail=audit_trail())


@report_bp.route("/admin/reports.csv")
def export_csv():
    rows = audit_trail(limit=100000)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["receipt_no", "plate_number", "amount", "method", "status", "timestamp"])
    for r in rows:
        writer.writerow([r["receipt_no"], r["plate_number"], r["amount"], r["method"], r["status"], r["timestamp"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=reconciliation.csv"})


# ---- dynamic rate editor (Objective 5) ----

@report_bp.route("/admin/rates", methods=["GET", "POST"])
def manage_rates():
    conn = get_connection()
    if request.method == "POST":
        rate_id = request.form.get("rate_id")
        amount = float(request.form["amount"])
        conn.execute("UPDATE rates SET amount=? WHERE rate_id=?", (amount, rate_id))
        conn.commit()
    tiers = conn.execute("SELECT * FROM rates ORDER BY tier_order").fetchall()
    conn.close()
    return render_template("admin_rates.html", tiers=tiers)
