# kscli — long-term memory for Claude Code, OpenClaw, and any AI agent

**A semantic memory CLI for AI coding agents.** Drop `kscli` into a Claude Code hook, an OpenClaw lifecycle event, an Aider plugin, or any MCP server and your agent stops forgetting yesterday's work.

> **Keywords:** Claude Code memory · OpenClaw memory · agent memory · AI coding assistant memory · MCP semantic search · Aider memory · Continue memory · long-term context for LLMs · RAG CLI · vector memory for shell agents

Your agent restarts and loses everything it learned. `kscli` gives it persistent, searchable memory backed by [Knowledge Stack](https://knowledgestack.ai) — write from a hook, read before the next prompt.

```bash
# Claude Code (.claude/settings.json hooks)
"Stop":         "kscli documents ingest --file $CLAUDE_TRANSCRIPT --path-part-id $MEM"
"UserPromptSubmit": "kscli chunks search -q \"$CLAUDE_PROMPT\" -p $MEM -l 3 -f json"

# OpenClaw (~/.openclaw/hooks.json)
"on_session_end":  "kscli documents ingest --file $OPENCLAW_TRANSCRIPT --path-part-id $MEM"
"on_user_prompt":  "kscli chunks search -q \"$OPENCLAW_PROMPT\" -p $MEM -l 3 -f json"
```

Two shell calls, one Knowledge Stack folder per agent, zero new infrastructure.

---

## Why agents need this

Built-in agent memory is one of three things:

1. **A scratchpad inside the context window** — wiped at compaction, invisible across sessions, capped by token budget.
2. **A flat key-value store** — fine for `user_email`, useless for *"what did we conclude about the Postgres migration last Tuesday"*.
3. **A vector DB you self-hosted** — works, but now you maintain Qdrant, an embedding service, a chunker, and a permissions layer. For one feature.

`kscli` is option 4: a CLI in front of a managed semantic store that already has chunking, embeddings, multi-tenant ACLs, and lineage. The agent doesn't need to know any of that exists. It runs `documents ingest` to remember and `chunks search` to recall.

## What it gives you

| Agent capability | The `kscli` command behind it |
|---|---|
| **Remember a conversation** | `kscli documents ingest --file transcript.md --path-part-id <agent>` |
| **Recall by meaning, not keyword** | `kscli chunks search -q "$prompt" -p <agent> -l 5` |
| **Per-agent / per-project namespaces** | `kscli folders create --name "agent:openclaw:project-x"` |
| **Forget specific things** | `kscli documents delete <id>` |
| **Inspect what the agent knows** | `kscli folders list -p <agent> -f tree` |
| **Audit which memory shaped a reply** | `kscli chunk-lineages describe <chunk>` |

Chunks come back with citations — file, section, score — so the agent can cite *why* it remembered something instead of hallucinating its provenance.

## A real session

```bash
# One-time: install + auth + carve out a memory folder for this agent.
uv tool install kscli
kscli login --api-key sk-user-...
MEM=$(kscli folders create --name "openclaw-memory" -f id-only)

# OpenClaw runs a coding task. At session end, write the transcript + diff to memory.
kscli documents ingest \
  --file ~/.openclaw/sessions/2026-04-29-refactor-auth.md \
  --path-part-id $MEM \
  --name "Refactor auth middleware (2026-04-29)"

# Tomorrow, OpenClaw is asked: "why did we drop the cookie-based session?"
# Its on-start hook runs:
kscli chunks search \
  -q "why did we drop the cookie-based session" \
  -p $MEM -l 3 -f json
# → [{"score": 0.91, "content": "...switched to JWT because the multi-tenant
#     cookie collision broke SSO for tenant 14...", "document": "Refactor auth..."}]
```

That JSON goes straight into the agent's system prompt as recalled context. The agent now answers grounded in its actual past work — not a hallucination, not "I don't have memory of previous conversations."

## Wire it into your agent in 30 seconds

The integration is identical across runtimes — write on session end, read on user prompt. Pick yours.

### Claude Code

`.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{
      "command": "kscli documents ingest --file \"$CLAUDE_TRANSCRIPT_PATH\" --path-part-id $KS_MEMORY --name \"Claude Code session $(date +%F)\""
    }],
    "UserPromptSubmit": [{
      "command": "kscli chunks search -q \"$CLAUDE_USER_PROMPT\" -p $KS_MEMORY -l 5 -f json"
    }]
  }
}
```

The `UserPromptSubmit` hook's stdout is injected as additional context — Claude Code now sees the five most relevant past moments before every reply.

### OpenClaw

`~/.openclaw/hooks.json`:

```json
{
  "on_session_end": "kscli documents ingest --file $OPENCLAW_TRANSCRIPT --path-part-id $KS_MEMORY --name \"$OPENCLAW_SESSION_TITLE\"",
  "on_user_prompt": "kscli chunks search -q \"$OPENCLAW_PROMPT\" -p $KS_MEMORY -l 5 -f json"
}
```

### Aider, Continue, Cursor agents, MCP servers, custom orchestrators

Anything that can spawn a subprocess and read JSON works. `kscli` makes no assumptions about the host — it's the universal memory primitive.

Set `KS_MEMORY` once to the path-part-id from `kscli folders create` and the agent has memory.

## Agent-friendly by design

`kscli` was built assuming an LLM, not a human, would often be the caller:

- **Predictable JSON.** Every command supports `-f json`. No surprise prose, no ANSI colors when piped.
- **Stable exit codes.** `0` success, `2` auth, `3` not found, `4` validation. An agent can branch on them without parsing stderr.
- **`kscli agent-help`** prints a compact, token-efficient reference designed for an agent to read into its own context.
- **`-f id-only`** for chaining: feed one command's output straight into the next via `xargs`.
- **No interactive prompts.** Every flag has a non-interactive equivalent. No `tty` required.

## Why not just use the SDK?

If you're writing the agent in Python and want to embed Knowledge Stack calls in-process, use [`ksapi`](https://pypi.org/project/ksapi/). If your agent runtime is *anything else* — Claude Code hooks, OpenClaw, Aider plugins, a Continue extension, a Go binary, a TypeScript orchestrator, an MCP server, a Bash cron job — `kscli` is the universal interface. Shell out, get JSON, move on.

## Compared to other agent-memory approaches

| Approach | Setup cost | Semantic search | Multi-tenant | Citations | Works with non-Python agents |
|---|---|---|---|---|---|
| Context-window scratchpad | Zero | No | No | No | Yes |
| Flat KV (`memory.json`) | Low | No | No | No | Yes |
| `mem0` / `letta` library | Medium | Yes | DIY | Partial | Python-only |
| Self-hosted Qdrant + chunker + embedder | High | Yes | DIY | DIY | Yes |
| **`kscli` + Knowledge Stack** | **One `uv tool install`** | **Yes** | **Yes** | **Yes (chunk lineage)** | **Yes** |

---

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv tool install kscli      # isolated venv, on PATH, no project pollution
kscli login --api-key sk-user-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
kscli whoami
```

API keys: **[app.knowledgestack.ai](https://app.knowledgestack.ai) → My Account → API Keys**. User-scoped, revocable, never logged.

## Command surface

Run `kscli <group> --help` for verbs and flags. The groups that matter for agent memory:

| Resource | What it's for in a memory model |
|---|---|
| `folders` | Namespaces — one per agent, per project, per user. |
| `documents` | A unit of memory (transcript, diff, postmortem, ADR). `ingest` writes; `delete` forgets. |
| `chunks` | The retrieval primitive. `search` is recall. |
| `tags` | Cross-cutting labels (`urgent`, `decision`, `incident`). |
| `chunk-lineages` | Audit trail — *why* the agent remembered this. |
| `threads`, `thread-messages` | If you want conversation memory as first-class objects. |
| `workflows` | Track ingestion to know when a memory is searchable. |

## Output formats for piping

```bash
kscli chunks search -q "..." -f json   # default for agents
kscli folders list -f id-only          # chain via xargs
kscli folders list -f tree             # human inspection
kscli folders list -f yaml             # config-friendly
```

`KSCLI_FORMAT=json` makes JSON the default for the whole shell.

## Config

| Env var | Default | Purpose |
|---|---|---|
| `KSCLI_BASE_URL` | `https://api-staging.knowledgestack.ai` | API endpoint |
| `KSCLI_FORMAT` | `table` | Default output format |
| `KSCLI_VERIFY_SSL` | `true` | TLS verification |
| `KSCLI_CONFIG` | `~/.config/kscli/config.json` | Config file |
| `KSCLI_CREDENTIALS_PATH` | `/tmp/kscli` | Credentials dir |

`flags > env > config > defaults`. Switch environments per-call with `kscli --base-url ...`.

## Development

```bash
make install-dev      # uv sync + pre-commit
make pre-commit       # lint + typecheck + test
make e2e-test         # against a live ks-backend (see docs/e2e-testing.md)
```

## Docs

| Page | Covers |
|---|---|
| [Quickstart](docs/quickstart.md) | First memory written and recalled, end-to-end |
| [Authentication](docs/authentication.md) | API keys, credential caching, TLS |
| [Configuration](docs/configuration.md) | Env vars, config file, precedence |
| [Recipes](docs/recipes.md) | Bulk ingest, piping, CI jobs |
| [Design patterns](docs/design_patterns.md) | Resource-first routing, SDK wrapper |
| [E2E testing](docs/e2e-testing.md) | Running and writing end-to-end tests |

Canonical site: **[docs.knowledgestack.ai/kscli](https://docs.knowledgestack.ai/kscli)**.

## License

See [LICENSE](LICENSE).
