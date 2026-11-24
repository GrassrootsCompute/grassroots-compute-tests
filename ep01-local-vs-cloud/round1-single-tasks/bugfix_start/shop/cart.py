from decimal import Decimal
from .pricing import money, apply_discount

TAX = Decimal("0.15")

class Cart:
    def __init__(self):
        self.items = {}

    def add(self, sku, price, qty=1):
        if qty <= 0:
            raise ValueError("qty must be positive")
        p, q = self.items.get(sku, (Decimal(str(price)), 0))
        self.items[sku] = (p, qty)

    def subtotal(self):
        return sum(p * q for p, q in self.items.values())

    def total(self, code=None):
        """Discount first, then add 15% TAX, then round to cents."""
        after = apply_discount(self.subtotal(), code)
        return money(after) * (1 + TAX)
