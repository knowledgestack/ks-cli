import json

import ksapi  # noqa: TC002


def format_api_error(e: ksapi.ApiException) -> str:
    """Format an ApiException for display without exiting."""
    status = e.status or 500
    detail = ""
    if e.body:
        try:
            body = json.loads(e.body)
            detail = body.get("detail", body)
        except Exception:
            detail = e.body
    return f"{status}: {detail}" if detail else str(status)
