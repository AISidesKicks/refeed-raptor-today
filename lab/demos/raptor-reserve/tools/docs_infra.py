"""Infrastructure and logistics documents for the Raptor Reserve corpus."""

from common import Doc, W

DOCS = [
    Doc(
        "rr-066",
        "North Point Lighthouse",
        "Infrastructure and logistics",
        "2026-03-01",
        W["maintenance"],
        f"""
The {W['north_point']} lighthouse was built in {W['lighthouse_built']} and decommissioned in {W['lighthouse_decommissioned']}. The tower is 23 m tall and sits on a granite foundation 40 m above the sea. It is listed on the state historic register.

The reserve restored the tower in {W['lighthouse_restored']} with a USD 48,000 grant from the state historic preservation office. The work replaced the roof, repaired the masonry, and rebuilt the lantern room windows. The light is not active; the Coast Guard uses a modern buoy at {W['narrows']}.

The tower is open for guided tours from June to September. Tours are limited to eight people and require a waiver. The stairs are steep and the lantern room is not accessible. Visitors with a fear of heights should wait at the base.

The 2026 project replaces six window panes damaged by storm Oscar and repaints the exterior railing. The cost is USD 7,400. The work is scheduled for May, before the tour season.

The maintenance team inspects the tower after every storm above 80 km/h.
""",
    ),
    Doc(
        "rr-067",
        "Solar Microgrid",
        "Infrastructure and logistics",
        "2026-02-10",
        W["maintenance"],
        f"""
The reserve runs an 18 kW solar array with a 24 kWh battery bank. The array is on the south roof of the research station and on a ground mount behind the maintenance shed. It supplies about 72 percent of the island's electricity.

In 2025 the array produced 21,400 kWh. The battery covered 86 percent of the nights. The diesel generator ran for 214 hours, mostly in December and January. The generator is a 20 kW unit with a 1,200 L tank.

The system has a remote monitor that the maintenance lead checks every morning. The monitor shows production, consumption, battery state, and any fault. A fault sends a text message to the maintenance lead and the director.

The 2026 project adds eight panels and replaces two batteries that are below 80 percent capacity. The cost is USD 22,000. The goal is to raise the solar share to 80 percent and cut generator hours below 150.

The array is cleaned four times a year. Snow is cleared after storms. The inverter is serviced every two years.
""",
    ),
    Doc(
        "rr-068",
        "Water System",
        "Infrastructure and logistics",
        "2026-02-10",
        W["maintenance"],
        f"""
The island's water comes from a 48 m well near the research station. A pump lifts water to a 12,000 L storage tank on the hill above the buildings. The tank feeds the visitor center, the research station, and the staff cabins by gravity.

The water passes through a sediment filter and a UV unit. The UV lamp is replaced every 12 months. The tank is cleaned every two years. The reserve tests the water monthly for bacteria and every quarter for nitrate and metals.

In 2025 the system used about 1,200 L per day in summer and 300 L per day in winter. There were no boil-water advisories. The pump failed once in July and was repaired in 6 hours with a spare.

The system is drained before 15 November to prevent freezing. The winter caretaker uses a separate 200 L tank in the research station.

The 2026 project replaces the UV unit and adds a second sediment filter. The cost is USD 3,800.
""",
    ),
    Doc(
        "rr-069",
        "Radio Network",
        "Infrastructure and logistics",
        "2026-03-15",
        W["maintenance"],
        f"""
The reserve uses a VHF radio network for field work and emergencies. The repeater is on {W['granite_ridge']} at 112 m. It covers the island, the ferry route, and most of the mainland shore.

There are four base stations: the visitor center, the research station, the maintenance shed, and the lighthouse. There are 12 handheld radios. Channel 1 is the calling channel, channel 2 is operations, channel 3 is emergency, and channel 4 is the mainland link.

Staff check their radio at the start of every shift. The repeater has a battery backup that lasts 36 hours. In 2025 the network had one outage of 6 hours after a lightning strike. The backup battery carried the repeater until the main power returned.

The reserve does not use the radio for private calls. Sensitive information goes by phone or email. Visitors do not use the network except in an emergency.

The 2026 project replaces the repeater antenna and adds a second backup battery. The cost is USD 5,200.
""",
    ),
    Doc(
        "rr-070",
        "Roads, Trails, and Bridges",
        "Infrastructure and logistics",
        "2026-04-01",
        W["maintenance"],
        f"""
The reserve maintains 4 km of access road and 9 km of trails. The road runs from the ferry landing at {W['seal_cove']} to the research station at {W['north_point']}. It is gravel and is not open to private vehicles.

There are two bridges: the Heron Marsh bridge and the South Beach bridge. Both are inspected every year. The Heron Marsh bridge has a 3 t load limit. The South Beach bridge was repaired after storm Oscar in 2026.

Trail work is scheduled in May and September. The team clears drains, replaces boardwalk planks, and cuts back vegetation. The 2026 boardwalk repair cost USD {W['storm_repair_cost']:,} and took six weeks.

The reserve uses a small tractor and two ATVs for maintenance. Heavy equipment comes by barge. Any project above USD 10,000 needs board approval.

Visitors should report a damaged trail or bridge to a ranger. Closed trails are marked with a red flag and a sign. Do not move a closure sign.
""",
    ),
    Doc(
        "rr-071",
        "Boats and Ferry Operations",
        "Infrastructure and logistics",
        "2026-05-01",
        W["maintenance"],
        f"""
The reserve operates four boats: two 6 m skiffs, one 8 m pontoon, and one 7 m rescue boat. The ferry from Sable Point is operated by a contractor and carries up to 24 passengers.

The crossing is 3.5 km and takes about 35 minutes. The ferry runs three times a day from May to October and twice a week in winter, weather permitting. The captain checks the marine forecast at 06:00 and 12:00.

All boats carry life jackets for every person, a VHF radio, a first aid kit, and a throw bag. The rescue boat is kept on a trailer at Seal Cove and can launch within 15 minutes. Staff practice a man-overboard drill every May.

The 2025 season had 212 ferry trips and no injuries. Two trips were cancelled for weather. The 2026 budget includes a new engine for the pontoon and a replacement trailer for the rescue boat.

The reserve does not allow private boats to land on the island without permission.
""",
    ),
    Doc(
        "rr-072",
        "Equipment Inventory",
        "Infrastructure and logistics",
        "2026-01-15",
        W["maintenance"],
        f"""
The reserve's equipment inventory includes 3 drones, 20 camera traps, 12 acoustic recorders, 2 ATVs, 1 tractor, 4 boats, 18 radios, and 40 pairs of binoculars.

Every item has an asset number, a purchase date, a warranty end date, and a location. The maintenance lead updates the register after every purchase, repair, or retirement. Items above USD 5,000 are tagged with a GPS tracker where possible.

The 2025 inventory found 94 percent of the items. The missing items were two camera traps lost to storm surge and one radio left on the mainland ferry. The reserve wrote off the camera traps and replaced the radio.

The 2026 plan adds 5 camera traps, 2 acoustic recorders, and a battery analyzer for the drone fleet. The cost is USD 9,800.

Staff should report a lost or damaged item the same day. Repeated loss can lead to a review of field privileges.
""",
    ),
    Doc(
        "rr-073",
        "Supplies and Deliveries",
        "Infrastructure and logistics",
        "2026-06-01",
        W["maintenance"],
        f"""
The reserve receives supplies by barge once a month from May to October and once every six weeks in winter. The average delivery is 1.2 t. The barge lands at Seal Cove at high tide.

The order is placed 10 days before the delivery. The maintenance lead checks the inventory, the weather, and the budget. Priority items are fuel, food, medical supplies, and spare parts. Non-urgent items wait for the next barge.

The winter stock is built in October. The reserve keeps 6 weeks of dry food, 1,200 L of diesel, 400 L of gasoline, and a spare propane tank. The goal is to be self-sufficient for 45 days if the ferry cannot run.

Deliveries are checked against the packing list. Damaged items are photographed and reported to the supplier within 48 hours. The receiver signs the manifest and files it in the maintenance shed.

The reserve does not accept unsolicited donations of equipment without prior approval.
""",
    ),
    Doc(
        "rr-074",
        "Waste Management",
        "Infrastructure and logistics",
        "2026-03-01",
        W["maintenance"],
        f"""
The reserve sent 1.1 t of waste to landfill in 2025. The diversion rate was 38 percent, up from 31 percent in 2024. The goal for 2026 is 45 percent.

Recycling covers glass, metal, paper, and number 1 and 2 plastics. Compost covers food scraps, paper towels, and plant material. The compost is used in the visitor center garden. Hazardous waste, including batteries, paint, and medical waste, goes to the mainland on the monthly barge.

The visitor center has three bins: landfill, recycling, and compost. Staff sort the bins at the end of each day. The reserve does not use single-use plastic bottles or straws.

The 2026 project adds a bear-proof compost bin and a battery collection box. The cost is USD 2,400. The reserve also plans to replace the diesel generator with a larger battery, which would cut both fuel use and waste oil.

Litter is recorded on the trail log. Most litter comes from the ferry landing and the South Beach parking area.
""",
    ),
    Doc(
        "rr-075",
        "Fire Prevention Plan",
        "Infrastructure and logistics",
        "2026-05-15",
        W["head_ranger"],
        f"""
The fire plan divides the island into three zones: the visitor center and cabins, the research station and lighthouse, and the forest and marsh.

The reserve keeps two portable pumps, 300 m of hose, and a 2,000 L water tank at the research station. The visitor center has four extinguishers and a sprinkler system. The cabins have smoke alarms and extinguishers.

The defensible space around the buildings is 500 m in the forest zone. The maintenance team clears dead wood and mows the grass before the fire season. The reserve does not allow campfires or fireworks.

The fire drill takes place in October. The scenario is a fire in the maintenance shed with a wind from the northwest. The drill tests the alarm, the evacuation, and the radio link to the mainland fire department.

The reserve has a mutual aid agreement with the Sable Point fire department. The response time is about 40 minutes by boat, so the first 40 minutes are the reserve's responsibility.

The plan is reviewed every year before the fire season.
""",
    ),
]
