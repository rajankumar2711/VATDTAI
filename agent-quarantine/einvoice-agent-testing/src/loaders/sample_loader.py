"""Discovers the 60 XML test samples and derives their metadata from path + filename."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.paths import TEST_DATA_DIR, COUNTRY_FOLDER_TO_CODE, SOURCE_FOLDER_TO_SHORT


@dataclass(frozen=True)
class Sample:
    sample_id: str          # e.g. BE-SAP-01, PL-ERP-04 (matches the master workbook)
    country_code: str       # BE / FR / PL
    country_name: str       # Belgium / France / Poland
    source_system: str      # SAP / CustomERP
    source_short: str       # SAP / ERP
    sequence: str           # 01..10
    invoice_id: str         # e.g. SAP-BE-2026-01001
    file_name: str
    path: Path

    def read_xml(self) -> str:
        return self.path.read_text(encoding="utf-8")


def _parse_file_name(file_name: str):
    stem = file_name[:-4] if file_name.lower().endswith(".xml") else file_name
    parts = stem.split("_")
    if len(parts) < 4:
        raise ValueError(f"Unexpected sample file name: {file_name}")
    # parts: [system, country_code, sequence, invoice_id...]
    sequence = parts[2]
    invoice_id = "_".join(parts[3:])
    return sequence, invoice_id


def discover_samples() -> List[Sample]:
    samples: List[Sample] = []
    for country_folder, country_code in COUNTRY_FOLDER_TO_CODE.items():
        for source_folder, source_short in SOURCE_FOLDER_TO_SHORT.items():
            folder = TEST_DATA_DIR / country_folder / source_folder
            if not folder.exists():
                continue
            for path in sorted(folder.glob("*.xml")):
                sequence, invoice_id = _parse_file_name(path.name)
                samples.append(
                    Sample(
                        sample_id=f"{country_code}-{source_short}-{sequence}",
                        country_code=country_code,
                        country_name=country_folder,
                        source_system=source_folder,
                        source_short=source_short,
                        sequence=sequence,
                        invoice_id=invoice_id,
                        file_name=path.name,
                        path=path,
                    )
                )
    return sorted(samples, key=lambda s: s.sample_id)


def population_groups() -> dict:
    """Groups samples by (country_code, source_system) for the BR-13 population agent."""
    groups: dict = {}
    for sample in discover_samples():
        groups.setdefault((sample.country_code, sample.source_system), []).append(sample)
    return groups
