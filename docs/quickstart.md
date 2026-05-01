# Quickstart

> 📚 **Reading this on GitHub?** The same page with embedded videos, zoomable screenshots, and a searchable TOC lives at **[docs.knowledgestack.ai/kscli/quickstart](https://docs.knowledgestack.ai/kscli/quickstart)**.

Go from nothing installed to a working semantic search against your own documents in about two minutes. Every command below is real — copy, paste, substitute the placeholder IDs.

<p align="center">
  <a href="https://docs.knowledgestack.ai/kscli/demo">
    <img src="https://docs.knowledgestack.ai/assets/kscli/quickstart-hero.gif"
         alt="End-to-end quickstart in 45 seconds"
         width="760" />
  </a>
</p>

## Prerequisites

- Python **3.12+** (`python --version`)
- [**uv**](https://docs.astral.sh/uv/) installed (`uv --version`). On macOS: `brew install uv`.
- A Knowledge Stack account at **[app.knowledgestack.ai](https://app.knowledgestack.ai)** — sign up with email/password or Google SSO.

## 1. Install `kscli`

```bash
uv tool install kscli
kscli --version
```

`uv tool install` builds an isolated venv and puts `kscli` on your `PATH`. Upgrade later with `uv tool upgrade kscli`.

## 2. Create an API key

<p align="center">
  <img src="https://docs.knowledgestack.ai/assets/kscli/api-key-create.gif"
       alt="Creating an API key from the My Account → API Keys dashboard"
       width="720" />
</p>

`kscli` authenticates with a user-scoped API key. Keys begin with `sk-user-` and carry your user's permissions.

1. Open **[app.knowledgestack.ai](https://app.knowledgestack.ai)** and sign in.
2. Click your avatar (top-right) → **My Account**.
3. Open the **API Keys** tab.
4. Click **Create API key**.
5. Label the key — pick something you'll still recognize six months from now (e.g. `kscli on macbook`, `kscli ingest job`).
6. **Copy the key now.** It is shown exactly once. If you lose it, revoke and create a new one.

> ⚠️ Treat the key like a password. Anyone with the key can act as you, including uploading and deleting documents.

## 3. Log in

<p align="center">
  <img src="https://docs.knowledgestack.ai/assets/kscli/login.gif"
       alt="kscli login validating the key and writing credentials"
       width="720" />
</p>

```bash
kscli login --api-key sk-user-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

What happens:

1. `kscli` calls `GET /users/me` with the key as a bearer token.
2. On success, the key is written to `/tmp/kscli/.credentials` with mode `0600`.
3. The resolved base URL and TLS settings are saved to `~/.config/kscli/config.json`.
4. You should see `Logged in successfully (https://api-staging.knowledgestack.ai).`

Verify:

```bash
kscli whoami
kscli whoami --format yaml   # includes tenant_id, email, roles
```

> **Different environment?** Pass `--url http://localhost:8000` (dev) or `--url https://api.knowledgestack.ai` (prod) to `login`. It is persisted to the config file.

## 4. Find a folder to put documents in

Every document lives under a folder. Every tenant has a root folder; you can create subfolders.

```bash
# See the whole folder tree
kscli folders list --format tree
```

Pick a folder, grab its `path_part_id` (not `id` — see "PathPart vs domain ID" at the bottom of this page):

```bash
kscli folders describe <folder-id> --format yaml
```

Create a dedicated subfolder for this tutorial:

```bash
kscli folders create \
    --name "kscli tutorial" \
    --parent-path-part-id <parent-path-part-id>
```

The response includes `id` and `path_part_id`. Save the `path_part_id` of the new folder — the next step needs it.

## 5. Ingest a document

<p align="center">
  <img src="https://docs.knowledgestack.ai/assets/kscli/ingest.gif"
       alt="Ingesting a PDF and watching the workflow progress"
       width="720" />
</p>

Grab any PDF from your Downloads folder and upload it.

```bash
kscli documents ingest \
    --file ~/Downloads/some-report.pdf \
    --path-part-id <tutorial-folder-path-part-id> \
    --name "Some report"
```

Ingestion runs in the background on the server: the file is uploaded, queued onto an ingestion workflow, then chunked, embedded, and indexed. `kscli` returns immediately with the new document's `id` and a workflow handle.

Watch the workflow progress:

```bash
kscli workflows list --limit 5
kscli workflows describe <workflow-id>
```

When the workflow is `completed`, the document is fully indexed and searchable. Small PDFs take seconds; large ones take a minute or two.

## 6. Run your first semantic search

<p align="center">
  <img src="https://docs.knowledgestack.ai/assets/kscli/search.gif"
       alt="kscli chunks search rendering a Rich table of ranked results"
       width="720" />
</p>

```bash
kscli chunks search \
    --query "what does the document say about revenue" \
    --parent-path-ids <tutorial-folder-path-part-id> \
    --limit 5
```

You'll get a Rich-table of top chunks sorted by relevance score. The `content` column holds the actual text that matched. Try:

```bash
# JSON for scripting
kscli chunks search -q "revenue" --parent-path-ids <id> -f json | jq '.[0]'

# Full-text instead of dense semantic
kscli chunks search -q "exact phrase" --search-type full_text --parent-path-ids <id>

# Filter by chunk type
kscli chunks search -q "quarterly results" --chunk-types TABLE --parent-path-ids <id>
```

## 7. Browse what got ingested

```bash
# Documents in the folder
kscli documents list --parent-path-part-id <tutorial-folder-path-part-id>

# The latest version of a specific document
kscli documents describe <document-id> --format yaml

# All chunks in that version
kscli chunks version-chunk-ids <version-id>
```

## 8. Clean up (optional)

```bash
kscli documents delete <document-id>
kscli folders delete <folder-id>
kscli logout
```

`kscli logout` removes the credentials file. The API key on the server is still valid — revoke it from the dashboard if you're done with it.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Not authenticated. Run: kscli login --api-key <key>` | No credentials file | Run `kscli login --api-key ...` |
| Exit code `2`, `Session expired...` | Key revoked or invalid | Create a new key in the dashboard and re-login |
| `SSL certificate verification failed` | Self-signed backend / corporate proxy | Set `KSCLI_CA_BUNDLE` or `KSCLI_VERIFY_SSL=false` for dev |
| `kscli: command not found` after install | `uv tool` bin directory not on `PATH` | Run `uv tool update-shell` and open a new terminal |
| Ingestion stuck in `running` | Worker not picking up tasks | Check backend workflow worker — `kscli workflows describe <id>` |
| `422` on `folders create` | Passed a folder `id` where a `path_part_id` is required | Use `--format yaml` on `describe` to see both |

## PathPart vs domain ID

This is the one conceptual bump newcomers hit. Every folder has **two** UUIDs:

- **`id`** — the folder's own record ID. Use with `describe`, `update`, `delete`.
- **`path_part_id`** — its position in the folder tree. Use with anything that needs a *parent* — creating a child folder, ingesting a document under the folder, scoping a search.

```bash
kscli folders describe  <folder_id>                          # id
kscli folders update    <folder_id> --name "Renamed"         # id
kscli folders delete    <folder_id>                          # id

kscli folders create    --parent-path-part-id <path_part_id> # path_part_id
kscli documents ingest  --path-part-id       <path_part_id>  # path_part_id
kscli chunks search     --parent-path-ids    <path_part_id>  # path_part_id
```

`kscli folders describe ... --format yaml` prints both so you can copy the right one.

## Next steps

- **Everything else is at [docs.knowledgestack.ai/kscli](https://docs.knowledgestack.ai/kscli)** — searchable reference, full video tutorials, release notes.
- [Recipes](recipes.md) — bulk ingest a directory, pipe into jq, run searches from CI
- [Authentication](authentication.md) — credential storage, TLS, exit codes
- [Configuration](configuration.md) — env vars, config file, precedence
- [Design patterns](design_patterns.md) — how the CLI is wired internally
