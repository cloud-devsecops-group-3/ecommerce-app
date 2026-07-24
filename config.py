import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "ecommercedb")
    DB_USER = os.environ.get("DB_USER", "ecomuser")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

    if DB_HOST:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        # Convenience fallback so the app also runs with zero setup locally.
        # Dev/Test/Prod always set DB_HOST, so this branch never fires there.
        SQLALCHEMY_DATABASE_URI = "sqlite:///local_ecommerce.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Server-to-server URL for the banking app's API. This is ecommerce's
    # backend talking to the bank's backend directly, so a Docker-internal
    # hostname (e.g. http://banking:5001 in compose) is fine here - unlike
    # the old BANK_PUBLIC_BASE, nothing here needs to be phone-reachable,
    # since the bank now returns its own fully-qualified, phone-reachable
    # qr_url in the API response.
    BANK_API_BASE = os.environ.get("BANK_API_BASE", "http://54-211-30-30.nip.io")
    ECOM_API_BASE = os.environ.get("ECOM_API_BASE", "http://98-95-123-28.nip.io")

    # Seconds to wait for the bank's payment-request API before giving up.
    BANK_API_TIMEOUT = float(os.environ.get("BANK_API_TIMEOUT", "5"))

    # Must match the MERCHANT account the banking app's seed script creates.
    MERCHANT_ACCOUNT = os.environ.get("MERCHANT_ACCOUNT", "pageturn-books")

    SHOP_NAME = os.environ.get("SHOP_NAME", "PageTurn Books")
