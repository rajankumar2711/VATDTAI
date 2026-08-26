"""Loads the four JSON configuration files under config/."""
import json
from functools import lru_cache

from src.paths import CONFIG_DIR


def _read_json(name: str) -> dict:
    path = CONFIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def load_business_rules() -> dict:
    return _read_json("business_rules.json")


@lru_cache(maxsize=None)
def load_countries() -> dict:
    return _read_json("countries.json")


@lru_cache(maxsize=None)
def load_agent_runtime() -> dict:
    return _read_json("agent_runtime.json")


@lru_cache(maxsize=None)
def load_source_field_mapping() -> dict:
    return _read_json("source_field_mapping.json")


def allowed_issue_types(business_rule_id: str) -> set:
    """Configured allowed issue types for a rule plus the common cross-cutting types."""
    br = load_business_rules()
    rule = br["rules"].get(business_rule_id)
    if rule is None:
        raise KeyError(f"Unknown business rule id: {business_rule_id}")
    return set(rule["allowed_issue_types"]) | set(br.get("common_issue_types", []))


def country_config(country_code: str) -> dict:
    return load_countries()["countries"].get(country_code, {})
