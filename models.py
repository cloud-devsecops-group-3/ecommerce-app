from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2), nullable=False)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.String(36), primary_key=True)  # uuid4
    total = db.Column(db.Numeric(10, 2), nullable=False)
    merchant_account = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")  # PENDING/PAID/FAILED
    bank_reference = db.Column(db.String(80))       # bank's transaction id, set at creation
    qr_url = db.Column(db.String(255))               # bank-hosted QR image, set at creation
    bank_transaction_id = db.Column(db.String(80))   # settlement id, set by the callback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    items = db.relationship(
        "OrderItem", backref="order", cascade="all, delete-orphan", lazy="joined"
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    # Snapshotted at purchase time - if the catalog price changes later,
    # past orders must still show what the customer actually paid.
    product_name = db.Column(db.String(120), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
