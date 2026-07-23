from models import db, Product

SEED_PRODUCTS = [
    ("The Silent Orchard", "A quiet, atmospheric novel", "12.99"),
    ("Ruled Notebook (200pg)", "A5 hardcover notebook", "4.50"),
    ("Intro to Data Structures", "Undergraduate CS textbook", "45.00"),
    ("Moonlight Chronicles Vol. 1", "Graphic novel / comic", "6.99"),
    ("Gel Pen 5-Pack", "Smooth-writing black gel pens", "3.25"),
    ("Poetry of the Quiet Hours", "Short-form poetry collection", "9.50"),
]


def seed_products():
    """Never insert products by hand - this runs at app startup and is
    a no-op once the table already has rows."""
    if Product.query.first():
        return
    for name, description, price in SEED_PRODUCTS:
        db.session.add(Product(name=name, description=description, price=price))
    db.session.commit()
