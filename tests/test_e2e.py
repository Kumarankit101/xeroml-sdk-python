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
    assert graph.v == "0.3.0", "v should be 0.3.0"
    assert graph.objective, "objective should be non-empty"
    assert graph.directive, "directive should be non-empty"
    assert graph.type, "type should be set"
    assert graph.confidence > 0, "confidence should be greater than 0"
    assert graph.phase, "phase should be set"
    assert len(graph.history) > 0, "history should have at least one entry"


@pytest.mark.e2e
def test_session_workflow(client: XeroML):
    session = client.create_session()
    assert session.session_id, "session_id should be non-empty"

    graph = session.parse("Build a REST API")
    assert graph.objective, "session parse should return an objective"
    assert graph.directive, "session parse should return a directive"
    assert graph.v == "0.3.0", "v should be 0.3.0"

    graph2 = session.get_graph()
    assert graph2.objective, "get_graph should return an objective"

    session.end()


@pytest.mark.e2e
def test_get_usage(client: XeroML):
    usage = client.get_usage()
    assert isinstance(usage.credits.used, int), "credits.used should be an int"
    assert isinstance(usage.credits.total, int), "credits.total should be an int"
    assert isinstance(usage.credits.remaining, int), "credits.remaining should be an int"
    assert usage.tier, "tier should be non-empty"
    assert isinstance(usage.rate_limit, int), "rate_limit should be an int"
    assert isinstance(usage.usage, list), "usage should be a list"


@pytest.mark.e2e
def test_list_sessions(client: XeroML):
    sessions = client.list_sessions()
    assert isinstance(sessions, list), "list_sessions should return a list"
