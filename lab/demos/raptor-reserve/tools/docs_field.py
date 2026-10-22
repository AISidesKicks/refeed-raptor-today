"""Field operations documents for the Raptor Reserve corpus."""

from common import Doc, W

DOCS = [
    Doc(
        "rr-026",
        "Spring Migration Count Protocol",
        "Field operations",
        "2026-03-01",
        W["head_ranger"],
        f"""
The spring migration count runs from 15 March to 31 May. Counts start 30 minutes after sunrise and last four hours. The reserve counts on three days each week, usually Tuesday, Thursday, and Saturday, plus one weekend day when volunteers are available.

There are six count stations: {W['north_point']}, {W['granite_ridge']}, {W['heron_marsh']}, {W['seal_cove']}, {W['south_beach']}, and the west edge of {W['blacktail_forest']}. Each station has two observers. One observer scans with binoculars while the other records. They switch every 30 minutes.

Counts are cancelled when wind is above 20 km/h, visibility is below 2 km, or rain is steady. Light drizzle is acceptable if the birds are moving. Observers record species, number, direction, height band, behavior, and weather every hour.

The data goes into the migration table the same day. The count coordinator checks for duplicate entries and obvious species errors before the weekly summary. Raptors that are too distant to identify are recorded as "unidentified raptor" and are not included in the species totals.

The protocol is the same each year. Changes need approval from the research committee.
""",
    ),
    Doc(
        "rr-027",
        "Fall Migration Count Protocol",
        "Field operations",
        "2026-08-01",
        W["head_ranger"],
        f"""
The fall migration count runs from 15 August to 15 November. The season is longer than spring because juvenile birds move later and the weather is more variable. The reserve counts on five days each week, with a fixed Saturday hawk watch at {W['granite_ridge']}.

The six spring stations are used again. The {W['granite_ridge']} station is the most productive in September and October, when northwest winds push birds along the ridge. The {W['seal_cove']} station is better in August, when ospreys and young harriers are still moving.

Observers record the same fields as the spring count. The fall count also records flock size for sharp-shinned hawks and broad-winged hawks, because those species often move in groups. A flock is counted as one observation with a group size, not as separate entries.

The 2025 season lost 11 count days to fog, rain, or high wind. The 2026 target is to lose no more than 9 days. The coordinator can add a make-up count on a Sunday if a front passes.

The fall report is due by 15 December.
""",
    ),
    Doc(
        "rr-028",
        "Nest Monitoring Protocol",
        "Field operations",
        "2026-03-15",
        W["ecologist"],
        f"""
Each raptor territory gets three visits. The first visit in April checks occupancy and nest building. The second visit in May records stage, clutch size, and incubation. The third visit in June counts chicks and estimates fledge date.

Observers stay at least 150 m from active nests. They use binoculars or a spotting scope, not a drone. If a bird alarm-calls or leaves the nest, the observer backs away and records the disturbance. A nest is not approached again for at least 48 hours.

The field form records territory id, date, time, observer, weather, distance, nest substrate, stage, adult behavior, chick count, and any threats. Photos are taken from the observation point, not from the nest.

A territory is occupied if an adult is seen in suitable habitat during the breeding season, or if a nest is active. A nest is successful if at least one chick fledges. The reserve does not count a nest as successful if the chicks disappeared before fledging, even if the cause is unknown.

Data is entered within 24 hours. The ecologist reviews all records before the annual breeding report.
""",
    ),
    Doc(
        "rr-029",
        "Banding Protocol",
        "Field operations",
        "2026-05-20",
        W["ecologist"],
        f"""
The reserve bands raptor chicks in June, when the birds are large enough for a USGS leg band but not yet able to fly. Two licensed banders work together. At least one staff member watches the nest and keeps the adults at a distance.

The team targets 30 chicks across six species: osprey, red-tailed hawk, northern harrier, American kestrel, barred owl, and peregrine falcon. The team does not band every nest; the goal is a representative sample, not a complete inventory.

Each bird gets a numbered USGS band and a color band with a two-letter code. The team records species, age, sex if known, weight, wing chord, bill length, body condition, and ectoparasites. Handling time is kept under 20 minutes per bird.

Equipment is disinfected between nests. Banders wear gloves and eye protection. If a chick is injured or severely underweight, the team stops and calls the veterinarian.

Data goes to the USGS Bird Banding Laboratory and to the reserve database. Resighting reports from visitors are welcome and should include the color code, date, and location.
""",
    ),
    Doc(
        "rr-030",
        "Camera Trap Network",
        "Field operations",
        "2026-04-01",
        W["ecologist"],
        f"""
The reserve operates {W['camera_traps']} camera traps on a roughly 2 km grid. The cameras are placed on trails, nest access routes, and known perch sites. They are not placed inside nest territories during the breeding season.

Each camera is deployed for 30 days. Staff check it every 7 days to replace batteries and download images. The camera records date, time, temperature, and moon phase. Images are tagged with species, number of individuals, behavior, and confidence.

In 2025 the network logged 4,100 trap nights and 1,240 raptor detections, or 0.30 detections per 100 trap nights. Red-tailed hawks were the most common detection, followed by barred owls and northern harriers. The network also recorded fox, deer, mink, and one otter.

Camera traps are useful for presence and behavior, not for abundance. The reserve combines them with the nest survey and the migration count to get a fuller picture.

Images of people are deleted unless they are part of a safety incident. The privacy policy in rr-098 applies.
""",
    ),
    Doc(
        "rr-031",
        "Acoustic Monitoring Array",
        "Field operations",
        "2026-04-10",
        W["ecologist"],
        f"""
The acoustic array has 12 stations: four at {W['heron_marsh']}, three at {W['blacktail_forest']}, two at {W['north_point']}, two at {W['south_beach']}, and one at {W['granite_ridge']}. Each station records 24 hours a day during the breeding season and 12 hours a day in winter.

Staff swap SD cards and batteries every two weeks. The recorders are mounted 2 to 4 m above the ground, away from the surf and the generator. The microphones are omnidirectional and have a usable range of about 300 m in open habitat.

The 2025 season produced 8,200 hours of audio. The classifier flagged 1,840 raptor calls. A human reviewer checked a 10 percent sample and found 92 percent precision and 78 percent recall. The main confusion was between merlin and American kestrel calls.

Acoustic data is stored as FLAC files with a date and station id. The classifier output is stored in a separate table so the raw audio can be reanalyzed with a better model. The reserve keeps raw audio for five years.

The array is not a replacement for the migration count. It is a way to detect cryptic species and to measure activity at night.
""",
    ),
    Doc(
        "rr-032",
        "Drone Flight Checklist",
        "Field operations",
        "2026-05-01",
        W["head_ranger"],
        f"""
Drone flights are used for nest surveys, shoreline mapping, and search and rescue. Every flight needs approval from the head ranger and a written flight plan.

The pilot checks the weather first. Flights are cancelled at {W['drone_wind_limit_kmh']} km/h wind, visibility below 2 km, rain, snow, or lightning within 10 km. The drone must stay within {W['drone_max_distance_km']} km of the pilot and above 30 m except during takeoff and landing.

The battery must be at least 80 percent at takeoff. The planned flight time cannot exceed {W['drone_battery_min']} minutes, which leaves a 30 percent reserve. The pilot does not fly over people, boats, or the visitor center.

No flight is allowed within 250 m of an active nest during the breeding season. The pilot checks the nest map before takeoff and logs the flight in the drone book. The log records date, pilot, purpose, weather, max altitude, duration, battery used, and any wildlife response.

If the drone loses link, the pilot switches to return-to-home and clears the landing zone. If the drone does not return, the pilot marks the last known point and calls the head ranger.
""",
    ),
    Doc(
        "rr-033",
        "Granite Ridge Weather Station",
        "Field operations",
        "2026-01-20",
        W["maintenance"],
        f"""
The {W['weather_station']} sits at {W['highest_point_m']} m on {W['granite_ridge']}. It records temperature, relative humidity, barometric pressure, wind speed, wind direction, solar radiation, and rainfall every 10 minutes.

The station has two wind sensors, one at 3 m and one at 10 m. The 10 m sensor is the official one for drone and safety decisions. The 3 m sensor is a backup and a check on shelter effects.

Staff clean the rain gauge every month and replace the desiccant every three months. The anemometer bearings are replaced every two years. The data logger has a battery backup and a solar panel.

In 2025 the station had 99.2 percent uptime. The longest gap was 11 hours after a lightning strike in July. The missing data was filled from the backup sensor and flagged in the database.

The station is part of a regional weather network. Data is shared hourly with the Maine Coast Trust and is available in the reserve's open data portal. The wind limit for drone flights is based on the 10 m sensor.
""",
    ),
    Doc(
        "rr-034",
        "Patrol Log, 12 September 2026",
        "Field operations",
        "2026-09-12",
        W["head_ranger"],
        f"""
Observer: Elin Ward, head ranger.
Route: {W['north_point']} to {W['heron_marsh']}, via the west trail and the lower boardwalk.
Time: 06:40 to 11:20.
Weather: fog at dawn, clearing by 09:00. Wind 14 km/h from the northwest. Visibility 1.2 km at 07:00, 8 km by 10:00. High tide 08:12.

At 07:05 I checked the North Point closure sign. The peregrine pair was on the cliff, no alarm calls. At 07:40 I found fresh osprey sticks on the platform at the Heron Marsh south nest. Two adults were circling, one carrying a fish.

At 08:20 I met four visitors near the lower boardwalk. They stayed on the trail and asked about the drone. I explained the 250 m nest rule and the 28 km/h wind limit. The wind was 14 km/h, so I approved the 09:30 drone flight over the marsh for the nest survey. I logged the approval in the drone book.

At 10:05 I checked the boardwalk repair from storm Oscar. The new decking is holding. One handrail bolt was loose; I tightened it and flagged the rail for the maintenance team.

No injured birds. No off-trail tracks. No dogs.
""",
    ),
    Doc(
        "rr-035",
        "Drone Crash Report, 3 August 2025",
        "Field operations",
        "2025-08-05",
        W["head_ranger"],
        f"""
On 3 August 2025 at 10:42, a reserve drone crashed in {W['heron_marsh']} during a nest survey. The pilot was Caleb Finch. The drone was 180 m from the pilot at 42 m altitude when the battery voltage dropped from 48 percent to 21 percent in less than 20 seconds. The drone entered a forced landing and hit the marsh.

No birds were harmed. The nearest active nest was 310 m away. The drone was recovered after a two-hour search. The camera and the flight log survived. The replacement cost was USD 2,100.

The cause was {W['drone_crash_cause']}. The battery had 94 charge cycles and had shown a small voltage sag on the previous flight. The maintenance log had not flagged it.

Corrective actions: retire drone batteries after 80 cycles, check voltage under load before every flight, and add a pre-flight battery health field to the drone book. The reserve also bought a battery analyzer and now keeps a spare battery at the marsh station.

The report was reviewed by the safety committee on 11 August 2025. The committee closed the case with all three actions complete.
""",
    ),
    Doc(
        "rr-036",
        "Storm Oscar Damage Report",
        "Field operations",
        "2026-01-22",
        W["maintenance"],
        f"""
Storm Oscar reached {W['island']} on {W['storm_date']}. The weather station recorded a peak gust of 118 km/h at 03:40. Rainfall was 41 mm in 12 hours. The ferry was cancelled for two days.

The South Beach boardwalk lost 42 m of decking and two support posts. The visitor center roof lost six shingles. The North Point lighthouse lost a window pane, and the old boathouse door was pushed in. No one was injured.

The reserve closed South Beach and the lower boardwalk on 18 January. The maintenance team rebuilt the boardwalk in six weeks. The repair cost USD {W['storm_repair_cost']:,}, covered by the capital budget and a USD 5,000 donation from the friends group. The new decking uses a higher grade of Marine Board and stainless fasteners.

The storm also moved the South Beach dune line by about 3 m. The reserve added the change to the shoreline monitoring dataset. The next survey will check whether the least tern nesting area is still above the spring high tide line.

The boardwalk reopened on 1 March 2026.
""",
    ),
    Doc(
        "rr-037",
        "Lead Poisoning Case: Juniper",
        "Field operations",
        "2024-10-25",
        W["vet"],
        f"""
On {W['lead_case_date']}, a visitor found an adult female peregrine on the ground near {W['north_point']}. The bird was weak, had drooping wings, and could not stand. The ranger team captured her with a net and brought her to the clinic.

The bird was known as {W['lead_case_bird']}, the female of the North Point pair. Her blood lead level was 0.42 ppm. The threshold for clinical concern is 0.2 ppm. She was started on chelation therapy, fluids, and a high-energy diet.

Juniper improved slowly. She gained weight in the first week, began standing in the second week, and was flying in the flight pen by day 14. She was {W['lead_case_outcome']} on 27 October 2024.

The total cost was USD 6,200. The source of the lead was never confirmed, but a spent rifle bullet was found in a deer carcass 1.8 km from the territory. The reserve banned lead ammunition in {W['lead_ban_year']}, but the ban does not cover neighboring land.

The case is used in the lead monitoring program and in the visitor center exhibit.
""",
    ),
    Doc(
        "rr-038",
        "Search and Rescue Drill",
        "Field operations",
        "2026-05-02",
        W["head_ranger"],
        f"""
The spring search and rescue drill took place on 2 May 2026. The scenario was a visitor who left the {W['granite_ridge']} trail at 11:00 and did not return to the visitor center by 15:00.

Fourteen staff took part. The duty officer set up the command post at the visitor center, assigned three search teams, and launched a drone. The teams covered the ridge trail, the north slope, and the service road. The drone flew a grid over the ridge and the upper forest.

The search found the "missing" visitor at 14:20, 600 m off trail, with a simulated ankle injury. The teams practiced packaging, carrying, and radio handoff. The whole drill took 3 hours and 10 minutes.

The after-action review found two problems: the trailhead sign still showed the winter hours, and the drone pilot had to wait 12 minutes for a battery. The sign was replaced the next day, and the drone kit now carries two spare batteries.

The next drill is the fall fire drill in October.
""",
    ),
    Doc(
        "rr-039",
        "Fuel Storage Inspection",
        "Field operations",
        "2026-06-14",
        W["maintenance"],
        f"""
The reserve stores fuel in a fenced compound behind the maintenance shed. The inventory on 14 June 2026 was 1,200 L of diesel and 400 L of gasoline. The diesel tank is double-walled and sits on a concrete pad. The gasoline is stored in four 100 L portable tanks.

The inspection checked tanks, hoses, valves, labels, secondary containment, fire extinguishers, and signage. There were no leaks. Two minor issues were found: a cracked hose on the diesel pump and a missing "no smoking" sign on the gate. Both were fixed the same day.

The compound has a 4,000 L containment curb and a drain that can be closed. Spill kits are stored at the gate and in the maintenance truck. Staff are trained to stop the source, contain the spill, and call the state spill line.

The next inspection is in December. The reserve does not store fuel at {W['north_point']} or {W['heron_marsh']}; all field equipment is refueled at the main compound.
""",
    ),
    Doc(
        "rr-040",
        "Winter Preparation Checklist",
        "Field operations",
        "2026-10-01",
        W["maintenance"],
        f"""
Winter preparation starts on 15 October and must be finished by 15 November. The island gets freezing spray, short days, and occasional storm surges, so the checklist is strict.

The 12 tasks are: shut off and drain the visitor center water lines; switch the solar array to winter mode; service the generator; inspect the lighthouse roof; secure the boat shed; pull the docks at {W['seal_cove']}; store the trail signs; winterize the research station; check the radio repeater battery; stock the emergency cabin; move the camera traps to the lower forest; and review the storm plan with staff.

The maintenance team works with the head ranger and the veterinarian. The veterinarian checks the clinic's oxygen, drugs, and heating before the last ferry. The data manager confirms that the off-island backup is current.

The checklist is signed by the maintenance lead and the director. Any incomplete task needs a written exception and a date. The reserve keeps a copy in the maintenance shed and a copy in the board packet.

The first winter storm usually arrives in late November. The last ferry is scheduled for 20 November.
""",
    ),
]
