#!/usr/bin/env python3
"""Local identity/session management for the governance dashboard."""

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_USERS_FILE = ".governance/identity-users.json"


def _now() -> int:
    return int(time.time())


def _pbkdf2(password: str, salt_hex: str, rounds: int = 210_000) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        rounds,
    )
    return digest.hex()


def hash_password(password: str) -> Dict[str, str]:
    salt = secrets.token_hex(16)
    return {"salt": salt, "hash": _pbkdf2(password, salt)}


def verify_password(password: str, expected_hash: str, salt_hex: str) -> bool:
    candidate = _pbkdf2(password, salt_hex)
    return hmac.compare_digest(candidate, expected_hash)


@dataclass
class IdentityUser:
    user_id: str
    name: str
    email: str
    roles: List[str]
    password_hash: str
    salt: str
    active: bool = True


class IdentityManager:
    def __init__(
        self,
        users_file: Path,
        session_ttl_seconds: int = 8 * 60 * 60,
        allow_passwordless_dev: bool = False,
    ):
        self.users_file = users_file
        self.session_ttl_seconds = max(300, int(session_ttl_seconds))
        self.allow_passwordless_dev = bool(allow_passwordless_dev)
        self._sessions: Dict[str, Dict] = {}
        self._users: Dict[str, IdentityUser] = {}
        self._bootstrap_users()
        self._load_users()

    @classmethod
    def from_env(cls, repo_root: Path) -> "IdentityManager":
        users_file = Path(os.environ.get("WBS_IDENTITY_USERS_FILE", DEFAULT_USERS_FILE))
        if not users_file.is_absolute():
            users_file = (repo_root / users_file).resolve()
        ttl = int(os.environ.get("WBS_SESSION_MAX_AGE", "28800"))
        allow_passwordless = (os.environ.get("WBS_ALLOW_PASSWORDLESS_DEV_LOGIN", "false").strip().lower() == "true")
        return cls(users_file=users_file, session_ttl_seconds=ttl, allow_passwordless_dev=allow_passwordless)

    def _bootstrap_users(self) -> None:
        if self.users_file.exists():
            return
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        defaults = [
            ("developer", "Developer", "developer@example.com", ["developer"]),
            ("admin", "Admin", "admin@example.com", ["admin", "developer"]),
            ("viewer", "Viewer", "viewer@example.com", ["viewer"]),
        ]
        payload = {"users": []}
        for user_id, name, email, roles in defaults:
            ph = hash_password(user_id)
            payload["users"].append(
                {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "roles": roles,
                    "password_hash": ph["hash"],
                    "salt": ph["salt"],
                    "active": True,
                }
            )
        self.users_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _load_users(self) -> None:
        raw = json.loads(self.users_file.read_text(encoding="utf-8"))
        users = {}
        for item in raw.get("users", []):
            user = IdentityUser(
                user_id=str(item.get("id") or "").strip(),
                name=str(item.get("name") or "").strip(),
                email=str(item.get("email") or "").strip().lower(),
                roles=[str(r).strip().lower() for r in item.get("roles", []) if str(r).strip()],
                password_hash=str(item.get("password_hash") or ""),
                salt=str(item.get("salt") or ""),
                active=bool(item.get("active", True)),
            )
            if not user.user_id or not user.email:
                continue
            users[user.user_id] = user
        self._users = users

    def _find_user(self, *, email: str = "", name: str = "") -> Optional[IdentityUser]:
        target_email = email.strip().lower()
        target_name = name.strip().lower()
        for user in self._users.values():
            if target_email and user.email == target_email:
                return user
            if target_name and user.name.lower() == target_name:
                return user
        return None

    def authenticate(self, *, email: str = "", name: str = "", password: str = "") -> Optional[Dict]:
        user = self._find_user(email=email, name=name)
        if not user or not user.active:
            return None
        password_ok = bool(password) and verify_password(password, user.password_hash, user.salt)
        if not password_ok:
            if not (self.allow_passwordless_dev and ("developer" in user.roles or "admin" in user.roles)):
                return None
        token = secrets.token_urlsafe(32)
        now = _now()
        session = {
            "token": token,
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "roles": user.roles,
            "role": self.primary_role(user.roles),
            "authenticated_at": now,
            "expires_at": now + self.session_ttl_seconds,
        }
        self._sessions[token] = session
        return session

    def primary_role(self, roles: List[str]) -> str:
        if "admin" in roles:
            return "Admin"
        if "developer" in roles:
            return "Developer"
        return "Viewer"

    def get_session(self, token: str) -> Optional[Dict]:
        token = (token or "").strip()
        if not token:
            return None
        sess = self._sessions.get(token)
        if not sess:
            return None
        if int(sess.get("expires_at") or 0) <= _now():
            self._sessions.pop(token, None)
            return None
        return sess

    def revoke(self, token: str) -> None:
        if token:
            self._sessions.pop(token, None)

    def user_payload(self, session: Optional[Dict]) -> Dict:
        if not session:
            return {}
        return {
            "name": session.get("name", ""),
            "email": session.get("email", ""),
            "role": session.get("role", "Viewer"),
            "roles": session.get("roles", []),
            "logged_in_at": session.get("authenticated_at"),
            "expires_at": session.get("expires_at"),
        }

    def has_any_role(self, session: Optional[Dict], roles: List[str]) -> bool:
        if not session:
            return False
        owned = {str(r).strip().lower() for r in session.get("roles", [])}
        required = {str(r).strip().lower() for r in roles}
        return bool(owned.intersection(required))
