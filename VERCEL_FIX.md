# VERCEL_FIX.md — TrustLens deploy outage runbook

> Read this BEFORE spending time re-diagnosing. This exact problem has happened
> ~4 times. The cause and fix are now known. Don't repeat the investigation.

> ⚠️ **2026-06-11 UPDATE:** Deployment Protection was set to **Disabled**, which
> recovered the alias once — but the timeout RETURNED ~15 min later with **no new
> deploy and protection still off**. So protection was NOT the (only) cause. The
> auto-generated `trust-lens-ai-beta.vercel.app` alias is intermittently going
> unbound at Vercel's edge. An empty-commit redeploy rebinds it each time
> (`d0dcdbb` did so → `http=200`), but this is a band-aid.
>
> 🎯 **DURABLE FIX (recommended): add a custom domain.** A real custom domain
> (e.g. `trustlens.app` / a subdomain) gets a stable alias binding that does not
> suffer this auto-`*.vercel.app` cutover flakiness. Until then: when it times
> out, push an empty commit (IMMEDIATE FIX below) and it comes back in ~90s.
> Keep Deployment Protection **Disabled** regardless.



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

## Root cause (confirmed)

The production alias `trust-lens-ai-beta.vercel.app` is unbound during a bad
**alias cutover**:

1. A push to `master` triggers Vercel to build a **new Production deployment**.
2. We observed (via `gh api .../deployments`) that **one push created TWO
   deployments for the same commit** — a `Preview` *and* a `Production`.
3. **Deployment Protection (Vercel Authentication) is ENABLED** on this project,
   so **Preview** deployments are gated (`401` → SSO redirect loop).
4. During the cutover window the alias can momentarily route to the *protected*
   preview deployment (or to no live deployment yet, because the previous
   Production deploy is already torn down). A protected/half-attached deployment
   refuses/hangs the connection at the edge → **TCP connection timeout**.
5. It does **not** always self-heal — the alias stays stuck until a **fresh,
   clean cutover** rebinds it to a healthy settled deployment.

Why a "revert" used to fix it: the revert's code was irrelevant — its only real
effect was **triggering a new cutover** to an already-warm deployment.

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
