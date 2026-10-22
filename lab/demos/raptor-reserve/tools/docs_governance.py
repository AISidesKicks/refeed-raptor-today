"""Governance documents for the Raptor Reserve corpus."""

from common import Doc, W

DOCS = [
    Doc(
        "rr-001",
        "Reserve Charter",
        "Governance",
        "2024-01-15",
        "Board of Trustees",
        f"""
{W['reserve']} is a nonprofit conservation area covering {W['island_area_ha']:,} hectares on {W['island']}, about 18 km east of Sable Point, Maine. The reserve was founded in {W['founded']} when the Harrow family transferred the island to the Raptor Reserve Trust. Its mission is to protect breeding and migratory raptors, maintain the island's coastal habitats, and support research and education that can be repeated by others.

The trust is governed by a nine-member board. The board appoints the director, approves the annual budget, and reviews the management plan every five years. Day-to-day operations are led by the director and the head ranger. The reserve has {W['staff_full']} full-time staff, {W['staff_seasonal']} seasonal staff, and about {W['volunteers']} active volunteers.

The reserve does not allow hunting, trapping, off-road vehicles, or lead ammunition. Visitors may use the marked trails from 7:00 to 19:00 between May and October, and from 8:00 to 16:00 between November and April. Research permits are required for any work that disturbs vegetation, wildlife, or the island's archaeological sites.

The charter can be amended by a two-thirds vote of the board, after a public comment period of at least 30 days. The current charter was last amended on 15 January 2024.
""",
    ),
    Doc(
        "rr-002",
        "Management Plan 2026-2035",
        "Governance",
        "2026-01-05",
        W["director"],
        f"""
The 2026-2035 management plan sets five priorities for {W['reserve']}.

1. Protect at least 90 percent of occupied raptor territories. The baseline is the 2025 breeding season, when 38 of 46 monitored territories were occupied.
2. Keep lead exposure below 10 percent of sampled raptors. The 2024 case involving the peregrine Juniper showed that the ban on lead ammunition is not enough on its own.
3. Maintain 9 km of trails and 4 km of access road without expanding the footprint.
4. Complete the North Point climate monitoring program and publish a 10-year report by 2030.
5. Grow the endowment to USD 6 million by 2035 so the reserve depends less on annual grants.

The plan uses a 10-year horizon but is reviewed every five years. The board will measure progress with the same indicators used in the annual research report: occupancy, fledging success, lead exposure, visitor numbers, and maintenance backlog.

The plan also commits the reserve to an open data policy. Every research dataset must have a named owner, a retention period, and a public summary. Sensitive nest locations are the only exception; they are stored at reduced precision.
""",
    ),
    Doc(
        "rr-003",
        "Operating Budget 2026",
        "Governance",
        "2026-01-12",
        W["director"],
        f"""
The 2026 operating budget is USD {W['budget_2026']:,}, a 6.4 percent increase over 2025. The increase covers two seasonal research assistants, a new acoustic sensor array, and repairs to the South Beach boardwalk after storm Oscar.

Spending is split across five programs: conservation 41 percent, research 22 percent, education 14 percent, facilities 17 percent, and administration 6 percent. Staff costs are 54 percent of the total. The contingency line is 4 percent of the operating budget.

Revenue comes from grants (38 percent), individual donations (27 percent), the endowment (19 percent), program fees (9 percent), and other sources (7 percent). The largest single grant is USD 240,000 from the Maine Coast Trust for coastal habitat work.

The board approved a projected surplus of USD 12,000. The finance committee will review the budget in July and October. Any line that moves by more than 10 percent needs board approval.

The capital budget is separate. It covers the lighthouse roof, the solar battery replacement, and the new boat engine. The capital budget for 2026 is USD 310,000.
""",
    ),
    Doc(
        "rr-004",
        "Staff Handbook",
        "Governance",
        "2026-02-01",
        W["head_ranger"],
        f"""
The staff handbook explains how work happens on {W['island']}. Full-time staff work a 40-hour week. Seasonal staff work 12 to 20 weeks, usually from April to September. Volunteers are covered by the volunteer handbook and work with a named supervisor.

The day starts with a 7:30 stand-up at the research station. Each team reports weather, wildlife, safety, and the day's plan. The radio channel for operations is channel 2. Channel 3 is reserved for emergencies. Staff who work alone must check in at 10:00 and 14:00.

Housing is available in eight cabins near Seal Cove. The cabins have shared kitchens and a strict quiet policy after 22:00. Pets are not allowed on the island. Staff may bring a boat only with the maintenance lead's approval.

Uniforms are required for visitor-facing work. Staff should report damaged equipment, wildlife injuries, and unsafe conditions the same day. The reserve follows a no-blame reporting policy for near misses, but repeated safety violations can lead to dismissal.

The handbook is reviewed every two years. The current version took effect on 1 February 2026.
""",
    ),
    Doc(
        "rr-005",
        "Safety Plan",
        "Governance",
        "2026-02-15",
        W["head_ranger"],
        f"""
The safety plan uses three risk levels. Green means normal work. Amber means limited work, with a buddy and a radio check every hour. Red means no field work except emergency response.

Weather limits are specific. Drone flights stop at {W['drone_wind_limit_kmh']} km/h wind, visibility below 2 km, or any lightning within 10 km. Staff stay at least 150 m from the cliff edge at North Point unless they are clipped in. Life jackets are required on all boats, including the 3.5 km crossing at The Narrows.

Field teams carry a first aid kit, a satellite messenger, and a VHF radio. The reserve has two automated external defibrillators, one at the visitor center and one at the research station. All staff are trained in CPR and wilderness first aid every two years.

Any injury, near miss, or equipment failure is reported within 24 hours. The safety committee reviews reports on the first Monday of each month. The committee can close a trail, a building, or a program until the risk is fixed.

The safety plan is tested in two drills each year: one lost-visitor drill in May and one fire drill in October.
""",
    ),
    Doc(
        "rr-006",
        "Emergency Response Plan",
        "Governance",
        "2026-02-15",
        W["head_ranger"],
        f"""
The emergency response plan covers medical emergencies, fire, lost visitors, severe weather, oil spills, and disease outbreaks in wildlife.

For a medical emergency, call 911, then switch to radio channel 3 and notify the duty officer. The Coast Guard responds on channel 16. The assembly point is the {W['visitor_center']}. The goal is to move visitors to the assembly point within 30 minutes and to evacuate the island within 2 hours if the ferry is available.

The island has three sirens: one at the visitor center, one at the research station, and one at Seal Cove. A continuous siren means evacuate to the assembly point. A pulsing siren means shelter in place.

For a lost visitor, the duty officer assigns a search team of at least four people. The team checks the trail log, the camera traps, and the last known location. The coast guard is notified after 60 minutes if the visitor is not found.

For an oil spill, staff stop the source, place absorbent pads, and call the state spill line. For a wildlife disease outbreak, staff wear gloves, double-bag carcasses, and call the veterinarian.
""",
    ),
    Doc(
        "rr-007",
        "Partnership with the Maine Coast Trust",
        "Governance",
        "2024-06-01",
        W["director"],
        f"""
{W['reserve']} and the {W['trust']} signed a 20-year partnership agreement in 2024. The agreement runs from 2024 to 2044 and focuses on coastal habitat, water quality, and shared monitoring.

The trust provides USD 250,000 over the first five years. It also funds two shared staff positions: a coastal ecologist and a community engagement coordinator. The reserve provides field sites, housing, and access to its long-term datasets.

Both organizations use the same monitoring protocols for water temperature, salinity, and shoreline change. Data is shared through the reserve's open data portal. Either partner can publish a summary, but the other partner gets 30 days to review it.

The agreement can be renewed for another 10 years by mutual consent. Either partner can exit with 12 months' notice. The first annual review took place in June 2025 and found that the shared monitoring had already produced one peer-reviewed paper.

The partnership does not transfer land ownership. The reserve remains the sole owner of the island.
""",
    ),
    Doc(
        "rr-008",
        "Research Permit Policy",
        "Governance",
        "2025-03-01",
        W["ecologist"],
        f"""
Any research on {W['island']} needs a permit. The application asks for the research question, methods, locations, dates, equipment, and the names of everyone who will be on the island. Applications are due at least 45 days before the field season.

Permit fees are waived for students, USD 150 for nonprofit researchers, and USD 400 for commercial researchers. The reserve limits the island to six active projects at a time so the birds are not disturbed.

Researchers must share raw data with the reserve within 90 days of the field season. They must submit an annual report and a plain-language summary. The reserve gets two copies of any publication, and the researcher must acknowledge the reserve in the paper.

Work within 250 m of an active nest needs a separate review by the veterinarian and the head ranger. Work that involves capturing, banding, or sampling birds needs federal and state permits in addition to the reserve permit.

Permits can be suspended for repeated disturbance, missing data, or unsafe behavior. The suspension is reviewed by the research committee.
""",
    ),
    Doc(
        "rr-009",
        "Data Management Policy",
        "Governance",
        "2025-09-01",
        W["data_manager"],
        f"""
The reserve owns the data collected on the island. Staff and researchers get a license to use the data for the purpose described in their permit.

All datasets need a named owner, a description, a date range, a license, and a retention period. The default retention period is 10 years. Nest locations are stored at reduced precision in public datasets. Visitor names, phone numbers, and payment details are never stored in the research database.

Backups follow the 3-2-1 rule: three copies, two media, one off-island. The primary store is a PostgreSQL database at the research station. The secondary is a nightly encrypted backup to the mainland office. The third is a monthly cold copy in a fireproof safe.

Sensitive data has a two-year embargo. After two years, the owner must either publish a summary or ask the board for an extension. The board can grant one extension of up to two years.

The data dictionary in document rr-096 lists the fields used by the corpus and the retrieval system.
""",
    ),
    Doc(
        "rr-010",
        "Land Acknowledgment",
        "Governance",
        "2026-06-01",
        W["board_chair"],
        f"""
{W['reserve']} sits on the traditional territory of the Wabanaki peoples, including the Passamaquoddy, Penobscot, Maliseet, and Mi'kmaq. These nations have lived on and cared for this coast for thousands of years. They fished the waters, gathered along the shore, and moved with the seasons long before the island had a lighthouse or a reserve.

The reserve does not own this history, and an acknowledgment alone does not repair it. The board commits to three actions: invite Wabanaki representatives to the annual planning meeting, support tribal youth internships in conservation, and review the reserve's archaeological policy with tribal historic preservation officers.

The island was transferred to the trust in {W['founded']}. The reserve recognizes that the transfer is part of a longer history of dispossession and that the record is incomplete.

The reserve asks visitors to treat the island as a living place, not a museum. Do not remove stones, feathers, or plants. Do not enter closed areas. If you meet a tribal representative or a researcher, listen first. The acknowledgment is a starting point, not a substitute for relationship.

This statement was approved by the board on 1 June 2026. It is reviewed every three years with tribal partners.
""",
    ),
]
