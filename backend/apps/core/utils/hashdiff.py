import hashlib
import json


def norm_str(s: str | None) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().split()).lower()


def norm_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
