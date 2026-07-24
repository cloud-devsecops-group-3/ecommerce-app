import uuid
from datetime import datetime

import requests
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import Order, OrderItem, db
from routes.cart import _cart_items

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/checkout")
def checkout():
    items, total = _cart_items()
    if not items:
        return redirect(url_for("cart.view"))
    return render_template(
        "checkout.html", items=items, total=total, shop_name=current_app.config["SHOP_NAME"]
    )


@orders_bp.route("/checkout", methods=["POST"])
def place_order():
    items, total = _cart_items()
    if not items:
        return redirect(url_for("cart.view"))

    order = Order(
        id=str(uuid.uuid4()),
        total=total,
        merchant_account=current_app.config["MERCHANT_ACCOUNT"],
        status="PENDING",
    )
    db.session.add(order)
    db.session.flush()  # order.id is now usable as a foreign key below

    for entry in items:
        product = entry["product"]
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=entry["quantity"],
                subtotal=entry["subtotal"],
            )
        )

    db.session.commit()
    session["cart"] = {}
    session.modified = True

    _register_with_bank(order)

    return redirect(url_for("orders.order_status", order_id=order.id))


def _register_with_bank(order: Order) -> None:
    """Tell the bank a payment is needed and get back its QR. The bank
    owns the transaction record and the QR image from this point on -
    we only store its reference and the URL to display."""
    base = current_app.config["ECOM_API_BASE"].rstrip("/")

    # payload = {
    #     "order_id": order.id,
    #     "amount": str(order.total),
    #     "merchant_account": order.merchant_account,
    #     "callback_url": url_for("orders.payment_callback", _external=True),
    #     "return_url": url_for("orders.order_status", order_id=order.id, _external=True),
    # }
    payload = {
        "order_id": order.id,
        "amount": str(order.total),
        "merchant_account": order.merchant_account,
        "callback_url": f"{base}/api/payment/callback",
        "return_url": f"{base}/order/{order.id}",
    }
    try:
        resp = requests.post(
            f"{current_app.config['BANK_API_BASE']}/api/payment-requests",
            json=payload,
            timeout=current_app.config["BANK_API_TIMEOUT"],
        )
        resp.raise_for_status()
        data = resp.json()
        order.bank_reference = data.get("transaction_id")
        order.qr_url = data.get("qr_url")
    except (requests.RequestException, ValueError):
        # Bank unreachable, timed out, or sent back something unparseable.
        # We don't leave the order silently stuck in PENDING with no QR -
        # fail it visibly so the customer isn't staring at a blank page.
        order.status = "FAILED"
    db.session.commit()


@orders_bp.route("/order/<order_id>")
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template(
        "order_status.html", order=order, shop_name=current_app.config["SHOP_NAME"]
    )


@orders_bp.route("/api/order/<order_id>")
def order_api(order_id):
    """Polled by the order-status page's JS until status flips to PAID."""
    order = Order.query.get_or_404(order_id)
    return jsonify(
        order_id=order.id,
        status=order.status,
        total=str(order.total),
        merchant_account=order.merchant_account,
        bank_reference=order.bank_reference,
        qr_url=order.qr_url,
        bank_transaction_id=order.bank_transaction_id,
        items=[
            {
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": str(i.unit_price),
                "subtotal": str(i.subtotal),
            }
            for i in order.items
        ],
    )


@orders_bp.route("/api/payment/callback", methods=["POST"])
def payment_callback():
    """Called by the banking app once it has settled the transaction on
    its own side. We never trust this payload for the amount or merchant -
    those already live in our own Order row. All this does is look up the
    order it names and flip its status."""
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    status = data.get("status")

    if not order_id or status not in ("PAID", "FAILED"):
        return jsonify(error="order_id and a valid status are required"), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify(error="unknown order_id"), 404

    if order.status == "PAID":
        # Already settled - callback must be safe to receive more than once.
        return jsonify(status="ok", order_id=order.id, order_status=order.status), 200

    order.status = status
    order.bank_transaction_id = data.get("transaction_id")
    if status == "PAID":
        order.paid_at = datetime.utcnow()
    db.session.commit()

    return jsonify(status="ok", order_id=order.id, order_status=order.status), 200
