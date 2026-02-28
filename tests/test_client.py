"""Unit tests for the XeroML Python SDK — mocks httpx to verify correct requests."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from xeroml import (
    AsyncXeroML,
    CreditsExhaustedError,
    InvalidAPIKeyError,
    ParseFailedError,
    RateLimitedError,
    SessionEndedError,
    SessionNotFoundError,
    XeroML,
    XeroMLError,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_GRAPH = {
    "schema_version": "0.1.0",
    "root_goal": "Refactor auth module",
    "sub_goals": [
        {
            "id": "sg_001",
            "goal": "Add OAuth2 support",
            "status": "pending",
            "priority": 0.9,
            "success_criteria": ["OAuth2 flow works"],
            "constraints": [],
            "uncertainty": 0.3,
            "context_requirements": [],
            "modality": "code",
            "dependencies": [],
            "children": [],
        }
    ],
    "meta": {
        "source": "user_input",
        "confidence": 0.85,
        "negotiation_history": [],
        "latent_states": {
            "goal_intent": "refactoring",
            "action_readiness": "executing",
            "ambiguity_level": "clear",
            "risk_sensitivity": "medium",
            "intent_scope": "compound",
        },
    },
}

SAMPLE_PARSE_RESPONSE = {
    "graph": SAMPLE_GRAPH,
    "request_id": "req_abc123",
    "latency_ms": 150,
}

SAMPLE_SESSION_RESPONSE = {"session_id": "sess_test123"}

SAMPLE_USAGE_RESPONSE = {
    "credits": {"used": 42, "total": 100, "remaining": 58},
    "tier": "free",
    "rate_limit": 100,
    "usage": [
        {"month": "2026-02-01", "parse_calls": 42, "drift_checks": 0, "session_creates": 5, "total_latency_ms": 1200},
    ],
}

SAMPLE_DRIFT_RESPONSE = {
    "detected": True,
    "drift_type": "scope_creep",
    "severity": 0.6,
    "description": "User added new requirement",
    "previous_goal": "Refactor auth",
    "current_goal": "Refactor auth + add payments",
}


def _mock_response(status: int = 200, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.is_success = 200 <= status < 300
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# Sync client tests
# ---------------------------------------------------------------------------


class TestXeroMLSync:
    def test_parse(self):
        client = XeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, SAMPLE_PARSE_RESPONSE)

        with patch.object(client._http, "request", return_value=mock_resp) as mock_req:
            graph = client.parse("Refactor auth module")

        mock_req.assert_called_once_with(
            "POST", "/v1/parse", json={"message": "Refactor auth module"}
        )
        assert graph.root_goal == "Refactor auth module"
        assert len(graph.sub_goals) == 1
        assert graph.meta.confidence == 0.85

    def test_parse_with_provider(self):
        client = XeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, SAMPLE_PARSE_RESPONSE)

        with patch.object(client._http, "request", return_value=mock_resp) as mock_req:
            client.parse("hello", provider="openai")

        mock_req.assert_called_once_with(
            "POST", "/v1/parse", json={"message": "hello", "provider": "openai"}
        )

    def test_create_session(self):
        client = XeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)

        with patch.object(client._http, "request", return_value=mock_resp) as mock_req:
            session = client.create_session()

        mock_req.assert_called_once_with("POST", "/v1/sessions", json={})
        assert session.session_id == "sess_test123"

    def test_create_session_with_id(self):
        client = XeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, {"session_id": "my_custom_id"})

        with patch.object(client._http, "request", return_value=mock_resp):
            session = client.create_session(session_id="my_custom_id")

        assert session.session_id == "my_custom_id"

    def test_get_usage(self):
        client = XeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, SAMPLE_USAGE_RESPONSE)

        with patch.object(client._http, "request", return_value=mock_resp):
            usage = client.get_usage()

        assert usage.credits.used == 42
        assert usage.credits.total == 100
        assert usage.tier == "free"

    def test_list_sessions(self):
        client = XeroML(api_key="xml_test_abc123")
        sessions_data = {
            "sessions": [
                {
                    "session_id": "s1",
                    "status": "active",
                    "turn_count": 2,
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:01:00Z",
                }
            ]
        }
        mock_resp = _mock_response(200, sessions_data)

        with patch.object(client._http, "request", return_value=mock_resp):
            sessions = client.list_sessions()

        assert len(sessions) == 1
        assert sessions[0].session_id == "s1"

    def test_headers(self):
        client = XeroML(api_key="xml_test_mykey", base_url="https://custom.api.com")
        assert client._http.headers["x-api-key"] == "xml_test_mykey"
        assert client._http.headers["content-type"] == "application/json"
        assert str(client._http.base_url) == "https://custom.api.com"

    def test_context_manager(self):
        with XeroML(api_key="xml_test_abc") as client:
            assert client.api_key == "xml_test_abc"


# ---------------------------------------------------------------------------
# Session tests
# ---------------------------------------------------------------------------


class TestSession:
    def test_session_parse(self):
        client = XeroML(api_key="xml_test_abc123")
        session_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        parse_resp = _mock_response(200, SAMPLE_PARSE_RESPONSE)

        with patch.object(client._http, "request", side_effect=[session_resp, parse_resp]):
            session = client.create_session()
            graph = session.parse("Refactor auth module")

        assert graph.root_goal == "Refactor auth module"

    def test_session_update(self):
        client = XeroML(api_key="xml_test_abc123")
        session_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        update_resp = _mock_response(200, {})

        with patch.object(
            client._http, "request", side_effect=[session_resp, update_resp]
        ) as mock_req:
            session = client.create_session()
            session.update("Here is the refactored code...")

        call_args = mock_req.call_args_list[1]
        assert call_args[0] == ("POST", "/v1/sessions/sess_test123/update")
        assert call_args[1]["json"]["response"] == "Here is the refactored code..."
        assert call_args[1]["json"]["role"] == "assistant"

    def test_session_check_drift(self):
        client = XeroML(api_key="xml_test_abc123")
        session_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        drift_resp = _mock_response(200, SAMPLE_DRIFT_RESPONSE)

        with patch.object(client._http, "request", side_effect=[session_resp, drift_resp]):
            session = client.create_session()
            drift = session.check_drift()

        assert drift.detected is True
        assert drift.drift_type == "scope_creep"
        assert drift.severity == 0.6

    def test_session_get_graph(self):
        client = XeroML(api_key="xml_test_abc123")
        session_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        graph_resp = _mock_response(200, {"graph": SAMPLE_GRAPH})

        with patch.object(client._http, "request", side_effect=[session_resp, graph_resp]):
            session = client.create_session()
            graph = session.get_graph()

        assert graph.root_goal == "Refactor auth module"

    def test_session_end(self):
        client = XeroML(api_key="xml_test_abc123")
        session_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        end_resp = _mock_response(200, {})

        with patch.object(
            client._http, "request", side_effect=[session_resp, end_resp]
        ) as mock_req:
            session = client.create_session()
            session.end()

        call_args = mock_req.call_args_list[1]
        assert call_args[0] == ("POST", "/v1/sessions/sess_test123/end")


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_invalid_api_key(self):
        client = XeroML(api_key="bad_key")
        error_body = {"error": {"code": "invalid_api_key", "message": "Invalid key", "status": 401}}
        mock_resp = _mock_response(401, error_body)

        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(InvalidAPIKeyError) as exc_info:
                client.parse("test")
        assert exc_info.value.status == 401
        assert exc_info.value.code == "invalid_api_key"

    def test_credits_exhausted(self):
        client = XeroML(api_key="xml_test_abc123")
        error_body = {
            "error": {
                "code": "credits_exhausted",
                "message": "All 100 credits used.",
                "status": 402,
                "details": {"credits_used": 100, "credits_total": 100},
            }
        }
        mock_resp = _mock_response(402, error_body)

        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(CreditsExhaustedError) as exc_info:
                client.parse("test")
        assert exc_info.value.status == 402
        assert exc_info.value.details["credits_used"] == 100

    def test_rate_limited(self):
        client = XeroML(api_key="xml_test_abc123")
        error_body = {"error": {"code": "rate_limited", "message": "Slow down", "status": 429}}
        mock_resp = _mock_response(429, error_body)

        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(RateLimitedError):
                client.parse("test")

    def test_parse_failed(self):
        client = XeroML(api_key="xml_test_abc123")
        error_body = {"error": {"code": "parse_failed", "message": "LLM failed", "status": 422}}
        mock_resp = _mock_response(422, error_body)

        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(ParseFailedError):
                client.parse("test")

    def test_session_not_found(self):
        client = XeroML(api_key="xml_test_abc123")
        error_body = {
            "error": {"code": "session_not_found", "message": "Not found", "status": 404}
        }
        mock_resp = _mock_response(404, error_body)

        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(SessionNotFoundError):
                client.list_sessions()

    def test_session_ended(self):
        client = XeroML(api_key="xml_test_abc123")
        session_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        error_body = {
            "error": {"code": "session_ended", "message": "Already ended", "status": 409}
        }
        ended_resp = _mock_response(409, error_body)

        with patch.object(client._http, "request", side_effect=[session_resp, ended_resp]):
            session = client.create_session()
            with pytest.raises(SessionEndedError):
                session.parse("test")

    def test_unknown_error(self):
        client = XeroML(api_key="xml_test_abc123")
        error_body = {
            "error": {"code": "internal_error", "message": "Server error", "status": 500}
        }
        mock_resp = _mock_response(500, error_body)

        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(XeroMLError) as exc_info:
                client.parse("test")
        assert exc_info.value.status == 500
        assert exc_info.value.code == "internal_error"


# ---------------------------------------------------------------------------
# Async client tests
# ---------------------------------------------------------------------------


class TestAsyncXeroML:
    @pytest.mark.asyncio
    async def test_async_parse(self):
        client = AsyncXeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, SAMPLE_PARSE_RESPONSE)
        mock_req = AsyncMock(return_value=mock_resp)

        with patch.object(client._http, "request", mock_req):
            graph = await client.parse("Refactor auth module")

        mock_req.assert_called_once_with(
            "POST", "/v1/parse", json={"message": "Refactor auth module"}
        )
        assert graph.root_goal == "Refactor auth module"

    @pytest.mark.asyncio
    async def test_async_create_session(self):
        client = AsyncXeroML(api_key="xml_test_abc123")
        mock_resp = _mock_response(200, SAMPLE_SESSION_RESPONSE)
        mock_req = AsyncMock(return_value=mock_resp)

        with patch.object(client._http, "request", mock_req):
            session = await client.create_session()

        assert session.session_id == "sess_test123"

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        client = AsyncXeroML(api_key="bad_key")
        error_body = {"error": {"code": "invalid_api_key", "message": "Invalid", "status": 401}}
        mock_resp = _mock_response(401, error_body)
        mock_req = AsyncMock(return_value=mock_resp)

        with patch.object(client._http, "request", mock_req):
            with pytest.raises(InvalidAPIKeyError):
                await client.parse("test")
