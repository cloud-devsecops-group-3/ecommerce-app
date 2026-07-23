import uuid

from models import Order, db


def _make_pending_order(app):
    with app.app_context():
        order = Order(
            id=str(uuid.uuid4()),
            total="12.99",
            merchant_account="pageturn-books",
            status="PENDING",
        )
        db.session.add(order)
        db.session.commit()
        return order.id


def test_callback_marks_order_paid(client, app):
    order_id = _make_pending_order(app)

    resp = client.post(
        "/api/payment/callback",
        json={"order_id": order_id, "status": "PAID", "transaction_id": "tx123"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["order_status"] == "PAID"

    with app.app_context():
        updated = Order.query.get(order_id)
        assert updated.status == "PAID"
        assert updated.bank_transaction_id == "tx123"
        assert updated.paid_at is not None


def test_callback_is_idempotent(client, app):
    order_id = _make_pending_order(app)

    client.post("/api/payment/callback", json={"order_id": order_id, "status": "PAID"})
    second = client.post(
        "/api/payment/callback",
        json={"order_id": order_id, "status": "PAID", "transaction_id": "different-id"},
    )
    assert second.status_code == 200

    with app.app_context():
        updated = Order.query.get(order_id)
        # Second callback must not overwrite the original settlement.
        assert updated.bank_transaction_id != "different-id"


def test_callback_rejects_missing_fields(client):
    resp = client.post("/api/payment/callback", json={"order_id": "abc"})
    assert resp.status_code == 400


def test_callback_rejects_unknown_order(client):
    resp = client.post(
        "/api/payment/callback", json={"order_id": str(uuid.uuid4()), "status": "PAID"}
    )
    assert resp.status_code == 404
