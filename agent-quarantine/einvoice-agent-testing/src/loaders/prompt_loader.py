"""Loads approved agent prompts with checksum and version for traceability (guide Sec 3)."""
import hashlib
from dataclasses import dataclass

from src.paths import PROMPTS_DIR
from src.loaders.config_loader import load_business_rules

PROMPT_VERSION = "1.0"


@dataclass(frozen=True)
class PromptRecord:
    business_rule_id: str
    agent_label: str
    name: str
    file_name: str
    version: str
    checksum: str
    text: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_prompt(business_rule_id: str) -> PromptRecord:
    rules = load_business_rules()["rules"]
    rule = rules.get(business_rule_id)
    if rule is None:
        raise KeyError(f"Unknown business rule id: {business_rule_id}")
    path = PROMPTS_DIR / rule["prompt_file"]
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return PromptRecord(
        business_rule_id=business_rule_id,
        agent_label=rule["agent_label"],
        name=rule["name"],
        file_name=rule["prompt_file"],
        version=PROMPT_VERSION,
        checksum=_sha256(text),
        text=text,
    )


def load_all_prompts() -> dict:
    rules = load_business_rules()["rules"]
    return {br_id: load_prompt(br_id) for br_id in rules}
