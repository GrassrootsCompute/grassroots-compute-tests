# Report module conventions

Every module in `reports/` exposes `compute(txns, year, month)` and must follow these rules.

## 1. Money rounding
Every money value a report returns (including values inside dicts) must be rounded with
`core.money.round_cents` (to cents, half-up), applied once to the final value. Do not use
`round()`, bare `Decimal.quantize()` without the rounding mode, or string formatting for rounding.
Percentages are not money: return them unrounded as Decimal.

## 2. Period filtering
Selecting the transactions of a month must use `core.dates.month_bounds` together with
`core.dates.in_period` (end bound exclusive). Never hand-write the comparison.

## 3. Bad input
A transaction whose `amount` is None is corrupt. `compute` must raise
`core.errors.ReportError` with code `"E_AMOUNT"` before doing anything else - never skip the
record, never return None, never raise a different exception type.

## 4. Everything else
Keep each report's business logic exactly as it is. Only fix violations of rules 1-3.
