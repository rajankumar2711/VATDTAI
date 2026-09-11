"""One-shot Phase 3 helper: extract dormant AI-agent step code from the active IM
step file into agent-quarantine/agent_step_defs_archived.py, and strip it from the
active file. Marker-based so it is robust to line shifts and the redacted line
inside the removed block."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # Playwright_Python/
SRC = ROOT / "tests" / "step_defs" / "test_e_invoice_management.py"
QDIR = ROOT / "agent-quarantine"
ARCHIVE = QDIR / "agent_step_defs_archived.py"

text = SRC.read_text(encoding="utf-8")
removed = []


def cut_span(s: str, start_anchor: str, end_anchor: str, include_end: bool) -> str:
    """Remove [start_anchor .. end_anchor] from module text; return removed chunk."""
    global text
    i = text.index(start_anchor)
    j = text.index(end_anchor, i)
    end = j + len(end_anchor) if include_end else j
    chunk = text[i:end]
    text = text[:i] + text[end:]
    return chunk


# 1. Two agent-only imports
for imp in (
    "from pageobjects.vat_data_ingestion_page import VatDataIngestionPage\n",
    "from utilities import einvoice_agent_e2e as agent_e2e\n",
):
    text = text.replace(imp, "", 1)
    removed.append(imp)

# 2. data_ingestion_page fixture (with its two leading blank lines)
fx = cut_span(
    text,
    "\n\n@pytest.fixture()\ndef data_ingestion_page(",
    "    return VatDataIngestionPage(get_page)\n",
    include_end=True,
)
removed.append(fx.lstrip("\n"))

# 3. Commented-out 7 agent @scenarios (+ TODO banner)
cm = cut_span(
    text,
    "# ------------------------------------------------------------------\n# TODO(agent-e2e):",
    "# def test_agent_reject_one(get_page, vat_context, im_page):\n#     pass\n",
    include_end=True,
)
removed.append(cm)

# 4. AGENT E2E STEPS section (header through last agent-wait function)
ae = cut_span(
    text,
    "# ==========================================\n# AGENT E2E STEPS (Track B",
    "# ==========================================\n# THEN STEPS (Assertions)",
    include_end=False,
)
removed.append(ae)

# 5. Review-Required assertion + AGENT ACTION STEPS section
ra = cut_span(
    text,
    '@then("Review Required invoices match the expected results workbook")',
    "# ==================================================================\n# UI/UX SMOKE SUITE STEPS",
    include_end=False,
)
removed.append(ra)

# Collapse any run of 3+ blank lines left behind down to 2
text = re.sub(r"\n{4,}", "\n\n\n", text)

# Write the stripped active file
SRC.write_text(text, encoding="utf-8")

# Build the quarantine archive
QDIR.mkdir(parents=True, exist_ok=True)
header = '''"""
ARCHIVED - dormant AI validation-agent step definitions (quarantined in Phase 3).

This module is intentionally OUTSIDE pytest testpaths and is NOT collected. It
preserves the agent-E2E / Accept-Reject step code and the 7 commented agent
@scenarios that used to live in tests/step_defs/test_e_invoice_management.py, so
they can be restored when the agent scenarios are re-added to the feature file.

See agent-quarantine/README.md for how to reactivate.
"""
import logging
import os
import re
import tempfile
from typing import Dict, Any

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, scenario, then, when, parsers

from pageobjects.vat_e_invoice_management_page import (
    VatEInvoiceManagementPage,
    file_contains_values,
    assert_export_format,
)
from pageobjects.vat_data_ingestion_page import VatDataIngestionPage
from utilities import einvoice_agent_e2e as agent_e2e

logger = logging.getLogger(__name__)


@pytest.fixture()
def data_ingestion_page(get_page: Page) -> VatDataIngestionPage:
    """Function-scoped fixture to provide Data Ingestion page object (for the agent E2E)."""
    return VatDataIngestionPage(get_page)


'''
body = "\n\n".join(chunk.strip("\n") for chunk in removed[3:])  # skip imports + fixture (in header)
ARCHIVE.write_text(header + body + "\n", encoding="utf-8")

print("REMOVED IMPORTS:", removed[0].strip(), "|", removed[1].strip())
print("Fixture chars:", len(fx))
print("Commented block chars:", len(cm))
print("Agent E2E section chars:", len(ae))
print("Review+Action section chars:", len(ra))
print("Active file now:", len(text.splitlines()), "lines")
print("Archive written:", ARCHIVE, "-", len(ARCHIVE.read_text(encoding='utf-8').splitlines()), "lines")
