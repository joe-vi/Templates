#!/usr/bin/env python3
"""End-to-end API test script for the FastAPI Clean Architecture Template.

Starts the FastAPI server, runs every endpoint scenario, then stops the server.

Usage:
    uv run python test_api.py
    uv run python test_api.py --port 8001
"""

import argparse
import subprocess
import sys
import time

import httpx

# ---------------------------------------------------------------------------
# Terminal colours
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

passed: int = 0
failed: int = 0


def _check(label: str, response: httpx.Response, expected_status: int) -> bool:
    """Print a pass/fail line and update global counters."""
    global passed, failed
    ok = response.status_code == expected_status
    mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
    status_tag = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
    print(f"  {mark} {label}")
    print(f"    {DIM}Expected {expected_status} · Got {response.status_code}{RESET}  {status_tag}")
    if not ok:
        try:
            print(f"    {DIM}Body: {response.json()}{RESET}")
        except Exception:
            print(f"    {DIM}Body: {response.text[:200]}{RESET}")
        failed += 1
    else:
        passed += 1
    return ok


def _section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{title}{RESET}")
    print(f"{DIM}{'─' * 60}{RESET}")


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def _start_server(port: int) -> subprocess.Popen:
    print(f"{BOLD}Starting FastAPI server on port {port}…{RESET}")
    proc = subprocess.Popen(
        ["uv", "run", "uvicorn", "src.main:app", "--host", "127.0.0.1", f"--port={port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(30):
        time.sleep(0.5)
        try:
            r = httpx.get(url, timeout=2)
            if r.status_code == 200:
                print(f"{GREEN}Server ready.{RESET}\n")
                return proc
        except httpx.ConnectError:
            pass
    proc.kill()
    print(f"{RED}Server failed to start within 15 s.{RESET}", file=sys.stderr)
    sys.exit(1)


def _stop_server(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print(f"\n{DIM}Server stopped.{RESET}")


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run_tests(base: str) -> None:
    with httpx.Client(base_url=base, timeout=10) as client:

        # ----------------------------------------------------------------
        # 1. Core health routes
        # ----------------------------------------------------------------
        _section("1. Core routes")
        _check("GET /  →  welcome message", client.get("/"), 200)
        _check("GET /health  →  healthy", client.get("/health"), 200)

        # ----------------------------------------------------------------
        # 2. Auth — login
        # ----------------------------------------------------------------
        _section("2. Auth — login")

        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "AdminPass123"})
        if _check("POST /auth/login  (valid credentials)", r, 200):
            body = r.json()
            access_token: str = body["access_token"]
            refresh_token: str = body["refresh_token"]
            assert body.get("token_type") == "bearer", "token_type must be 'bearer'"
        else:
            print(f"\n{RED}Cannot continue without a valid access token.{RESET}")
            return

        _check(
            "POST /auth/login  (wrong password)  →  401",
            client.post("/api/v1/auth/login", json={"username": "admin", "password": "WRONG"}),
            401,
        )
        _check(
            "POST /auth/login  (non-existent user)  →  401",
            client.post("/api/v1/auth/login", json={"username": "nobody", "password": "pass"}),
            401,
        )
        _check(
            "POST /auth/login  (missing fields)  →  422",
            client.post("/api/v1/auth/login", json={}),
            422,
        )

        # ----------------------------------------------------------------
        # 3. Auth — token refresh
        # ----------------------------------------------------------------
        _section("3. Auth — token refresh")

        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        if _check("POST /auth/refresh  (valid refresh token)", r, 200):
            access_token = r.json()["access_token"]   # keep the newest token

        _check(
            "POST /auth/refresh  (invalid token)  →  401",
            client.post("/api/v1/auth/refresh", json={"refresh_token": "not.a.valid.token"}),
            401,
        )
        _check(
            "POST /auth/refresh  (missing field)  →  422",
            client.post("/api/v1/auth/refresh", json={}),
            422,
        )

        # ----------------------------------------------------------------
        # 4. Users — authentication enforcement
        # ----------------------------------------------------------------
        _section("4. User routes — auth enforcement")
        auth = {"Authorization": f"Bearer {access_token}"}

        _check(
            "GET /users  (no auth header)  →  401",
            client.get("/api/v1/users"),
            401,
        )
        _check(
            "GET /users  (invalid token)  →  401",
            client.get("/api/v1/users", headers={"Authorization": "Bearer garbage"}),
            401,
        )

        # ----------------------------------------------------------------
        # 5. Users — create
        # ----------------------------------------------------------------
        _section("5. Users — create")

        r = client.post(
            "/api/v1/users",
            json={"email": "testscript@example.com", "username": "testscript", "password": "TestPass123", "role": "user"},
            headers=auth,
        )
        if _check("POST /users  (valid payload)  →  201", r, 201):
            new_user_id: int = r.json()["id"]
        else:
            new_user_id = -1

        _check(
            "POST /users  (duplicate email/username)  →  409",
            client.post(
                "/api/v1/users",
                json={"email": "testscript@example.com", "username": "testscript", "password": "TestPass123", "role": "user"},
                headers=auth,
            ),
            409,
        )
        _check(
            "POST /users  (invalid email format)  →  422",
            client.post(
                "/api/v1/users",
                json={"email": "not-an-email", "username": "someone", "password": "TestPass123"},
                headers=auth,
            ),
            422,
        )
        _check(
            "POST /users  (password too short)  →  422",
            client.post(
                "/api/v1/users",
                json={"email": "short@example.com", "username": "shortpw", "password": "abc"},
                headers=auth,
            ),
            422,
        )
        _check(
            "POST /users  (missing username)  →  422",
            client.post(
                "/api/v1/users",
                json={"email": "nouser@example.com", "password": "TestPass123"},
                headers=auth,
            ),
            422,
        )

        # ----------------------------------------------------------------
        # 6. Users — read
        # ----------------------------------------------------------------
        _section("6. Users — read")

        _check(
            "GET /users  (authenticated)  →  200",
            client.get("/api/v1/users", headers=auth),
            200,
        )

        if new_user_id != -1:
            r = client.get(f"/api/v1/users/{new_user_id}", headers=auth)
            if _check(f"GET /users/{new_user_id}  (found)  →  200", r, 200):
                u = r.json()
                assert u["username"] == "testscript", f"unexpected username: {u['username']}"
                assert u["role"] == "user", f"unexpected role: {u['role']}"

        _check(
            "GET /users/999999  (not found)  →  404",
            client.get("/api/v1/users/999999", headers=auth),
            404,
        )

        # ----------------------------------------------------------------
        # 7. Users — update role
        # ----------------------------------------------------------------
        _section("7. Users — update role")

        if new_user_id != -1:
            r = client.patch(f"/api/v1/users/{new_user_id}/role", json={"role": "admin"}, headers=auth)
            if _check(f"PATCH /users/{new_user_id}/role  (user → admin)  →  200", r, 200):
                updated = client.get(f"/api/v1/users/{new_user_id}", headers=auth).json()
                assert updated["role"] == "admin", f"role not updated: {updated['role']}"

            r = client.patch(f"/api/v1/users/{new_user_id}/role", json={"role": "user"}, headers=auth)
            _check(f"PATCH /users/{new_user_id}/role  (admin → user)  →  200", r, 200)

        _check(
            "PATCH /users/999999/role  (not found)  →  404",
            client.patch("/api/v1/users/999999/role", json={"role": "admin"}, headers=auth),
            404,
        )
        _check(
            "PATCH /users/1/role  (invalid role value)  →  422",
            client.patch("/api/v1/users/1/role", json={"role": "SUPERUSER"}, headers=auth),
            422,
        )

        # ----------------------------------------------------------------
        # 8. Users — delete
        # ----------------------------------------------------------------
        _section("8. Users — delete")

        if new_user_id != -1:
            _check(
                f"DELETE /users/{new_user_id}  →  200",
                client.delete(f"/api/v1/users/{new_user_id}", headers=auth),
                200,
            )
            _check(
                f"GET /users/{new_user_id}  (after delete)  →  404",
                client.get(f"/api/v1/users/{new_user_id}", headers=auth),
                404,
            )

        _check(
            "DELETE /users/999999  (not found)  →  404",
            client.delete("/api/v1/users/999999", headers=auth),
            404,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="End-to-end API test script")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Skip server start/stop; assume it is already running on --port",
    )
    args = parser.parse_args()

    base_url = f"http://127.0.0.1:{args.port}"
    proc = None

    if not args.no_start:
        proc = _start_server(args.port)

    try:
        run_tests(base_url)
    finally:
        if proc is not None:
            _stop_server(proc)

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    total = passed + failed
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    if failed == 0:
        print(f"{BOLD}{GREEN}  All {total} checks passed.{RESET}")
    else:
        print(f"{BOLD}  {GREEN}{passed} passed{RESET}  {RED}{failed} failed{RESET}  (total {total})")
    print(f"{BOLD}{'═' * 60}{RESET}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
