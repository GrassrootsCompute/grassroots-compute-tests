from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Txn:
    when: date
    amount: Optional[Decimal]  # negative = spending; None = corrupted record
    category: str = "other"
    merchant: str = ""
