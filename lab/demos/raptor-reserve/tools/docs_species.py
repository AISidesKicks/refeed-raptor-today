"""Species and ecology documents for the Raptor Reserve corpus."""

from common import Doc, SPECIES, W

THREATS = {
    "Peregrine falcon": "lead poisoning, human disturbance at the cliffs, and severe weather during the fledge window",
    "Osprey": "nest platform damage, fishing line entanglement, and low fish availability in cold springs",
    "Northern harrier": "marsh drainage, nest trampling by deer, and low vole years",
    "Short-eared owl": "grassland succession, early mowing, and low vole years",
    "Barred owl": "competition with great horned owls and loss of large cavity trees",
    "Red-tailed hawk": "disturbance at the radar tower and collisions with vehicles on the access road",
    "Merlin": "disturbance of coastal spruce nests and predation by raccoons",
    "American kestrel": "loss of nest cavities, pesticide exposure, and grassland succession",
    "Bald eagle": "human disturbance at Seal Cove and lead poisoning from scavenged carcasses",
}


def species_doc(s: dict) -> Doc:
    return Doc(
        f"rr-{s['id']:03d}",
        s["name"],
        "Species and ecology",
        "2026-03-01",
        W["ecologist"],
        f"""
{s['name']} ({s['sci']}) is a {s['status']} raptor in the reserve's monitoring program. In 2025, the reserve monitored {s['pairs']} breeding pairs, which fledged {s['fledged']} chicks. The birds nest in {s['habitat']}. Their diet is mainly {s['diet']}.

The 2025 nest checks used the standard three-visit protocol: occupancy in April, stage and clutch size in May, and chick count in June. Observers stayed at least 150 m from active nests. {s['note']}

The main threats are {THREATS[s['name']]}. The reserve manages them with seasonal trail closures, a ban on lead ammunition, and a 250 m no-fly zone around active nests.

Visitors should watch from the marked viewpoints and keep 100 m from any bird that is alarm-calling or carrying food. If a bird leaves a nest because of a visitor, the visitor should back away slowly and report the encounter to a ranger.
""",
    )


DOCS = [species_doc(s) for s in SPECIES] + [
    Doc(
        "rr-020",
        "Prey Base and Small Mammal Survey",
        "Species and ecology",
        "2025-11-20",
        W["ecologist"],
        f"""
The reserve runs a small mammal survey every August with 60 live traps placed in six grids: two in {W['heron_marsh']}, two on {W['granite_ridge']}, one in {W['blacktail_forest']}, and one at {W['south_beach']}. Each grid is trapped for three nights. Animals are marked, measured, and released.

The 2025 sample caught 214 individuals. Meadow voles were 42 percent of the catch, deer mice 27 percent, masked shrews 14 percent, meadow jumping mice 9 percent, and other species 8 percent. The vole index was the highest since 2019, which is one reason the harrier and short-eared owl pairs fledged more chicks than in 2024.

Voles are the main prey for northern harriers and short-eared owls. Deer mice matter more for barred owls and red-tailed hawks. The survey is not a complete census; it is an index that the reserve compares across years.

The 2026 survey will add two grids at the restored South Beach boardwalk to see whether the repair changed small mammal movement along the dunes.
""",
    ),
    Doc(
        "rr-021",
        "Migration Patterns",
        "Species and ecology",
        "2026-06-10",
        W["ecologist"],
        f"""
{W['island']} sits on the North Atlantic flyway, and the reserve records both spring and fall migration. The fall count in 2025 tallied {W['fall_count_2025']:,} raptors of {W['fall_species_2025']} species. The spring count in 2026 tallied {W['spring_count_2026']:,} raptors of {W['spring_species_2026']} species.

The fall peak was 22 September, when 612 birds passed {W['granite_ridge']} in six hours. Sharp-shinned hawks were the most numerous species, followed by American kestrels, merlins, ospreys, and northern harriers. The spring peak was 4 May, when 388 birds moved north in a single day after a week of southerly winds.

Weather matters more than the calendar. Cold fronts with northwest winds produce the biggest fall flights. Fog, rain, and strong southerly winds shut the count down. The 2025 fall season lost 11 count days to weather. The 2026 spring season lost 7.

The reserve uses the same six count stations every year so the numbers are comparable. Count data is stored in the migration table and summarized in the annual research report.
""",
    ),
    Doc(
        "rr-022",
        "Nest Sites and Breeding Summary",
        "Species and ecology",
        "2025-08-30",
        W["ecologist"],
        f"""
The reserve monitors 46 raptor territories across the island. In 2025, 38 territories were occupied, 67 chicks fledged, and the overall fledging success was 78 percent. The 2024 season had 44 territories, 35 occupied, 59 chicks fledged, and 74 percent success.

The largest share of nests belongs to ospreys (14), followed by red-tailed hawks (9), northern harriers (6), American kestrels (5), short-eared owls (4), barred owls (3), peregrine falcons (2), merlins (2), and bald eagles (1).

Nests are concentrated at {W['north_point']} (peregrines and red-tailed hawks), {W['seal_cove']} (ospreys and bald eagles), {W['heron_marsh']} (harriers and short-eared owls), and {W['blacktail_forest']} (barred owls). The {W['granite_ridge']} radar tower is the most productive red-tailed hawk site on the island.

The reserve does not publish exact nest coordinates. Public maps show territories at 1 km resolution. Researchers with a permit can request the precise locations from the data manager.
""",
    ),
    Doc(
        "rr-023",
        "Lead Poisoning in Raptors",
        "Species and ecology",
        "2025-01-20",
        W["vet"],
        f"""
Lead poisoning is the reserve's most preventable raptor health problem. Birds ingest lead from spent ammunition in carcasses and from fishing weights. Even small amounts can cause weakness, blindness, digestive problems, and death.

The reserve banned lead ammunition in {W['lead_ban_year']}. Visitors, staff, and researchers must use non-lead shot or slugs. The ban is written into the charter and the research permit.

In October 2024, the reserve treated an adult female peregrine named {W['lead_case_bird']}. Her blood lead level was 0.42 ppm, well above the 0.2 ppm threshold. She was {W['lead_case_outcome']}. The case cost USD 6,200 and is documented in rr-037.

The 2025 sampling program tested 12 raptors. One bird was above 0.2 ppm, or 8.3 percent of the sample. The management plan target is below 10 percent, so the reserve is inside the target but not by much.

Staff should report any bird that is lethargic, unable to stand, or has drooping wings. Do not handle the bird without gloves. Call the veterinarian and keep the bird warm and quiet.
""",
    ),
    Doc(
        "rr-024",
        "Window Collisions at the Visitor Center",
        "Species and ecology",
        "2026-01-30",
        W["head_ranger"],
        f"""
The {W['visitor_center']} has a large glass wall facing {W['seal_cove']}. Birds sometimes fly into it, especially during migration. In 2024 the reserve recorded 9 collisions; in 2025 it recorded 7. Four of the 2025 collisions were fatal.

Most collisions involved ovenbirds, white-throated sparrows, and ruby-crowned kinglets. The strikes happened on foggy mornings and on days with strong onshore winds. The window reflects the sky and the trees behind the building.

In 2025 the reserve added dot decals to the worst panes and moved a bird feeder from 3 m to 12 m from the glass. The feeder move is important: a feeder close to the window is safer than one at mid-distance, because birds cannot build up speed.

Staff check the glass every morning during migration. Any stunned bird goes into a dark cardboard box for one hour. If it recovers, it is released near the cove. If it does not, the veterinarian is called.

The reserve plans to replace the remaining untreated panes in 2027.
""",
    ),
    Doc(
        "rr-025",
        "Avian Influenza Monitoring",
        "Species and ecology",
        "2026-04-15",
        W["vet"],
        f"""
The reserve has monitored avian influenza since 2022. The program focuses on dead birds, sick birds, and birds that are found near communal roosts. Staff wear gloves and masks, double-bag carcasses, and disinfect boots and equipment.

Between 2022 and 2025 the reserve submitted 120 samples. None tested positive for highly pathogenic avian influenza. Three dead birds in 2025 were tested for other causes: one had lead poisoning, one had a wing fracture, and one was too decomposed to diagnose.

The reserve does not close trails when a single dead bird is found. It closes a trail if three or more dead birds are found in the same area within seven days, or if a positive case is confirmed within 10 km. The closure lasts until the state veterinarian clears the area.

Visitors should not touch dead or sick birds. Report the location to a ranger and keep pets away. The reserve does not allow dogs on the island, so this is mostly a rule for staff and researchers.

The 2026 plan adds two sampling sites at {W['heron_marsh']} and {W['south_beach']}.
""",
    ),
]
