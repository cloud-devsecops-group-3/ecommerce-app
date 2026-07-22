"""
PageTurn Books — e-commerce MVP
Group 3 (Bookstore) | QR Payment Prototype

Flow implemented here (steps 1-5 and 11 of the process flow; 6-10 happen
in the banking app):
    1. Open Bookstore        -> GET /
    2. Select Book           -> product listed on /
    3. Click Buy             -> POST /buy/<product_id>
    4. QR Appears            -> GET /order/<order_id> renders the QR
    5. Scan QR               -> QR encodes a URL into the banking app
    11. Order Status = PAID  -> POST /api/orders/<order_id>/paid (callback)

Everything environment-specific (DB connection, the bank's public URL,
this shop's merchant account) comes from environment variables so the
exact same Docker image runs unchanged in Dev, Test, and Prod.
"""

import os
import uuid
from datetime import datetime
from io import BytesIO

import qrcode
from flask import Flask, render_template, redirect, url_for, jsonify, request, send_file

from models import db, Product, Order

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration - everything from environment variables, nothing hardcoded.
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "ecommercedb")
DB_USER = os.environ.get("DB_USER", "ecomuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

if DB_HOST:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    # Convenience fallback so the app also runs with zero setup (e.g. a
    # laptop with no MySQL running yet). Dev/Test/Prod always set DB_HOST,
    # so this branch never fires outside quick local testing.
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local_ecommerce.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Public URL of the banking app that a PHONE can reach - never localhost.
# e.g. http://bank.<VM_IP>.nip.io in Dev, http://bank:5001 style service
# name only works container-to-container, NOT for a phone scanning a QR.
BANK_PUBLIC_BASE = os.environ.get("BANK_PUBLIC_BASE", "http://localhost:5001")

# This shop's merchant account - must match what the banking app's seed
# script created as a MERCHANT account (see project brief, Group 3).
MERCHANT_ACCOUNT = os.environ.get("MERCHANT_ACCOUNT", "pageturn-books")

SHOP_NAME = os.environ.get("SHOP_NAME", "PageTurn Books")

db.init_app(app)

# ---------------------------------------------------------------------------
# Idempotent seeding - products are never inserted by hand. Runs at import
# time (not only under __main__) so it also fires under gunicorn.
# ---------------------------------------------------------------------------
SEED_PRODUCTS = [
    ("The Silent Orchard", "A quiet, atmospheric novel", "12.99"),
    ("Ruled Notebook (200pg)", "A5 hardcover notebook", "4.50"),
    ("Intro to Data Structures", "Undergraduate CS textbook", "45.00"),
    ("Moonlight Chronicles Vol. 1", "Graphic novel / comic", "6.99"),
    ("Gel Pen 5-Pack", "Smooth-writing black gel pens", "3.25"),
    ("Poetry of the Quiet Hours", "Short-form poetry collection", "9.50"),
]


def seed_products():
    if Product.query.first():
        return
    for name, description, price in SEED_PRODUCTS:
        db.session.add(Product(name=name, description=description, price=price))
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_products()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/")
def index():
    products = Product.query.order_by(Product.id).all()
    return render_template("index.html", products=products, shop_name=SHOP_NAME)


@app.route("/buy/<int:product_id>", methods=["POST"])
def buy(product_id):
    product = Product.query.get_or_404(product_id)
    order = Order(
        id=str(uuid.uuid4()),
        product_id=product.id,
        product_name=product.name,
        amount=product.price,
        merchant_account=MERCHANT_ACCOUNT,
        status="PENDING",
    )
    db.session.add(order)
    db.session.commit()
    return redirect(url_for("order_status", order_id=order.id))


@app.route("/order/<order_id>")
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template(
        "order_status.html", order=order, shop_name=SHOP_NAME
    )


@app.route("/qr/<order_id>.png")
def order_qr(order_id):
    """Generated on demand (no file storage needed) so it works the same
    way whether there's 1 replica (Dev/Test) or several (Prod)."""
    order = Order.query.get_or_404(order_id)
    pay_url = (
        f"{BANK_PUBLIC_BASE}/pay"
        f"?order_id={order.id}"
        f"&amount={order.amount}"
        f"&merchant_account={order.merchant_account}"
    )
    img = qrcode.make(pay_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/orders/<order_id>")
def order_api(order_id):
    """Polled by the order-status page's JS until status flips to PAID."""
    order = Order.query.get_or_404(order_id)
    return jsonify(
        order_id=order.id,
        status=order.status,
        amount=str(order.amount),
        merchant_account=order.merchant_account,
        bank_transaction_id=order.bank_transaction_id,
    )


@app.route("/api/orders/<order_id>/paid", methods=["POST"])
def order_mark_paid(order_id):
    """Callback from the banking app once it has debited the customer and
    credited the merchant. Body: {"transaction_id": "..."}"""
    order = Order.query.get_or_404(order_id)
    data = request.get_json(silent=True) or {}
    order.status = "PAID"
    order.bank_transaction_id = data.get("transaction_id")
    order.paid_at = datetime.utcnow()
    db.session.commit()
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
