"""Schema-tolerant validation: errors block runs; missing facts remain UNKNOWN warnings."""
from __future__ import annotations

from dataclasses import dataclass, field
from .master_loader import MasterWorkbook


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_master(master: MasterWorkbook) -> ValidationReport:
    report = ValidationReport()
    store, origin, route, hours = (master.tables[x] for x in ("STORE", "ORIGIN", "ROUTE_MATRIX", "STORE_HOUR"))
    if store.store_id.duplicated().any(): report.errors.append("STORE.store_id is not unique")
    ids = set(store.store_id.dropna())
    if not set(origin.store_id.dropna()).issubset(ids): report.errors.append("ORIGIN has unknown store_id")
    if not set(route.origin_store_id.dropna()).issubset(ids) or not set(route.destination_store_id.dropna()).issubset(ids): report.errors.append("ROUTE_MATRIX has unknown store reference")
    if (route.origin_store_id == route.destination_store_id).any(): report.errors.append("ROUTE_MATRIX has self-route")
    if hours.duplicated(["store_id", "day_of_week"]).any(): report.errors.append("STORE_HOUR has duplicate store/day")
    for table, column in (("STORE", "parking_available"), ("STORE", "representative_price_krw"), ("STORE_HOUR", "open_time")):
        if column in master.tables[table] and master.tables[table][column].isna().any():
            report.warnings.append(f"{table}.{column} has missing values; preserve as UNKNOWN")
    return report
