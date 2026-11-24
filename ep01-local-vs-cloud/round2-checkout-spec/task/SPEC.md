# Checkout spec

Implement `checkout(items, codes)` in `shop/checkout.py`.

- `items`: list of `(sku, unit_price, qty)`; unit_price is a str or Decimal, qty a positive int. The same sku may appear more than once: merge them (the first unit_price wins).
- `codes`: list of promo code strings (may be empty). Codes are case-insensitive and surrounding whitespace is ignored. Duplicate codes count once.
  - `SAVE10`: 10% off the goods. `SAVE20`: 20% off the goods. At most one percentage code may be used: if both are given, use the larger one.
  - `FLAT5`: $5 off the goods, never taking goods below $0.
  - `BOGO:<sku>` (sku part case-sensitive as written after the colon, but the `BOGO:` prefix is case-insensitive): for that sku, every 2nd unit is free (qty 3 -> 1 free, qty 4 -> 2 free). Unknown sku in a BOGO code is ignored.
  - `FREESHIP`: shipping is free.
  - Any other code: raise `ValueError` whose message contains the original code text as given.
- Order: BOGO first, then the percentage code, then FLAT5.
- Shipping: $7.50, but free if goods after all discounts are >= $50.00, or with FREESHIP. Shipping is $0 if the cart is empty.
- TAX 15% on (goods after discounts + shipping).
- Rounding: keep full precision during the calculation; round every returned amount to cents, half-up.
- Return a dict with Decimal values: `goods`, `discount` (goods before discounts minus goods after), `shipping`, `tax`, `total` where total = goods + shipping + tax (computed from the rounded parts).
