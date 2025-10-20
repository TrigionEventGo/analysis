# Eventix Dagelijks Verkooprapport

Dit systeem haalt automatisch dagelijks je verkoopgegevens op van Eventix en stuurt deze per e-mail door als CSV-rapport.

## Wat het doet

- **Bepaalt gisteren** in Nederlandse tijdzone (Europe/Amsterdam)
- **Haalt orders op** via Eventix API (`GET /orders` met pagination en datum filtering)
- **Genereert CSV** met orderdetails (ID, datum, event, bedrag)
- **Stuurt e-mail** met samenvatting en CSV-bijlage
- **Draait automatisch** elke ochtend om 07:30 NL-tijd via GitHub Actions

## Setup

### 1. GitHub Secrets instellen

Ga naar je GitHub repository → Settings → Secrets and variables → Actions en voeg deze secrets toe:

#### Eventix OAuth2 API
- `EVENTIX_COMPANY_GUID` - Jouw company GUID bij Eventix
- `EVENTIX_ACCESS_TOKEN` - Jouw OAuth2 access token (3 dagen geldig)
- `EVENTIX_REFRESH_TOKEN` - Jouw OAuth2 refresh token (1 jaar geldig)
- `EVENTIX_CLIENT_ID` - Jouw OAuth2 client ID
- `EVENTIX_CLIENT_SECRET` - Jouw OAuth2 client secret

#### E-mail configuratie (Brevo)
- `BREVO_API_KEY` - Je Brevo API key voor e-mail verzending
- `MAIL_FROM` - Afzender e-mailadres (bijv. rapport@jouwdomein.nl)
- `MAIL_TO` - Ontvanger(s), bijv. `sales@bedrijf.nl` of `naam@bedrijf.nl,team@bedrijf.nl`

### 2. Lokale test

```bash
# Dependencies installeren
pip install -r requirements.txt

# Environment variables instellen (Windows)
set EVENTIX_COMPANY_GUID=jouw-guid
set EVENTIX_ACCESS_TOKEN=jouw-access-token
set EVENTIX_REFRESH_TOKEN=jouw-refresh-token
set EVENTIX_CLIENT_ID=jouw-client-id
set EVENTIX_CLIENT_SECRET=jouw-client-secret
set BREVO_API_KEY=jouw-brevo-api-key
set MAIL_FROM=rapport@jouwdomein.nl
set MAIL_TO=ontvanger@bedrijf.nl

# Script uitvoeren
python report_daily_sales.py
```

#### OAuth2 Token Management
Het script beheert automatisch je OAuth2 tokens via de officiële Eventix endpoint:
- **Access tokens** worden automatisch ververst wanneer ze verlopen (3 dagen)
- **Refresh tokens** worden opgeslagen en hergebruikt (365 dagen geldig, éénmalig gebruik)
- **Token bestand** (`eventix_tokens.json`) wordt lokaal opgeslagen voor persistentie
- **Endpoint**: `https://auth.openticket.tech/tokens` (officiële Eventix OAuth2 service)
- **Orders API**: `https://api.openticket.tech/orders` (werkende orders endpoint)

### 3. GitHub Actions

Het systeem draait automatisch via GitHub Actions:
- **Wintertijd**: 06:30 UTC (07:30 NL-tijd)
- **Zomertijd**: 05:30 UTC (07:30 NL-tijd)
- **Handmatig**: Via "Actions" tab → "Dagelijks verkooprapport" → "Run workflow"

## Output

### CSV bestand
Elke dag wordt een CSV aangemaakt in `output/sales_YYYY-MM-DD.csv` met:
- `order_id` - Order ID van Eventix
- `created_at` - Aanmaakdatum
- `event_name` - Naam van het evenement
- `currency` - Valuta (meestal EUR)
- `total` - Totaalbedrag

### E-mail
- Onderwerp: "Verkooprapport YYYY-MM-DD – X orders, €Y,YY"
- Inhoud: Samenvatting met aantal orders en omzet
- Bijlage: CSV bestand met alle details

## Aanpassingen

### Meer dan 1000 orders per dag?
Voeg paging toe door de `limit` en `offset` parameters aan te passen in de `fetch_orders_via_statistics_orders()` functie.

### Andere tijdsfilter?
Pas `range_applies_to` aan naar `updated_at` in plaats van `created_at` voor gewijzigde orders.

### Specifieke events?
Voeg event GUIDs toe aan de `events` parameter in de API call.

### Andere SMTP provider?
De code ondersteunt alle SMTP providers met SSL/TLS. Populaire opties:
- **Gmail**: smtp.gmail.com:465
- **SendGrid**: smtp.sendgrid.net:465
- **Outlook**: smtp-mail.outlook.com:587 (STARTTLS)

## Troubleshooting

### API foutmeldingen
- Controleer of je OAuth2 tokens geldig zijn (`EVENTIX_ACCESS_TOKEN`, `EVENTIX_REFRESH_TOKEN`)
- Verificeer je `EVENTIX_COMPANY_GUID`
- Check of de API endpoints beschikbaar zijn
- Controleer of je `EVENTIX_CLIENT_ID` en `EVENTIX_CLIENT_SECRET` correct zijn

### OAuth2 Token Problemen
- **Refresh token verlopen**: Na 365 dagen moet je opnieuw autoriseren via de Eventix dashboard
- **Refresh token eenmalig gebruik**: Elke refresh token kan maar één keer gebruikt worden
- **Access token verlopen**: Wordt automatisch ververst, maar kan 401 errors geven tijdens refresh

### E-mail problemen (Brevo)
- Controleer of je Brevo API key geldig is
- Verificeer of het afzender e-mailadres geverifieerd is in Brevo
- Controleer Brevo quota en limieten

### Timing issues
- Het script gebruikt Nederlandse tijdzone
- GitHub Actions draait in UTC, vandaar de verschillende cron schedules voor zomer/winter

## Bestandsstructuur

```
Event-Go/
├── report_daily_sales.py    # Hoofdscript met OAuth2 ondersteuning
├── requirements.txt         # Python dependencies
├── README.md               # Deze documentatie
├── output/                 # CSV bestanden
│   └── .gitkeep
├── eventix_tokens.json     # OAuth2 token opslag (wordt automatisch aangemaakt)
└── .github/
    └── workflows/
        └── cron.yml        # GitHub Actions workflow
```
