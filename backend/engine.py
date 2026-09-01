# backend/engine.py
# ========================================================
# TTD CROWD MATH ENGINE
#
# CORE LOGIC (from real pilgrim experience):
# 1. "Where the queue starts, there the devotee will be!"
# 2. Devotees walk FORWARD only toward temple
# 3. NEW devotees don't know local place names!
#    → Every location gets: simple description +
#      distance + directions from bus stand/station
#
# GEOGRAPHY (temple → outward):
# VQC → Krishnateja (NEAR) → Octopus (FAR)
# → Silathoranam (EXTREME DAYS ONLY!)
# ========================================================

from datetime import datetime

class TTDCrowdEngine:
    def __init__(self):
        # VQC: 31 compartments x ~450 people each
        self.COMPARTMENT_CAPACITY = 450
        self.TOTAL_COMPARTMENTS   = 31
        self.VQC_MAX_CAPACITY     = self.COMPARTMENT_CAPACITY * self.TOTAL_COMPARTMENTS

        # Temple clears 2500 pilgrims per hour (free darshan line)
        self.TEMPLE_FLOW_RATE = 2500

        # ========================================================
        # POSITION DISTANCES FROM TEMPLE (standard hours)
        # ========================================================
        self.POSITION_DISTANCE = {
            "Alipiri":            24.0,
            "Toll Gate":          22.0,
            "Silathoranam":       18.0,   # EXTREME days only!
            "Octopus Circle":     13.0,   # FAR
            "Krishnateja Circle": 8.5,    # NEAR temple
            "vqc_entry":          5.0,
            "vqc_middle":         3.0,
            "vqc_exit":           1.5,
        }

        self.DISPLAY_NAMES = {
            "Alipiri":            "Alipiri (Foot of Hills)",
            "Toll Gate":          "Toll Gate",
            "Silathoranam":       "Silathoranam (EXTREME days)",
            "Octopus Circle":     "Octopus Circle",
            "Krishnateja Circle": "Krishnateja Circle",
            "vqc_entry":          "VQC Entry Gate",
            "vqc_middle":         "VQC Middle",
            "vqc_exit":           "VQC Exit (Almost at temple!)",
        }

        # ========================================================
        # 🆕 NEW DEVOTEE FRIENDLY LOCATION GUIDE!
        # Every place explained for first-time visitors:
        # - What it looks like
        # - How far from temple
        # - How to reach from Bus Stand / Railway Station
        # - What landmarks to look for
        # ========================================================
        self.LOCATION_INFO = {
            "Krishnateja Circle": {
                "simple":      "A big traffic circle (roundabout) on Tirumala hill",
                "distance":    "About 1.5 km before the main temple",
                "look_for":    "Big roundabout with TTD security checkpost and crowd barriers",
                "from_bus":    "Take FREE TTD bus from Tirupati Bus Stand → tell conductor 'Krishnateja Circle' → they will stop",
                "from_train":  "Tirupati Railway Station → walk 5 min to Bus Stand → FREE TTD bus → Krishnateja Circle",
                "from_alipiri":"After climbing Alipiri steps, walk 10 min on main road → you will see the big circle",
                "facilities":  ["Drinking Water 💧", "Toilets 🚻", "TTD Security Post 👮", "Small Shops 🏪"],
            },
            "Octopus Circle": {
                "simple":      "A large junction circle with roads going in many directions (like octopus arms!)",
                "distance":    "About 4 km before the main temple",
                "look_for":    "Huge junction where multiple roads meet, long queue barriers visible",
                "from_bus":    "FREE TTD bus from Bus Stand → ask for 'Octopus Circle'",
                "from_train":  "Railway Station → Bus Stand → FREE TTD bus → Octopus Circle",
                "from_alipiri":"After Alipiri steps, take the main road downhill direction for 25 min",
                "facilities":  ["Drinking Water 💧", "Toilets 🚻", "Police Booth 👮"],
            },
            "Silathoranam": {
                "simple":      "Famous natural rock arch (stone rainbow!) - a tourist spot on the hill",
                "distance":    "About 6 km before the main temple",
                "look_for":    "Natural stone arch formation, garden area, VERY long queues on extreme days",
                "from_bus":    "FREE TTD bus → ask for 'Silathoranam' - everyone knows this tourist spot",
                "from_train":  "Railway Station → Bus Stand → FREE TTD bus → Silathoranam",
                "from_alipiri":"This is far - take the free bus instead of walking",
                "facilities":  ["Drinking Water 💧", "Toilets 🚻", "Garden View Point 📷", "Medical Aid 🏥"],
            },
            "Alipiri": {
                "simple":      "The foot of the hills - where the walking steps to Tirumala begin",
                "distance":    "At the BOTTOM of the hill (7 hills climb!)",
                "look_for":    "Huge Alipiri arch gate, footsteps starting point, lots of shops",
                "from_bus":    "Local city bus/auto from anywhere in Tirupati → 'Alipiri'",
                "from_train":  "Auto from Railway Station (10 min) → Alipiri gate",
                "from_alipiri":"You are already here!",
                "facilities":  ["Free Luggage Counter 🎒", "Toilets 🚻", "Shops 🏪", "Medical 🏥", "Free Chappal Stand 👡"],
            },
            "vqc_entry": {
                "simple":      "The main entry gate of Vaikuntam Queue Complex (big building near temple)",
                "distance":    "Right next to the main temple",
                "look_for":    "Large building entrance with 'VQC' boards and security scanning",
                "from_bus":    "FREE TTD bus → final stop near temple → follow crowd to VQC",
                "from_train":  "Railway Station → Bus Stand → FREE bus to Tirumala → VQC",
                "from_alipiri":"After steps, walk toward temple towers - VQC is beside it",
                "facilities":  ["Full Facilities Inside 🏢", "Annaprasadam 🍛", "Medical 🏥", "Lockers 🔒"],
            },
            "vqc_middle": {
                "simple":      "Inside the VQC building compartments",
                "distance":    "Inside the queue complex building",
                "look_for":    "You are inside! Halls with seats, TV screens, fans",
                "from_bus":    "Already inside the system",
                "from_train":  "Already inside the system",
                "from_alipiri":"Already inside the system",
                "facilities":  ["Seats 💺", "Food Service 🍛", "Water 💧", "Toilets 🚻", "TV 📺"],
            },
            "vqc_exit": {
                "simple":      "The exit door of VQC - temple is RIGHT THERE!",
                "distance":    "2 minutes from temple entry!",
                "look_for":    "Exit gates opening toward temple, you can HEAR the temple chants!",
                "from_bus":    "Already inside the system",
                "from_train":  "Already inside the system",
                "from_alipiri":"Already inside the system",
                "facilities":  ["Temple in sight! 🛕"],
            },
        }

    # ========================================================
    # FUNCTION 1: NEW DEVOTEE WAIT + FULL GUIDE
    # ========================================================
    def new_devotee_wait(self, total_wait_hours, tail_location):
        """
        "Where the queue starts, there the devotee will be!"
        PLUS full beginner guide for that location!
        """
        full_hours = int(total_wait_hours)
        minutes    = int((total_wait_hours - full_hours) * 60)

        return {
            "joins_at": tail_location,
            "display":  f"{full_hours} Hours {minutes} Mins",
            "hours":    full_hours,
            "minutes":  minutes,
            "route":    self.get_pilgrim_route(tail_location),
            "guide":    self.LOCATION_INFO.get(tail_location, {})
        }

    # ========================================================
    # FUNCTION 2: PILGRIM ROUTE (FORWARD ONLY)
    # ========================================================
    def get_pilgrim_route(self, start_location):
        ROUTE = [
            ("Alipiri",            "🚗 Alipiri"),
            ("Toll Gate",          "🛣️ Toll Gate"),
            ("Silathoranam",       "🌿 Silathoranam"),
            ("Octopus Circle",     "⭕ Octopus Circle"),
            ("Krishnateja Circle", "📍 Krishnateja Circle"),
            ("vqc_entry",          "🚪 VQC Entry Gate"),
            ("vqc_middle",         "🏢 Inside VQC Compartments"),
            ("vqc_exit",           "🚶 VQC Exit"),
            ("temple",             "🛕 TEMPLE DARSHAN 🙏"),
        ]

        keys = [k for k, _ in ROUTE]

        if start_location not in keys:
            start_location = "Krishnateja Circle"

        start_idx = keys.index(start_location)
        return [label for _, label in ROUTE[start_idx:]]

    # ========================================================
    # FUNCTION 3: VALID IN-QUEUE POSITIONS
    # ========================================================
    def get_valid_positions(self, tail_location):
        tail_dist = self.POSITION_DISTANCE.get(tail_location, 8.5)

        valid = [
            (loc, dist)
            for loc, dist in self.POSITION_DISTANCE.items()
            if dist <= tail_dist
        ]

        valid.sort(key=lambda x: x[1], reverse=True)
        return valid

    # ========================================================
    # FUNCTION 4: IN-QUEUE DEVOTEE WAIT
    # ========================================================
    def calculate_your_wait(self, total_wait_hours, your_location, tail_location):
        your_distance = self.POSITION_DISTANCE.get(your_location, 8.5)
        tail_distance = self.POSITION_DISTANCE.get(tail_location, 8.5)

        if your_distance >= tail_distance:
            your_hours = total_wait_hours
        else:
            your_hours = total_wait_hours * (your_distance / tail_distance)

        full_hours = int(your_hours)
        minutes    = int((your_hours - full_hours) * 60)

        return {
            "hours":   full_hours,
            "minutes": minutes,
            "display": f"{full_hours} Hours {minutes} Mins",
            "route":   self.get_pilgrim_route(your_location),
            "guide":   self.LOCATION_INFO.get(your_location, {})
        }

    # ========================================================
    # FUNCTION 5: COMPARTMENT BREAKDOWN
    # ========================================================
    def build_compartment_breakdown(self, active_compartments, pilgrims_waiting):
        compartments = []

        for comp_num in range(1, self.TOTAL_COMPARTMENTS + 1):

            if comp_num < active_compartments:
                compartments.append({
                    "number":   comp_num,
                    "floor":    self.get_floor(comp_num),
                    "people":   self.COMPARTMENT_CAPACITY,
                    "capacity": self.COMPARTMENT_CAPACITY,
                    "percent":  100,
                    "status":   "FULL",
                    "emoji":    "🔴",
                    "display":  f"🔴 FULL        ({self.COMPARTMENT_CAPACITY}/{self.COMPARTMENT_CAPACITY} people)"
                })

            elif comp_num == active_compartments:
                full_comps_people = (active_compartments - 1) * self.COMPARTMENT_CAPACITY
                people            = pilgrims_waiting - full_comps_people
                people            = max(0, min(people, self.COMPARTMENT_CAPACITY))
                percent           = int((people / self.COMPARTMENT_CAPACITY) * 100)

                if percent >= 75:
                    status, emoji = "ALMOST FULL", "🟠"
                elif percent >= 50:
                    status, emoji = "PARTIAL", "🟡"
                else:
                    status, emoji = "LOW", "🟢"

                compartments.append({
                    "number":   comp_num,
                    "floor":    self.get_floor(comp_num),
                    "people":   people,
                    "capacity": self.COMPARTMENT_CAPACITY,
                    "percent":  percent,
                    "status":   status,
                    "emoji":    emoji,
                    "display":  f"{emoji} {status:12} ({people}/{self.COMPARTMENT_CAPACITY} people | {percent}% full)"
                })

            else:
                compartments.append({
                    "number":   comp_num,
                    "floor":    self.get_floor(comp_num),
                    "people":   0,
                    "capacity": self.COMPARTMENT_CAPACITY,
                    "percent":  0,
                    "status":   "EMPTY",
                    "emoji":    "🟢",
                    "display":  f"🟢 EMPTY       (0/{self.COMPARTMENT_CAPACITY} people)"
                })

        return compartments

    # ========================================================
    # FUNCTION 6: GET FLOOR NUMBER
    # ========================================================
    def get_floor(self, comp_num):
        if comp_num <= 11:
            return "Ground Floor"
        elif comp_num <= 21:
            return "First Floor"
        else:
            return "Second Floor"

    # ========================================================
    # FUNCTION 7: VQC HEATMAP GRID
    # ========================================================
    def build_vqc_heatmap(self, active_compartments, pilgrims_waiting):
        import numpy as np

        grid       = np.zeros((3, 11))
        comp_count = 0

        for row in range(3):
            for col in range(11):
                comp_count += 1

                if comp_count < active_compartments:
                    grid[row][col] = 100
                elif comp_count == active_compartments:
                    full_comps_people = (active_compartments - 1) * self.COMPARTMENT_CAPACITY
                    people            = max(0, pilgrims_waiting - full_comps_people)
                    grid[row][col]    = int((people / self.COMPARTMENT_CAPACITY) * 100)
                else:
                    grid[row][col] = 0

        return grid

    # ========================================================
    # FUNCTION 8: OUTDOOR CROWD (TAIL-AWARE, CORRECT ORDER)
    # ========================================================
    def calculate_outdoor_crowd(self, queue_location, pilgrims_waiting, total_wait_hours):
        total_in_system = int(total_wait_hours * self.TEMPLE_FLOW_RATE)
        inside_vqc      = pilgrims_waiting
        outside_line    = max(0, total_in_system - inside_vqc)

        tail = queue_location

        if tail == "Krishnateja Circle":
            active = {"krishnateja": 1.00}

        elif tail == "Octopus Circle":
            active = {"krishnateja": 0.45, "octopus": 0.55}

        elif tail == "Silathoranam":
            # EXTREME DAY! Silathoranam OPEN!
            active = {"krishnateja": 0.25, "octopus": 0.35, "silathoranam": 0.40}

        elif tail in ["Alipiri", "Toll Gate"]:
            active = {"krishnateja": 0.25, "octopus": 0.35, "silathoranam": 0.40}

        else:
            active = {}

        fills = {"krishnateja": 0, "octopus": 0, "silathoranam": 0}
        for segment, weight in active.items():
            fills[segment] = int(outside_line * weight)

        return {
            "total_in_system":   total_in_system,
            "inside_vqc":        inside_vqc,
            "outside_line":      outside_line,
            "krishnateja_fill":  fills["krishnateja"],
            "octopus_fill":      fills["octopus"],
            "silathoranam_fill": fills["silathoranam"],
            "silathoranam_open": tail in ["Silathoranam", "Alipiri", "Toll Gate"],
            "is_outdoor":        outside_line > 0,
            "tail_location":     tail
        }

    # ========================================================
    # FUNCTION 9: BEST TIME TO VISIT
    # ========================================================
    def calculate_best_time_today(self, current_wait_hours):
        current_day = datetime.now().weekday()
        is_weekend  = current_day >= 4

        time_slots = [
            {"hour": 3,  "label": "3:00 AM",  "multiplier": 0.30},
            {"hour": 5,  "label": "5:00 AM",  "multiplier": 0.40},
            {"hour": 7,  "label": "7:00 AM",  "multiplier": 0.70},
            {"hour": 9,  "label": "9:00 AM",  "multiplier": 1.00},
            {"hour": 12, "label": "12:00 PM", "multiplier": 0.80},
            {"hour": 15, "label": "3:00 PM",  "multiplier": 0.60},
            {"hour": 18, "label": "6:00 PM",  "multiplier": 0.90},
            {"hour": 21, "label": "9:00 PM",  "multiplier": 0.70},
        ]

        hourly_predictions = []
        best_slot          = None
        best_hours         = 999

        for slot in time_slots:
            multiplier = slot["multiplier"]
            if is_weekend:
                multiplier *= 1.25

            predicted_wait = current_wait_hours * multiplier
            full_h         = int(predicted_wait)
            mins           = int((predicted_wait - full_h) * 60)

            slot_data = {
                "time":   slot["label"],
                "wait":   f"{full_h}H {mins}M",
                "hours":  predicted_wait,
                "status": self.get_crowd_status(predicted_wait)
            }
            hourly_predictions.append(slot_data)

            if predicted_wait < best_hours:
                best_hours = predicted_wait
                best_slot  = slot_data

        return {
            "best_time":          best_slot,
            "hourly_predictions": hourly_predictions,
            "is_weekend":         is_weekend
        }

    # ========================================================
    # FUNCTION 10: CROWD STATUS
    # ========================================================
    def get_crowd_status(self, wait_hours):
        if wait_hours >= 20:
            return {"label": "EXTREME",   "color": "#FF0000", "emoji": "🔴"}
        elif wait_hours >= 15:
            return {"label": "VERY HIGH", "color": "#FF4500", "emoji": "🟠"}
        elif wait_hours >= 10:
            return {"label": "HIGH",      "color": "#FF6B00", "emoji": "🟡"}
        elif wait_hours >= 6:
            return {"label": "MODERATE",  "color": "#FFD700", "emoji": "🟡"}
        elif wait_hours >= 3:
            return {"label": "LOW",       "color": "#00FF88", "emoji": "🟢"}
        else:
            return {"label": "VERY LOW",  "color": "#00FF00", "emoji": "🟢"}

    # ========================================================
    # MASTER PROCESS
    # ========================================================
    def process(self, scraped_data, your_location=None):
        wait_times   = scraped_data.get("wait_times", {})
        free_darshan = wait_times.get("free_darshan", {})
        total_wait   = free_darshan.get("avg", 18)

        active_comp  = scraped_data.get("active_compartments", 21)
        total_comp   = scraped_data.get("total_compartments",  31)
        pilgrims     = scraped_data.get("pilgrims_waiting",    8360)
        tail         = scraped_data.get("queue_location", "Krishnateja Circle")

        new_devotee = self.new_devotee_wait(total_wait, tail)

        your_wait = None
        if your_location:
            your_wait = self.calculate_your_wait(total_wait, your_location, tail)

        compartments = self.build_compartment_breakdown(active_comp, pilgrims)
        vqc_grid     = self.build_vqc_heatmap(active_comp, pilgrims)
        outdoor      = self.calculate_outdoor_crowd(tail, pilgrims, total_wait)
        best_time    = self.calculate_best_time_today(total_wait)
        status       = self.get_crowd_status(total_wait)

        return {
            "scraped":        scraped_data,
            "new_devotee":    new_devotee,
            "your_wait":      your_wait,
            "your_location":  your_location,
            "compartments":   compartments,
            "vqc_grid":       vqc_grid,
            "active_comp":    active_comp,
            "total_comp":     total_comp,
            "outdoor":        outdoor,
            "best_time":      best_time,
            "status":         status,
            "total_wait":     total_wait,
        }


# ========================================================
# HELPER: Print the New Devotee Guide nicely
# ========================================================
def print_location_guide(guide):
    if not guide:
        return
    print(f"   ℹ️  WHAT IS IT : {guide.get('simple', 'N/A')}")
    print(f"   📏 DISTANCE    : {guide.get('distance', 'N/A')}")
    print(f"   👀 LOOK FOR    : {guide.get('look_for', 'N/A')}")
    print("   ─────────────────────────────────")
    print("   🧭 HOW TO REACH:")
    print(f"      🚌 From Bus Stand : {guide.get('from_bus', 'N/A')}")
    print(f"      🚂 From Railway   : {guide.get('from_train', 'N/A')}")
    print(f"      🚶 From Alipiri   : {guide.get('from_alipiri', 'N/A')}")
    print("   ─────────────────────────────────")
    facilities = guide.get('facilities', [])
    if facilities:
        print(f"   🏪 FACILITIES  : {' | '.join(facilities)}")


# ========================================================
# TEST WITH REAL SCRAPER DATA
# ========================================================
if __name__ == "__main__":
    from scraper import TTDLiveScraper

    print("🌐 Fetching REAL data from tirumalainfo.com...")
    scraper   = TTDLiveScraper()
    real_data = scraper.get_live_data()

    engine = TTDCrowdEngine()

    # ========================================================
    # SCREEN 1: NEW DEVOTEE (WITH BEGINNER GUIDE!)
    # ========================================================
    result = engine.process(real_data)

    print("\n" + "="*55)
    print("🛕 TTD LIVE - MAIN SCREEN")
    print("="*55)
    print(f"📡 Source         : {real_data['source']}")
    print(f"🕒 Time           : {real_data['timestamp']}")
    print(f"🌡️ Temp           : {real_data['weather'].get('temperature','N/A')}°C | AQI: {real_data['weather'].get('aqi','N/A')}")
    print("-"*55)
    print(f"📍 QUEUE STARTS AT: {result['new_devotee']['joins_at']}")
    print(f"   (New devotees automatically join here!)")
    print("-"*55)
    print("🆕 FIRST TIME IN TIRUPATI? HERE IS YOUR GUIDE:")
    print("-"*55)
    print_location_guide(result['new_devotee']['guide'])
    print("-"*55)
    print(f"⏱️ IF YOU JOIN NOW:")
    free  = real_data['wait_times'].get('free_darshan', {})
    ssd   = real_data['wait_times'].get('ssd_token', {})
    rs300 = real_data['wait_times'].get('rs300', {})
    print(f"   🔴 Free Darshan : {free.get('display', 'N/A')}")
    print(f"   🟡 SSD Token    : {ssd.get('display',  'N/A')}")
    print(f"   🟢 Rs.300       : {rs300.get('display','N/A')}")
    print("-"*55)
    print("🚶 YOUR JOURNEY (FORWARD ONLY):")
    print("   " + " → ".join(result['new_devotee']['route']))
    print("-"*55)
    print(f"🚨 Crowd Status   : {result['status']['emoji']} {result['status']['label']}")
    print(f"👥 Pilgrims In VQC: {real_data['pilgrims_waiting']:,}")
    print(f"✅ Darshan Done   : {real_data['darshan_completed']:,}")
    print(f"🚪 Compartments   : {real_data['active_compartments']}/{real_data['total_compartments']}")
    print("="*55)

    # ========================================================
    # SCREEN 2: ALREADY IN QUEUE?
    # ========================================================
    print("\n🚶 ARE YOU ALREADY INSIDE THE QUEUE? (y/n): ", end="")
    already_in = input().strip().lower()

    if already_in == "y":
        tail_location = real_data['queue_location']
        valid = engine.get_valid_positions(tail_location)

        print("\n" + "="*55)
        print("📍 WHERE ARE YOU NOW? (Current position)")
        print(f"   (Queue tail today: {tail_location})")
        print("="*55)

        for i, (loc, dist) in enumerate(valid, 1):
            print(f"   {i} = {engine.DISPLAY_NAMES[loc]}")
        print("="*55)

        choice = input("Enter your choice: ").strip()

        try:
            idx = int(choice) - 1
            your_location = valid[idx][0]
        except (ValueError, IndexError):
            your_location = tail_location

        result = engine.process(real_data, your_location=your_location)

        print("\n" + "="*55)
        print("⏳ YOUR REMAINING JOURNEY")
        print("="*55)
        print(f"📍 Your Position  : {engine.DISPLAY_NAMES.get(your_location, your_location)}")
        print(f"📍 Queue Tail     : {tail_location}")
        print(f"⏳ REMAINING WAIT : {result['your_wait']['display']}")
        print("-"*55)
        print("ℹ️ ABOUT THIS SPOT:")
        print_location_guide(result['your_wait']['guide'])
        print("-"*55)
        print("🚶 YOUR ROUTE FORWARD:")
        print("   " + " → ".join(result['your_wait']['route']))
        print("="*55)

    # ========================================================
    # FULL DETAILS
    # ========================================================
    print("\n" + "="*55)
    print("🏢 VQC COMPARTMENTS (REAL DATA):")
    print("="*55)

    current_floor = ""
    for comp in result['compartments']:
        if comp['floor'] != current_floor:
            current_floor = comp['floor']
            print(f"\n  📌 {current_floor}:")
        print(f"     Compartment {comp['number']:02d}: {comp['display']}")

    print("\n" + "="*55)
    print("🌿 OUTDOOR QUEUE (CORRECT GEOGRAPHY!):")
    print("   Order: VQC → Krishnateja → Octopus → Silathoranam")
    print("="*55)
    outdoor = result['outdoor']
    print(f"   👥 TOTAL In System : {outdoor['total_in_system']:,} people")
    print(f"      (Real wait {result['total_wait']}hrs x 2500/hr)")
    print(f"   🏢 Inside VQC      : {outdoor['inside_vqc']:,} (REAL scraped)")
    print(f"   🌿 OUTSIDE LINE    : {outdoor['outside_line']:,} people")
    print(f"   📍 Queue TAIL at   : {outdoor['tail_location']}")
    print("-"*55)
    print("   SEGMENT STATUS (temple → outward):")
    if outdoor['krishnateja_fill'] > 0:
        print(f"      📍 Krishnateja  : {outdoor['krishnateja_fill']:,} ✅ ACTIVE")
    else:
        print(f"      📍 Krishnateja  : 0 (empty)")
    if outdoor['octopus_fill'] > 0:
        print(f"      ⭕ Octopus      : {outdoor['octopus_fill']:,} ✅ ACTIVE")
    else:
        print(f"      ⭕ Octopus      : 0 (empty - beyond tail)")
    if outdoor['silathoranam_fill'] > 0:
        print(f"      🌿 Silathoranam : {outdoor['silathoranam_fill']:,} 🚨 EXTREME DAY - OPEN!")
    else:
        print(f"      🌿 Silathoranam : 0 (CLOSED - opens only on extreme days)")
    print("="*55)
    print("💡 BEST TIME TO VISIT TODAY:")
    print("="*55)
    best = result['best_time']['best_time']
    print(f"   ✅ Best Time : {best['time']}")
    print(f"   ⏱️ Wait Time : {best['wait']}")
    print("-"*55)
    print("📊 FULL DAY PREDICTIONS:")
    for slot in result['best_time']['hourly_predictions']:
        emoji = slot['status']['emoji']
        print(f"   {slot['time']:10} → Wait: {slot['wait']:10} {emoji} {slot['status']['label']}")
    print("="*55)
