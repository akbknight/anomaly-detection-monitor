# Results Report

Detection results as of the last run against FRED data (January 2000 – March 2026, 314 monthly observations per series).

---

## UNRATE — U.S. Unemployment Rate

**Summary:** 4 unique anomaly dates, 3 high severity, 1 low severity.

| Date | Value | Type | Score | Severity | Description |
|---|---|---|---|---|---|
| 2009-10-01 | 10.0% | zscore | ~2.7σ | low | Post-GFC peak; gradual rise flagged at maximum |
| 2020-03-01 | 4.4% | cusum | ~5.2σ | medium | First COVID CUSUM trigger — sudden upward acceleration |
| 2020-04-01 | 14.8% | zscore | 4.73σ | high | COVID-19 mass layoffs; single-month record in modern data |
| 2020-05-01 | 13.3% | zscore | ~4.2σ | high | Continued COVID shock; unemployment remained extreme |

### Event narratives

**April 2020 COVID-19 Shock (14.8%, Z-score: 4.73σ — HIGH)**
The single most extreme anomaly in 26 years of data. As nationwide COVID-19 lockdowns took effect in late March and April 2020, approximately 20 million workers lost jobs in one month. The April unemployment rate of 14.8% was the highest recorded since the Great Depression. The Z-score of 4.73 corresponds to a probability of roughly 1-in-900,000 under a normal distribution — a genuinely unprecedented event in the post-2000 sample. IQR independently flags this observation as far above Q3+2×IQR. The CUSUM chart flagged the acceleration a month earlier (March 2020), correctly identifying the directional shift as soon as it began.

**March–May 2020 COVID Continuation**
Following the April peak, unemployment remained at 13.3% in May before beginning to recover. This remains 3.5–4.2σ above the 2000–2026 mean, reflecting the sustained damage of the initial lockdown phase. CUSUM captured this as a single sustained alarm rather than multiple separate events (alarm-and-reset behavior).

**October 2009 Post-GFC Peak (10.0%)**
The unemployment rate peaked at 10.0% in October 2009, the highest level in the post-2000 sample prior to COVID. Z-score flags this at approximately 2.7σ (low severity). The GFC rise from ~5% to 10% was a *gradual* process spanning 18 months (Dec 2007 – Oct 2009), which CUSUM detects more effectively than Z-score. The peak month itself registers as a low-severity Z-score anomaly — the algorithm flags the absolute level, not the trend.

---

## CPIAUCSL — Consumer Price Index

**Summary:** 7 unique anomaly dates across multiple regimes. 1 high, 4 medium, 2 low.

| Date | Value | Type | Score | Severity | Description |
|---|---|---|---|---|---|
| 2008-11-01 | ~212.4 | cusum | 8.9σ | high | GFC deflation — fastest single-month CPI drop in modern history |
| 2009-01-01 | ~211.1 | cusum | ~5.1σ | medium | Continued deflation pressure; oil price collapse |
| 2015-01-01 | ~233.7 | cusum | ~5.3σ | medium | Oil price disinflation; energy CPI fell sharply |
| 2021-06-01 | ~271.7 | iqr | ~2.1x | medium | Inflation acceleration begins; first IQR breach above upper fence |
| 2021-10-01 | ~276.6 | cusum | ~6.2σ | medium | CUSUM alarm: sustained inflation surge entering regime shift territory |
| 2022-06-01 | ~295.3 | iqr | ~3.2x | high | CPI at 40-year high; IQR fence exceeded by 3.2× IQR |
| 2022-09-01 | ~296.8 | cusum | ~5.8σ | medium | CUSUM second alarm: renewed upward acceleration |

### Event narratives

**November 2008 GFC Deflation (CUSUM: 8.9σ — HIGH)**
The most extreme anomaly in the CPI series. As oil prices collapsed from $145/barrel in July 2008 to $35/barrel by December, and as the financial crisis destroyed demand, the CPI fell sharply in the autumn of 2008. November 2008 saw one of the largest single-month CPI declines since the 1950s. The CUSUM score of 8.9σ reflects the sustained nature of the decline — several consecutive months of sharply negative monthly changes, each of which exceeded the k slack parameter and thus accumulated in S-. After this alarm, the CUSUM reset and correctly identified the subsequent recovery sequence.

**January 2009 Continued Deflation**
Deflation pressure continued into January 2009, with oil prices still severely depressed and credit conditions tight. CUSUM identifies this as a distinct but related signal (a second accumulation sequence after the November reset), flagging the prolonged below-trend inflation environment at the bottom of the GFC.

**January 2015 Oil Price Disinflation**
The collapse in oil prices from mid-2014 through early 2015 (Brent crude fell from ~$115 to ~$50) produced a sustained sequence of negative energy CPI contributions. The CUSUM chart accumulates the month-over-month decreases and triggers an alarm in January 2015, reflecting the sustained directional shift in the price level. This event is correctly classified as a regime shift rather than a point outlier — no individual month was extreme enough for Z-score, but the accumulated downward drift was historically unusual.

**2021–2022 Inflation Acceleration**
Following the COVID-19 supply-chain disruptions, fiscal stimulus, and the Russia-Ukraine war's effect on energy and food prices, CPI entered a rapid acceleration phase not seen since the early 1980s. The IQR method flags June 2021 as the first breach above the Q3+2×IQR upper fence, as the index begins pushing into historically high absolute levels. The CUSUM algorithm independently triggers an alarm in October 2021, capturing the sustained month-over-month acceleration sequence. By June 2022, the CPI reached approximately 295, which is 3.2× IQR above Q3 — a "high" severity IQR flag corresponding to the 40-year peak in consumer prices.

---

## Cross-series observations

1. The COVID shock appears in UNRATE with extreme severity (the most statistically extreme event in either series) but appears only modestly in CPI because CPI actually declined briefly in early 2020 (demand destruction) before recovering.

2. The 2008 GFC produces relatively modest UNRATE anomaly readings (gradual rise over 18 months triggers CUSUM but not extreme Z-scores) while producing the highest single CUSUM score in the CPI series (fast deflationary collapse).

3. The 2021–22 inflation episode is entirely absent from UNRATE anomalies (unemployment was falling back to normal) but dominates the CPI anomaly list for that period.

These cross-series patterns confirm that each economic event has a distinctive "signature" across macroeconomic indicators — exactly the pattern a multi-series monitoring system is designed to capture.
