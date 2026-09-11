# Agent notes for VATDTAI (Playwright_Python)

## Pushing code to GitHub (IMPORTANT)

`git push` to github.com does NOT work on this machine: EY's **Zscaler** proxy
blocks the git-receive-pack upload (returns HTTP 403 with a Zscaler block page),
and SSH to GitHub is also reset. Reads (clone/fetch) work fine.

`api.github.com` IS reachable, so push code using the **GitHub Git Data API**
instead of `git push`.

### How to push the latest local code
1. Commit changes locally as usual.
2. Make sure `gh` is signed in as the repo owner and it is the active account:
   - `gh auth status` (switch if needed: `gh auth switch --hostname github.com --user rajankumar2711`)
3. Run the helper:
   - `python docs/_api_push.py`

The script (`docs/_api_push.py`):
- Auto-detects the current branch tip and the remote tip.
- Uploads only changed blobs (base64) via `curl.exe` (handles the Zscaler cert),
  with retry/backoff and a resume cache.
- Builds the tree in chunks, creates one commit whose tree exactly matches the
  local tip, and fast-forwards the branch ref (no history overwrite).
- Verifies success by matching the remote commit's tree SHA to the local tip's
  tree SHA (content is byte-identical even though commit SHAs differ).

Defaults in the script: OWNER=`rajankumar2711`, REPO=`VATDTAI`,
BRANCH=`Rajan_AI_VAT_automation`. Edit these constants for other targets.

### Notes
- `configuration/config.ini` is gitignored (real secrets); `config.ini.example`
  must contain placeholders only - never real URLs/usernames/passwords.
- Do not attempt to bypass Zscaler; the API method above is the sanctioned path
  since it uses the normally allowed `api.github.com`.
