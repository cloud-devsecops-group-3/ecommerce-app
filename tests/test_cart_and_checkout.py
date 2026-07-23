from unittest.mock import Mock, patch

from models import Order, Product


def test_add_two_products_and_checkout_registers_with_bank(client, app):
    with app.app_context():
        products = Product.query.order_by(Product.id).limit(2).all()
        p1, p2 = products[0], products[1]
        p1_id, p2_id = p1.id, p2.id
        expected_total = float(p1.price) * 2 + float(p2.price) * 1

    client.post(f"/cart/add/{p1_id}", data={"quantity": 2})
    client.post(f"/cart/add/{p2_id}", data={"quantity": 1})

    cart_resp = client.get("/cart")
    assert cart_resp.status_code == 200

    fake_bank_response = Mock()
    fake_bank_response.raise_for_status = Mock()
    fake_bank_response.json.return_value = {
        "transaction_id": "bank-txn-1",
        "qr_url": "http://bank.example/qr/bank-txn-1.png",
    }
    with patch("routes.orders.requests.post", return_value=fake_bank_response) as mock_post:
        checkout_resp = client.post("/checkout", follow_redirects=True)
    assert checkout_resp.status_code == 200
    mock_post.assert_called_once()  # ecommerce must register the order with the bank

    with app.app_context():
        order = Order.query.first()
        assert order is not None
        assert order.status == "PENDING"
        assert len(order.items) == 2
        assert round(float(order.total), 2) == round(expected_total, 2)
        assert order.bank_reference == "bank-txn-1"
        assert order.qr_url == "http://bank.example/qr/bank-txn-1.png"

    # Cart should be empty again after checkout
    cart_resp = client.get("/cart")
    assert b"Your cart is empty" in cart_resp.data


def test_checkout_fails_order_if_bank_is_unreachable(client, app):
    import requests

    with app.app_context():
        product = Product.query.first()
        product_id = product.id

    client.post(f"/cart/add/{product_id}", data={"quantity": 1})

    with patch("routes.orders.requests.post", side_effect=requests.ConnectionError()):
        checkout_resp = client.post("/checkout", follow_redirects=True)
    assert checkout_resp.status_code == 200

    with app.app_context():
        order = Order.query.first()
        assert order.status == "FAILED"
        assert order.qr_url is None


def test_checkout_with_empty_cart_redirects_to_cart(client):
    resp = client.post("/checkout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Your cart is empty" in resp.data
