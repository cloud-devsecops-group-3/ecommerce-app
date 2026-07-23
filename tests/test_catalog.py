def test_index_lists_seeded_products(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"The Silent Orchard" in resp.data
    assert b"Gel Pen 5-Pack" in resp.data
