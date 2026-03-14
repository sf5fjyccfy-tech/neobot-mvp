# Legacy Endpoint Mapping (`app/api` -> `app/routers`)

Scope:

- Legacy endpoints defined in `backend/app/api/*`
- Active runtime routes mounted from `backend/app/routers/*` via `backend/app/main.py`

Status summary:

- `app/api` is not mounted in `main.py`
- Legacy endpoints are currently dormant in runtime
- Cleanup should be migration-first for endpoints without active equivalent

Applied in this branch (`2026-03-14`):

- Removed `backend/app/api/auth.py` (active equivalent exists in `backend/app/routers/auth.py`)
- Removed `backend/app/api/analytics.py` (active equivalent exists in `backend/app/routers/analytics.py`)
- Removed `backend/app/api/whatsapp.py` (legacy global WhatsApp endpoints)
- Removed `backend/app/api/whatsapp_qr.py` (legacy global QR/websocket endpoints)
- Removed `backend/app/api/conversations.py` (legacy recent conversations endpoint)
- Removed `backend/app/api/products.py` (legacy product endpoints)
- Removed `backend/app/api/admin.py` (legacy admin endpoints)
- Removed `backend/app/api/knowledge.py` (legacy knowledge endpoints)
- Removed `backend/app/api/payments.py` (legacy payment simulation endpoints)

Current state:

- No executable legacy endpoint modules remain under `backend/app/api/`
- `backend/app/api/` now contains deprecation docs only

## Exact or Near-Exact Equivalents

| Legacy endpoint | Active endpoint | Status | Action |
| --- | --- | --- | --- |
| `POST /api/auth/register` (`api/auth.py`) | `POST /api/auth/register` (`routers/auth.py`) | Equivalent | Keep active route only; legacy removable |
| `GET /api/tenants/{tenant_id}/analytics/dashboard` (`api/analytics.py`) | `GET /api/tenants/{tenant_id}/analytics/dashboard` (`routers/analytics.py`) | Equivalent | Keep active route only; legacy removable |

## Partial / Different Contract

| Legacy endpoint | Active candidate | Gap | Action |
| --- | --- | --- | --- |
| `POST /api/auth/token` (`api/auth.py`) | `POST /api/auth/login` (`routers/auth.py`) | Path and payload contract differ | If clients still require `/token`, add explicit compatibility alias in active router, then remove legacy |
| `GET /api/tenants/{tenant_id}/analytics/products/popular` (`api/analytics.py`) | `GET /api/tenants/{tenant_id}/analytics/clients/top` and other analytics routes | Different metric semantics | Add new active endpoint if needed, then remove legacy |
| `GET /api/tenants/{tenant_id}/analytics/conversion` (`api/analytics.py`) | `GET /api/tenants/{tenant_id}/analytics/conversion-funnel` | Response model likely different | Harmonize response contract in active router, then remove legacy |
| `GET /whatsapp/status` (`api/whatsapp.py`, `api/whatsapp_qr.py`) | Tenant-scoped WhatsApp/session routes under `/api/tenants/{tenant_id}/whatsapp/*` and `/api/whatsapp/*` | Legacy is global/non-tenant; active is tenant/session-oriented | Do not revive global route; migrate callers to active tenant/session routes |
| `POST /whatsapp/disconnect` (`api/whatsapp.py`) | `DELETE /api/tenants/{tenant_id}/whatsapp/session` and `POST /api/whatsapp/disconnect` | Different scope and semantics | Standardize on active route family |

## No Active Equivalent (Migration Needed Before Deletion)

| Legacy endpoint | Notes | Action |
| --- | --- | --- |
| `GET /admin/tenants` (`api/admin.py`) | Legacy super-admin list | Implement in active admin router or confirm obsolete |
| `GET /admin/analytics` (`api/admin.py`) | Legacy global platform metrics | Implement active admin metrics route or confirm obsolete |
| `POST /admin/tenants/{tenant_id}/activate` (`api/admin.py`) | Legacy toggle activation | Implement active admin action route or confirm obsolete |
| `GET /tenants/{tenant_id}/conversations/recent` (`api/conversations.py`) | Legacy recent conversations aggregator | Implement in active conversation router if still needed |
| `GET /api/tenants/{tenant_id}/products` (`api/products.py`) | Legacy product search | Implement in active product router/service if needed |
| `GET /api/tenants/{tenant_id}/products/{product_id}` (`api/products.py`) | Legacy product detail | Implement in active product router/service if needed |
| `GET /api/tenants/{tenant_id}/categories` (`api/products.py`) | Legacy category list | Implement in active product router/service if needed |
| `POST /api/create-payment` (`api/payments.py`) | Legacy payment simulation | Replace with production payment flow or archive |
| `GET /payment-success` (`api/payments.py`) | Legacy callback flow | Replace with production payment callback route or archive |
| `GET /admin/knowledge/global` (`api/knowledge.py`) | Legacy knowledge admin | Add to active knowledge router or confirm obsolete |
| `POST /admin/knowledge/global` (`api/knowledge.py`) | Legacy knowledge admin write | Add to active knowledge router or confirm obsolete |
| `GET /tenants/{tenant_id}/knowledge` (`api/knowledge.py`) | Legacy tenant knowledge read | Add active equivalent if still in product scope |
| `POST /tenants/{tenant_id}/knowledge/{knowledge_type}` (`api/knowledge.py`) | Legacy tenant knowledge write | Add active equivalent if still in product scope |
| `GET /tenants/{tenant_id}/conversation-templates` (`api/knowledge.py`) | Legacy templates read | Add active equivalent if still in product scope |
| `POST /whatsapp/start` (`api/whatsapp.py`) | Legacy global start | Migrate to active tenant/session creation flow |
| `POST /whatsapp/restart` (`api/whatsapp_qr.py`) | Legacy restart endpoint | Migrate callers to active reconnect flow |
| `WS /whatsapp/ws` (`api/whatsapp_qr.py`) | Legacy websocket status channel | Re-implement under active namespace if required |
| `GET /whatsapp/connect` (`api/whatsapp_qr.py`) | Legacy embedded HTML UI | Keep out of API runtime unless explicitly needed |

## Safe Deletion Order

1. Delete legacy endpoints with exact equivalents first (`api/auth.py`, `api/analytics.py`) after confirming no external client uses legacy-only contracts.
2. For partial contracts, add compatibility aliases in active routers if required.
3. Migrate or formally de-scope no-equivalent endpoints.
4. Remove remaining `app/api/*.py` files and keep a changelog note.

## Verification Checklist

- Confirm no `app.api` references in `backend/app/main.py`
- Confirm frontend calls active endpoints only
- Run backend integration tests
- Smoke test auth, analytics dashboard, WhatsApp session lifecycle
