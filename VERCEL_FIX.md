# VERCEL_FIX.md — TrustLens deploy outage runbook

> Read this BEFORE spending time re-diagnosing. This exact problem has happened
> ~4 times. The cause and fix are now known. Don't repeat the investigation.

> ✅ **2026-06-11 — ACTUAL ROOT CAUSE FOUND & FIXED (commit `e29465c`).**
> Earlier theories (Deployment Protection, "alias cutover", root-vs-frontend
> `vercel.json` location) were all RED HERRINGS — each "fix" only appeared to work
> because the redeploy happened to finish during a good window.
>
> **The real cause:** `frontend/vercel.json` contained a non-standard
> `"git": { "deploymentEnabled": { "master": true } }` block (added in commits
> `3c8e189`/`1eb73c1`, right before the outages began). With that block present,
> Vercel intermittently **created the production deployment but skipped assigning
> the `trust-lens-ai-beta.vercel.app` alias to it** — so the build showed
> `state: success` while the hostname refused TCP connections at the edge.
>
> **How it was proven (do this exact test if it recurs):**
> - Build status was `success` ("Deployment has completed") — so NOT a build error.
> - `curl` to BOTH Vercel edge IPs (`64.29.17.131`, `216.198.79.131`) for OUR
>   host → `connect=0.000000s` timeout, BUT `vercel.com`, `google.com`, and a
>   DIFFERENT project `trustlens.vercel.app` all returned `200` instantly from the
>   same machine/network. ⇒ network path fine, only OUR alias unbound ⇒ Vercel
>   alias-assignment, not ISP, not code.
>
> **The fix:** delete the `git.deploymentEnabled` block; keep `vercel.json`
> minimal (`{ "$schema": ..., "framework": "nextjs" }`). Default git integration
> then auto-assigns the production alias reliably. After pushing `e29465c` the
> alias recovered to `http=200 connect=0.03s` and stayed stable.
>
> 🎯 **Still recommended for extra safety:** add a real custom domain — custom
> domains don't depend on the auto-`*.vercel.app` assignment at all.




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
