# Decision Log

Key design decisions made during development, with rationale.

---

## 1. Why three detectors instead of one

**Decision:** Run Z-score, IQR, and CUSUM independently on each series.

**Rationale:** Each algorithm detects a structurally different type of anomaly. Z-score detects single-point magnitude outliers (fast spikes above the historical mean). IQR is robust to heavy tails and provides distribution-free confirmation of point outliers, which is important for the CPI series, which is right-skewed. CUSUM catches sustained directional shifts (the COVID unemployment ramp, the 2008 deflation sequence, the 2021–22 inflation acceleration) — events that accumulate across 3–6 months and whose individual monthly values may not be extreme in isolation.

A single method would leave systematic blind spots. The combination of all three, with deduplication by severity, covers the full anomaly taxonomy without significantly increasing false-alarm rate.

---

## 2. Why CUSUM operates on differences, not levels

**Decision:** Apply CUSUM to month-over-month first differences (d_t = x_t - x_{t-1}) rather than to the raw series values.

**Rationale:** The unemployment rate and CPI both have natural long-run means that shift across economic regimes — the "normal" unemployment rate in 2020 is structurally different from the "normal" in 2000. A CUSUM chart on raw levels would continuously accumulate across these regime shifts and trigger alarms that reflect secular trends rather than structural breaks. By operating on differences, the input to CUSUM is approximately stationary with a near-zero mean, isolating months where the *rate of change* itself becomes abnormally persistent. This is the correct target for detecting events like the 2020 COVID shock (which produced 5+ consecutive months of extreme monthly changes).

---

## 3. Why k = 0.5 * sigma (CUSUM slack parameter)

**Decision:** Set the reference value (slack) k = 0.5 * sigma_d, where sigma_d is the standard deviation of first differences.

**Rationale:** k = 0.5 * sigma is the standard "reference value" recommended in statistical process control literature (Montgomery, 2012, "Introduction to Statistical Quality Control", 7th ed., p. 420). It is derived from the optimal CUSUM design for detecting a 1-sigma shift in process mean. It balances detection speed (low k catches small shifts faster) against false alarm rate (low k also accumulates noise faster). Setting k = 0.5 * sigma specifically optimizes ARL (Average Run Length) for the case of a one-standard-deviation step change, which is the relevant scale for monthly macroeconomic disruptions.

---

## 4. Why threshold h = 4 * sigma (CUSUM alarm threshold)

**Decision:** Set the alarm threshold h = 4.0 * sigma_d.

**Rationale:** h = 4 * sigma is calibrated from ARL (Average Run Length) analysis to produce approximately 1 false alarm per 200 observations under the null hypothesis of no process shift (Montgomery 2012, Table 9.2). For a 314-month series, this implies fewer than 2 expected false alarms from noise alone — an acceptable rate for a monitoring dashboard. A lower threshold (e.g., h = 3 sigma) would produce more frequent but weaker signals; a higher threshold (h = 5 sigma) would reduce false alarms but delay detection of real events by 1–2 months.

---

## 5. Why start at January 2000

**Decision:** Slice all series to start on 2000-01-01, discarding pre-2000 history.

**Rationale:** FRED provides UNRATE from 1948 and CPIAUCSL from 1947. However, extending the window to pre-2000 data introduces several complications without adding portfolio-relevant crisis events:
- The BLS revised the CPI methodology in 1998 (geometric mean formula), creating a measurement discontinuity.
- Pre-2000 data includes the oil shocks of the 1970s and early 1980s disinflation, which would inflate the global sigma estimates and make the 2.5σ threshold less sensitive to post-2000 events.
- The Y2K period involved data-collection disruptions that affect seasonal adjustment quality.
- All major events relevant to a U.S.-equity-oriented risk monitor fall within the 2000–present window: the dot-com recession, 9/11, 2008 GFC, 2020 COVID shock, 2021–22 inflation surge.

---

## 6. Why Z-score threshold = 2.5 (not 2.0 or 3.0)

**Decision:** Flag observations with |z| > 2.5.

**Rationale:** The standard 2.0 threshold flags approximately 4.6% of observations under normality — far too many for a monitoring context where each flag requires human review. The 3.0 threshold flags only 0.27%, which is overly conservative for macroeconomic series that routinely experience meaningful but not extreme deviations. The 2.5 threshold (approximately 1.2% of observations flagged) represents a reasonable operating point for a dashboard where the goal is to surface events that are genuinely unusual rather than trivially common.

---

## 7. Why IQR multiplier = 2.0 (not 1.5)

**Decision:** Use fence width multiplier = 2.0 instead of the classical Tukey (1977) value of 1.5.

**Rationale:** Tukey's 1.5 fence is designed for exploratory data analysis on clean, roughly normal data. For macroeconomic series spanning 26 years and multiple economic regimes, the IQR itself is large enough that 1.5 * IQR fences capture only extremely severe outliers while also flagging a handful of moderate deviations as false positives during volatile periods. A multiplier of 2.0 produces cleaner results: it consistently flags the same high-severity events identified by Z-score (providing useful confirmation) without introducing additional noise.
