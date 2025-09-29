import os

from .local import *

USE_REAL_DB = os.getenv("USE_REAL_DB", "0").lower() in ("1", "true", "yes")

if not USE_REAL_DB:
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    SQLITE_NAME = os.path.join(ROOT_DIR, ".pytest.sqlite3")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": SQLITE_NAME,
            "TEST": {"NAME": SQLITE_NAME},
        }
    }

    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
