# ecommerce-app — PageTurn Books (Group 3)

Flask MVP for the bookstore side of the QR payment prototype: browse,
add multiple books to a cart, checkout, pay via QR in the banking app.

## Architecture

Application factory (`create_app()` in `app.py`) + three blueprints, so
each concern lives in its own file instead of one large `app.py`:

| Blueprint | File | Routes |
|---|---|---|
| `catalog` | `routes/catalog.py` | `/`, `/health` |
| `cart` | `routes/cart.py` | `/cart`, `/cart/add`, `/cart/update`, `/cart/remove` |
| `orders` | `routes/orders.py` | `/checkout`, `/order/<id>`, `/qr/<id>.png`, `/api/order/<id>`, `/api/payment/callback` |

The cart lives entirely in the signed Flask session cookie (no DB writes
until checkout) — a `{product_id: quantity}` dict. Checkout snapshots
each cart line into an `OrderItem` (product name and price at time of
purchase, so later catalog price changes never rewrite past orders).

## Data model

- `Product` — the catalog
- `Order` — one per checkout, `total`, `status` (`PENDING` / `PAID` / `FAILED`), `merchant_account`, `bank_transaction_id`
- `OrderItem` — one row per distinct book in that order, snapshotted price + qty

## Registering a payment with the bank

The bank owns QR generation entirely now - this app never renders a QR
image. At checkout, after creating the local `Order`, we call:

```
POST {BANK_API_BASE}/api/payment-requests   (server-to-server)
Body: {
  "order_id": "...",
  "amount": "23.48",
  "merchant_account": "pageturn-books",
  "callback_url": ".../api/payment/callback",
  "return_url": ".../order/<order_id>"
}
Response: {
  "transaction_id": "...",
  "qr_url": "http://bank.<ip>.nip.io/qr/<transaction_id>.png"
}
```

We store `transaction_id` as `Order.bank_reference` and `qr_url` as-is,
then just `<img src="{{ order.qr_url }}">` it on the status page.
`BANK_API_BASE` is server-to-server, so a Docker-internal hostname (e.g.
`http://banking:5001`) works fine — unlike the QR URL, nothing here needs
to be phone-reachable, since the bank returns its own fully-qualified,
phone-reachable `qr_url`.

If the bank is unreachable, times out, or returns something we can't
parse, the order is marked `FAILED` immediately rather than left stuck
in `PENDING` with no QR to show.

## The payment callback

`POST /api/payment/callback` is what the banking app calls once it has
settled the transaction on its own side:

```json
{ "order_id": "...", "status": "PAID", "transaction_id": "..." }
```

This app never trusts the callback for *how much* was paid or *who* the
merchant is — those already live in our own `Order` row from checkout.
The callback only supplies the outcome (`PAID`/`FAILED`) and a
transaction id for our records. It's also idempotent: a repeated
callback for an already-`PAID` order is accepted (200) but doesn't
overwrite the original settlement — the banking app may retry on
network failure without corrupting state on this side.

## Environment variables

| Var | Purpose | Example (Dev) |
|---|---|---|
| `DB_HOST` | MySQL host. Unset → falls back to local SQLite. | `mysql` |
| `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | MySQL connection | `3306` / `ecommercedb` / `ecomuser` / — |
| `BANK_API_BASE` | Banking app's API, server-to-server | `http://banking:5001` (compose) |
| `BANK_API_TIMEOUT` | Seconds to wait for the bank's API before failing the order | `5` |
| `MERCHANT_ACCOUNT` | Must match the MERCHANT account the banking app's seed script creates | `pageturn-books` |
| `SHOP_NAME` | Display name | `PageTurn Books` |
| `SECRET_KEY` | Signs the session cookie the cart lives in | (set a real random value outside Dev) |
| `PORT` | Port for local `flask run` (Docker always uses 5000) | `5000` |

## Run locally (no Docker)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt   # includes pytest
export BANK_API_BASE=http://<VM_PUBLIC_IP>:5001
python app.py            # listens on 0.0.0.0:5000, SQLite fallback DB
```

## Run tests

```bash
pytest
```

Tests run against an in-memory SQLite DB (see `tests/conftest.py`) and
never touch the real MySQL database.

## Run with Docker

```bash
docker build -t ecommerce-app:dev .
docker run -d --name ecom -p 5000:5000 \
  -e BANK_API_BASE=http://<VM_PUBLIC_IP>:5001 \
  -e MERCHANT_ACCOUNT=pageturn-books \
  -e SECRET_KEY=change-me \
  ecommerce-app:dev
```

## Not in scope (per project brief)

- Signup/login, admin CRUD, wishlist, discount codes — out of scope,
  keep the app minimal.
- The banking side of the flow (accounts, `/pay`, debit/credit, the
  code that calls our `/api/payment/callback`) lives in `banking-app`,
  not here.
