"""SDK client helpers for kscli."""

import json
import sys
from contextlib import contextmanager
from typing import Any, Protocol, runtime_checkable

import certifi
import click
import ksapi
import urllib3

from kscli.auth import load_credentials
from kscli.config import get_base_url, get_tls_config

_STATUS_MESSAGES = {
    401: "Session expired. Run: kscli login --api-key <key>",
    403: "Permission denied",
    404: "Not found",
    409: "Conflict",
    422: "Validation error",
}

_EXIT_CODES = {
    401: 2,
    403: 1,
    404: 3,
    409: 1,
    422: 4,
}


@runtime_checkable
class _SupportsToDict(Protocol):
    def to_dict(self) -> dict[str, Any] | list[Any]: ...


def get_api_client(ctx: click.Context) -> ksapi.ApiClient:
    """Build an authenticated SDK ApiClient from click context and cached credentials."""
    creds = load_credentials()
    base_url = get_base_url(ctx.obj.get("base_url"))

    verify_ssl, ca_bundle = get_tls_config()

    config = ksapi.Configuration(host=base_url)
    config.verify_ssl = verify_ssl
    if verify_ssl:
        config.ssl_ca_cert = ca_bundle or certifi.where()

    client = ksapi.ApiClient(config)
    client.default_headers["authorization"] = f"Bearer {creds['api_key']}"
    return client


def handle_api_error(e: ksapi.ApiException) -> None:
    """Map SDK ApiException to error messages and exit codes matching original behavior."""
    status = e.status or 500
    detail = ""
    if e.body:
        try:
            body = json.loads(e.body)
            detail = body.get("detail", body)
        except Exception:
            detail = e.body
    prefix = _STATUS_MESSAGES.get(status, f"Server error: {status}")
    click.echo(f"Error: {prefix}: {detail}", err=True)
    sys.exit(_EXIT_CODES.get(status, 1))


@contextmanager
def handle_client_errors():
    """Context manager to catch API and connection errors (SSL, timeout, etc)."""
    try:
        yield
    except ksapi.ApiException as e:
        handle_api_error(e)
    except urllib3.exceptions.MaxRetryError as e:
        if isinstance(e.reason, urllib3.exceptions.SSLError):
            _handle_ssl_error()
        click.echo(f"Error: Connection failed: {e.reason or e}", err=True)
        sys.exit(1)
    except urllib3.exceptions.SSLError:
        _handle_ssl_error()
    except Exception as e:
        # Unexpected errors
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _handle_ssl_error() -> None:
    click.echo(
        "Error: SSL certificate verification failed.\n\n"
        "This is often due to missing local certificates or a corporate proxy.\n\n"
        "Solutions:\n"
        "1. Install Python certificates (macOS): Run 'Install Certificates.command'\n"
        "2. Set KSCLI_CA_BUNDLE to your custom CA bundle path\n"
        "3. (Insecure) Set KSCLI_VERIFY_SSL=false for development",
        err=True,
    )
    sys.exit(1)


def to_dict(obj: object) -> dict[str, Any] | list[Any]:
    """Convert an SDK response model to a plain dict/list for print_result()."""
    if obj is None:
        return {}
    normalized = _normalize_value(obj)
    if isinstance(normalized, (dict, list)):
        return normalized
    return {}


def _normalize_value(obj: Any) -> Any:
    """Recursively normalize SDK models nested in dict/list responses."""
    if isinstance(obj, _SupportsToDict):
        return _normalize_value(obj.to_dict())
    if isinstance(obj, dict):
        return {key: _normalize_value(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_normalize_value(item) for item in obj]
    return obj
