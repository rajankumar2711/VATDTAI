"""Central path resolution for the e-invoice agent testing harness."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PROMPTS_DIR = BASE_DIR / "prompts"
TEST_DATA_DIR = BASE_DIR / "test-data"
EXPECTED_RESULTS_DIR = BASE_DIR / "expected results"
CONFIG_DIR = BASE_DIR / "config"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_RAW_DIR = RESULTS_DIR / "raw"
RESULTS_NORMALIZED_DIR = RESULTS_DIR / "normalized"
RESULTS_REPORTS_DIR = RESULTS_DIR / "reports"

WORKBOOK_NAME = "EInvoice_Agent_Test_Master_60_Samples_v3.xlsx"


def workbook_path() -> Path:
    return EXPECTED_RESULTS_DIR / WORKBOOK_NAME


COUNTRY_FOLDER_TO_CODE = {"Belgium": "BE", "France": "FR", "Poland": "PL"}
SOURCE_FOLDER_TO_SHORT = {"SAP": "SAP", "CustomERP": "ERP"}
