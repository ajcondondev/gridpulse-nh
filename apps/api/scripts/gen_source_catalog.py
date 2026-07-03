"""Regenerate docs/source_catalog.md from the source registry.

Usage (from apps/api, with the venv active):

    python -m scripts.gen_source_catalog
"""

from pathlib import Path

from app.registry import SOURCES

DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"


def _key_cell(source) -> str:
    if source.requires_api_key:
        return f"`{source.api_key_env_var or '?'}` (required)"
    if source.api_key_env_var:
        return f"`{source.api_key_env_var}` (optional)"
    return "none"


def build_catalog() -> str:
    lines = [
        "# Source Catalog",
        "",
        "_Generated from `apps/api/app/registry.py` — the registry is the source of "
        "truth. Regenerate with `python -m scripts.gen_source_catalog` from `apps/api`._",
        "",
        f"{len(SOURCES)} sources. Statuses: `active` (working connector), "
        "`requires_key` (works with a free key), `research` / `not_implemented` "
        "(no stable public API yet), `test_fixture_only` (synthetic, tests only).",
        "",
        "| Source | Category | Status | API key | Format | Geography | Updates |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in SOURCES:
        lines.append(
            f"| {s.name} | {s.category.value} | `{s.status.value}` | {_key_cell(s)} "
            f"| {s.data_format} | {s.data_geography} | {s.update_frequency} |"
        )
    lines += [
        "",
        "Per-source URLs, notes, and last-verified dates are available in the app "
        "under **Sources**, or via `GET /sources`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / "source_catalog.md"
    out_path.write_text(build_catalog(), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
