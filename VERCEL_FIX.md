# VERCEL_FIX.md — TrustLens deploy outage runbook

> Read this BEFORE spending time re-diagnosing. This exact problem has happened
> ~4 times. The cause and fix are now known. Don't repeat the investigation.

> ✅ **2026-06-11 — TRUE ROOT CAUSE PROVEN: it's the local ISP, NOT Vercel and
> NOT this repo.** Every code/config theory below (Deployment Protection, "alias
> cutover", `vercel.json` location, the `git.deploymentEnabled` block) was a RED
> HERRING. Each "fix" only *seemed* to work because the ISP route to Vercel's edge
> happened to recover during the ~90s build window.
>
> **The real cause:** the developer's ISP **intermittently blackholes Vercel's
> `*.vercel.app` edge IP ranges** (`64.29.17.x` / `216.198.79.x`). When it's
> flapping, the TCP handshake to those IPs never completes → `connect=0.000000s`
> timeout in `curl` and `ERR_CONNECTION_TIMED_OUT` in the browser. The deployment,
> build, alias, and DNS are all fine the entire time.
>
> **How it was proven (run this exact test if it recurs):**
> 1. `gh api .../deployments/<id>/statuses` → build `state: success`. Not a build issue.
> 2. Hit several hosts back-to-back from the same machine:
>    ```bash
>    curl -sS -o NUL -w "%{http_code} connect=%{time_connect}s\n" --max-time 12 https://trust-lens-ai-beta.vercel.app/
>    curl -sS -o NUL -w "%{http_code} connect=%{time_connect}s\n" --max-time 12 https://trustlens.vercel.app/   # UNRELATED vercel project
>    curl -sS -o NUL -w "%{http_code} connect=%{time_connect}s\n" --max-time 12 https://vercel.com/
>    ```
>    During a flap, **our site AND the unrelated `*.vercel.app` project BOTH
>    timed out together** (`connect=0`) — that rules out our project entirely.
> 3. **Turn on a VPN and re-run the same 3 curls → all returned `http=200`.**
>    Same hosts, same minute, only the network path changed. Case closed.
>
> 🎯 **THE FIX (network, do one of these):**
> - **Use a VPN** when the site appears "down" — instant workaround (verified).
> - Switch DNS won't help (DNS resolves fine); the block is at the IP/routing layer.
> - Long-term: report the `64.29.x` / `216.198.x` blackhole to the ISP, OR put the
>   site behind a **custom domain on Cloudflare** (different edge IPs your ISP
>   isn't dropping) — this also removes any `*.vercel.app` dependency.
>
> ⛔ **Do NOT** push empty commits / edit `vercel.json` / toggle Vercel settings to
> "fix" this — those did nothing; recovery was always just the ISP route healing.





---

## The symptom

Right after pushing to `master`, the live site goes "down":

- In the browser: `ERR_CONNECTION_TIMED_OUT` (page just hangs / never loads).
- From CLI: `curl https://trust-lens-ai-beta.vercel.app` returns
  `curl: (28) Connection timed out` with `connect=0.000000s` (the TCP socket
  never even opens).

It has happened **even when the commit changed ZERO frontend code.** That is the
key tell: **the breakage is the deploy/alias cutover, NOT your code.**

---

## Root cause (CONFIRMED 2026-06-11)

The production alias `trust-lens-ai-beta.vercel.app` was left **unbound** because
the non-standard `git.deploymentEnabled` block in `frontend/vercel.json` made
Vercel build the Production deployment but **skip the alias-assignment step**:

1. A push to `master` triggers a new Production build → finishes `state: success`.
2. With `"git": { "deploymentEnabled": { "master": true } }` present, the alias
   was intermittently **not** re-pointed to that successful deployment.
3. The edge then has no live deployment for the SNI host → it drops the TCP
   handshake → `connect=0.000000s` timeout (the socket never opens).
4. Removing that block (commit `e29465c`, minimal `vercel.json`) restored the
   default git integration, which auto-assigns the alias reliably → recovered to
   `http=200 connect=0.03s`.

Why a "revert" / empty commit used to "fix" it: the code was irrelevant — the new
push just happened to trigger an alias assignment that succeeded that time. It was
a coin flip, which is why the problem kept coming back.

> ⚠️ The sections below ("dual Preview+Production deploy", "Deployment
> Protection 401") describe the EARLIER, DISPROVEN theories. They are kept only
> as a record of what was ruled out — do NOT treat them as the cause.


### What is NOT the cause
- Not your component code (broke with no frontend change).
- Not DNS — `nslookup trust-lens-ai-beta.vercel.app` resolves fine
  (`64.29.17.131`, `216.198.79.131`).
- Not Vercel being down — `curl https://vercel.com` returns `200` in <1s.

---

## IMMEDIATE FIX (when the site is down right now)

Force a fresh production cutover. Cheapest reliable lever (no dashboard needed):

```bash
git commit --allow-empty -m "chore: force clean Vercel production redeploy"
git push origin master
```

Then wait ~60–120s for the build and poll until it returns 200:

```bash
# Windows cmd — repeat a few times over ~2 min
curl -sS -o NUL -w "http=%{http_code} connect=%{time_connect}s total=%{time_total}s\n" --max-time 15 https://trust-lens-ai-beta.vercel.app/
```

- `http=200` → recovered. Done.
- still `total=15s connect=0s` after ~3 min → cutover still stuck; either push
  another empty commit, or use the dashboard fix below.

### Inspect deployments without the dashboard (gh is authed)
```bash
gh api repos/mahdiebene/TrustLensAI/deployments --jq ".[0:5] | .[] | {id, ref, environment, created_at}"
```
If you see a `Preview` AND a `Production` deployment for the **same commit**, that
is the dual-deploy race described above.

---

## PERMANENT FIX (do this once to stop it recurring)

Pick **one**. In order of preference:

### Option A — Turn OFF Deployment Protection (1 click, recommended)
Vercel Dashboard → Project `trust-lens-ai` → **Settings → Deployment Protection**
→ **Vercel Authentication** → set to **Disabled** (or **Only Production
Deployments**) → **Save**.

- Removes the `401`/SSO state that the alias can get stuck on during cutover.
- Preview URLs become reachable (they already have unguessable hashes and aren't
  indexed — Vercel's documented design assumption).
- This is what most Vercel teams run with.

### Option B — Stop creating a Preview deploy on every master push
If the project is configured to deploy previews for the production branch, that
dual-deploy is what races. In **Settings → Git**, ensure only Production builds
on `master` (no overlapping preview/branch deploy rule for `master`).

### Option C — Skip Deployment Protection for the production domain only
Dashboard → Deployment Protection → **Protection Bypass / allowlist** the
production alias, so the alias never serves a gated response even mid-cutover.

> A + a post-deploy health check (below) is the combination that ends this class
> of incident.

---

## SAFE PUSH WORKFLOW (current rule: master is the only branch)

> Per project owner: **do NOT create feature branches.** Push to `master`.

1. (Optional but cheap) verify the build locally first:
   ```bash
   cd frontend && npm run dev   # eyeball the change at http://localhost:3000
   ```
2. Commit + push to master.
3. **Immediately run the post-deploy health check** and watch it for ~2 min:
   ```bash
   curl -sS -o NUL -w "http=%{http_code} connect=%{time_connect}s total=%{time_total}s\n" --max-time 15 https://trust-lens-ai-beta.vercel.app/
   ```
4. If it times out → run the IMMEDIATE FIX above (empty-commit redeploy).

---

## One-line health check (paste anytime)

```bash
curl -sS -o NUL -w "http=%{http_code} connect=%{time_connect}s total=%{time_total}s\n" --max-time 15 https://trust-lens-ai-beta.vercel.app/
```

| Result | Meaning |
|---|---|
| `http=200` | Healthy. |
| `http=401` | Alias serving a protection-gated deploy → apply Permanent Fix A. |
| `connect=0 total=15s` (timeout) | Alias unbound mid-cutover → IMMEDIATE FIX (empty-commit redeploy). |
| `http=404 DEPLOYMENT_NOT_FOUND` | Alias points at a deleted deploy → redeploy. |

---

## Quick facts (so the AI doesn't re-derive them)

- Production alias: `https://trust-lens-ai-beta.vercel.app`
- Vercel project: `trust-lens-ai` (scope `mahdis-projects-f2c28533`)
- GitHub repo: `mahdiebene/TrustLensAI`, only branch = `master`
- `gh` CLI is authenticated (scopes: repo, read:org, gist) — use it to inspect
  deployments instead of guessing.
- No `vercel` CLI installed locally; `tsc` is only available via Next, not standalone.
