# agent-quarantine

Dormant code for the **e-Invoice validation-agent** testing effort (Track B). It is
kept here, out of the active Playwright/pytest-bdd UI suite, so it does not affect
collection or CI while remaining available for a future re-activation.

Nothing in this folder is collected by pytest: `pytest.ini` sets
`testpaths = tests step_defs` and `python_files = test_*.py`, and this folder is
neither of those paths nor does `agent_step_defs_archived.py` match `test_*.py`.

## Contents

| Path | What it is |
|------|------------|
| `einvoice-agent-testing/` | Test-data XMLs, expected-results workbook, and results output for the agent flow. |
| `einvoice_agent_e2e.py` | Helper module: file discovery, offline comparison, report/Excel generation. (Formerly `utilities/einvoice_agent_e2e.py`.) |
| `agent_step_defs_archived.py` | The agent step definitions, Accept/Reject action steps, the `data_ingestion_page` fixture, and the 7 commented-out agent `@scenario`s. (Extracted from `tests/step_defs/test_e_invoice_management.py`.) |
| `Prompt Files/` | AI-agent authoring prompts (bug creation, test-case creation, Quality Intelligence Suite). |
| `AppContext File/` | AI-agent application context and business rules used by the test-data agent. |

## Dependencies

Install the agent-only requirements before running the flow:

```
pip install -r requirements-agent.txt
```

## Re-activation (future)

1. Move `einvoice_agent_e2e.py` back to `utilities/einvoice_agent_e2e.py`
   (restores the `from utilities import einvoice_agent_e2e` import path) and move
   `einvoice-agent-testing/` back to the repo root (or update `EAT_DIR`).
2. Fold the step code from `agent_step_defs_archived.py` back into
   `tests/step_defs/test_e_invoice_management.py` and re-add the corresponding
   agent scenarios to `tests/features/Vat_e_invoice_management.feature`.
3. Uncomment / restore the 7 agent `@scenario` decorators.
4. The `AgentE2E`, `AgentAction`, `TC_AGENT_*`, and `Client_*` markers are still
   registered in `pytest.ini`, so no marker changes are needed.
