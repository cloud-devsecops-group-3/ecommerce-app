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
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    merchant_account = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")  # PENDING/PAID
    bank_transaction_id = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    product = db.relationship("Product")
