import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.source import Source

logger = logging.getLogger(__name__)

_KEY_ATTR_MAP = {
    "EIA_API_KEY": "eia_api_key",
    "NOAA_TOKEN": "noaa_token",
    "NREL_API_KEY": "nrel_api_key",
    "OPENEI_API_KEY": "openei_api_key",
}


def validate_registry(sources: list["Source"], settings) -> list[str]:
    """Return a list of warning strings describing registry inconsistencies."""
    warnings: list[str] = []

    for source in sources:
        # Active source must have a connector built
        if source.status == "active" and not source.connector_implemented:
            warnings.append(
                f"Source '{source.id}' is marked active but connector_implemented=False — "
                "set status to not_implemented or build the connector."
            )

        # Mock data should never appear outside test_fixture_only
        if source.is_mock_data and source.status != "test_fixture_only":
            warnings.append(
                f"Source '{source.id}' has is_mock_data=True but status is '{source.status}' — "
                "mock sources should use status=test_fixture_only."
            )

        # Required key not configured
        if source.requires_api_key and source.api_key_env_var:
            attr = _KEY_ATTR_MAP.get(source.api_key_env_var)
            if attr:
                val = getattr(settings, attr, "")
                if not val:
                    warnings.append(
                        f"Source '{source.id}' requires {source.api_key_env_var} "
                        "but it is not set in .env — fetches will fail."
                    )

    return warnings


def log_registry_warnings(sources: list["Source"], settings) -> None:
    for warning in validate_registry(sources, settings):
        logger.warning("[Registry] %s", warning)
