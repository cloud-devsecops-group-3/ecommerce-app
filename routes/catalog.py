from flask import Blueprint, current_app, jsonify, render_template

from models import Product

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/health")
def health():
    return jsonify(status="ok"), 200


@catalog_bp.route("/")
def index():
    products = Product.query.order_by(Product.id).all()
    return render_template(
        "index.html", products=products, shop_name=current_app.config["SHOP_NAME"]
    )
