import json

from AbstractTest import ParentEntity
from endpoints.AbstractEPTest import AbstractEndpointTest


class DummyEndpointTest(AbstractEndpointTest):
    base_endpoint = "role"
    entity_name = "role"
    parent_entities = [
        ParentEntity(
            name="team",
            foreign_key="team_id",
            path_level=1,
            is_path=True,
            test_class=lambda: None,
        )
    ]
    NESTING_CONFIG_OVERRIDES = {"DETAIL": 1}

    def __init__(self):
        self.tracked_entities = {}


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class DummyServer:
    def __init__(self):
        self.calls = []

    def get(self, url, headers):
        self.calls.append(url)
        if len(self.calls) == 1:
            return DummyResponse(404, {"detail": "Not Found"})
        return DummyResponse(200, {"role": {"id": "role123"}})


def test_encode_query_values_with_lists():
    assert AbstractEndpointTest._encode_query_values(["id"]) == "id"
    assert (
        AbstractEndpointTest._encode_query_values(["id", "name", "created_at"])
        == "id,name,created_at"
    )


def test_encode_query_values_trims_and_deduplicates():
    assert AbstractEndpointTest._encode_query_values("id,name") == "id,name"
    assert (
        AbstractEndpointTest._encode_query_values([" id ", "name", "id"]) == "id,name"
    )
    assert (
        AbstractEndpointTest._encode_query_values(("team.members", "team.members"))
        == "team.members"
    )
    assert AbstractEndpointTest._encode_query_values(None) is None


def test_resolve_parent_context_uses_cached_parent_ids():
    dummy = DummyEndpointTest()
    dummy.tracked_entities = {
        "get_parent_ids": {"team_id": "TEAM123"},
        "get_path_parent_ids": {},
    }

    parent_ids, path_ids = dummy._resolve_parent_context(
        "get", {}, None, detail_nesting_level=1
    )

    assert parent_ids["team_id"] == "TEAM123"
    assert path_ids["team_id"] == "TEAM123"


def test_resolve_parent_context_falls_back_to_team_argument():
    dummy = DummyEndpointTest()
    dummy.tracked_entities = {}

    parent_ids, path_ids = dummy._resolve_parent_context(
        "get", {}, "TEAM456", detail_nesting_level=1
    )

    assert parent_ids["team_id"] == "TEAM456"
    assert path_ids["team_id"] == "TEAM456"


def test_get_falls_back_to_non_nested_endpoint(monkeypatch):
    dummy = DummyEndpointTest()
    dummy.tracked_entities = {
        "get": {"id": "role123"},
        "get_parent_ids": {"team_id": "TEAM123"},
        "get_path_parent_ids": {"team_id": "TEAM123"},
    }

    server = DummyServer()

    result = dummy._get(
        server,
        jwt_token="token",
        user_id="user",
        team_id="TEAM123",
        get_key="get",
        fields=["id"],
    )

    assert result["id"] == "role123"
    assert dummy.tracked_entities["get_path_parent_ids"] == {}
    assert server.calls == [
        "/v1/team/TEAM123/role/role123?fields=id",
        "/v1/role/role123?fields=id",
    ]
