# Finance & Quantitative Development Rules

This document defines core engineering, computation, and time-series processing rules for quantitative research, financial data pipelines, technical indicators, asset allocation, and backtesting.

---

## 1. NaN Propagation & Fail-Fast Principles

Financial calculations require strict mathematical rigor. Default framework behaviors (such as Pandas' default `skipna=True` or `pct_change(fill_method='pad')`) silently mask anomalies, leading to distorted indicators, survivorship bias, and incorrect portfolio returns.

### Core Invariants
* **Input NaN Must Yield Output NaN**: Missing data (`NaN`) must never be silently dropped or masked with default constants (e.g., `0.0`). It must propagate through all intermediate calculations to the final output.
* **Input with NaN but Non-NaN Output is a Violation**: Silent loss of `NaN` distorts downstream signals and weights.
* **Input without NaN but NaN Output Indicates Logic Error**: Check for numerical instability (e.g., division by zero, empty arrays, invalid bounds).

### Pandas/NumPy NaN Preservation Patterns
* **Explicit `skipna=False` on Aggregations**:
  Explicitly pass `skipna=False` to reduction/aggregation operations so any NaN in the window propagates:
  ```python
  mean_val = series.mean(skipna=False)
  std_val = returns.std(skipna=False)
  mdd_val = drawdown.min(skipna=False)
  sum_val = series.sum(min_count=1)  # min_count prevents empty sum from returning 0.0
  ```
* **EWM Silent Skip Restoration (`calc_ema`, `calc_rsi`)**:
  `ewm().mean()` skips NaNs by default and reuses prior values. Always restore NaNs:
  ```python
  ema = series.ewm(span=period, adjust=False).mean().where(series.notna())
  ```
* **Explicit `fill_method=None` on `pct_change()`**:
  Default `pct_change()` forward-fills NaNs, converting missing prices into `0.0` returns. Always disable padding:
  ```python
  returns = prices.pct_change(fill_method=None)
  momentum_n = prices.pct_change(n, fill_method=None)
  ```
* **Boolean Conditions to Float**:
  Evaluating `series > threshold` maps `NaN` to `False`, which becomes `0.0` upon float conversion. Restore `NaN` via `.where()`:
  ```python
  signal = (series > threshold).where(series.notna()).astype(float)
  ```
* **Stateful Conditions & `ffill()`**:
  When preserving state with forward-fill, reapply original NaN masks:
  ```python
  state = raw_signal.ffill().fillna(0.0)
  return state.where(original_series.notna())
  ```
* **Downside Volatility & Win Rate**:
  Guard inputs containing `NaN` so that metrics compute to `NaN` rather than computing raw ratios over masked data:
  ```python
  negative_sq = returns.where(returns < 0, 0).where(returns.notna(), np.nan) ** 2
  sum_sq = negative_sq.sum(axis=0, skipna=False)
  ```

### Restricted `dropna` at Designated Checkpoints Only
* **No Premature `dropna()`**: Do not drop NaNs midway through indicator or signal calculations.
* **Single Pre-Evaluation Gateway**: Call `dropna()` exactly once immediately before computing final backtest summary metrics to isolate the common valid historical window and strip warm-up lookback periods.

### TDD for NaN Propagation
* When creating any new calculation or signal function, write unit tests verifying that mid-series NaNs propagate to the output (`test_nan_mid_series_propagates`) *before* writing the implementation.

---

## 2. Vectorization First (Performance & Simplicity)

* **Prioritize Vectorized Operations**:
  Always use Pandas and NumPy vectorized and broadcasting routines over procedural iteration.
* **Strict Loop Restrictions**:
  - Prohibit Python `for` / `while` loops, `.iterrows()`, `.itertuples()`, and row-wise `.apply()` across time steps or assets.
  - Exceptions are permitted **only** for strictly path-dependent state machines (e.g., dynamic stop-loss or recursive cash/margin constraints where step $t$ fundamentally requires the output of step $t-1$).
* **Panel-Level (`date × ticker`) Computations**:
  Avoid looping over tickers. Perform indicators, cross-sectional rankings, and normalizations across 2D DataFrames simultaneously:
  ```python
  # Preferred: 2D panel vectorization
  ranks = returns_df.rank(axis=1, ascending=False)
  top_n_weights = (ranks <= n).astype(float).div(n)
  ```
* **Vectorized Backtesting**:
  Calculate portfolio returns via matrix multiplication between the weights DataFrame and asset returns DataFrame, or utilize dedicated vectorized engines (e.g., `vectorbt`) before resorting to event-driven loops.

---

## 3. Financial Data Integrity & Time-Series Principles

* **Maximize Historical Data Horizon**:
  - Avoid hardcoding arbitrary start dates when downloading asset prices (e.g., via `yfinance`). Always pull the longest available history automatically.
  - Prefer proxy assets or mutual fund tickers with longer history when testing long-term macro strategies.
* **Strict Chronological Ordering**:
  - Guarantee `pd.DatetimeIndex` on all loaded price panels.
  - Enforce `sort_index()` ascending immediately upon loading or importing historical data before passing to pipelines or backtesters.
* **Strict Lookahead Bias Prevention**:
  - Decisions made for rebalancing at timestamp $t$ must only use information available at or before $t$.
  - Explicitly verify `.shift(1)` application on signal Series/DataFrames before computing trade returns.
* **Standardized Backtest Console Output**:
  - Backtest runners (`run/**/*.py`) must print structured Markdown or fixed-width text tables to the console upon completion.
  - Include essential metrics (CAGR, Annualized Volatility, Sharpe Ratio, Max Drawdown) formatted with consistent percentage and decimal precision (`%.2f%%`).
