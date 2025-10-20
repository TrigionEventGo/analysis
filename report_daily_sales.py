# report_daily_sales.py
import os, sys, csv, json
from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import requests
import time
import base64
from sib_api_v3_sdk.rest import ApiException
from sib_api_v3_sdk import SendSmtpEmail, SendSmtpEmailAttachment, SendSmtpEmailTo, SendSmtpEmailSender, Configuration, TransactionalEmailsApi

API_BASE = os.getenv("EVENTIX_BASE", "https://api.openticket.tech")
COMPANY_GUID = os.environ["EVENTIX_COMPANY_GUID"]
# OAuth2 tokens
ACCESS_TOKEN = os.environ["EVENTIX_ACCESS_TOKEN"]
REFRESH_TOKEN = os.environ["EVENTIX_REFRESH_TOKEN"]
CLIENT_ID = os.environ["EVENTIX_CLIENT_ID"]
CLIENT_SECRET = os.environ["EVENTIX_CLIENT_SECRET"]
# Token storage file (for persistence across runs)
TOKEN_FILE = Path("eventix_tokens.json")

# Brevo (Sendinblue) configuration
BREVO_API_KEY = os.environ["BREVO_API_KEY"]
MAIL_FROM = os.environ["MAIL_FROM"]
MAIL_TO = os.environ["MAIL_TO"]        # comma-gescheiden lijst kan ook

NL = ZoneInfo("Europe/Amsterdam")

def load_tokens():
    """Load tokens from file if they exist and are not expired"""
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                # Check if access token is still valid (with 1 hour buffer)
                if tokens.get('expires_at', 0) > time.time() + 3600:
                    return tokens.get('access_token'), tokens.get('refresh_token')
        except Exception:
            pass
    return None, None

def save_tokens(access_token, refresh_token, expires_in):
    """Save tokens to file with expiration time"""
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_at': time.time() + expires_in
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def load_refresh_token():
    """Return the most recent refresh token (file first, then env)."""
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                rt = tokens.get('refresh_token')
                if rt:
                    return rt
        except Exception:
            pass
    return REFRESH_TOKEN

def refresh_access_token():
    """Refresh the access token using refresh token"""
    url = "https://auth.openticket.tech/tokens"  # Official Eventix OAuth2 endpoint
    # Always prefer the latest refresh token from file, as Eventix uses one-time refresh tokens
    refresh_token = load_refresh_token()
    form = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    
    try:
        # OAuth2 token endpoints expect application/x-www-form-urlencoded
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        response = requests.post(url, data=form, headers=headers, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        
        new_access_token = token_data['access_token']
        new_refresh_token = token_data.get('refresh_token', refresh_token)  # Keep old if not provided
        expires_in = token_data.get('expires_in', 259200)  # 3 days default
        
        # Save new tokens
        save_tokens(new_access_token, new_refresh_token, expires_in)
        return new_access_token
        
    except requests.HTTPError as e:
        try:
            err_text = e.response.text if e.response is not None else str(e)
        except Exception:
            err_text = str(e)
        print(f"Token refresh failed ({getattr(e.response, 'status_code', '?')}): {err_text}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Token refresh failed: {e}", file=sys.stderr)
        return None

def get_valid_access_token():
    """Get an access token without proactive refresh.

    Preference: valid token from file -> ENV access token.
    Actual refresh happens only upon 401 responses.
    """
    # Prefer a still-valid token saved on disk
    access_token, _ = load_tokens()
    if access_token:
        return access_token

    # Fall back to the provided ENV access token by default
    return ACCESS_TOKEN

def nl_yesterday_range():
    today_nl = datetime.now(NL).date()
    y = today_nl - timedelta(days=1)
    start = datetime(y.year, y.month, y.day, 0, 0, 0, tzinfo=NL)
    end   = datetime(y.year, y.month, y.day, 23, 59, 59, tzinfo=NL)
    return start.isoformat(), end.isoformat(), y

def fetch_orders_via_orders_api(start_iso, end_iso):
    """Gebruik het werkende orders endpoint met pagination."""
    url = f"{API_BASE}/orders"
    
    # Get valid access token
    access_token = get_valid_access_token()
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {access_token}",
        "Company": COMPANY_GUID,
        "X-Authorization-By-OpenTicket": "1",
        "User-Agent": "Eventix-Daily-Report/1.0"
    }
    
    all_orders = []
    page = 1
    per_page = 100  # Haal meer orders per pagina op
    
    while True:
        params = {
            "page": page,
            "per_page": per_page,
            "include": "payments,shop,tickets_count",
            "append": "events",
            "created_at": f"{start_iso},{end_iso}"  # Datum filter
        }
        
        try:
            r = requests.get(url, params=params, headers=headers, timeout=60)
            
            # If token is expired/invalid, try to refresh and retry once
            if r.status_code == 401:
                print("Access token unauthorized (401). Trying refresh...", file=sys.stderr)
                access_token = refresh_access_token()
                if access_token:
                    headers["Authorization"] = f"Bearer {access_token}"
                    r = requests.get(url, params=params, headers=headers, timeout=60)
                else:
                    # No new token obtained; include server response for easier debugging
                    try:
                        print(f"401 response: {r.text}", file=sys.stderr)
                    except Exception:
                        pass
            
            # Raise for non-2xx after potential retry
            if r.status_code >= 400:
                try:
                    print(f"Error response ({r.status_code}): {r.text}", file=sys.stderr)
                except Exception:
                    pass
                r.raise_for_status()
            data = r.json()
            
            # Add orders from this page
            if 'data' in data and data['data']:
                all_orders.extend(data['data'])
                
                # Check if there are more pages
                if page >= data.get('last_page', 1):
                    break
                page += 1
            else:
                break
                
        except Exception as e:
            print(f"Error fetching page {page}: {e}", file=sys.stderr)
            break
    
    return {"data": all_orders}

# Fallback functie verwijderd - we gebruiken alleen het werkende orders endpoint

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
    Gebaseerd op de nieuwe orders API data structuur.
    """
    orders = []
    
    # Haal orders uit de data array
    candidates = payload.get("data", [])
    if not isinstance(candidates, list):
        return orders

    for o in candidates:
        # Order ID
        oid = o.get("guid", "")
        
        # Created at
        created = o.get("created_at", "")
        
        # Event name - uit de events object
        event_name = ""
        if "events" in o and isinstance(o["events"], dict):
            # Events is een dict met event_id: event_name
            event_names = list(o["events"].values())
            if event_names:
                event_name = event_names[0]  # Neem de eerste event naam
        
        # Currency - standaard EUR
        currency = "EUR"
        
        # Total amount - probeer verschillende velden
        total = 0.0
        
        # Probeer finn_price (inclusief service fee)
        if "finn_price" in o:
            total = float(o["finn_price"]) / 100  # Convert from cents
        # Probeer finn_value (zonder service fee)
        elif "finn_value" in o:
            total = float(o["finn_value"]) / 100  # Convert from cents
        # Probeer amount
        elif "amount" in o:
            total = float(o["amount"])
        
        # Probeer payment total als fallback
        if total == 0.0 and "payments" in o and isinstance(o["payments"], list) and o["payments"]:
            payment = o["payments"][0]  # Neem eerste payment
            if "finn_price" in payment:
                total = float(payment["finn_price"]) / 100
            elif "amount" in payment:
                total = float(payment["amount"])

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
    """Send email using Brevo API"""
    
    # Configure Brevo API
    configuration = Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY
    
    # Create API instance with configuration
    api_instance = TransactionalEmailsApi(configuration)
    
    # Prepare sender
    sender = SendSmtpEmailSender(email=MAIL_FROM, name="Eventix Daily Report")
    
    # Prepare recipients
    recipients = []
    for email in MAIL_TO.split(','):
        recipients.append(SendSmtpEmailTo(email=email.strip()))
    
    # Prepare attachments
    email_attachments = []
    for path in attachments:
        p = Path(path)
        if p.exists():
            with open(p, 'rb') as f:
                content = f.read()
                encoded_content = base64.b64encode(content).decode('utf-8')
                attachment = SendSmtpEmailAttachment(
                    content=encoded_content,
                    name=p.name
                )
                email_attachments.append(attachment)
    
    # Create email
    send_smtp_email = SendSmtpEmail(
        sender=sender,
        to=recipients,
        subject=subject,
        html_content=body.replace('\n', '<br>'),
        text_content=body,
        attachment=email_attachments if email_attachments else None
    )
    
    try:
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent successfully. Message ID: {api_response.message_id}")
    except ApiException as e:
        print(f"Error sending email: {e}")
        raise

def main():
    start_iso, end_iso, y_date = nl_yesterday_range()
    try:
        payload = fetch_orders_via_orders_api(start_iso, end_iso)
    except Exception as e:
        print("Kon orders niet ophalen:", e, file=sys.stderr)
        # Stuur een foutmelding e-mail
        try:
            error_subject = f"Fout in verkooprapport {y_date.isoformat()}"
            error_body = f"Er is een fout opgetreden bij het ophalen van orders voor {y_date.isoformat()}:\n\n{str(e)}\n\nControleer de Eventix API credentials en probeer opnieuw."
            send_mail(error_subject, error_body, [])
        except:
            pass  # Als e-mail ook faalt, negeer dan
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
    
    try:
        send_mail(subject, body, [csv_path])
        print("Rapport verstuurd:", csv_path)
    except Exception as e:
        print("Fout bij versturen e-mail:", e, file=sys.stderr)
        print("CSV wel aangemaakt:", csv_path)

if __name__ == "__main__":
    main()
