from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from models import Product

cart_bp = Blueprint("cart", __name__)


def _get_cart():
    """Cart lives in the signed session cookie: {product_id (str): quantity}."""
    return session.setdefault("cart", {})


def _cart_items():
    """Resolve the session cart against the live product catalog."""
    cart = session.get("cart", {})
    items = []
    total = 0
    for pid_str, qty in cart.items():
        product = Product.query.get(int(pid_str))
        if not product:
            continue  # product removed from catalog since it was added
        subtotal = float(product.price) * qty
        total += subtotal
        items.append({"product": product, "quantity": qty, "subtotal": subtotal})
    return items, total


@cart_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def add(product_id):
    Product.query.get_or_404(product_id)  # 404 early if the id is bogus
    qty = max(1, int(request.form.get("quantity", 1)))
    cart = _get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart.view"))


@cart_bp.route("/cart")
def view():
    items, total = _cart_items()
    return render_template(
        "cart.html", items=items, total=total, shop_name=current_app.config["SHOP_NAME"]
    )


@cart_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def update(product_id):
    qty = int(request.form.get("quantity", 1))
    cart = _get_cart()
    if qty <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = qty
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart.view"))


@cart_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove(product_id):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart.view"))
