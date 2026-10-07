# DAX Measures for CloudFinOps

Paste these into **Modeling → New Measure** in Power BI Desktop.
Each measure assumes the corresponding base table is loaded.

---

## KPI measures (use on the Executive Overview page)

```dax
Total Cost = SUM(vw_daily_cost[total_cost])
```

```dax
Total Records = SUM(vw_daily_cost[record_count])
```

```dax
Latest Month Cost = 
CALCULATE(
    SUM(vw_monthly_cost[total_cost]),
    LASTDATE(vw_monthly_cost[year_month])
)
```

```dax
Previous Month Cost = 
VAR CurrentMonth = MAX(vw_monthly_cost[year_month])
RETURN
CALCULATE(
    SUM(vw_monthly_cost[total_cost]),
    vw_monthly_cost[year_month] < CurrentMonth
)
```

```dax
MoM Change Amount = [Latest Month Cost] - [Previous Month Cost]
```

```dax
MoM Change % = 
DIVIDE([MoM Change Amount], [Previous Month Cost], BLANK())
```

```dax
Average Daily Cost = 
AVERAGEX(
    VALUES(vw_daily_cost[full_date]),
    CALCULATE(SUM(vw_daily_cost[total_cost]))
)
```

```dax
Projected Annual Cost = [Average Daily Cost] * 365
```

---

## Budget measures (populated after Phase 11)

```dax
Budget Amount = SUM(vw_budget_vs_actual[budget_amount])
```

```dax
Budget Actual = SUM(vw_budget_vs_actual[actual_amount])
```

```dax
Budget Utilization % = 
DIVIDE([Budget Actual], [Budget Amount], BLANK())
```

```dax
Budget Remaining = [Budget Amount] - [Budget Actual]
```

```dax
Budget Status = 
SWITCH(
    TRUE(),
    [Budget Utilization %] >= 0.9,  "CRITICAL",
    [Budget Utilization %] >= 0.8,  "WARNING",
    "OK"
)
```

---

## Anomaly measures (populated after Phase 6)

```dax
Anomaly Count = COUNTROWS(vw_anomalies)
```

```dax
Anomaly Cost Impact = 
SUMX(
    FILTER(vw_anomalies, vw_anomalies[deviation] > 0),
    vw_anomalies[deviation]
)
```

```dax
Critical Anomaly Count = 
CALCULATE(
    COUNTROWS(vw_anomalies),
    vw_anomalies[severity] = "CRITICAL"
)
```

---

## Forecast measures (populated after Phase 7)

```dax
Forecast Cost = SUM(vw_forecasts[predicted_cost])
```

```dax
Forecast Upper Bound = SUM(vw_forecasts[upper_bound])
```

```dax
Forecast Lower Bound = SUM(vw_forecasts[lower_bound])
```

```dax
Forecast vs Actual % = 
DIVIDE([Latest Month Cost], [Forecast Cost], BLANK()) - 1
```

---

## Optimization measures (populated after Phase 8)

```dax
Potential Monthly Savings = 
SUM(vw_optimization_savings[total_estimated_monthly_saving])
```

```dax
Open Recommendations = 
SUMX(
    FILTER(vw_optimization_savings, vw_optimization_savings[status] = "OPEN"),
    vw_optimization_savings[recommendation_count]
)
```

---

## Time-intelligence helpers

Power BI needs a proper date table for these. Recommended:

1. Create a **new table** (Modeling → New Table):

   ```dax
   Date = CALENDARAUTO()
   ```

2. Mark it as a date table: right-click the table → **Mark as date table**.
3. Create the relationship:
   `Date[Date]` → `vw_daily_cost[full_date]` (1-to-many).

Then these work:

```dax
Cost MTD = TOTALMTD([Total Cost], 'Date'[Date])
```

```dax
Cost QTD = TOTALQTD([Total Cost], 'Date'[Date])
```

```dax
Cost YTD = TOTALYTD([Total Cost], 'Date'[Date])
```

```dax
Cost Same Period Last Year = 
CALCULATE([Total Cost], SAMEPERIODLASTYEAR('Date'[Date]))
```

```dax
Cost YoY % = 
DIVIDE(
    [Total Cost] - [Cost Same Period Last Year],
    [Cost Same Period Last Year],
    BLANK()
)
```

---

## Conditional formatting measures

```dax
MoM Color = 
VAR pct = [MoM Change %]
RETURN
    SWITCH(
        TRUE(),
        ISBLANK(pct), "#808080",
        pct > 0.05,   "#d13438",
        pct > 0,      "#ff8c00",
        pct <= 0,     "#107c10"
    )
```

Apply with **Format → Conditional formatting → Font color → Field value = [MoM Color]**.