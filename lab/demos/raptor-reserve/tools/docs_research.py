"""Research and monitoring documents for the Raptor Reserve corpus."""

from common import Doc, W

DOCS = [
    Doc(
        "rr-041",
        "Fall Migration Report 2025",
        "Research and monitoring",
        "2025-12-12",
        W["ecologist"],
        f"""
The 2025 fall migration count tallied {W['fall_count_2025']:,} raptors of {W['fall_species_2025']} species. That is 6.8 percent more than the 4,506 birds counted in 2024. The season ran for 92 count days; 11 days were lost to fog, rain, or wind above 20 km/h.

The peak day was 22 September, when 612 birds passed {W['granite_ridge']} in six hours. Sharp-shinned hawks were the most numerous species with 1,842 birds, or 38.3 percent of the total. American kestrels followed with 714, merlins with 388, ospreys with 301, and northern harriers with 276. The remaining species made up 1,291 birds.

Juveniles were 61 percent of the flight, which is close to the 10-year average of 59 percent. The age ratio suggests a good breeding season across the region, not just on the island.

The count was helped by four strong northwest wind events in late September. The count was hurt by a week of southerly winds in early October, when very few birds moved. Observers logged 18 hours of "no flight" time, which is excluded from the effort-adjusted index.

The full table is in the annual data release. The 2025 report is the basis for the fall trend line in the 2026 management review.
""",
    ),
    Doc(
        "rr-042",
        "Spring Migration Report 2026",
        "Research and monitoring",
        "2026-06-15",
        W["ecologist"],
        f"""
The 2026 spring migration count tallied {W['spring_count_2026']:,} raptors of {W['spring_species_2026']} species. That is 4.1 percent fewer than the 4,116 birds counted in 2025. The season ran for 74 count days; 7 days were lost to weather.

The peak day was 4 May, when 388 birds moved north after a week of southerly winds. Sharp-shinned hawks led the count with 1,506 birds. American kestrels followed with 622, northern harriers with 244, ospreys with 198, and merlins with 141. The remaining species made up 1,236 birds.

A late cold snap from 10 to 14 April slowed the early movement. The first osprey was seen on 28 March, which is 4 days later than the 10-year average. The first broad-winged hawk was seen on 19 April, which is 2 days earlier than average.

The reserve recorded 13 species, one fewer than in 2025. The missing species was the rough-legged hawk, which usually appears in small numbers in March. Observers also reported an unusually high number of unidentified accipiters, likely because the cold snap kept birds low and fast.

The spring count is shorter than the fall count and more sensitive to weather. The report recommends adding one make-up week in late May to reduce the gap.
""",
    ),
    Doc(
        "rr-043",
        "Breeding Season Report 2025",
        "Research and monitoring",
        "2025-09-15",
        W["ecologist"],
        f"""
The 2025 breeding season monitored 46 raptor territories. Of those, 38 were occupied, 30 were successful, and 67 chicks fledged. Overall fledging success was 78 percent, up from 74 percent in 2024.

The species totals were: osprey 14 pairs and 21 fledged; red-tailed hawk 9 pairs and 12 fledged; northern harrier 6 pairs and 8 fledged; American kestrel 5 pairs and 9 fledged; short-eared owl 4 pairs and 5 fledged; barred owl 3 pairs and 4 fledged; peregrine falcon 2 pairs and 3 fledged; merlin 2 pairs and 3 fledged; bald eagle 1 pair and 2 fledged.

Eight territories were unoccupied. Five were small forest nests that have been vacant for at least two years. Three were coastal sites disturbed by storm repair. The reserve will not count those three as lost until the 2026 season.

The main negative factors were a late May storm that destroyed two osprey nests, one lead exposure case in a red-tailed hawk, and repeated visitor disturbance at the North Point overlook. The lead case was treated and released. The overlook now has a seasonal closure sign and a rope barrier.

The 2026 target is 40 occupied territories and 70 fledged chicks. The research committee will review the target in March.
""",
    ),
    Doc(
        "rr-044",
        "Breeding Season Report 2024",
        "Research and monitoring",
        "2024-09-20",
        W["ecologist"],
        f"""
The 2024 breeding season monitored 44 raptor territories. Of those, 35 were occupied, 26 were successful, and 57 chicks fledged. Overall fledging success was 74 percent.

The season was difficult. A late May storm destroyed two osprey nests and one red-tailed hawk nest. A red-tailed hawk chick was found with a wing fracture and was treated by the veterinarian. The adult female peregrine, Juniper, was found with lead poisoning on 9 October 2024 and was released after 18 days of treatment.

The species totals were: osprey 14 pairs and 19 fledged; red-tailed hawk 9 pairs and 11 fledged; northern harrier 6 pairs and 7 fledged; American kestrel 4 pairs and 7 fledged; short-eared owl 4 pairs and 4 fledged; barred owl 3 pairs and 3 fledged; peregrine falcon 2 pairs and 2 fledged; merlin 1 pair and 2 fledged; bald eagle 1 pair and 2 fledged.

The 2025 season improved because the vole population increased and the spring weather was calmer. The reserve cautions that two years are not a trend. The 10-year occupancy analysis (rr-045) is the better guide.

The full nest table and the disturbance log are in the annual data release.
""",
    ),
    Doc(
        "rr-045",
        "Occupancy Analysis 2016-2025",
        "Research and monitoring",
        "2026-02-20",
        W["ecologist"],
        f"""
The reserve analyzed 10 years of nest records for 38 long-term territories. Occupancy increased from 62 percent in 2016 to 74 percent in 2025, a gain of 12 percentage points. The trend is positive but not uniform across species.

The best-supported model included nest platform availability, lead exposure, and spring wind. Detection probability was 0.82, which means a single visit can miss an occupied territory about 18 percent of the time. The three-visit protocol reduces that error.

Colonization probability was 0.09 per territory per year. Extinction probability was 0.04. The osprey group drove most of the colonization, because new platforms were added in 2018 and 2021. The forest raptors were more stable.

The model has limits. The territories are not a random sample; they are the sites the reserve can safely monitor. The 2016 records are less detailed than the 2025 records. The analysis controls for effort but cannot fully remove observer effects.

The recommendation is to keep the three-visit protocol and add two new forest territories in 2027. The full model code and data are available to permitted researchers.
""",
    ),
    Doc(
        "rr-046",
        "Osprey Survival Analysis",
        "Research and monitoring",
        "2026-03-10",
        W["ecologist"],
        f"""
The reserve has banded 120 osprey chicks since 2016. Resightings and recoveries show first-year survival of 71 percent and adult survival of 84 percent. The average recapture probability is 0.31, so the estimates have wide confidence intervals.

The 2025 cohort fledged 21 chicks, the highest since 2019. The 2024 cohort fledged 19. The difference is within the range expected from prey availability and spring weather.

Most first-year mortality happens in the first 60 days after fledging. The main known causes are fishing line entanglement, power line collisions, and starvation during cold snaps. The reserve works with the local fishing community to collect line and to mark the worst power lines.

The analysis uses a Cormack-Jolly-Seber model with time-varying survival and a constant recapture probability. The model is run in R with the marked package. The data is checked by the data manager and archived with the annual banding file.

The reserve plans to add a color-band resighting program in 2027. The goal is to raise recapture probability above 0.50 and narrow the survival estimates.
""",
    ),
    Doc(
        "rr-047",
        "Diet Study from Pellets and Prey Remains",
        "Research and monitoring",
        "2025-11-30",
        W["ecologist"],
        f"""
The diet study analyzed 214 pellets and prey remains collected in 2025. Meadow voles were 61 percent of the items, deer mice 18 percent, birds 12 percent, and insects 9 percent. The sample includes pellets from harriers, short-eared owls, barred owls, and red-tailed hawks.

The species differ. Harriers and short-eared owls ate mostly voles. Barred owls ate more deer mice and frogs. Red-tailed hawks took larger prey, including rabbits and squirrels. Ospreys were not included because their diet is fish and is recorded separately at the nest.

The 2025 result matches the small mammal survey, which found a high vole index. The reserve uses both datasets to check whether a change in raptor numbers is linked to prey.

The method has limits. Pellets underestimate soft-bodied prey and overestimate prey with hard parts. The sample is not random; collectors pick up pellets that are easy to find. The report uses percentages, not absolute biomass.

The 2026 plan is to add stable isotope analysis on a subset of feathers to separate marine and terrestrial prey.
""",
    ),
    Doc(
        "rr-048",
        "Genetic Sampling Plan",
        "Research and monitoring",
        "2026-04-05",
        W["vet"],
        f"""
The reserve began collecting feather samples for genetic analysis in 2023. The goal is to estimate relatedness, diversity, and population structure for the island's peregrine, merlin, and kestrel populations.

Sixty samples have been collected so far. The analysis found three genetic clusters, which match the three species. Within the peregrine cluster, heterozygosity was 0.68 and the inbreeding coefficient was close to zero. The sample is too small to detect a recent bottleneck.

Samples are collected from feathers found at nest sites, not from live birds, unless the bird is already being handled for banding. Each sample gets a number, a location, a date, and a storage note. DNA is extracted at the mainland lab and the sequence data is stored on the reserve server.

The permit requires a federal bird banding permit and a state scientific collection permit. The reserve does not allow commercial use of the genetic data. Results are shared with the state wildlife agency.

The 2026 plan adds 20 samples from the South Beach kestrel population.
""",
    ),
    Doc(
        "rr-049",
        "Stable Isotope Study",
        "Research and monitoring",
        "2026-05-12",
        W["ecologist"],
        f"""
The stable isotope study uses 40 feather samples from 2025 to separate marine and terrestrial prey in the diet of island raptors. The ratio of carbon and nitrogen isotopes in feathers reflects the food web where the feather grew.

The samples fell into two groups. Ospreys and bald eagles had marine signatures, as expected from a fish diet. Harriers, kestrels, and red-tailed hawks had terrestrial signatures. Peregrines and merlins were intermediate, which fits a diet of shorebirds and songbirds that move between habitats.

The method cannot identify prey species. It can only separate broad habitat groups. The reserve uses it as a check on the pellet study, not as a replacement. The sample is also biased toward birds that molted on the island.

The study cost USD 4,800 and was funded by the friends group. The full isotope table is in the annual data release. The 2026 plan is to add 20 samples from the mainland migration station to compare local and migrant birds.
""",
    ),
    Doc(
        "rr-050",
        "Acoustic Classifier Evaluation",
        "Research and monitoring",
        "2026-01-15",
        W["ecologist"],
        f"""
The reserve evaluated its bird call classifier on 8,200 hours of audio from the 12-station array. The classifier flagged 1,840 raptor calls. A human reviewer checked a 10 percent sample.

Precision was 92 percent: most flagged calls were raptors. Recall was 78 percent: the classifier missed about one in five raptor calls. The main confusion was between merlin and American kestrel calls, which overlap in frequency and duration.

The classifier works best for osprey, red-tailed hawk, and bald eagle. It works less well for silent species and for calls mixed with wind, surf, or insects. The array is not a substitute for the migration count; it is a way to detect activity at night and in dense vegetation.

The 2026 plan is to retrain the classifier with 2,000 new labeled calls and to add a second reviewer for the low-confidence files. The reserve will keep the raw audio so a better model can be applied later.
""",
    ),
    Doc(
        "rr-051",
        "Thermal Drone Survey",
        "Research and monitoring",
        "2025-10-10",
        W["ecologist"],
        f"""
The reserve tested a thermal drone for nest surveys in 2025. The team flew 14 missions and detected 22 nests. Ground surveys found 25 nests in the same areas, so the drone missed 3.

The drone worked best in open marsh and grassland, where heat signatures were easy to separate from rocks and vegetation. It worked less well in the forest, where the canopy hid the nests. The flights were limited to early morning, before the sun warmed the ground.

The project cost USD 18,700, including the drone, the thermal camera, training, and repairs. The team saved about 40 field hours compared with walking the same routes. The savings do not yet cover the cost.

The reserve will use the drone as a supplement, not a replacement. Every drone detection is checked on the ground. The 2026 plan is to fly the South Beach and Heron Marsh routes twice a month during the breeding season.

The full flight log and the detection table are in the annual data release.
""",
    ),
    Doc(
        "rr-052",
        "Camera Trap Capture Rates",
        "Research and monitoring",
        "2026-01-25",
        W["ecologist"],
        f"""
The 20-camera network logged 4,100 trap nights in 2025 and 1,240 raptor detections. That is 0.30 detections per 100 trap nights. The rate is similar to 2024 (0.28) and higher than 2023 (0.22).

Red-tailed hawks had the highest rate at 0.11 detections per 100 trap nights. Barred owls were 0.07, northern harriers 0.05, and American kestrels 0.03. The remaining detections were other raptors or unidentified birds.

The network also recorded fox, deer, mink, river otter, and one domestic cat. The cat was reported to the mainland animal control office. The reserve does not allow pets, but a cat can swim or arrive on a boat.

Capture rates are not abundance. A curious bird can trigger a camera many times, and a shy bird can avoid it. The reserve uses the rates as an index and combines them with the nest survey.

The 2026 plan is to add five cameras at the South Beach dune restoration site and to test a new trigger setting that reduces false positives from grass movement.
""",
    ),
    Doc(
        "rr-053",
        "Phenology Shift Analysis",
        "Research and monitoring",
        "2026-07-01",
        W["ecologist"],
        f"""
The reserve analyzed 10 years of first-arrival and last-departure dates for 14 migratory raptor species. Spring arrival is now 5 days earlier than in 2016. Fall departure is 3 days later. The changes are small but consistent.

Ospreys and northern harriers show the strongest spring shift. Merlins and sharp-shinned hawks show the weakest. The pattern matches warmer spring water and earlier snowmelt on the mainland, but the island data alone cannot prove the cause.

The analysis uses the first confirmed sighting of each species at a count station. Observations are filtered for unusual early records, which are checked against photos or a second observer. The trend is estimated with a simple linear model and a 95 percent confidence interval.

A 5-day shift can matter. If prey peaks before chicks hatch, the nest can fail. The reserve will compare the phenology data with the prey survey and the breeding dates in 2027.

The full species table is in the annual data release.
""",
    ),
    Doc(
        "rr-054",
        "Population Viability Model",
        "Research and monitoring",
        "2026-08-15",
        W["ecologist"],
        f"""
The reserve built a 100-year population viability model for the island's raptor community. The model uses current survival, fecundity, and carrying capacity. It projects a 2 percent annual growth rate and an 8 percent probability of dropping below 20 breeding pairs within 100 years.

The most sensitive parameters are adult survival, fledging success, and lead exposure. A 5 percent drop in adult survival has a larger effect than a 5 percent drop in fecundity. A 10 percent increase in lead exposure moves the extinction risk to 14 percent.

The model is simple. It does not include density dependence, disease, or a catastrophic storm. It treats the island as closed, which is not true for juveniles. The results are a planning tool, not a prediction.

The reserve will update the model every five years with new survival and occupancy estimates. The code and the parameter table are in the data release. The 2027 research plan includes a sensitivity analysis for wind energy and climate change.
""",
    ),
    Doc(
        "rr-055",
        "Research Priorities 2027",
        "Research and monitoring",
        "2026-09-01",
        W["director"],
        f"""
The 2027 research plan has five priorities and a budget of USD 180,000.

1. Lead exposure. Expand sampling to 20 birds and test a non-lead ammunition exchange program with local hunters. Budget: USD 35,000.
2. Climate and phenology. Add two weather stations and compare prey timing with chick hatching. Budget: USD 42,000.
3. AI-assisted monitoring. Evaluate the acoustic classifier and the RAPTOR summary tree on the reserve's own records. Budget: USD 28,000.
4. Wind energy risk. Map migration corridors and flight heights near the proposed offshore turbine area. Budget: USD 45,000.
5. Genetics. Add 20 samples and test for a recent bottleneck in the kestrel population. Budget: USD 30,000.

The plan assumes the Maine Coast Trust grant is renewed at the current level. If it is not, the wind energy study is deferred and the lead program is reduced to 12 samples.

Each project has a named lead, a data-sharing plan, and a public summary. The research committee reviews progress in June and December.
""",
    ),
]
