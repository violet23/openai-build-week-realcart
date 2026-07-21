"""Local single-user OAuth helpers for Gmail and Pinterest Sandbox."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from time import time
from urllib.parse import urlencode

import httpx

from realcart_api.settings import settings

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
PINTEREST_SCOPES = "boards:read,pins:read"


class OAuthConfigurationError(RuntimeError):
    """Raised when a provider has not been configured for OAuth."""


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None


class LocalOAuthStore:
    """Process-memory storage for a local hackathon build; never writes tokens to disk."""

    def __init__(self) -> None:
        self._tokens: dict[str, OAuthToken] = {}
        self._states: dict[str, str] = {}

    def create_state(self, provider: str) -> str:
        state = secrets.token_urlsafe(32)
        self._states[provider] = state
        return state

    def consume_state(self, provider: str, state: str) -> None:
        expected = self._states.pop(provider, None)
        if expected is None or not secrets.compare_digest(expected, state):
            raise OAuthConfigurationError("OAuth state did not match; start the connection again")

    def set_token(self, provider: str, payload: dict[str, object]) -> None:
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise OAuthConfigurationError(f"{provider} did not return an access token")
        refresh_token = payload.get("refresh_token")
        expires_in = payload.get("expires_in")
        self._tokens[provider] = OAuthToken(
            access_token=access_token,
            refresh_token=refresh_token if isinstance(refresh_token, str) else None,
            expires_at=(
                time() + float(expires_in)
                if isinstance(expires_in, int | float | str)
                else None
            ),
        )

    def access_token(self, provider: str) -> str | None:
        token = self._tokens.get(provider)
        if token is not None:
            if token.expires_at is not None and token.expires_at <= time():
                return None
            return token.access_token
        if provider == "gmail":
            return settings.gmail_access_token or None
        if provider == "pinterest":
            return settings.pinterest_access_token or None
        return None

    def connected(self, provider: str) -> bool:
        return self.access_token(provider) is not None


oauth_store = LocalOAuthStore()


def authorization_url(provider: str) -> str:
    state = oauth_store.create_state(provider)
    if provider == "gmail":
        if not settings.google_client_id or not settings.google_client_secret:
            raise OAuthConfigurationError("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first")
        query = urlencode(
            {
                "client_id": settings.google_client_id,
                "redirect_uri": settings.google_redirect_uri,
                "response_type": "code",
                "scope": GMAIL_SCOPE,
                "access_type": "offline",
                "include_granted_scopes": "true",
                "prompt": "consent",
                "state": state,
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    if provider == "pinterest":
        if not settings.pinterest_client_id or not settings.pinterest_client_secret:
            raise OAuthConfigurationError(
                "Set PINTEREST_CLIENT_ID and PINTEREST_CLIENT_SECRET first"
            )
        query = urlencode(
            {
                "client_id": settings.pinterest_client_id,
                "redirect_uri": settings.pinterest_redirect_uri,
                "response_type": "code",
                "scope": PINTEREST_SCOPES,
                "state": state,
            }
        )
        return f"https://www.pinterest.com/oauth/?{query}"
    raise OAuthConfigurationError(f"Unknown OAuth provider: {provider}")


async def exchange_code(provider: str, *, code: str, state: str) -> None:
    oauth_store.consume_state(provider, state)
    async with httpx.AsyncClient(timeout=20) as client:
        if provider == "gmail":
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.google_redirect_uri,
                },
            )
        elif provider == "pinterest":
            response = await client.post(
                f"{settings.pinterest_api_base_url}/oauth/token",
                auth=httpx.BasicAuth(
                    settings.pinterest_client_id, settings.pinterest_client_secret
                ),
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.pinterest_redirect_uri,
                },
            )
        else:
            raise OAuthConfigurationError(f"Unknown OAuth provider: {provider}")
    try:
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise OAuthConfigurationError(f"{provider} token exchange failed") from error
    if not isinstance(payload, dict):
        raise OAuthConfigurationError(f"{provider} returned an invalid token response")
    oauth_store.set_token(provider, payload)
