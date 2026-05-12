"""Document checkout helper.

The backend requires a checkout (write lock) on a document before mutating its
versions, sections, chunks, or deleting the document itself. The current
generated `ksapi` does not expose the checkout endpoints, so this helper calls
them via the SDK's raw `param_serialize` + `call_api` path while reusing the
authenticated `ApiClient`.

Endpoints (from the backend OpenAPI):
- ``POST   /v1/documents/{path_part_id}/checkout`` — acquire or renew
- ``DELETE /v1/documents/{path_part_id}/checkout`` — release
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

import ksapi

if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator

_RESOURCE_PATH = "/v1/documents/{path_part_id}/checkout"
_HTTP_OK_MIN = 200
_HTTP_OK_MAX = 300  # exclusive upper bound

log = logging.getLogger(__name__)


def _raw_call(
    api_client: ksapi.ApiClient,
    method: str,
    path_part_id: uuid.UUID,
) -> None:
    """Call the checkout endpoint and raise ApiException on non-2xx."""
    method_, url, headers, body, post_params = api_client.param_serialize(
        method=method,
        resource_path=_RESOURCE_PATH,
        path_params={"path_part_id": str(path_part_id)},
        header_params={"Accept": "application/json"},
        body=None,
        auth_settings=[],
    )
    response = api_client.call_api(
        method_, url, header_params=headers, body=body, post_params=post_params
    )
    response.read()
    if not _HTTP_OK_MIN <= response.status < _HTTP_OK_MAX:
        text = response.data.decode("utf-8", errors="replace") if response.data else None
        raise ksapi.ApiException.from_response(
            http_resp=response, body=text, data=None
        )


def acquire_document_checkout(
    api_client: ksapi.ApiClient, path_part_id: uuid.UUID
) -> None:
    """Acquire (or renew) a write lock on a document."""
    _raw_call(api_client, "POST", path_part_id)


def release_document_checkout(
    api_client: ksapi.ApiClient, path_part_id: uuid.UUID
) -> None:
    """Release a write lock on a document."""
    _raw_call(api_client, "DELETE", path_part_id)


@contextmanager
def with_document_checkout(
    api_client: ksapi.ApiClient, path_part_id: uuid.UUID
) -> Iterator[None]:
    """Acquire a document checkout for the body of the block, release on exit.

    Release errors are logged and swallowed so they don't mask the primary
    operation's outcome — the lock will expire on its TTL regardless.
    """
    acquire_document_checkout(api_client, path_part_id)
    try:
        yield
    finally:
        try:
            release_document_checkout(api_client, path_part_id)
        except ksapi.ApiException as exc:
            log.debug("Failed to release checkout on %s: %s", path_part_id, exc)


def resolve_document_path_part_id(
    api_client: ksapi.ApiClient, document_id: uuid.UUID
) -> uuid.UUID:
    """Look up a document's path_part_id by document_id."""
    documents_api = ksapi.DocumentsApi(api_client)
    return documents_api.get_document(document_id).path_part_id


def resolve_version_document_path_part_id(
    api_client: ksapi.ApiClient, version_id: uuid.UUID
) -> uuid.UUID:
    """Look up the parent document's path_part_id for a version."""
    versions_api = ksapi.DocumentVersionsApi(api_client)
    parent = versions_api.get_document_version(version_id).parent_path_id
    if parent is None:
        msg = f"Version {version_id} has no parent document path_part_id"
        raise ksapi.ApiException(status=404, reason=msg)
    return parent


_MAX_ANCESTOR_WALK = 32


def resolve_ancestor_document_path_part_id(
    api_client: ksapi.ApiClient, path_part_id: uuid.UUID
) -> uuid.UUID:
    """Walk up the path-part tree until reaching a node whose part_type is DOCUMENT.

    Use when starting from a section, chunk, or version path_part_id — anything
    below a document in the path tree.
    """
    path_parts_api = ksapi.PathPartsApi(api_client)
    current = path_part_id
    for _ in range(_MAX_ANCESTOR_WALK):
        part = path_parts_api.get_path_part(current)
        if part.part_type == "DOCUMENT":
            return part.path_part_id
        if part.parent_path_id is None:
            break
        current = part.parent_path_id
    msg = f"No DOCUMENT ancestor found for path_part {path_part_id}"
    raise ksapi.ApiException(status=404, reason=msg)
