import os
import json

import qrcode

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    abort
)

from config import Config
# from models import db, Product, Order
# from seed import seed_products


app = Flask(__name__)
app.config.from_object(Config)

# db.init_app(app)


# with app.app_context():
#     db.create_all()
#     seed_products()


products = [
    {"id": 1, "name": "Novel", "price": 350},
    {"id": 2, "name": "Notebook", "price": 80},
    {"id": 3, "name": "Textbook", "price": 650},
    {"id": 4, "name": "Comic", "price": 250},
    {"id": 5, "name": "Pen", "price": 35},
]

orders = {}
next_order_id = 1

QR_FOLDER = os.path.join("static", "qr")
os.makedirs(QR_FOLDER, exist_ok=True)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/")
def index():

    # products = Product.query.order_by(Product.id).all()

    return render_template(
        "index.html",
        products=products
    )


# @app.route("/buy/<int:product_id>", methods=["POST"])
# def buy(product_id):

#     product = Product.query.get_or_404(product_id)

#     order = Order(
#         product_id=product.id,
#         amount=product.price,
#         status="PENDING"
#     )

#     db.session.add(order)
#     db.session.commit()

#     return redirect(
#         url_for(
#             "checkout",
#             order_id=order["id"]
#         )
#     )
@app.route("/buy/<int:product_id>", methods=["POST"])
def buy():

    global next_order_id

    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if product is None:
        abort(404)

    order = {
        "id": next_order_id,
        "product": product,
        "amount": product["price"],
        "status": "PENDING"
    }

    orders[next_order_id] = order

    next_order_id += 1

    return redirect(
        url_for(
            "checkout",
            order_id=order["id"]
        )
    )


@app.route("/checkout/<int:order_id>")
def checkout(order_id):

    # order = Order.query.get_or_404(order_id)
    order = orders.get(order_id)

    if order is None:
        abort(404)

    qr_payload = {
        "order_id": order["id"],
        "amount": order["amount"],
        "merchant_account": app.config["MERCHANT_ACCOUNT"]
    }

    #
    # Phone opens this URL after scanning.
    #
    payment_url = (
        f"{app.config['BANK_PUBLIC_BASE']}/pay?"
        f"payload={json.dumps(qr_payload)}"
    )

    img = qrcode.make(payment_url)

    filename = f"order_{order["id"]}.png"

    filepath = os.path.join(
        QR_FOLDER,
        filename
    )

    img.save(filepath)

    return render_template(
        "checkout.html",
        order=order,
        qr_image=filename,
        payment_url=payment_url
    )


@app.route("/status/<int:order_id>")
def status(order_id):

    # order = Order.query.get_or_404(order_id)
    order = orders.get(order_id)

    if order is None:
        abort(404)

    return render_template(
        "status.html",
        order=order
    )


@app.route("/payment-success", methods=["POST"])
def payment_success():

    data = request.get_json()
    
    order = orders.get(data["order_id"])

    if order:
        order["status"] = "PAID"

    return jsonify({"success": True})

    # if not data:
    #     return jsonify(
    #         {
    #             "error": "Missing JSON body"
    #         }
    #     ), 400

    # order_id = data.get("order_id")

    # if order_id is None:
    #     return jsonify(
    #         {
    #             "error": "order_id is required"
    #         }
    #     ), 400

    # order = Order.query.get(order_id)

    # if order is None:
    #     return jsonify(
    #         {
    #             "error": "Order not found"
    #         }
    #     ), 404

    # order.status = "PAID"

    # db.session.commit()

    # return jsonify(
    #     {
    #         "success": True,
    #         "order_id": order["id"],
    #         "status": order.status
    #     }
    # )


@app.route("/api/order/<int:order_id>")
def api_order(order_id):

    order = Order.query.get_or_404(order_id)

    return jsonify(
        {
            "id": order["id"],
            "product_id": order.product_id,
            "amount": order["amount"],
            "status": order.status
        }
    )


@app.errorhandler(404)
def not_found(error):

    return render_template(
        "404.html"
    ), 404


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )