from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import bcrypt

USERS_FILE = "users.json"


@dataclass(frozen=True)
class AuthUser:
    username: str
    role: str = "user"


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _users_path(path: str | Path | None = None) -> Path:
    return Path(path or USERS_FILE)


def hash_password(password: str) -> str:
    pwd = (password or "").strip()
    if not pwd:
        raise ValueError("Password must not be empty.")
    hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    pwd = (password or "").strip()
    ph = (password_hash or "").strip()
    if not pwd or not ph:
        return False
    try:
        return bool(bcrypt.checkpw(pwd.encode("utf-8"), ph.encode("utf-8")))
    except Exception:
        return False


def load_users(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    p = _users_path(path)
    if not p.exists():
        return {}
    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        username = _normalize_username(k) or _normalize_username(str(v.get("username") or ""))
        if not username:
            continue
        password_hash = str(v.get("password_hash") or "").strip()
        role = str(v.get("role") or "user").strip() or "user"
        if not password_hash:
            continue
        result[username] = {"username": username, "password_hash": password_hash, "role": role}
    return result


def save_users(users: dict[str, dict[str, Any]], path: str | Path | None = None) -> None:
    p = _users_path(path)
    normalized: dict[str, dict[str, Any]] = {}
    for username, rec in (users or {}).items():
        u = _normalize_username(username)
        if not u or not isinstance(rec, dict):
            continue
        normalized[u] = {
            "username": u,
            "password_hash": str(rec.get("password_hash") or "").strip(),
            "role": str(rec.get("role") or "user").strip() or "user",
        }
    p.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def has_any_users(path: str | Path | None = None) -> bool:
    return bool(load_users(path))


def create_user(
    username: str,
    password: str,
    *,
    role: str = "user",
    path: str | Path | None = None,
    overwrite: bool = False,
) -> AuthUser:
    u = _normalize_username(username)
    if not u:
        raise ValueError("Username must not be empty.")
    pwd = (password or "").strip()
    if len(pwd) < 6:
        raise ValueError("Password must be at least 6 characters.")

    users = load_users(path)
    if (u in users) and not overwrite:
        raise ValueError("User already exists.")

    users[u] = {"username": u, "password_hash": hash_password(pwd), "role": (role or "user").strip() or "user"}
    save_users(users, path)
    return AuthUser(username=u, role=users[u]["role"])


def authenticate(username: str, password: str, path: str | Path | None = None) -> AuthUser | None:
    u = _normalize_username(username)
    if not u:
        return None
    users = load_users(path)
    rec = users.get(u)
    if not rec:
        return None
    if not verify_password(password, str(rec.get("password_hash") or "")):
        return None
    role = str(rec.get("role") or "user").strip() or "user"
    return AuthUser(username=u, role=role)

