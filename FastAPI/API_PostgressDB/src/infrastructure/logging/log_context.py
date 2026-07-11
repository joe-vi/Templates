from contextvars import ContextVar

# Cross-cutting observability metadata only (request id, authenticated user
# id) — set by the request_context middleware and the JWT guard so every log
# line carries them. Never used for control flow or transactional state;
# the shared DB session is injected, not kept in a ContextVar.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
