from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Txn:
    when: date
    amount: Decimal  # negative = spending, positive = income
    note: str = ""
    category: str = "uncategorized"
    currency: str = "XBS"
