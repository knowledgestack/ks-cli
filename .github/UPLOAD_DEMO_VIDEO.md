# Uploading the kscli demo video

The hero video in `README.md` is served from **GitHub's user-attachments CDN** — the same storage backend that powers drag-and-drop uploads in issues and PRs. That URL is backed by GitHub, cached globally, costs nothing, does not bloat the repo, and renders inline on every `README.md` view on github.com.

This document is the playbook for replacing the placeholder video URL after the Remotion render completes.

## Why user-attachments and not something else?

| Option | Renders inline on github.com? | Repo bloat? | CDN-backed? | Effort |
|---|---|---|---|---|
| **`user-attachments` URL in `<video>` tag** ✅ | Yes | None | Yes (GitHub) | One-time upload |
| `<img>` GIF from external CDN | Yes (as GIF, not a real video) | None | Depends | Medium |
| `<video>` with raw.githubusercontent.com path | Partial (depends on size) | Yes (MP4 in repo) | Yes | Low |
| GitHub Release asset | Not inline | No | Yes | Medium |
| External `<video>` URL (S3, Cloudflare, etc.) | **No** — GitHub sanitizes cross-origin video src | None | Varies | High |

GitHub's README renderer only allows HTML5 `<video>` tags whose `src` points at `github.com/user-attachments/assets/...` or a raw file inside the same repo. Anything else is stripped. That makes `user-attachments` the correct answer.

## How to upload

**You need:** the final `kscli-demo.mp4` from the Remotion render (spec: [ks-marketing/content/2026-04-15-ks-cli-demo-video/brief.md](../../ks-marketing/content/2026-04-15-ks-cli-demo-video/brief.md)).

**Target format:** H.264 MP4, 1920×1080 @ 30fps, ~45 seconds, under 10 MB (user-attachments hard cap is 10 MB per file — tune the Remotion render bitrate if you're over).

### Step-by-step

1. Go to [github.com/knowledgestack/ks-cli/issues/new](https://github.com/knowledgestack/ks-cli/issues/new).
2. In the issue body, **drag `kscli-demo.mp4` directly into the text area** (or paste it from the clipboard).
3. GitHub uploads the file and rewrites it in-place to a markdown image link like:
   ```
   ![kscli-demo](https://github.com/user-attachments/assets/3f1b2c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d)
   ```
4. **Copy the URL** — only the `https://github.com/user-attachments/assets/<uuid>` part, without the markdown syntax.
5. **Do not submit the issue.** Close the draft (the URL stays live even if the issue is never created — user-attachments are not tied to issue lifecycle).
6. Open `README.md` and find the `HERO MEDIA` HTML comment block. The README currently has **two blocks**:
    - an active `<a><img></a>` fallback that shows a clickable poster
    - a commented-out `<video>` block marked *"once the Remotion MP4 is uploaded..."*

   **Swap them:**
    - Delete the active `<a><img></a>` block.
    - Uncomment the `<video>` block (remove the wrapping `<!--` / `-->`).
    - Paste the copied URL in place of `PASTE-UUID-HERE` on the `src` attribute.
7. Do the same swap in `ks-docs/cli/index.mdx` — it has the same two blocks inside `{/* ... */}` MDX comments.
8. Commit and open a PR against both repos titled `docs: wire up demo video`.

### One-liner sanity check

Before pushing, preview the `<video>` tag renders correctly by pasting the full `<video ...>` block into a **new** issue body on the same repo. If it plays in the preview pane, it will play in the README.

## Updating the poster frame

The `<video>` tag also references a `poster=` image (shown before the user hits play). The render pipeline outputs `hero-poster.png` alongside the MP4 — upload it using the same drag-and-drop trick, or publish it to `docs.knowledgestack.ai/assets/kscli/hero-poster.png` via the ks-docs deploy (see [ks-docs cli section](../../ks-docs/cli/index.mdx)).

## Rotating or removing the video

user-attachments URLs never expire and are not revocable individually. To change the video, upload a new one and replace the URL — the old asset stays on GitHub's CDN but is no longer referenced.

## Related

- [README.md](../README.md) — the actual embed
- [ks-marketing brief](../../ks-marketing/content/2026-04-15-ks-cli-demo-video/brief.md) — the Remotion video spec
- [Mintlify cli/index.mdx](../../ks-docs/cli/index.mdx) — the same video embedded in the hosted docs site
