# -*- coding: utf-8 -*-
"""Convenience client wrappers that pick credentials from environment.

The vanilla :class:`evergis_api.Client` and :class:`evergis_api.AsyncClient`
require ``base_url`` and ``sb_token`` to be passed explicitly. In examples
and short scripts that means writing the same setup code again
(``load_dotenv()`` + ``os.getenv(...)``), which also breaks in
environments where there is no ``.env`` file at all (production
deployments where credentials come from the process environment or a
secret manager).

This module exposes thin subclasses (sync + async) that:

* try to load a ``.env`` from the current working directory tree if
  ``python-dotenv`` is installed - does nothing when neither the
  package nor the file is present;
* fall back to ``EVERGIS_HOST`` / ``EVERGIS_SB_TOKEN`` env variables
  when ``base_url`` / ``sb_token`` are not given explicitly;
* raise a clear ``RuntimeError`` if neither source provides them.

Usage::

    from evergis_tools import Client

    with Client() as c:
        username = c.account.get_user_info().username

    # async variant
    from evergis_tools import AsyncClient
    import asyncio

    async def main():
        async with AsyncClient() as c:
            print(await c.account.get_user_info())

    asyncio.run(main())
"""

from __future__ import annotations

import os
from typing import Any, Optional

from evergis_api import AsyncClient as _BaseAsyncClient
from evergis_api import Client as _BaseClient


_DOTENV_LOADED = False


def _maybe_load_dotenv() -> None:
    """Best-effort ``.env`` discovery. Idempotent and silent on failure.

    Two-pass load:

    * ``.env`` - common defaults, picked up first.
    * ``.env.{ENV}`` - environment-specific overrides, loaded
      second with ``override=True`` so its values win over the common
      file. ``ENV=beta`` → ``.env.beta``,
      ``ENV=staging`` → ``.env.staging``, etc.

    Both files are looked up by ``find_dotenv`` (walks up from cwd);
    missing files are silently ignored.
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore
    except ImportError:
        _DOTENV_LOADED = True
        return

    load_dotenv()
    env_name = os.getenv("ENV")
    if env_name:
        env_path = find_dotenv(f".env.{env_name}", usecwd=True)
        if env_path:
            load_dotenv(env_path, override=True)
    _DOTENV_LOADED = True


def _resolve_creds(
    base_url: Optional[str], sb_token: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    """Fill in (base_url, sb_token) from env / .env if missing.

    Returns ``None`` for any value still missing - the caller forwards
    only non-None creds to the base class so its built-in defaults
    (e.g. internal ``base_url="http://evergis"``) still apply on prod
    runners that don't expose ``EVERGIS_HOST`` / ``EVERGIS_SB_TOKEN``.
    """
    _maybe_load_dotenv()
    base_url = base_url if base_url is not None else os.getenv("EVERGIS_HOST")
    sb_token = sb_token if sb_token is not None else os.getenv("EVERGIS_SB_TOKEN")
    return base_url, sb_token


def _build_init_kwargs(
    base_url: Optional[str],
    sb_token: Optional[str],
    extra: dict,
) -> dict:
    """Pass only non-None creds so base-class defaults still apply."""
    init_kwargs = dict(extra)
    if base_url is not None:
        init_kwargs["base_url"] = base_url
    if sb_token is not None:
        init_kwargs["sb_token"] = sb_token
    return init_kwargs


class Client(_BaseClient):
    """Drop-in replacement for ``evergis_api.Client`` with env defaults.

    See module docstring for the resolution order. ``*args`` / ``**kwargs``
    are forwarded to the underlying :class:`evergis_api.Client`.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        sb_token: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        base_url, sb_token = _resolve_creds(base_url, sb_token)
        super().__init__(*args, **_build_init_kwargs(base_url, sb_token, kwargs))


class AsyncClient(_BaseAsyncClient):
    """Async counterpart of :class:`Client`.

    Same env-defaulting behaviour as :class:`Client`; forwards everything
    else to :class:`evergis_api.AsyncClient`.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        sb_token: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        base_url, sb_token = _resolve_creds(base_url, sb_token)
        super().__init__(*args, **_build_init_kwargs(base_url, sb_token, kwargs))


__all__ = ["Client", "AsyncClient"]
