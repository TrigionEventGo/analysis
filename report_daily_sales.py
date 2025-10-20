# report_daily_sales.py
import os, sys, csv, json, smtplib, ssl, mimetypes
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import requests

API_BASE = os.getenv("EVENTIX_BASE", "https://api.eventix.io")
COMPANY_GUID = os.environ["EVENTIX_COMPANY_GUID"]
TOKEN = os.environ["EVENTIX_TOKEN"]  # Bearer token of andere header (zie Eventix)
MAIL_FROM = os.environ["MAIL_FROM"]
MAIL_TO = os.environ["MAIL_TO"]        # comma-gescheiden lijst kan ook
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

NL = ZoneInfo("Europe/Amsterdam")

def nl_yesterday_range():
    today_nl = datetime.now(NL).date()
    y = today_nl - timedelta(days=1)
    start = datetime(y.year, y.month, y.day, 0, 0, 0, tzinfo=NL)
    end   = datetime(y.year, y.month, y.day, 23, 59, 59, tzinfo=NL)
    return start.isoformat(), end.isoformat(), y

def fetch_orders_via_statistics_orders(start_iso, end_iso):
    """Probeer de 'statistics/orders/{company_guid}'-endpoint eerst."""
    url = f"{API_BASE}/statistics/orders/{COMPANY_GUID}"
    # Body volgt de collectie (offset/limit/timeunit/range_applies_to/start/end/filters/etc.).
    body = {
        "offset": 0,
        "limit": 1000,          # als je >1000 verwacht: in pages lopen
        "timeunit": "day",
        "range_applies_to": "created_at",   # pas aan naar 'updated_at' indien gewenst
        "start": start_iso,
        "end": end_iso,
        "filters": "",
        "events": "",
        "sorting": "",
        "purchase_channels": ["api","shop"]
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }
    r = requests.post(url, json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()

def fetch_orders_via_search(start_iso, end_iso):
    """Fallback: 'statistics/search' geeft een lijst orders (max 1000)."""
    url = f"{API_BASE}/statistics/search"
    # Veel implementaties accepteren een 'filters' string; als jouw tenant een ander
    # formaat vereist, pas dit aan (Eventix kan per omgeving verschillen).
    body = {
        "search": "",
        "limit": 1000,
        "offset": 0,
        "filters": f"created_at>={start_iso} AND created_at<={end_iso}",
        "events": "",
        "sorting": "created_at:asc"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }
    r = requests.post(url, json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()

def try_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def extract_orders(payload):
    """
    Normaliseer naar lijst van orders met minimaal:
    id, created_at, event_name, currency, total (float)
    We proberen een paar veel-voorkomende sleutelvarianten.
    """
    orders = []
    # vaak zitten resultaten onder 'data', 'orders', of direct in payload
    candidates = []
    for k in ("orders", "data", "hits", "results"):
        v = payload.get(k)
        if isinstance(v, list):
            candidates = v
            break
    if not candidates and isinstance(payload, list):
        candidates = payload

    for o in candidates:
        oid = o.get("id") or o.get("guid") or o.get("_id") or ""
        created = o.get("created_at") or o.get("created") or o.get("@timestamp") or ""
        event_name = (
            try_get(o, "event", "name")
            or try_get(o, "event_name")
            or try_get(o, "event", "title")
            or ""
        )
        currency = (
            try_get(o, "currency")
            or try_get(o, "total", "currency")
            or "EUR"
        )
        # total proberen op verschillende plekken/keys
        total = (
            try_get(o, "total")
            or try_get(o, "amount_total")
            or try_get(o, "grand_total")
            or try_get(o, "revenue")
            or 0
        )
        try:
            total = float(total)
        except Exception:
            total = 0.0

        orders.append({
            "order_id": oid,
            "created_at": created,
            "event_name": event_name,
            "currency": currency,
            "total": total
        })
    return orders

def write_csv(orders, y_date):
    outdir = Path("output"); outdir.mkdir(exist_ok=True)
    fn = outdir / f"sales_{y_date.isoformat()}.csv"
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["order_id","created_at","event_name","currency","total"])
        w.writeheader()
        for row in orders:
            w.writerow(row)
    return fn

def summarize(orders):
    total_orders = len(orders)
    revenue = sum(o["total"] for o in orders)
    return total_orders, revenue

def send_mail(subject, body, attachments):
    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    for path in attachments:
        p = Path(path)
        ctype, _ = mimetypes.guess_type(p.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as s:
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def main():
    start_iso, end_iso, y_date = nl_yesterday_range()
    try:
        payload = fetch_orders_via_statistics_orders(start_iso, end_iso)
    except Exception as e1:
        # fallback naar 'statistics/search'
        try:
            payload = fetch_orders_via_search(start_iso, end_iso)
        except Exception as e2:
            print("Kon orders niet ophalen:", e1, e2, file=sys.stderr)
            sys.exit(1)

    orders = extract_orders(payload)
    csv_path = write_csv(orders, y_date)
    n, revenue = summarize(orders)
    subject = f"Verkooprapport {y_date.isoformat()} – {n} orders, €{revenue:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.')
    body = (
        f"Goedemorgen,\n\n"
        f"Hierbij het verkooprapport voor {y_date.isoformat()} (NL-tijd):\n"
        f"- Aantal orders: {n}\n"
        f"- Omzet: €{revenue:,.2f}\n\n"
        f"In de bijlage vind je de CSV met details.\n"
        f"Periode: {start_iso} t/m {end_iso}\n"
    )
    send_mail(subject, body, [csv_path])
    print("Rapport verstuurd:", csv_path)

if __name__ == "__main__":
    main()
