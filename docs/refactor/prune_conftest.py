"""Phase C: remove 4 dead fixtures from conftest.py, simplify the dead
authenticated_vat_page screenshot-hook branch, and drop imports that become
unused. Marker-based for safety."""
import re
from pathlib import Path

CT = Path(__file__).resolve().parent.parent.parent / "conftest.py"
text = CT.read_text(encoding="utf-8-sig")  # strip BOM


def cut(start_anchor: str, end_anchor: str):
    global text
    i = text.index(start_anchor)
    j = text.index(end_anchor, i + len(start_anchor))
    text = text[:i] + text[j:]


# a) authenticated_vat_page fixture
cut("# Module-scoped authenticated VAT DTAI fixture",
    "# VAT DTAI Test Context - Shared state across navigation steps (function-scoped)")
# b) vat_module_context fixture
cut("# Module-scoped VAT context for shared session",
    "# API Request Context")
# c) api_request_context fixture
cut("# API Request Context",
    "# Singleton logger instance for the whole test session")

# d) excel_writer fixture (to EOF)
i = text.index("@pytest.fixture\ndef excel_writer(request):")
text = text[:i].rstrip() + "\n"

# e) simplify the screenshot hook branch (authenticated_vat_page no longer exists)
text = text.replace(
    '''                page = None
                if "authenticated_vat_page" in item.funcargs:
                    page = item.funcargs["authenticated_vat_page"]["page"]
                elif "get_page" in item.funcargs:
                    page = item.funcargs["get_page"]''',
    '''                page = None
                if "get_page" in item.funcargs:
                    page = item.funcargs["get_page"]''',
)

# f) drop imports that are now unused
# APIRequestContext (only used by removed fixture signature/annotation)
if "APIRequestContext" not in re.sub(r"^from playwright\.sync_api import .*$", "", text, flags=re.M):
    text = text.replace("from playwright.sync_api import Playwright, Page, APIRequestContext, sync_playwright\n",
                        "from playwright.sync_api import Playwright, Page, sync_playwright\n")

# Whole-line imports removable if their symbol no longer appears in the body
def drop_line_if_unused(import_line: str, symbol: str):
    global text
    body = text.replace(import_line, "")
    if not re.search(rf"\b{re.escape(symbol)}\b", body):
        text = body

drop_line_if_unused("from typing import Generator\n", "Generator")
drop_line_if_unused("from styleframe import StyleFrame, Styler\n", "StyleFrame")
drop_line_if_unused("import pandas as pd\n", "pd")
drop_line_if_unused("import json\n", "json")
drop_line_if_unused("import tempfile\n", "tempfile")

# collapse 3+ blank lines
text = re.sub(r"\n{4,}", "\n\n\n", text)
CT.write_text(text, encoding="utf-8")
print("conftest.py now:", len(text.splitlines()), "lines")
for sym in ("authenticated_vat_page", "vat_module_context", "api_request_context",
            "excel_writer", "APIRequestContext", "StyleFrame"):
    print(f"  remaining '{sym}':", text.count(sym))
