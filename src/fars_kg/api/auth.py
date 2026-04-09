from __future__ import annotations

from fastapi import Request


OPERATOR_TOKEN_HEADER = "X-FARS-Operator-Token"
OPERATOR_SESSION_COOKIE = "fars_operator_session"


def operator_access_granted(request: Request, operator_token: str | None) -> bool:
    if not operator_token:
        return True
    header_token = request.headers.get(OPERATOR_TOKEN_HEADER)
    cookie_token = request.cookies.get(OPERATOR_SESSION_COOKIE)
    return header_token == operator_token or cookie_token == operator_token
