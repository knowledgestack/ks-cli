# Recipes

> 📚 **Hosted version:** [docs.knowledgestack.ai/kscli/recipes](https://docs.knowledgestack.ai/kscli/recipes) — includes screencasts for the bulk-ingest and CI recipes.

<p align="center">
  <img src="https://docs.knowledgestack.ai/assets/kscli/recipes-bulk-ingest.gif"
       alt="Bulk ingesting a directory of PDFs with kscli folders bulk-ingest"
       width="720" />
</p>

Common `kscli` workflows. Every snippet assumes you've already run `kscli login`.

## Bulk ingest a directory of PDFs

The `folders bulk-ingest` verb uploads every file in a local directory to a target folder in one shot.

```bash
# Dry-run first — prints what would be uploaded without touching the server
kscli folders bulk-ingest ~/Documents/annual-reports \
    --folder-id <tutorial-folder-id> \
    --extensions .pdf \
    --dry-run

# Execute
kscli folders bulk-ingest ~/Documents/annual-reports \
    --folder-id <tutorial-folder-id> \
    --extensions .pdf,.docx,.md
```

Pair with `kscli workflows list --limit 50` to watch the ingestion workflows drain.

## Search from a shell script

```bash
#!/usr/bin/env bash
set -euo pipefail

QUERY="${1:?usage: search.sh <query>}"
FOLDER="${KSCLI_SEARCH_FOLDER:-<your-folder-path-part-id>}"

kscli chunks search \
    --query "$QUERY" \
    --parent-path-ids "$FOLDER" \
    --limit 10 \
    --format json \
  | jq -r '.[] | "[\(.score | tostring | .[0:4])] \(.content)"'
```

Usage:

```bash
./search.sh "quarterly revenue drivers"
```

## Pipe IDs into another command

`--format id-only` emits one ID per line — perfect for `xargs`.

```bash
# Delete every empty folder under a parent
kscli folders list --parent-path-part-id <parent> -f id-only \
  | xargs -I {} kscli folders delete {}

# Re-run every failed workflow from the last hour
kscli workflows list --status failed -f id-only \
  | xargs -I {} kscli workflows rerun {}
```

## Extract the top search hit as structured data

```bash
kscli chunks search -q "latency SLO" --parent-path-ids <id> -f json \
  | jq '{id: .[0].id, score: .[0].score, content: .[0].content}'
```

## Ingest a document and wait for it to be searchable

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE="$1"
FOLDER="$2"

result=$(kscli documents ingest --file "$FILE" --path-part-id "$FOLDER" -f json)
workflow_id=$(echo "$result" | jq -r '.workflow_id')

echo "Ingested. Waiting for workflow $workflow_id..."
until [ "$(kscli workflows describe "$workflow_id" -f json | jq -r .status)" = "completed" ]; do
  sleep 2
done
echo "Ready to search."
```

## Run a search from GitHub Actions

```yaml
# .github/workflows/search-knowledge.yml
name: Query knowledge base

on:
  workflow_dispatch:
    inputs:
      query:
        description: "Search query"
        required: true

jobs:
  search:
    runs-on: ubuntu-latest
    steps:
      - uses: astral-sh/setup-uv@v3
      - name: Install kscli
        run: uv tool install kscli
      - name: Log in
        env:
          KSCLI_API_KEY: ${{ secrets.KSCLI_API_KEY }}
        run: kscli login --api-key "$KSCLI_API_KEY" --url https://api.knowledgestack.ai
      - name: Search
        run: |
          kscli chunks search \
            --query "${{ inputs.query }}" \
            --parent-path-ids ${{ vars.KSCLI_FOLDER_ID }} \
            --format json \
            --limit 5 > results.json
      - uses: actions/upload-artifact@v4
        with:
          name: search-results
          path: results.json
```

Store the key in repository secrets as `KSCLI_API_KEY` and the folder ID in repository variables as `KSCLI_FOLDER_ID`.

## Tag documents for filtered search

```bash
# Create a tag
tag_id=$(kscli tags create --name "q4-reports" -f id-only)

# Attach it to a folder (propagates to every document inside)
kscli tags attach --tag-id "$tag_id" --path-part-id <folder-path-part-id>

# Filter search by tag
kscli chunks search \
    --query "revenue growth" \
    --tag-ids "$tag_id" \
    --limit 5
```

## Copy a document between folders (by re-ingesting)

There is no `move` verb — download the source file locally, then ingest under the new folder.

```bash
# 1. Get the current version's contents
kscli document-versions contents <version-id> > /tmp/copy.bin

# 2. Re-ingest under the target folder
kscli documents ingest \
    --file /tmp/copy.bin \
    --path-part-id <new-folder-path-part-id> \
    --name "Copied report"
```

## Switch between local dev and prod quickly

Keep credentials for each environment in separate directories:

```bash
# Local dev
export KSCLI_CREDENTIALS_PATH=~/.config/kscli-local
export KSCLI_CONFIG=~/.config/kscli-local/config.json
kscli login --api-key sk-user-local... --url http://localhost:8000

# Production
export KSCLI_CREDENTIALS_PATH=~/.config/kscli-prod
export KSCLI_CONFIG=~/.config/kscli-prod/config.json
kscli login --api-key sk-user-prod... --url https://api.knowledgestack.ai
```

Wrap the two in shell functions (`kscli-local`, `kscli-prod`) to flip between them.

## YAML for config review, table for humans, JSON for scripts

```bash
kscli settings show --format yaml        # quick eyeball check
kscli folders list --format table        # daily use
kscli folders list --format json | jq    # scripting
kscli folders list --format tree         # hierarchy at a glance
```

## Troubleshoot a stuck ingestion

```bash
# Find recent workflows
kscli workflows list --limit 10

# Drill into one
kscli workflows describe <workflow-id> --format yaml

# Cancel and re-run
kscli workflows cancel <workflow-id>
kscli workflows rerun  <workflow-id>
```

## See also

- **[docs.knowledgestack.ai/kscli](https://docs.knowledgestack.ai/kscli)** — full docs home with video tutorials
- [Quickstart](quickstart.md) — the happy path for new users
- [Authentication](authentication.md) — API key flow, credential storage
- [Configuration](configuration.md) — env vars, precedence, TLS
