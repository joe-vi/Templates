"""Per-request logging correlation carried in context variables.

Context variables are the right tool here: they carry cross-cutting
*observability* metadata (request id, authenticated user id) that should appear
on every log line without threading it through every signature. They do not
drive control flow or transactional behaviour — unlike a shared DB session,
which is why session state is *not* kept this way.
"""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
