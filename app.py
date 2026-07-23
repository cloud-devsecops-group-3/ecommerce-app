"""
PageTurn Books - e-commerce MVP
Group 3 (Bookstore) | QR Payment Prototype

Implements steps 1-5 and 11 of the process flow (browse, add to cart,
checkout, QR appears, order starts PENDING, flips to PAID on callback).
Steps 6-10 (choose account, confirm, balances move) happen in the
separate banking-app; this app only ever talks to it over HTTP.
"""

import os

from flask import Flask, session

from config import Config
from models import db
from seed import seed_products


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    from routes.cart import cart_bp
    from routes.catalog import catalog_bp
    from routes.orders import orders_bp

    app.register_blueprint(catalog_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)

    @app.context_processor
    def inject_cart_count():
        cart = session.get("cart", {})
        return {"cart_count": sum(cart.values())}

    with app.app_context():
        db.create_all()
        seed_products()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
