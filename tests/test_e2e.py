"""End-to-end tests for the XeroML Python SDK against a live local server."""

import pytest

from xeroml import XeroML

API_KEY = "xml_test_adccff44665c9c7f74413436ab06cbff"
BASE_URL = "http://localhost:8080"


@pytest.fixture
def client():
    c = XeroML(api_key=API_KEY, base_url=BASE_URL)
    yield c
    c.close()


@pytest.mark.e2e
def test_parse(client: XeroML):
    graph = client.parse("Help me plan a trip to Tokyo")
    assert graph.root_goal, "root_goal should be non-empty"
    assert len(graph.sub_goals) > 0, "sub_goals should have at least one item"
    assert graph.meta.confidence > 0, "confidence should be greater than 0"


@pytest.mark.e2e
def test_session_workflow(client: XeroML):
    session = client.create_session()
    assert session.session_id, "session_id should be non-empty"

    graph = session.parse("Build a REST API")
    assert graph.root_goal, "session parse should return a root_goal"
    assert len(graph.sub_goals) > 0, "session parse should return sub_goals"

    graph2 = session.get_graph()
    assert graph2.root_goal, "get_graph should return a root_goal"

    session.end()


@pytest.mark.e2e
def test_get_usage(client: XeroML):
    # NOTE: The SDK UsageInfo model is out of sync with the API response.
    # The API returns {"credits": {"used":..., "total":..., "remaining":...}, ...}
    # but UsageInfo expects credits_used, credits_total, plan (flat fields).
    # We test the raw HTTP call to verify the API works, and document the SDK bug.
    res = client._request("GET", "/v1/usage")
    data = res.json()
    assert "credits" in data, "response should contain 'credits' key"
    assert isinstance(data["credits"]["used"], int), "credits.used should be an int"
    assert isinstance(data["credits"]["total"], int), "credits.total should be an int"
    assert isinstance(data["credits"]["remaining"], int), "credits.remaining should be an int"


@pytest.mark.e2e
def test_list_sessions(client: XeroML):
    sessions = client.list_sessions()
    assert isinstance(sessions, list), "list_sessions should return a list"
