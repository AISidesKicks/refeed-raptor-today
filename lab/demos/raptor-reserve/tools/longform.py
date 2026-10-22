"""Long-form expansion for the Raptor Reserve corpus.

The source modules keep the unique facts and the lead paragraphs. This module
adds the sections that make each document long enough to chunk: scope, roles,
methods, safety, review, and related records. The goal is 500 to 800 words per
document, which gives the RAPTOR tree two to four chunks per document.
"""

from __future__ import annotations

from dataclasses import replace

from common import Doc, SPECIES, W


SPECIES_BY_NAME = {s["name"]: s for s in SPECIES}


DETAILS = {
    "Peregrine falcon": {
        "field_marks": "stocky falcon with a dark helmet, a pale throat, and long, pointed wings",
        "confusion": "the merlin, which is smaller and lacks the heavy helmet",
        "hunting": "stooping from a height and striking birds in flight",
        "timeline": "Courtship starts in late March. Eggs are laid in mid-April, hatch in late May, and the chicks fledge in late June.",
        "prev_pairs": 2,
        "prev_fledged": 2,
    },
    "Osprey": {
        "field_marks": "large fish hawk with a white head, a dark eye stripe, and angled wings",
        "confusion": "the bald eagle, which has a white head and tail but a different flight profile",
        "hunting": "hovering over the water and plunging feet-first",
        "timeline": "Pairs return in late March. Eggs are laid in late April, hatch in late May, and the chicks fledge in July.",
        "prev_pairs": 14,
        "prev_fledged": 19,
    },
    "Northern harrier": {
        "field_marks": "slender hawk with a white rump patch and a low, buoyant flight",
        "confusion": "the rough-legged hawk, which is larger and has a different wing pattern",
        "hunting": "coursing low over the marsh and pouncing on prey",
        "timeline": "Courtship begins in April. Eggs are laid in May, hatch in June, and the chicks fledge in July.",
        "prev_pairs": 6,
        "prev_fledged": 7,
    },
    "Short-eared owl": {
        "field_marks": "medium owl with small ear tufts, yellow eyes, and a moth-like flight",
        "confusion": "the long-eared owl, which has taller ear tufts and orange eyes",
        "hunting": "quartering low over the meadow and dropping on prey",
        "timeline": "Nesting starts in April. Eggs are laid in May, hatch in June, and the chicks fledge in July.",
        "prev_pairs": 4,
        "prev_fledged": 4,
    },
    "Barred owl": {
        "field_marks": "large, round-headed owl with dark eyes and horizontal barring",
        "confusion": "the great horned owl, which has ear tufts and yellow eyes",
        "hunting": "still-hunting from a perch and gliding through the forest",
        "timeline": "Courtship begins in February. Eggs are laid in March, hatch in April, and the young leave the nest in May.",
        "prev_pairs": 3,
        "prev_fledged": 3,
    },
    "Red-tailed hawk": {
        "field_marks": "broad-winged hawk with a rusty tail and a pale chest",
        "confusion": "the broad-winged hawk, which is smaller and has a different tail pattern",
        "hunting": "soaring over the ridge and dropping on mammals",
        "timeline": "Courtship begins in March. Eggs are laid in April, hatch in May, and the chicks fledge in June.",
        "prev_pairs": 9,
        "prev_fledged": 11,
    },
    "Merlin": {
        "field_marks": "small, compact falcon with pointed wings and a streaked chest",
        "confusion": "the American kestrel, which is more colorful and hovers more often",
        "hunting": "fast pursuit of songbirds in open air",
        "timeline": "Pairs return in April. Eggs are laid in May, hatch in June, and the chicks fledge in July.",
        "prev_pairs": 1,
        "prev_fledged": 2,
    },
    "American kestrel": {
        "field_marks": "small, colorful falcon with a rusty back and two dark face stripes",
        "confusion": "the merlin, which is larger and lacks the face stripes",
        "hunting": "hovering and pouncing on insects and voles",
        "timeline": "Courtship begins in April. Eggs are laid in May, hatch in June, and the chicks fledge in July.",
        "prev_pairs": 4,
        "prev_fledged": 7,
    },
    "Bald eagle": {
        "field_marks": "very large eagle with a white head and tail in adults",
        "confusion": "the osprey, which is smaller and has a dark eye stripe",
        "hunting": "soaring and scavenging, and taking fish from the surface",
        "timeline": "Courtship begins in February. Eggs are laid in March, hatch in April, and the chicks fledge in June.",
        "prev_pairs": 1,
        "prev_fledged": 2,
    },
}


def _section(title: str, text: str) -> str:
    return f"## {title}\n\n{text.strip()}"


def governance(doc: Doc) -> str:
    if doc.id == "rr-001":
        scope = f"""
{doc.title} is the top-level document for the reserve. It sets the mission, the board structure, and the amendment rule. The management plan (rr-002) and the specific policies sit below it. When two documents disagree, the charter wins.
"""
        related = """
Management plan (rr-002), safety plan (rr-005), emergency response (rr-006), data policy (rr-009), and the data dictionary (rr-096).
"""
    else:
        scope = f"""
{doc.title} applies to the board, the director, full-time and seasonal staff, volunteers, researchers, and contractors working on {W['island']}. It does not replace the charter (rr-001), the emergency response plan (rr-006), or the safety plan (rr-005). When two documents disagree, the charter wins, then the management plan, then the specific policy.
"""
        related = """
Charter (rr-001), management plan (rr-002), safety plan (rr-005), emergency response (rr-006), data policy (rr-009), and the data dictionary (rr-096).
"""
    return "\n\n".join(
        [
            _section("Scope", scope),
            _section(
                "Roles and responsibilities",
                f"""
The board approves the document. The director, {W['director']}, owns implementation and reports exceptions to the board. The head ranger, {W['head_ranger']}, is the day-to-day contact for field staff. The data manager, {W['data_manager']}, keeps the signed copy in the document register and makes sure the shared drive has the current version.
""",
            ),
            _section(
                "What staff should do",
                """
Read the document during onboarding. Ask the director or the head ranger if a situation is not covered. Record decisions that deviate from the document, including the reason and the date. Do not edit the shared copy. Send proposed changes to the data manager.
""",
            ),
            _section(
                "Records and evidence",
                """
The reserve keeps the approved version, the board minutes, the public comment summary, and the annual review memo. Records are kept for 10 years. Personnel details are stored separately and are not part of the public corpus.
""",
            ),
            _section(
                "Review and amendment",
                """
Review follows the schedule in the document. If the document does not set one, the default is every two years. Proposed changes go to the board packet 14 days before the meeting. A charter change needs a two-thirds vote; other documents need a simple majority.
""",
            ),
            _section(
                "Common failure modes",
                """
The most common problems are outdated copies, unclear ownership, and field decisions that are never written down. The reserve fixes these by naming one owner, using a single document register, and reviewing the field log at the Monday safety meeting.
""",
            ),
            _section("Related records", related),
        ]
    )


def ecology_topic(doc: Doc) -> str:
    """Expansion for prey, migration, nest site, and health topics."""

    return "\n\n".join(
        [
            _section(
                "Why this matters",
                f"""
{doc.title} connects the bird survey to the habitat and the food web. A change in one species is hard to interpret without the prey base, the weather, and the nesting sites. The reserve tracks all of them together.
""",
            ),
            _section(
                "How the reserve measures it",
                """
The field team uses the standard protocols: six count stations, three nest visits, 60 live traps, and the 20-camera network. Observations are entered within 24 hours. The ecologist checks the records before the weekly summary and the annual report.
""",
            ),
            _section(
                "What the data shows",
                f"""
The 2025 season was a high vole year, which improved the outlook for harriers and short-eared owls. The 2024 season was average. The reserve treats a single year as a signal, not a trend, and waits for at least three years before changing a management target.
""",
            ),
            _section(
                "Seasonal timing",
                """
The reserve records the first arrival, the first nest, and the first fledge for each species. The 2025 season was about 5 days earlier than the 2016 baseline. The timing matters because a chick that hatches before the prey peak can starve, and a chick that hatches after the peak can miss the easiest food. The field team compares the timing with the small mammal index and the weather station data.
""",
            ),
            _section(
                "How to read the numbers",
                """
The counts are indices, not a complete census. A high count can mean more birds or better weather for counting. A low count can mean fewer birds or fog that kept them on the ground. The report gives the effort and the weather so a reader can judge the number instead of taking it at face value.
""",
            ),
            _section(
                "What visitors can do",
                """
Stay on the trail and keep 100 m from any bird that is alarm-calling. Report a dead or injured bird to a ranger. Do not feed the birds or leave food scraps. If you find a pellet, leave it in place; the diet study needs a clean sample.
""",
            ),
            _section(
                "Management implications",
                """
The reserve can manage trails, disturbance, lead, and nest platforms. It cannot manage the weather or the ocean. When a pressure is outside the reserve's control, the team documents it and adjusts the interpretation instead of claiming credit for the change.
""",
            ),
            _section(
                "Related records",
                """
The annual breeding summary (rr-043), the migration reports (rr-041 and rr-042), the prey survey (rr-020), and the management plan (rr-002).
""",
            ),
        ]
    )


def species(doc: Doc) -> str:
    if doc.title not in SPECIES_BY_NAME:
        return ecology_topic(doc)
    s = SPECIES_BY_NAME[doc.title]
    d = DETAILS[doc.title]
    return "\n\n".join(
        [
            _section(
                "Field identification",
                f"""
{s['name']} is a {d['field_marks']}. It is most often confused with {d['confusion']}. The scientific name is {s['sci']}. At the reserve, the best clues are the flight silhouette, the wing pattern, and the habitat.
""",
            ),
            _section(
                "Habitat and territory",
                f"""
The species nests in {s['habitat']}. The reserve monitors {s['pairs']} territories. Observers check the territories from the ground and stay at least 150 m from active nests. The birds use the same territory across years when the site is undisturbed.
""",
            ),
            _section(
                "Diet and hunting",
                f"""
The diet is mainly {s['diet']}. The birds hunt by {d['hunting']}. Pellets and prey remains are collected for the diet study (rr-047) when they are found away from nests.
""",
            ),
            _section(
                "Breeding timeline",
                f"""
{d['timeline']} The reserve's three-visit protocol matches this schedule: occupancy in April, stage and clutch size in May, and chick count in June.
""",
            ),
            _section(
                "Monitoring results",
                f"""
The 2025 season recorded {s['pairs']} pairs and {s['fledged']} fledged chicks. The 2024 season recorded {d['prev_pairs']} pairs and {d['prev_fledged']} fledged chicks. The long-term trend is reported in the annual breeding summary (rr-043) and the occupancy analysis (rr-045).
""",
            ),
            _section(
                "Threats and management",
                """
The lead paragraph lists the main threats. The management response has three parts: seasonal trail closures, a ban on lead ammunition, and a 250 m no-fly zone around active nests. Nest platforms are added where a natural site is unstable. The management plan target is to protect at least 90 percent of occupied territories.
""",
            ),
            _section(
                "Visitor guidance",
                """
The lead paragraph gives the distance rule. The short version: stay on the marked trail, keep 100 m from a bird that is alarm-calling or carrying food, and do not use playback, drones, or food to get a closer look. Report injured birds to a ranger.
""",
            ),
        ]
    )


def field(doc: Doc) -> str:
    return "\n\n".join(
        [
            _section(
                "Purpose and scope",
                f"""
{doc.title} is the standard procedure for this part of the field program. It applies to staff, seasonal employees, and trained volunteers. It does not replace the safety plan (rr-005) or the emergency response plan (rr-006).
""",
            ),
            _section(
                "Roles",
                f"""
The head ranger, {W['head_ranger']}, owns the procedure. The field lead assigns teams and checks the weather. The data manager, {W['data_manager']}, checks the records. The veterinarian, {W['vet']}, is consulted for any wildlife handling.
""",
            ),
            _section(
                "Procedure",
                """
1. Check the weather, the tide, and the radio.
2. Sign out at the research station and record the team.
3. Follow the route and the timing in the document.
4. Record the data in the field form before leaving the site.
5. Report any safety issue, injury, or unusual wildlife behavior to the head ranger.
6. Sign in at the end of the shift.
""",
            ),
            _section(
                "Data and records",
                """
Records go into the field database within 24 hours. Each record needs date, time, observer, location, weather, and a confidence note. Photos are optional and should not include people without consent. The data manager checks the records before the weekly summary.
""",
            ),
            _section(
                "Safety",
                f"""
Work in pairs. Carry a radio, a first aid kit, and water. Stay 150 m from the cliff edge at {W['north_point']}. Do not fly a drone above {W['drone_wind_limit_kmh']} km/h wind or within 250 m of an active nest. Stop work in lightning, fog below 2 km visibility, or a red risk level.
""",
            ),
            _section(
                "Why it matters",
                """
Consistent records are the only way to compare years. A missed field or a changed route can look like a population change. The reserve would rather lose a day of data than publish a number that cannot be defended.
""",
            ),
            _section(
                "Review",
                f"""
The procedure is reviewed before each field season. Changes are tested in a drill and then added to the next version. The current version took effect on {doc.date}.
""",
            ),
        ]
    )


def research(doc: Doc) -> str:
    return "\n\n".join(
        [
            _section(
                "Background",
                f"""
{doc.title} is part of the reserve's long-term monitoring program. The question is whether the island's raptor population is changing, and whether the change is driven by weather, prey, disease, or human disturbance. The reserve has collected comparable data since 2016.
""",
            ),
            _section(
                "Methods",
                """
The analysis uses the standard field protocols. Counts use six fixed stations and a four-hour window. Nest checks use three visits and a 150 m observation distance. Occupancy models use the 2016-2025 records and account for detection probability. The data manager checks the records before analysis.
""",
            ),
            _section(
                "Results",
                """
The headline numbers are in the document. The full tables are in the annual data release. Estimates are reported with 95 percent confidence intervals. A difference is treated as meaningful only when the intervals do not overlap and the field effort was similar.
""",
            ),
            _section(
                "What changed since the last report",
                """
The previous report used the same routes and the same three-visit protocol, so the comparison is direct. The 2026 analysis adds the new South Beach boardwalk data and the two acoustic stations installed in 2025. The older records are flagged where the effort or the observer changed. A difference that comes from a new route is not treated as a population change.
""",
            ),
            _section(
                "Discussion",
                """
The reserve reads the results against the management plan. A single year is not a trend. A change that appears in one species but not in its prey or habitat is treated with caution. The team also checks whether a new observer, a new route, or a new sensor could explain the pattern.
""",
            ),
            _section(
                "Recommendations",
                """
The document ends with actions for the next season. Each action has an owner, a date, and a check. Actions that need money go to the budget process. Actions that need a protocol change go to the research committee.
""",
            ),
            _section(
                "Data availability",
                f"""
The summary is public. The raw data is available to researchers with a permit and a data-sharing agreement. Sensitive nest locations are stored at reduced precision. The data manager can provide the data dictionary (rr-096) and the file naming rules (rr-097).
""",
            ),
        ]
    )


def visitor(doc: Doc) -> str:
    return "\n\n".join(
        [
            _section(
                "Audience",
                f"""
{doc.title} is for visitors, volunteers, teachers, and program partners. It assumes no prior knowledge of raptors. Staff should use it as the source for talks and trail conversations.
""",
            ),
            _section(
                "What to expect",
                """
The reserve is a working conservation site, not a zoo. Birds are wild and sightings are not guaranteed. The best times are early morning and late afternoon. The visitor center has a live nest camera, a touch table, and a small exhibit on lead poisoning.
""",
            ),
            _section(
                "What to bring",
                """
Bring layers, water, sunscreen, and insect repellent. Sturdy shoes are better than sandals on the ridge. Binoculars are available at the front desk, but the reserve has only 12 pairs. A phone is useful for the audio guide; the app works offline after the first download. Leave drones, dogs, and playback devices at home.
""",
            ),
            _section(
                "Planning your visit",
                """
Book the ferry in advance. Bring layers, water, and sturdy shoes. The island has no food service; the visitor center sells snacks and water. Cell service is limited to the visitor center. Tell someone on the mainland which trails you plan to walk.
""",
            ),
            _section(
                "Access and timing",
                """
The island is reached by the reserve ferry from Sable Point. The crossing takes 35 minutes. The visitor center is open from May to October, 9:00 to 17:00. Trails close at 19:00. The South Beach boardwalk is closed in winter and after storms.
""",
            ),
            _section(
                "Rules",
                """
Stay on marked trails. Keep 100 m from nesting birds. Do not use playback. Do not fly drones. Do not bring dogs. Pack out everything you bring in. Report injured wildlife to a ranger.
""",
            ),
            _section(
                "Accessibility",
                """
The visitor center and the first 1.2 km of the Seal Cove trail are accessible. The boardwalk has a gentle grade and benches every 200 m. The audio guide is available at the front desk. Service animals are welcome.
""",
            ),
            _section(
                "Group visits",
                """
Groups of 10 or more should book at least two weeks in advance. School groups use the school program (rr-058). Commercial tour operators need a permit and must follow the photography policy (rr-061). The visitor center can provide a staff guide for a fee.
""",
            ),
        ]
    )


def infra(doc: Doc) -> str:
    return "\n\n".join(
        [
            _section(
                "Overview",
                f"""
{doc.title} is part of the reserve's infrastructure and logistics. The document names the owner, the maintenance schedule, the risks, and the records. The goal is reliable service with a small footprint.
""",
            ),
            _section(
                "Specifications",
                """
The specifications are in the document. The maintenance lead keeps the current configuration, the warranty papers, and the service log. Any change to the specifications needs approval from the director and the board if the cost is above USD 10,000.
""",
            ),
            _section(
                "Maintenance",
                f"""
Preventive maintenance follows the annual calendar. The team logs every inspection, repair, and replacement. Critical spares are kept on the island. The maintenance lead, {W['maintenance']}, reviews the log at the first Monday meeting.
""",
            ),
            _section(
                "Spare parts and tools",
                """
The maintenance shed keeps the spare parts that the team needs to keep this part of the operation running: filters, fuses, fasteners, and the parts named in the service manual. Critical parts are ordered before the winter ferry gap. The inventory is checked on the first Monday of each month.
""",
            ),
            _section(
                "Risks",
                """
The main risks are weather, salt corrosion, wildlife damage, and supply delays. The reserve keeps a storm kit, a spare parts bin, and a contingency line in the budget. Any outage that affects safety is reported to the director the same day.
""",
            ),
            _section(
                "Winter",
                """
The system is checked before 15 November. The team follows the winter checklist for this system: freeze protection where needed, battery and fuel checks, access marking, and a photo report from the winter caretaker. Any fault is logged and reported to the maintenance lead.
""",
            ),
            _section(
                "Records",
                """
This part of the operation has a page in the asset register with the installation date, the warranty end date, the service history, and the replacement cost. The register is reviewed every year with the budget.
""",
            ),
            _section(
                "Contacts",
                f"""
The maintenance lead is {W['maintenance']}. The director is {W['director']}. The board's facilities committee reviews major projects. The reserve's insurance carrier is notified of any incident above USD 5,000.
""",
            ),
        ]
    )


def history(doc: Doc) -> str:
    return "\n\n".join(
        [
            _section(
                "Background",
                f"""
{doc.title} is part of the reserve's effort to document the island's human history. The reserve is a conservation area, but the island was used for fishing, farming, military defense, and lighthouse keeping long before {W['founded']}.
""",
            ),
            _section(
                "Timeline",
                """
The timeline in the document is built from photographs, maps, oral histories, and public records. Dates are given as the reserve's best estimate. When sources disagree, the archive note explains the conflict.
""",
            ),
            _section(
                "How the archive got the story",
                """
The archive builds each file from at least two sources: a photograph, a map, a letter, a newspaper clipping, or an oral history. The archivist writes a short note when the sources disagree. Donors sign a deed of gift that says how the material can be used. The reserve does not buy historical documents, and it does not remove a name unless the family asks.
""",
            ),
            _section(
                "People",
                """
The archive names the people who appear in the records. Descendants can ask for a correction or for a name to be removed. The reserve does not publish personal contact details.
""",
            ),
            _section(
                "Significance",
                """
The history matters because conservation is not only about birds. The island's past shapes the trails, the buildings, and the relationships with the fishing community. The reserve includes this history in visitor talks and school programs.
""",
            ),
            _section(
                "What is missing",
                """
The archive is thin on Wabanaki history, women's work, and the years after the lighthouse closed. The reserve is working with tribal partners and local historians to fill those gaps. Anyone with a photograph, a letter, or a story can contact the director.
""",
            ),
            _section(
                "How to use the archive",
                """
Start with the archive inventory (rr-084). Request a box by number and use gloves. Photographs may be scanned at 600 dpi. Oral history recordings are available on a tablet at the visitor center. Commercial use needs a written agreement.
""",
            ),
            _section(
                "Sources",
                """
The archive holds 2,300 photographs, 140 maps, and 60 oral history recordings. The originals are stored in a climate-controlled room at the research station. Digital copies are available to researchers by request.
""",
            ),
        ]
    )


def methods(doc: Doc) -> str:
    return "\n\n".join(
        [
            _section(
                "Question",
                f"""
This document answers a practical question for the reserve's library: how does this part of the pipeline work, and when is it worth using? The goal is not to sell a model or a framework. The goal is to explain one piece of the retrieval pipeline so a reader can run it, measure it, and decide whether it is worth the cost.
""",
            ),
            _section(
                "Method",
                """
The method is a small local stack: EmbeddingGemma 2 for embeddings, a SQLite store, numpy cosine search, and a RAPTOR summary tree. The writer is LFM2.5-8B-A1B. The decision model is d1-3B. The app is FastAPI plus static HTML. No cloud model and no API key.
""",
            ),
            _section(
                "What the numbers mean",
                """
Retrieval numbers describe whether the right passage was found. Answer numbers describe whether the final text is supported. Calibration numbers describe whether the model knows how sure it is. A good demo reports all three, not just the answer quality.
""",
            ),
            _section(
                "Limitations",
                """
The corpus is small and synthetic. The results are a lab result, not a benchmark. A judge model can prefer its own output. A reranker can look good because the gold passages are easy. The project reports the cost and the failure cases next to the wins.
""",
            ),
            _section(
                "Practical use",
                f"""
Use the method when the corpus is small enough to inspect and the question needs evidence. Do not use it when a keyword search or a single document is enough. The librarian guide (rr-095) shows how to ask a question that the loop can actually answer.
""",
            ),
            _section(
                "Further reading",
                """
The primary sources are the RAPTOR paper (arXiv 2401.18059), the SearchJev paper (arXiv 2610.05107), the EmbeddingGemma 2 model card, the LFM2.5 model card, and the d1-3B model card. The lab's INTENT.md has the full reference list.
""",
            ),
        ]
    )


EXPANDERS = {
    "Governance": governance,
    "Species and ecology": species,
    "Field operations": field,
    "Research and monitoring": research,
    "Visitor and education": visitor,
    "Infrastructure and logistics": infra,
    "History and culture": history,
    "Data and methods": methods,
}


def expand(doc: Doc) -> Doc:
    """Return a copy of the document with its category sections added."""

    expander = EXPANDERS.get(doc.category)
    if expander is None:
        return doc
    body = doc.body.strip() + "\n\n" + expander(doc).strip()
    return replace(doc, body=body)
