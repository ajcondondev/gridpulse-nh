from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_sources_returns_all():
    res = client.get("/sources")
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert data["total"] == len(data["sources"])
    assert data["total"] > 0


def test_list_sources_excludes_mock_by_default():
    res = client.get("/sources")
    ids = [s["id"] for s in res.json()["sources"]]
    assert "mock_demand" not in ids


def test_list_sources_includes_mock_with_param():
    res = client.get("/sources?include_mock=true")
    ids = [s["id"] for s in res.json()["sources"]]
    assert "mock_demand" in ids


def test_production_sources_are_all_real_data():
    res = client.get("/sources")
    for source in res.json()["sources"]:
        assert source.get("is_mock_data") is False, (
            f"Source '{source['id']}' has is_mock_data=True but appears in the production list"
        )
        assert source.get("is_real_data") is True, (
            f"Source '{source['id']}' has is_real_data=False but appears in the production list"
        )


def test_get_source_mock_demand():
    res = client.get("/sources/mock_demand")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "mock_demand"
    assert data["status"] == "test_fixture_only"
    assert data["is_mock_data"] is True
    assert data["is_real_data"] is False
    assert data["category"] == "electricity"


def test_get_source_not_found():
    res = client.get("/sources/does_not_exist")
    assert res.status_code == 404


def test_get_source_isone_csv_is_active():
    res = client.get("/sources/isone_csv")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "isone_csv"
    assert data["status"] == "active"
    assert data["data_format"] == "CSV"


def test_get_source_openei_rates_is_active():
    res = client.get("/sources/openei_rates")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "openei_rates"
    assert data["status"] == "active"


def test_get_source_epa_egrid_is_active():
    res = client.get("/sources/epa_egrid")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "epa_egrid"
    assert data["status"] == "active"


def test_fetch_source_returns_not_implemented_message():
    res = client.post("/sources/epa_ejscreen/fetch")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert "source_id" in data


def test_fetch_source_unknown_returns_404():
    res = client.post("/sources/unknown_source/fetch")
    assert res.status_code == 404


# ── Phase 14: status model and metadata accuracy ────────────────────────────

VALID_STATUSES = {"active", "requires_key", "manual_import", "planned", "research", "not_implemented", "test_fixture_only"}


def test_all_source_statuses_are_valid():
    res = client.get("/sources")
    for source in res.json()["sources"]:
        assert source["status"] in VALID_STATUSES, (
            f"Source '{source['id']}' has unknown status '{source['status']}'"
        )


def test_active_sources_have_last_verified():
    res = client.get("/sources")
    for source in res.json()["sources"]:
        if source["status"] == "active":
            assert source.get("last_verified"), (
                f"Active source '{source['id']}' is missing last_verified"
            )


def test_eia_requires_key_status():
    res = client.get("/sources/eia_isone_load")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "requires_key"
    assert data["requires_api_key"] is True


def test_noaa_requires_key_status():
    res = client.get("/sources/noaa_weather")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "requires_key"
    assert data["requires_api_key"] is True


def test_isone_csv_has_no_key_required():
    res = client.get("/sources/isone_csv")
    data = res.json()
    assert data["requires_api_key"] is False


def test_source_detail_includes_phase_added():
    res = client.get("/sources/cdc_svi")
    data = res.json()
    assert data["phase_added"] == 12


def test_source_detail_includes_access_type():
    res = client.get("/sources/fema_flood")
    data = res.json()
    assert data["access_type"] == "arcgis_rest"


def test_not_implemented_sources_have_correct_status():
    not_implemented_ids = ["epa_ejscreen", "nhsaves", "nh_puc", "eversource_sustainability"]
    for source_id in not_implemented_ids:
        res = client.get(f"/sources/{source_id}")
        assert res.status_code == 200
        assert res.json()["status"] == "not_implemented", (
            f"{source_id} should be not_implemented"
        )


def test_manchester_gis_is_research():
    res = client.get("/sources/manchester_gis")
    assert res.status_code == 200
    assert res.json()["status"] == "research"


def test_active_sources_have_connector_implemented():
    res = client.get("/sources")
    for source in res.json()["sources"]:
        if source["status"] == "active":
            assert source.get("connector_implemented") is True, (
                f"Active source '{source['id']}' has connector_implemented=False"
            )


def test_requires_key_sources_have_api_key_env_var():
    for source_id in ["eia_isone_load", "noaa_weather"]:
        res = client.get(f"/sources/{source_id}")
        data = res.json()
        assert data.get("api_key_env_var"), (
            f"Source '{source_id}' requires a key but api_key_env_var is not set"
        )


def test_registry_validation_no_active_without_connector():
    from app.config import settings
    from app.registry import SOURCES
    from app.registry_validation import validate_registry
    warnings = validate_registry(SOURCES, settings)
    active_connector_warnings = [
        w for w in warnings if "active" in w and "connector_implemented=False" in w
    ]
    assert not active_connector_warnings, (
        f"Registry has active sources without connectors: {active_connector_warnings}"
    )


def test_registry_validation_no_mock_in_wrong_status():
    from app.config import settings
    from app.registry import SOURCES
    from app.registry_validation import validate_registry
    warnings = validate_registry(SOURCES, settings)
    mock_status_warnings = [w for w in warnings if "is_mock_data=True" in w]
    assert not mock_status_warnings, (
        f"Registry has mock sources with incorrect status: {mock_status_warnings}"
    )


def test_registry_validation_warns_on_active_without_connector():
    from app.schemas.source import Source, SourceCategory, SourceStatus
    from app.registry_validation import validate_registry

    bad_source = Source(
        id="fake_broken",
        name="Broken",
        description="Test",
        category=SourceCategory.electricity,
        status=SourceStatus.active,
        connector_implemented=False,
    )

    class _FakeSettings:
        pass

    warnings = validate_registry([bad_source], _FakeSettings())
    assert any("connector_implemented=False" in w for w in warnings)


def test_registry_validation_warns_on_mock_with_wrong_status():
    from app.schemas.source import Source, SourceCategory, SourceStatus
    from app.registry_validation import validate_registry

    bad_source = Source(
        id="sneaky_mock",
        name="Sneaky",
        description="Test",
        category=SourceCategory.electricity,
        status=SourceStatus.active,
        is_mock_data=True,
        connector_implemented=True,
    )

    class _FakeSettings:
        pass

    warnings = validate_registry([bad_source], _FakeSettings())
    assert any("is_mock_data=True" in w for w in warnings)


def test_source_catalog_docs_exist():
    import pathlib
    docs = pathlib.Path(__file__).parent.parent.parent.parent / "docs"
    assert (docs / "source_catalog.md").exists()
    assert (docs / "source_roadmap.md").exists()
    assert (docs / "progress_tracker.md").exists()
    assert (docs / "data_source_disclaimers.md").exists()
