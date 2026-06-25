"""Authentication helpers."""

from __future__ import annotations

from evergis_api import Client
from evergis_api.schemas import LoginDc, LoginResultDc


def login_with_credentials(
    client: Client,
    username: str,
    password: str,
) -> LoginResultDc:
    """Login by username/password and attach the returned bearer token.

    Calls ``account.authenticate`` and stores the returned JWT on the
    client via ``set_bearer_token`` so the next API calls on the same
    client are authenticated automatically.

    Args:
        client: An ``evergis_api.Client`` instance. Typically constructed
            without an ``sb_token`` because this helper supplies a JWT.
        username: User name.
        password: User password.

    Returns:
        The full ``LoginResultDc`` (token + refreshToken + redirectUrl
        + username) so the caller can persist the refresh token if needed.
    """
    result = client.account.authenticate(
        body=LoginDc(username=username, password=password)
    )
    client.account.set_bearer_token(result.token)
    return result
