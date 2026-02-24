"""E2E test fixtures for kscli CLI tests."""

import secrets
from collections.abc import Generator  # noqa: TC003
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli, run_kscli_ok

# ---------------------------------------------------------------------------
# E2E environment constants
# ---------------------------------------------------------------------------

E2E_BASE_URL = "http://localhost:28000"

# Resolve ADMIN_API_KEY from ks-backend/.env.e2e at import time.
_KS_BACKEND_ENV_E2E = Path(__file__).resolve().parents[3] / "ks-backend" / ".env.e2e"


def _read_admin_api_key() -> str:
    """Parse ADMIN_API_KEY from ks-backend/.env.e2e."""
    if not _KS_BACKEND_ENV_E2E.is_file():
        pytest.exit(
            f"Cannot find {_KS_BACKEND_ENV_E2E}. "
            "Ensure ks-backend is checked out alongside ks-cli.",
            returncode=1,
        )
    for line in _KS_BACKEND_ENV_E2E.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("ADMIN_API_KEY=") and not stripped.startswith("#"):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    pytest.exit(
        f"ADMIN_API_KEY not found in {_KS_BACKEND_ENV_E2E}",
        returncode=1,
    )
    return ""  # unreachable, keeps type checker happy


E2E_ADMIN_API_KEY = _read_admin_api_key()

# ---------------------------------------------------------------------------
# Well-known seed data UUIDs (from ../ks-backend/seed/seed_data.py)
# ---------------------------------------------------------------------------

PWUSER1_ID = "00000000-0000-0000-0001-000000000001"
PWUSER2_ID = "00000000-0000-0000-0001-000000000002"
PWUSER3_ID = "00000000-0000-0000-0001-000000000005"

SHARED_TENANT_ID = "00000000-0000-0000-0002-000000000005"
PWUSER1_TENANT_ID = "00000000-0000-0000-0002-000000000001"

AGENTS_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000219"
SHARED_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000100"
MANY_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000101"
MANY_DOCS_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000202"
NESTED_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000203"
READONLY_TEST_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000222"
USERS_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000208"
PWUSER1_THREADS_FOLDER_PATH_PART_ID = "00000000-0000-0000-0003-000000000210"

# In seed data, folder id == path_part_id
SHARED_FOLDER_ID = SHARED_FOLDER_PATH_PART_ID

COMPLEX_DOC_ID = "00000000-0000-0000-0004-000000000051"
COMPLEX_DOC_ACTIVE_VERSION_ID = "00000000-0000-0000-0005-000000000061"
FIRST_SIMPLE_DOC_ID = "00000000-0000-0000-0004-000000000001"
FIRST_SIMPLE_VERSION_ID = "00000000-0000-0000-0005-000000000001"
FIRST_SECTION_ID = "00000000-0000-0000-0006-000000000001"
FIRST_CHUNK_ID = "00000000-0000-0000-0007-000000000001"
SECOND_CHUNK_ID = "00000000-0000-0000-0007-000000000002"
CHUNK_101_ID = "00000000-0000-0000-0007-000000000101"

TAG_MANY_ID = "00000000-0000-0000-0012-000000000001"
TAG_NESTED_ID = "00000000-0000-0000-0012-000000000002"
TAG_SYSTEM_ID = "00000000-0000-0000-0012-000000000003"

PERMISSION_PWUSER3_SHARED_READ = "00000000-0000-0000-0013-000000000001"

NONEXISTENT_UUID = "00000000-0000-0000-0000-999999999999"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def cli_env(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """Session-scoped env dict with kscli config pointing at the e2e backend.

    Uses an isolated credentials path so tests don't interfere with user's
    local kscli setup.  The subprocess helper (run_kscli) strips any inherited
    ADMIN_API_KEY / KSCLI_BASE_URL from os.environ before merging these values,
    so the subprocess always targets localhost:28000 with the e2e admin key.
    """
    tmp = tmp_path_factory.mktemp("kscli")
    credentials_path = str(tmp / ".credentials")
    config_path = str(tmp / "config.json")
    return {
        "KSCLI_BASE_URL": E2E_BASE_URL,
        "ADMIN_API_KEY": E2E_ADMIN_API_KEY,
        "KSCLI_VERIFY_SSL": "false",
        "KSCLI_CREDENTIALS_PATH": credentials_path,
        "KSCLI_CONFIG": config_path,
    }


@pytest.fixture(scope="session")
def cli_authenticated(cli_env: dict[str, str]) -> dict[str, str]:
    """Authenticate as pwuser1 in their personal tenant. Returns env dict.

    All seed filesystem data (folders, documents, versions, sections, chunks,
    lineages, tags, threads) lives in pwuser1's personal tenant, so we
    authenticate there for the tests to find the seed data.
    """
    run_kscli_ok(
        [
            "assume-user",
            "--tenant-id", PWUSER1_TENANT_ID,
            "--user-id", PWUSER1_ID,
        ],
        env=cli_env,
        format_json=False,
    )
    return cli_env


@pytest.fixture(scope="session")
def kscli_parent_folder(
    cli_authenticated: dict[str, str],
) -> Generator[dict[str, Any]]:
    """Session-scoped folder at /agents/kscli_<hex> for test isolation.

    Creates the folder at session start; deletes it at session teardown.
    """
    result = run_kscli_ok(
        [
            "folders", "create",
            "--name", f"kscli_{secrets.token_hex(4)}",
            "--parent-path-part-id", AGENTS_FOLDER_PATH_PART_ID,
        ],
        env=cli_authenticated,
    )
    folder = result.json_output
    yield folder
    # Teardown: delete (suppress errors if already gone)
    run_kscli(
        ["folders", "delete", folder["id"]],
        env=cli_authenticated,
        format_json=False,
    )


@pytest.fixture
def isolation_folder(
    cli_authenticated: dict[str, str],
    kscli_parent_folder: dict[str, Any],
) -> Generator[dict[str, Any]]:
    """Per-test ephemeral folder for write-test isolation.

    Creates iso_{hex} under the session parent; cascade-deletes on teardown.
    """
    result = run_kscli_ok(
        [
            "folders", "create",
            "--name", f"iso_{secrets.token_hex(6)}",
            "--parent-path-part-id", kscli_parent_folder["path_part_id"],
        ],
        env=cli_authenticated,
    )
    folder = result.json_output
    yield folder
    run_kscli(
        ["folders", "delete", folder["id"]],
        env=cli_authenticated,
        format_json=False,
    )
