# SmartBay Parking System

Modern web-based parking system: live slot display, automated entry/exit,
M-Pesa/card/cash payment, barrier control, dynamic rates, admin reporting.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

- **Display Board** `/display` — live bay availability, auto-refreshes.
- **Entry** `/entry` — record a vehicle's arrival.
- **Exit** `/exit` — get fee quote, pay, open barrier.
- **Admin** `/admin` — revenue/VAT summary, audit trail, `/admin/rates` to
  change fees without touching code.

Rates ship with the brief's defaults: free ≤30 min, KShs.50 ≤2h,
KShs.100 ≤4h, KShs.300 ≤6h, KShs.500 beyond — editable anytime in
`/admin/rates`.

See `DESIGN.md` for module breakdown, algorithms, data structures and DB
schema.

## Project layout

```
app.py                 # wires modules together, entry point
database.py            # schema + connection
models.py              # dataclasses
slot_manager.py        # slot monitoring, display, allocation
entry_module.py         # entry lane control
exit_module.py          # exit + barrier control
fee_calculator.py       # duration & fee computation
payment_module.py       # M-Pesa / card / cash
exception_handler.py    # custom exceptions + audit logging
reporting.py             # admin dashboard, rates editor, CSV export
templates/               # Jinja2 HTML views
static/                  # CSS + JS (display board polling, payment flow)
```
