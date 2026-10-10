# Memory: NaN Propagation Rule

- **Scope**: Quant Pipeline (Signals & Backtesting)
- **Principle**: Enforce strict Fail-Fast validation via NaN Propagation

---

## 1. The Core Principle

In this quantitative trading system, **data missingness (NaN) must never be silently ignored or hidden**. Masking data anomalies (e.g., via default framework interpolation, `skipna=True`, or `.fillna(0.0)`) leads to silent data distortion, survivorship bias, and incorrect portfolio allocations.

1. **Propagation by Default**:
   All statistical, rolling, aggregation, and mathematical functions must natively propagate `NaN`. 
   If an input vector or window contains even a single `NaN`, the calculated output must be `NaN`.
   - Explicitly pass `skipna=False` to pandas/numpy methods (e.g., `mean`, `std`, `min`, `max`, `sum(min_count=1)`).
   - Never replace `NaN` with default constants (like `0.0` or empty strings) unless it is a mathematically proven non-error state (like unallocated portfolio weights).

2. **Explicit Handling Only at Designated Checkpoints**:
   The removal of `NaN` (such as via `.dropna()`) is strictly restricted to intentional preprocessing gateways, most notably **right before final performance metrics evaluation** (to strip out lookback warm-up periods).

---

## 2. Code Reference Guidelines

- **Standard Volatility**: Use `returns.std(skipna=False)`.
- **Maximum Drawdown (MDD)**: Use `drawdown.min(skipna=False)`.
- **Downside Volatility (Sortino)**: Prevent NaN from converting to 0 in conditional boolean masks. Ensure `.mean(skipna=False)` or similar aggregation is applied.
- **Win Rate**: Guard inputs containing `NaN` to explicitly output `NaN` instead of computing raw true/false ratios.
- **Correlation & Selection**: Let NaNs in correlation metrics naturally propagate. If any asset in the selection universe contains `NaN` values, propagate `NaN` weights through portfolio allocation.
