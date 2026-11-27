"""Small stdlib-only signed access tokens for StrokeSpeak learner sessions."""

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_TOKEN_ISSUER = "strokespeak"
_TOKEN_LIFETIME_SECONDS = 8 * 60 * 60
_BEARER = HTTPBearer(auto_error=False)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _signing_secret() -> bytes:
    secret = os.getenv("STROKESPEAK_AUTH_SECRET", "").encode("utf-8")
    if len(secret) < 32:
        raise RuntimeError("STROKESPEAK_AUTH_SECRET must contain at least 32 bytes in backend/.env")
    return secret


def create_access_token(user_id: int) -> str:
    if user_id < 1:
        raise ValueError("user_id must be positive")
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"iss": _TOKEN_ISSUER, "sub": str(user_id), "iat": now, "exp": now + _TOKEN_LIFETIME_SECONDS}
    signing_input = f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(_signing_secret(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _decode_access_token(token: str) -> int:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected_signature = hmac.new(_signing_secret(), signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, _b64url_decode(encoded_signature)):
            raise ValueError("Invalid signature")
        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
        if header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("Invalid token header")
        if payload.get("iss") != _TOKEN_ISSUER or int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("Expired or invalid token")
        user_id = int(payload["sub"])
        if user_id < 1:
            raise ValueError("Invalid user")
        return user_id
    except Exception as error:
        raise ValueError("Invalid or expired access token") from error


def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_BEARER),
) -> int | None:
    if credentials is None:
        return None
    try:
        return _decode_access_token(credentials.credentials)
    except ValueError:
        return None


def get_current_user_id(user_id: int | None = Depends(get_optional_user_id)) -> int:
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in to access learner data.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def require_user_scope(authenticated_user_id: int | None, requested_user_id: int) -> None:
    if authenticated_user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in to access learner data.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if authenticated_user_id != requested_user_id:
        raise HTTPException(status_code=403, detail="You cannot access another learner's data.")


def _configured_user_ids(setting_name: str) -> set[int]:
    configured = os.getenv(setting_name, "")
    return {int(part.strip()) for part in configured.split(",") if part.strip().isdigit()}


def is_admin_user_id(user_id: int) -> bool:
    return int(user_id) in _configured_user_ids("STROKESPEAK_ADMIN_USER_IDS")


def is_developer_user_id(user_id: int) -> bool:
    return int(user_id) in _configured_user_ids("STROKESPEAK_DEVELOPER_USER_IDS")


def has_demo_quiz_access(user_id: int) -> bool:
    return int(user_id) in _configured_user_ids("STROKESPEAK_DEMO_QUIZ_ACCESS_USER_IDS")


def get_current_admin_user_id(user_id: int = Depends(get_current_user_id)) -> int:
    if not is_admin_user_id(user_id):
        raise HTTPException(status_code=403, detail="This action is limited to configured StrokeSpeak administrators.")
    return user_id
