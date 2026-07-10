FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files (uv.lock is gitignored; the glob tolerates its absence)
COPY pyproject.toml uv.lock* ./

# Install dependencies (no dev deps, no project itself yet);
# uses uv.lock when present, resolves fresh otherwise
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY src/ ./src/

# Install the project
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
