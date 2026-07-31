"""Loads the master expected-results workbook into structured, queryable golden data."""
from dataclasses import dataclass, field
from typing import Dict, List

import openpyxl

from src.paths import workbook_path


@dataclass
class GoldenSample:
    sample_id: str
    country: str
    country_code: str
    system: str
    invoice_id: str
    file_name: str
    scenario: str
    tax_category: str
    tax_rate: str
    customer_type: str
    expected_status: str
    expected_finding_count: int
    expected_findings: List[str] = field(default_factory=list)
    should_not_flag: List[str] = field(default_factory=list)


@dataclass
class ExpectedFinding:
    sample_id: str
    invoice_id: str
    agent: str
    issue_type: str
    severity: str
    problem: str
    expected_rule: str
    root_cause: str
    suggested_fix: str


@dataclass
class NegativeAssertion:
    sample_id: str
    invoice_id: str
    should_not_flag: str
    reason: str


@dataclass
class GoldenData:
    samples: Dict[str, GoldenSample]
    expected_findings: List[ExpectedFinding]
    negative_assertions: List[NegativeAssertion]
    rule_matrix: Dict[str, Dict[str, int]]

    def findings_for(self, sample_id: str) -> List[ExpectedFinding]:
        return [f for f in self.expected_findings if f.sample_id == sample_id]

    def negatives_for(self, sample_id: str) -> List[NegativeAssertion]:
        return [n for n in self.negative_assertions if n.sample_id == sample_id]


def _split_multi(value) -> List[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() == "none":
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def _rows(ws):
    return list(ws.iter_rows(values_only=True))


def load_golden_data() -> GoldenData:
    path = workbook_path()
    if not path.exists():
        raise FileNotFoundError(f"Master workbook not found: {path}")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    samples: Dict[str, GoldenSample] = {}
    for row in _rows(wb["All_Samples"])[1:]:
        if row[3] is None:
            continue
        sample_id = str(row[3]).strip()
        try:
            count = int(row[11]) if row[11] is not None else 0
        except (TypeError, ValueError):
            count = 0
        samples[sample_id] = GoldenSample(
            sample_id=sample_id,
            country=str(row[0]).strip() if row[0] else "",
            country_code=str(row[1]).strip() if row[1] else "",
            system=str(row[2]).strip() if row[2] else "",
            invoice_id=str(row[5]).strip() if row[5] else "",
            file_name=str(row[4]).strip() if row[4] else "",
            scenario=str(row[6]).strip() if row[6] else "",
            tax_category=str(row[7]).strip() if row[7] else "",
            tax_rate=str(row[8]).strip() if row[8] else "",
            customer_type=str(row[9]).strip() if row[9] else "",
            expected_status=str(row[10]).strip() if row[10] else "",
            expected_finding_count=count,
            expected_findings=_split_multi(row[12]),
            should_not_flag=_split_multi(row[13]),
        )

    expected_findings: List[ExpectedFinding] = []
    for row in _rows(wb["Expected_Findings"])[1:]:
        if row[2] is None:
            continue
        expected_findings.append(
            ExpectedFinding(
                sample_id=str(row[2]).strip(),
                invoice_id=str(row[3]).strip() if row[3] else "",
                agent=str(row[4]).strip() if row[4] else "",
                issue_type=str(row[5]).strip() if row[5] else "",
                severity=str(row[6]).strip() if row[6] else "",
                problem=str(row[7]).strip() if row[7] else "",
                expected_rule=str(row[8]).strip() if row[8] else "",
                root_cause=str(row[9]).strip() if row[9] else "",
                suggested_fix=str(row[10]).strip() if row[10] else "",
            )
        )

    negative_assertions: List[NegativeAssertion] = []
    for row in _rows(wb["Negative_Assertions"])[1:]:
        if row[2] is None:
            continue
        negative_assertions.append(
            NegativeAssertion(
                sample_id=str(row[2]).strip(),
                invoice_id=str(row[3]).strip() if row[3] else "",
                should_not_flag=str(row[4]).strip() if row[4] else "",
                reason=str(row[5]).strip() if row[5] else "",
            )
        )

    rule_matrix: Dict[str, Dict[str, int]] = {}
    matrix_rows = _rows(wb["Rule_Matrix"])
    header = matrix_rows[0]
    sample_columns = [(idx, str(col).strip()) for idx, col in enumerate(header)
                      if idx > 0 and col and str(col).strip() != "Coverage"]
    for row in matrix_rows[1:]:
        issue_type = row[0]
        if issue_type is None:
            continue
        issue_type = str(issue_type).strip()
        per_sample: Dict[str, int] = {}
        for idx, sample_id in sample_columns:
            try:
                per_sample[sample_id] = int(row[idx]) if row[idx] is not None else 0
            except (TypeError, ValueError):
                per_sample[sample_id] = 0
        rule_matrix[issue_type] = per_sample

    wb.close()
    return GoldenData(
        samples=samples,
        expected_findings=expected_findings,
        negative_assertions=negative_assertions,
        rule_matrix=rule_matrix,
    )
