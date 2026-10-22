"""Shared seed data for the Raptor Reserve corpus.

The island, the staff, the counts, and the incidents are fictional. The bird
species are real, and the methods wing cites public research. The builder uses
these values so the documents and the eval questions cannot drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Doc:
    """One corpus document."""

    id: str
    title: str
    category: str
    date: str
    author: str
    body: str
    source: str = "Raptor Reserve internal record"


W = {
    "reserve": "Raptor Reserve",
    "island": "Blacktail Island",
    "island_area_ha": 4820,
    "island_length_km": 12,
    "island_width_km": 6,
    "coords": "44.31 N, 68.02 W",
    "founded": 1987,
    "director": "Dr. Mara Voss",
    "head_ranger": "Elin Ward",
    "ecologist": "Tomas Reed",
    "vet": "Dr. Priya Nair",
    "maintenance": "Caleb Finch",
    "education": "June Okafor",
    "data_manager": "Samir Haddad",
    "board_chair": "Helen Harrow",
    "trust": "Maine Coast Trust",
    "budget_2026": 1_840_000,
    "staff_full": 9,
    "staff_seasonal": 22,
    "volunteers": 60,
    "highest_point_m": 112,
    "lighthouse_built": 1892,
    "lighthouse_decommissioned": 1968,
    "lighthouse_restored": 2019,
    "visitor_center_opened": 2008,
    "first_peregrine": 1994,
    "iba_year": 2024,
    "fall_count_2025": 4812,
    "fall_species_2025": 14,
    "spring_count_2026": 3947,
    "spring_species_2026": 13,
    "peregrine_pairs": 2,
    "peregrine_fledged_2025": 3,
    "osprey_nests": 14,
    "osprey_fledged_2025": 21,
    "harrier_pairs": 6,
    "seowl_pairs": 4,
    "barred_pairs": 3,
    "redtail_pairs": 9,
    "merlin_pairs": 2,
    "kestrel_pairs": 5,
    "bald_eagle_pairs": 1,
    "camera_traps": 20,
    "drone_wind_limit_kmh": 28,
    "drone_battery_min": 24,
    "drone_max_distance_km": 3.5,
    "lead_ban_year": 2019,
    "storm_name": "Oscar",
    "storm_date": "2026-01-18",
    "storm_repair_cost": 18400,
    "drone_crash_date": "2025-08-03",
    "drone_crash_cause": "battery failure",
    "lead_case_date": "2024-10-09",
    "lead_case_bird": "Juniper",
    "lead_case_outcome": "treated for 18 days and released",
    "eval_questions": 50,
    "corpus_docs": 100,
    "corpus_license": "CC BY 4.0",
    "north_point": "North Point",
    "heron_marsh": "Heron Marsh",
    "granite_ridge": "Granite Ridge",
    "seal_cove": "Seal Cove",
    "blacktail_forest": "Blacktail Forest",
    "south_beach": "South Beach",
    "visitor_center": "Seal Cove Visitor Center",
    "research_station": "North Point Research Station",
    "weather_station": "Granite Ridge Weather Station",
    "old_boathouse": "Old Boathouse",
    "schoolhouse": "Island Schoolhouse",
    "narrows": "The Narrows",
}


SPECIES = [
    {
        "id": 11,
        "name": "Peregrine falcon",
        "sci": "Falco peregrinus",
        "pairs": 2,
        "fledged": 3,
        "habitat": "the cliffs at North Point",
        "diet": "pigeons, shorebirds, and other medium-sized birds",
        "status": "state threatened",
        "note": "The North Point pair has nested on the same ledge since 2018.",
    },
    {
        "id": 12,
        "name": "Osprey",
        "sci": "Pandion haliaetus",
        "pairs": 14,
        "fledged": 21,
        "habitat": "platform nests and dead snags around Seal Cove and Heron Marsh",
        "diet": "fish, mostly menhaden and mackerel",
        "status": "state special concern",
        "note": "The oldest known nest platform was built in 1998.",
    },
    {
        "id": 13,
        "name": "Northern harrier",
        "sci": "Circus hudsonius",
        "pairs": 6,
        "fledged": 8,
        "habitat": "Heron Marsh and the South Beach grassland",
        "diet": "meadow voles and small birds",
        "status": "state special concern",
        "note": "Harriers are the reserve's main vole predator.",
    },
    {
        "id": 14,
        "name": "Short-eared owl",
        "sci": "Asio flammeus",
        "pairs": 4,
        "fledged": 5,
        "habitat": "the open meadows east of Granite Ridge",
        "diet": "meadow voles",
        "status": "state endangered",
        "note": "Winter numbers peak in years with high vole abundance.",
    },
    {
        "id": 15,
        "name": "Barred owl",
        "sci": "Strix varia",
        "pairs": 3,
        "fledged": 4,
        "habitat": "Blacktail Forest",
        "diet": "small mammals, frogs, and large insects",
        "status": "least concern",
        "note": "The first barred owl was recorded on the island in 1996.",
    },
    {
        "id": 16,
        "name": "Red-tailed hawk",
        "sci": "Buteo jamaicensis",
        "pairs": 9,
        "fledged": 12,
        "habitat": "Granite Ridge and the forest edges",
        "diet": "mammals and medium-sized birds",
        "status": "least concern",
        "note": "The Granite Ridge pair nests on the old radar tower.",
    },
    {
        "id": 17,
        "name": "Merlin",
        "sci": "Falco columbarius",
        "pairs": 2,
        "fledged": 3,
        "habitat": "the coastal spruce stands",
        "diet": "songbirds",
        "status": "state special concern",
        "note": "Merlins arrived as breeders in 2012.",
    },
    {
        "id": 18,
        "name": "American kestrel",
        "sci": "Falco sparverius",
        "pairs": 5,
        "fledged": 9,
        "habitat": "the South Beach grassland",
        "diet": "insects and voles",
        "status": "state special concern",
        "note": "Kestrel numbers have declined 22 percent since 2015.",
    },
    {
        "id": 19,
        "name": "Bald eagle",
        "sci": "Haliaeetus leucocephalus",
        "pairs": 1,
        "fledged": 2,
        "habitat": "Seal Cove",
        "diet": "fish and carrion",
        "status": "least concern",
        "note": "The pair first nested on the island in 2011.",
    },
]


def slugify(text: str) -> str:
    """Make a short, stable file slug."""

    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)
