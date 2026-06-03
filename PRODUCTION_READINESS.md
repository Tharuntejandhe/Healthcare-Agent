# Production Readiness — MediHealth

Status of the gaps found in the production-readiness audit. Items are split into
**fixed in code** (done in this branch) and **requires your action** (legal /
billing / infra changes that code cannot perform).

> ⚠️ **Real-PHI gate.** Even with everything below "fixed in code", this app is
> **not** cleared to handle real US patient data until the *Requires your action*
> HIPAA items are complete. Until then, run it on **synthetic / your-own test
> data only.**

Legend: ✅ done · 🔧 your action required · 🟡 recommended follow-up (code)

---

## ✅ Fixed in code (this branch)

### Authentication & sessions
- ✅ **Revocable tokens.** JWTs now carry a `jti` + `ver` claim. `POST /auth/logout`
  denylists the `jti` (single-session); `POST /auth/logout-all` bumps the user's
  `token_version` (kills every session). A stolen token is no longer valid for 8
  days. — `core/security.py`, `api/deps.py`, `models/token.py`, `crud/crud_token.py`
- ✅ **Password change invalidates other sessions** and returns a fresh token.
  — `api/v1/users.py`, `crud/crud_user.set_password`
- ✅ **Algorithm pinning** on decode (rejects `alg:none` / RS256→HS256 confusion).
- ✅ **Real logout in the UI** calls the server to revoke (was localStorage-only).
  — `frontend/src/lib/auth.ts`, `Sidebar.tsx`, `profile/page.tsx`
- ✅ **Idle auto-logoff** after 15 min inactivity (HIPAA §164.312(a)(2)(iii)).
  — `frontend/src/components/providers/IdleTimeout.tsx`

### PHI handling
- ✅ **PHI no longer cached in `localStorage`.** Reports are persisted in a new
  `documents` table and listed via `GET /documents`; the dashboard fetches from
  the API and scrubs any legacy `patient_reports_*` keys. — `models/document.py`,
  `api/v1/documents.py`, `frontend/src/app/dashboard/page.tsx`
- ✅ **PHI access audit log** (§164.312(b)): who/what/when/IP/request-id recorded
  for upload, view, delete, report, risk, chat, vision, speech, login, logout,
  export, deletion. — `models/audit.py`, `services/audit.py`, all routers
- ✅ **Right of Access export** (`GET /users/me/export`) and **account deletion**
  (`DELETE /users/me`) that purges files + FAISS index + metadata. — `api/v1/users.py`
- ✅ **User activity view** (`GET /users/me/activity`) for transparency.

### Correctness / reliability
- ✅ **FAISS write safety.** Per-user lock around load→add→save + atomic
  temp-dir-then-rename persistence (fixes silent lost-update/corruption on
  concurrent uploads). Added `delete_user_index`. — `services/ai/rag.py`
- ✅ **CVE-2024-5998** mitigated: pinned `langchain-community>=0.2.9`.

### AI safety
- ✅ **Standardized medical disclaimer** appended to every AI response
  (chat + vision). — `services/ai/disclaimer.py`
- ✅ **Removed unsafe prompting** ("act as a doctor / never refuse"); agents now
  give educational framing and recommend professional care. — `agents/*`
- ✅ **Persistent disclaimer banner** on every authenticated screen.

### CI / supply chain
- ✅ **Postgres CI job** runs the suite + `alembic upgrade head` against real
  Postgres (prod-parity; the old job only used SQLite).
- ✅ **`pip-audit`** dependency scan job added (non-blocking — see 🟡 below).
- ✅ **Tests**: 26 passing (logout/revocation, password change, document
  list/delete, ownership/IDOR, export, account deletion, disclaimer).

---

## 🔧 Requires your action (cannot be done in code)

### HIPAA — blockers before real patient data
1. 🔧 **Sign BAAs and move to BAA-eligible tiers** for every vendor that touches PHI:
   - **Render** → Scale/Enterprise *HIPAA-enabled workspace* (+20% usage fee).
   - **Neon** → Scale plan, enable HIPAA at org + project, accept BAA.
   - **Vercel** → Pro HIPAA add-on (or Enterprise) + accept BAA.
   - **Groq** → paid/GA tier + execute BAA, **and stop sending PHI to the preview
     vision model** `llama-4-scout` (preview models are excluded from Groq's BAA).
     Pick a GA vision model or drop the image path until one is covered.
2. 🔧 **Documented Security Risk Analysis** (§164.308(a)(1)) and written policies:
   data retention/disposal, breach-notification/incident response, access control.
3. 🔧 **Confirm encryption-at-rest posture** is attestable under the signed BAAs
   (DB, disk/object store) so breach "safe harbor" applies.

### Regulatory (the AI feature itself)
4. 🔧 **Decide the product's regulatory posture.** Patient-facing disease *risk
   scores* can meet the FDA device definition. Either (a) reposition as
   clearly-educational and remove diagnostic/threshold/risk-score claims, or
   (b) pursue the FDA/clinical-validation path. The softened prompts + disclaimer
   reduce but do **not** remove this; product/legal must decide.

### Infrastructure
5. 🔧 **Shared rate-limit store (Redis).** Set `RATE_LIMIT_STORAGE_URI=redis://…`
   (Render Key Value) so limits are correct across workers — *code already supports it.*
6. 🔧 **Move uploads + vectors off the single Render disk** (object storage +
   managed vector DB) to enable multi-instance, zero-downtime deploys and durable
   PHI storage. (The Render persistent disk pins you to one instance and blocks
   zero-downtime deploys.)
7. 🔧 **Error tracking + metrics + alerting** (e.g. Sentry + a metrics/APM stack).
   Structured logs alone can't page anyone or scope a breach in time.
8. 🔧 **Run migrations as a Render pre-deploy step**, not from the app container
   entrypoint, before scaling past one instance.

---

## 🟡 Recommended code follow-ups (next wave)
- 🟡 **Move the access token to an httpOnly+Secure+SameSite cookie / BFF** to
  close the localStorage XSS vector entirely. (This branch makes tokens
  *revocable* + adds idle logoff + removes PHI from localStorage, which sharply
  cuts the risk, but the token itself is still JS-readable. This is a login-flow
  refactor and should be done deliberately with end-to-end testing.)
- 🟡 **Short access token + rotating refresh token.** Reduce `ACCESS_TOKEN_EXPIRE_MINUTES`
  from 8 days and add refresh rotation.
- 🟡 **Fully pin dependencies with hashes** (`pip-compile`/`uv` lockfile) and flip
  the `pip-audit` CI job to blocking once the tree is clean.
- 🟡 **Periodic purge** of expired `revoked_tokens` rows (`crud_token.purge_expired`).
- 🟡 **Per-user rate-limit keys** in addition to IP, for authenticated routes.

---

## How to verify locally
```bash
# backend
cd backend && source venv/bin/activate
pytest -q                      # 26 passing
alembic upgrade head           # applies 0001→0003

# frontend
cd frontend
npx tsc --noEmit && npm run build
```
