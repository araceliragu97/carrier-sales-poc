import os


class Settings:
    """
    Central place for config. Everything comes from environment variables so the
    same code works locally, in Docker, and once deployed -- you just change the
    .env file or the host's env var settings, never the code.
    """

    # Clients (HappyRobot's webhook tool) must send this in the X-API-Key header.
    API_KEY: str = os.getenv("API_KEY", "dev-local-key-change-me")

    # SQLite file. In Docker this will be mounted to a volume so data survives restarts.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./carrier_sales.db")

    # FMCSA QCMobile API key (called a "WebKey"). Get one free at
    # https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted (requires a login.gov account).
    # If this is left empty, the carrier-verification endpoint falls back to a mock
    # response so you can keep developing without waiting on FMCSA signup.
    FMCSA_WEBKEY: str = os.getenv("FMCSA_WEBKEY", "")

    FMCSA_BASE_URL: str = "https://mobile.fmcsa.dot.gov/qc/services/carriers"


settings = Settings()
