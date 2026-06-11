# Agent Notes

## Authoritative Sources

- Public REGOS API Swagger: https://api.regos.uz/v1/swagger/public-v1/swagger.json
- Public REGOS webhook documentation: https://docs.regos.uz/ru/api/webhooks
- Public webhook list: `POST https://api.regos.uz/v1/Webhook/Get` without authorization.
- Public REGOS product context: https://regos.uz/ru and https://apps.regos.uz

Use these sources before changing REGOS API contracts, webhook names, or user-facing integration copy.

## REGOS API Conventions

- Reference examples:
  - Base response/result types: [`schemas/api/base.py`](schemas/api/base.py)
  - Common filters: [`schemas/api/common/filters.py`](schemas/api/common/filters.py)
  - API namespace registry: [`core/api/regos_api.py`](core/api/regos_api.py)
  - Integration route registry: [`routes/clients.py`](routes/clients.py)
- Add request/response/read models under `schemas/api/<area>/<resource>.py`.
- Add transport wrappers under `core/api/<area>/<resource>.py`.
- Expose new services through the matching namespace in `core/api/regos_api.py`.
- Service methods should call REGOS via `self.api.call(PATH, req_or_payload, ResponseModel)`; integrations should use `RegosAPI(...)` instead of hand-written HTTP calls for REGOS REST endpoints.
- Keep endpoint paths as REGOS method strings, for example `Resource/Get` or `Resource/Edit`.
- Request schemas normally use `BaseSchema` with `model_config = ConfigDict(extra="forbid")`.
- Read/response payload schemas normally use `model_config = ConfigDict(extra="ignore")` to tolerate newer API fields.
- API responses should extend `APIBaseResponse[...]`; mutation-like results usually use `ArrayResult`, create results usually use `AddResult`.
- When the public Swagger adds fields that are not yet in local schemas, update the schema first and keep existing legacy aliases only when current integrations still need them.

## Webhook Conventions

- Integrations are subscribed to webhooks manually in REGOS; do not auto-subscribe from integration code.
- Verify webhook names with the public webhook list before hardcoding them.
- REGOS sends webhooks as `action=HandleWebhook` with `event_id`, `occurred_at`, `connected_integration_id`, and nested `data.action` / `data.data`.
- Use `event_id` when it is available for retry-safe idempotency; REGOS keeps it stable across retries.
- Webhook endpoints should return `200 OK` quickly. REGOS waits about 3 seconds and retries delivery up to 3 times on failures.
- Webhook handlers may also accept direct calls (`action=<WebhookName>, data={...}`) only when that matches existing integration route patterns.

## Integration Code Style

- Write integration code for a human maintainer first: clear names, small methods, explicit data flow, and predictable control flow.
- Do not duplicate methods or create parallel implementations of the same action. If behavior diverges, extract the shared part and name the difference.
- Avoid excessive fallbacks. Add a fallback only when the API or existing production payloads justify it; document the reason in a short comment near the branch.
- Prefer one canonical path through the code. Normalize inputs once at the boundary, then pass typed or well-shaped data through the rest of the integration.
- Keep public integration actions thin. Put validation, REGOS calls, external calls, and side effects into focused private helpers.
- Use dataclasses or small typed config objects for runtime settings instead of passing loose dictionaries through many layers.
- Redis queues, locks, dedupe keys, and retry markers must always have an explicit TTL or bounded `MAXLEN`; do not create permanent integration keys.
- Keep error handling intentional: catch exceptions where the integration can return a meaningful response or add useful context; do not swallow errors silently.
- Comments should explain why something exists, which external contract it protects, or what non-obvious business rule is being enforced. Do not add comments that merely restate the next line.
- Public methods and complex helpers should have concise docstrings or nearby comments describing their role, expected input shape, and important side effects.
- Do not add speculative abstractions, unused settings, unused imports, compatibility branches, or "just in case" options.
- After editing, scan the integration for dead code, repeated parsing helpers, unused fallback paths, and settings that are documented but not used.

## Integration Code Review

- Start reviews with risks and defects, ordered by severity. Keep summaries secondary.
- Check the external contract first: REGOS API paths, request/response schemas, webhook names, callback signatures, and required headers.
- Verify that every documented setting is used in code and every required code setting is documented.
- Look for duplicate logic, repeated parsing, broad fallback branches, dead helpers, unused imports, and settings that exist only because the code was generated or copied.
- Check idempotency for inbound webhooks, external callbacks, retries, and repeated user actions.
- Check side effects: entity updates, status/stage transitions, outgoing messages, file uploads, and external HTTP calls should happen once and in the intended order.
- Check error handling paths: expected business errors should return meaningful responses; unexpected errors should keep useful logs and not be silently swallowed.
- Check data boundaries: normalize input at the edge, validate required fields early, and avoid passing raw payload dictionaries deep into business logic.
- Check that REGOS REST calls use existing schemas/services through `RegosAPI(...)` unless the target is not part of REGOS API.
- Check that webhook subscription is not performed by integration code.
- Check README accuracy against implementation, public REGOS sources, and the actual settings/action names.
- When suggesting changes, prefer smaller focused fixes over broad rewrites. Do not introduce new abstractions unless they remove real duplication or clarify a real contract.
- If tests are absent, state the concrete residual risk and the smallest useful verification command or scenario.

## Integration README Conventions

- Treat integration README files as marketplace-facing product documentation plus concise technical setup notes.
- Follow the established README shape used by mature integrations: localized name, short description, full description, processed events/actions, settings table, and setup flow.
- Write names and descriptions in RU, UZ, and EN when the README is intended for marketplace/catalog use.
- Descriptions must sound human, commercial, and motivational: explain the business scenario, the value for the team, and the outcome for the customer.
- Avoid generic AI-sounding copy: no filler promises, no repeated "this integration allows you to...", no unsupported claims, and no feature lists disguised as prose.
- Before writing marketing descriptions, search current REGOS public materials and align wording with REGOS positioning and terminology.
- Keep technical facts in tables or setup sections; do not repeat the same facts in short description, full description, and setup text unless the repetition serves a different reader need.
