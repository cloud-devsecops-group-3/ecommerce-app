# ecommerce-app — PageTurn Books (Group 3)

Flask MVP for the bookstore side of the QR payment prototype. Implements
steps 1–5 and 11 of the process flow; steps 6–10 (choose account, confirm,
balances move) happen in the separate `banking-app`.

## Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Product listing |
| `/buy/<product_id>` | POST | Creates a PENDING order, redirects to its status page |
| `/order/<order_id>` | GET | Shows the QR code and polls for payment |
| `/qr/<order_id>.png` | GET | Generates the QR image on demand (no file storage needed) |
| `/api/orders/<order_id>` | GET | JSON status, polled by the status page |
| `/api/orders/<order_id>/paid` | POST | Callback the banking app hits once payment clears |
| `/health` | GET | Liveness/readiness probe, returns `{"status":"ok"}` |

## QR contents

The QR encodes a URL into the banking app, not raw JSON, so a phone camera
can open it directly:

```
{BANK_PUBLIC_BASE}/pay?order_id=<id>&amount=<amount>&merchant_account=<account>
```

`BANK_PUBLIC_BASE` must be a host the phone can reach (e.g.
`http://bank.<VM_IP>.nip.io` in Dev) — never `localhost` or a
Docker-internal service name.

## Environment variables

| Var | Purpose | Example (Dev) |
|---|---|---|
| `DB_HOST` | MySQL host. If unset, falls back to a local SQLite file so the app also runs with zero setup. | `mysql` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_NAME` | MySQL database | `ecommercedb` |
| `DB_USER` | MySQL user | `ecomuser` |
| `DB_PASSWORD` | MySQL password | — |
| `BANK_PUBLIC_BASE` | Banking app URL reachable by a phone | `http://bank.20-51-32-10.nip.io` |
| `MERCHANT_ACCOUNT` | Must match the MERCHANT account the banking app's seed script creates | `pageturn-books` |
| `SHOP_NAME` | Display name | `PageTurn Books` |
| `PORT` | Port for local `flask run` (Docker always uses 5000) | `5000` |

## Run locally (no Docker)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export BANK_PUBLIC_BASE=http://<VM_PUBLIC_IP>:5001
python app.py            # listens on 0.0.0.0:5000, SQLite fallback DB
```

## Run with Docker

```bash
docker build -t ecommerce-app:dev .
docker run -d --name ecom -p 5000:5000 \
  -e BANK_PUBLIC_BASE=http://<VM_PUBLIC_IP>:5001 \
  -e MERCHANT_ACCOUNT=pageturn-books \
  ecommerce-app:dev
```

## Data

Products are seeded idempotently at startup (`seed_products()` in `app.py`,
runs at import time so it also fires under gunicorn) — never inserted by
hand. `orders` starts empty and fills up as customers buy.

## Not in scope (per project brief)

- Signup/registration, admin CRUD, cart/multi-item checkout — out of scope,
  keep the app minimal.
- The banking side of the flow (accounts, `/pay`, debit/credit, the
  `/api/orders/<id>/paid` caller) lives in `banking-app`, not here.
