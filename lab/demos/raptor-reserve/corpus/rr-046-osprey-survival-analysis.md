# Osprey Survival Analysis

Category: Research and monitoring
Date: 2026-03-10
Author: Tomas Reed
Source: Raptor Reserve internal record

The reserve has banded 120 osprey chicks since 2016. Resightings and recoveries show first-year survival of 71 percent and adult survival of 84 percent. The average recapture probability is 0.31, so the estimates have wide confidence intervals.

The 2025 cohort fledged 21 chicks, the highest since 2019. The 2024 cohort fledged 19. The difference is within the range expected from prey availability and spring weather.

Most first-year mortality happens in the first 60 days after fledging. The main known causes are fishing line entanglement, power line collisions, and starvation during cold snaps. The reserve works with the local fishing community to collect line and to mark the worst power lines.

The analysis uses a Cormack-Jolly-Seber model with time-varying survival and a constant recapture probability. The model is run in R with the marked package. The data is checked by the data manager and archived with the annual banding file.

The reserve plans to add a color-band resighting program in 2027. The goal is to raise recapture probability above 0.50 and narrow the survival estimates.

## Background

Osprey Survival Analysis is part of the reserve's long-term monitoring program. The question is whether the island's raptor population is changing, and whether the change is driven by weather, prey, disease, or human disturbance. The reserve has collected comparable data since 2016.

## Methods

The analysis uses the standard field protocols. Counts use six fixed stations and a four-hour window. Nest checks use three visits and a 150 m observation distance. Occupancy models use the 2016-2025 records and account for detection probability. The data manager checks the records before analysis.

## Results

The headline numbers are in the document. The full tables are in the annual data release. Estimates are reported with 95 percent confidence intervals. A difference is treated as meaningful only when the intervals do not overlap and the field effort was similar.

## What changed since the last report

The previous report used the same routes and the same three-visit protocol, so the comparison is direct. The 2026 analysis adds the new South Beach boardwalk data and the two acoustic stations installed in 2025. The older records are flagged where the effort or the observer changed. A difference that comes from a new route is not treated as a population change.

## Discussion

The reserve reads the results against the management plan. A single year is not a trend. A change that appears in one species but not in its prey or habitat is treated with caution. The team also checks whether a new observer, a new route, or a new sensor could explain the pattern.

## Recommendations

The document ends with actions for the next season. Each action has an owner, a date, and a check. Actions that need money go to the budget process. Actions that need a protocol change go to the research committee.

## Data availability

The summary is public. The raw data is available to researchers with a permit and a data-sharing agreement. Sensitive nest locations are stored at reduced precision. The data manager can provide the data dictionary (rr-096) and the file naming rules (rr-097).
