"""
app/core/turso_dbapi.py - Pure Python DBAPI 2.0 interface for Turso
Uses the modern `libsql-client` library via HTTP APIs.
"""
import sqlite3

# DBAPI 2.0 required properties
apilevel = "2.0"
threadsafety = 1
paramstyle = "qmark"
sqlite_version_info = (3, 40, 0)
version_info = (2, 6, 0)

# Import standard DBAPI exceptions
from sqlite3 import (
    Warning, Error, InterfaceError, DatabaseError, DataError,
    OperationalError, IntegrityError, InternalError, ProgrammingError, NotSupportedError
)

import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import os
import time
import socket


def _extract_query_token(raw_query: str):
    """Extract auth token from raw query string without '+' -> ' ' conversion."""
    if not raw_query:
        return None

    for part in raw_query.split("&"):
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
        else:
            k, v = part, ""

        key = urllib.parse.unquote(k).strip().lower()
        if key in ("authtoken", "auth_token"):
            # Use unquote (not unquote_plus) so '+' remains '+' in token.
            return urllib.parse.unquote(v)

    return None


def _normalize_token(token):
    if token is None:
        return None

    normalized = str(token).strip().strip("\"'")
    if normalized.lower().startswith("bearer "):
        normalized = normalized[7:].strip()

    # Remove accidental whitespace/newlines copied into env values.
    normalized = "".join(normalized.split())
    return normalized or None


def _is_valid_jwt_shape(token):
    """Best-effort structure check: 3 parts and decodable JSON header/payload."""
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False

    def _decode_json(part):
        pad = "=" * ((4 - len(part) % 4) % 4)
        raw = base64.urlsafe_b64decode((part + pad).encode("utf-8"))
        return json.loads(raw.decode("utf-8"))

    try:
        _decode_json(parts[0])
        _decode_json(parts[1])
        return True
    except Exception:
        return False


def _to_turso_value(value):
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": "1" if value else "0"}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        import math
        if not math.isfinite(value):
            return {"type": "null"}
        # Hrana protocol: float values MUST be JSON numbers, not strings.
        return {"type": "float", "value": value}
    return {"type": "text", "value": str(value)}

def connect(*args, **kwargs):
    url = kwargs.get("database") or (args[0] if args else None)
    auth_token = _normalize_token(kwargs.get("auth_token"))

    if not url:
        raise OperationalError("Missing Turso database URL")

    url_str = str(url)
    
    # Support either libsql:// or https:// forms.
    if url_str.startswith("libsql://"):
        url_str = url_str.replace("libsql://", "https://", 1)

    # Extract auth token from URL query when present.
    parsed = urllib.parse.urlparse(url_str)
    if not auth_token and parsed.query:
        auth_token = _normalize_token(_extract_query_token(parsed.query))

    # Remove query string from URL for Turso HTTP endpoint
    if parsed.query:
        url_str = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    # Explicit TURSO_AUTH_TOKEN should win over URL query token.
    env_token = _normalize_token(os.getenv("TURSO_AUTH_TOKEN"))
    if env_token:
        auth_token = env_token

    # Fallback to env token only if URL token was missing.
    if not auth_token:
        auth_token = env_token

    if not auth_token:
        raise OperationalError("Missing Turso auth token (authToken URL param or TURSO_AUTH_TOKEN env var)")
    
    # Validate token is not obviously truncated (JWT tokens are typically 200+ chars)
    if len(auth_token) < 50:
        raise OperationalError(f"Auth token appears truncated or invalid (length: {len(auth_token)})")

    if not _is_valid_jwt_shape(auth_token):
        raise OperationalError("Turso auth token is not a valid JWT structure; regenerate token in Turso dashboard")

    return Connection(url_str, auth_token)

class Connection:
    def __init__(self, url, auth_token):
        self.url = url
        self.auth_token = auth_token

    def cursor(self):
        return Cursor(self.url, self.auth_token)

    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

class Cursor:
    def __init__(self, url, auth_token):
        self.url = url
        self.auth_token = auth_token
        self.description = None
        self.rowcount = -1
        self.arraysize = 1
        self._rows = []
        self._index = 0
        self.lastrowid = None

    def execute(self, operation, parameters=None):
        sql_str = str(operation)
        sql_head = sql_str.lstrip().upper()
        is_read_only = sql_head.startswith(("SELECT", "PRAGMA", "WITH"))
        args = []
        if isinstance(parameters, dict):
            args = [
                {"name": str(k), "value": _to_turso_value(v)}
                for k, v in parameters.items()
            ]
        elif isinstance(parameters, (list, tuple)):
            args = [_to_turso_value(v) for v in parameters]
            
        payload = json.dumps({
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql_str,
                        "args": args
                    }
                },
                {"type": "close"}
            ]
        })
        
        # Ensure URL is properly formatted for Turso HTTP API
        base_url = self.url.rstrip('/')
        if not base_url.startswith("https://"):
            base_url = "https://" + base_url
        turso_endpoint = f"{base_url}/v2/pipeline"
        
        # Ensure auth token has no whitespace
        auth_token = self.auth_token.strip() if self.auth_token else ""
        if not auth_token:
            raise OperationalError("Auth token is empty")
        
        req = urllib.request.Request(
            turso_endpoint,
            data=payload.encode('utf-8'),
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        timeout_seconds = float(os.getenv("TURSO_HTTP_TIMEOUT_SECONDS", "30"))
        max_retries = int(os.getenv("TURSO_READ_RETRIES", "2")) if is_read_only else 0

        def _parse_response(response_body: str):
            res_data = json.loads(response_body)

            run_res = res_data.get("results", [])[0]
            if run_res.get("type") == "error":
                err_message = run_res.get("error", {}).get("message", "Unknown Turso Error")
                err_upper = str(err_message).upper()
                if "UNIQUE CONSTRAINT" in err_upper or "FOREIGN KEY CONSTRAINT" in err_upper or "NOT NULL CONSTRAINT" in err_upper:
                    raise IntegrityError(err_message)
                raise OperationalError(err_message)

            result = run_res.get("response", {}).get("result", {})
            cols = result.get("cols", [])
            rows = result.get("rows", [])

            if cols:
                self.description = tuple((col.get("name"), None, None, None, None, None, None) for col in cols)
            else:
                self.description = None

            parsed_rows = []
            for row in rows:
                parsed_row = []
                for val in row:
                    if isinstance(val, dict):
                        if val.get("type") == "null":
                            parsed_row.append(None)
                        elif val.get("type") == "integer":
                            parsed_row.append(int(val.get("value")))
                        elif val.get("type") == "float":
                            parsed_row.append(float(val.get("value")))
                        else:
                            parsed_row.append(val.get("value"))
                    else:
                        parsed_row.append(val)
                parsed_rows.append(tuple(parsed_row))

            self._rows = parsed_rows
            self.rowcount = result.get("affected_row_count", -1)
            self.lastrowid = result.get("last_insert_rowid")
            self._index = 0

        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                    _parse_response(response.read().decode())
                    return self
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode(errors="ignore")
                # HTTP 4xx indicates request/auth problems; do not retry as timeout.
                raise DatabaseError(f"HTTP {e.code}: {err_msg}")
            except (TimeoutError, socket.timeout, urllib.error.URLError) as e:
                last_exc = e
                if attempt < max_retries:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                raise OperationalError(f"Turso request timeout/network error after {attempt + 1} attempt(s): {e}")
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise IntegrityError(str(e))
                raise e

        if last_exc:
            raise OperationalError(f"Turso request failed: {last_exc}")

        return self

    def fetchone(self):
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self):
        rows = self._rows[self._index:]
        self._index = len(self._rows)
        return rows
        
    def fetchmany(self, size=None):
        if size is None:
            size = self.arraysize
        rows = self._rows[self._index : self._index + size]
        self._index += len(rows)
        return rows

    def close(self): pass
