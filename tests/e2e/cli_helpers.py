"""Subprocess helpers for invoking kscli in e2e tests."""

import contextlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any

# Env vars stripped from the inherited environment before merging test overrides.
# Prevents the developer's shell config from contaminating e2e subprocess calls.
_SANITIZED_KEYS = frozenset({
    "USER_API_KEY",
    "KSCLI_BASE_URL",
    "KSCLI_VERIFY_SSL",
    "KSCLI_CREDENTIALS_PATH",
    "KSCLI_CONFIG",
    "KSCLI_FORMAT",
    "KSCLI_CA_BUNDLE",
})


@dataclass
class CliResult:
    """Result of a kscli subprocess invocation."""

    exit_code: int
    stdout: str
    stderr: str
    json_output: Any = field(default=None)


def run_kscli(
    args: list[str],
    *,
    env: dict[str, str],
    timeout: int = 30,
    format_json: bool = True,
) -> CliResult:
    """Run kscli as a subprocess and return the result.

    The inherited os.environ is sanitized (kscli/admin keys removed) before
    the test-provided ``env`` dict is merged on top, so the subprocess always
    uses exactly the values the test intends.

    Args:
        args: CLI arguments (e.g. ["folders", "list"]).
        env: Environment variables (merged on top of sanitized os.environ).
        timeout: Subprocess timeout in seconds.
        format_json: If True, prepend --format json to args.
    """
    cmd = ["kscli"]
    # Always enforce the base URL via CLI flag (highest precedence),
    # so config-file writes from settings tests can't redirect requests.
    base_url = env.get("KSCLI_BASE_URL")
    if base_url:
        cmd.extend(["--base-url", base_url])
    if format_json:
        cmd.extend(["--format", "json"])
    cmd.extend(args)

    # Start from os.environ, strip vars that could contaminate, then overlay test env.
    merged_env = {k: v for k, v in os.environ.items() if k not in _SANITIZED_KEYS}
    merged_env.update(env)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=merged_env,
        check=False,
    )

    json_output = None
    if proc.stdout.strip():
        with contextlib.suppress(json.JSONDecodeError):
            json_output = json.loads(proc.stdout)

    return CliResult(
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        json_output=json_output,
    )


def run_kscli_ok(
    args: list[str],
    *,
    env: dict[str, str],
    timeout: int = 30,
    format_json: bool = True,
) -> CliResult:
    """Run kscli and assert exit code 0."""
    result = run_kscli(args, env=env, timeout=timeout, format_json=format_json)
    assert result.exit_code == 0, (
        f"Expected exit code 0, got {result.exit_code}.\n"
        f"Command: kscli {' '.join(args)}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    return result


def run_kscli_fail(
    args: list[str],
    *,
    env: dict[str, str],
    expected_code: int | None = None,
    timeout: int = 30,
    format_json: bool = True,
) -> CliResult:
    """Run kscli and assert non-zero exit code."""
    result = run_kscli(args, env=env, timeout=timeout, format_json=format_json)
    assert result.exit_code != 0, (
        f"Expected non-zero exit code, got 0.\n"
        f"Command: kscli {' '.join(args)}\n"
        f"stdout: {result.stdout}"
    )
    if expected_code is not None:
        assert result.exit_code == expected_code, (
            f"Expected exit code {expected_code}, got {result.exit_code}.\n"
            f"Command: kscli {' '.join(args)}\n"
            f"stderr: {result.stderr}"
        )
    return result
