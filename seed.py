from models import db, Product


def seed_products():

    if Product.query.count() > 0:
        return

    products = [

        Product(
            name="Novel",
            price=350
        ),

        Product(
            name="Notebook",
            price=80
        ),

        Product(
            name="Textbook",
            price=650
        ),

        Product(
            name="Comic",
            price=250
        ),

        Product(
            name="Pen",
            price=35
        )

    ]

    db.session.add_all(products)

    db.session.commit()

    print("Products seeded.")