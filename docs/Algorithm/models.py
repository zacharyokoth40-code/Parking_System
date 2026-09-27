"""
Models Module
Plain data containers passed between modules. Kept dependency-free
so any module can import them without importing Flask or sqlite3.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Slot:
    slot_id: int
    bay_number: str
    status: str  # FREE | OCCUPIED | OUT_OF_SERVICE


@dataclass
class Vehicle:
    entry_id: int
    plate_number: str
    slot_id: int
    entry_time: str
    exit_time: Optional[str]
    status: str  # ACTIVE | COMPLETED


@dataclass
class RateTier:
    rate_id: int
    tier_order: int
    max_minutes: Optional[int]  # None = open-ended top tier
    amount: float


@dataclass
class Transaction:
    txn_id: int
    entry_id: int
    amount: float
    method: str
    status: str
    receipt_no: str
    timestamp: str
