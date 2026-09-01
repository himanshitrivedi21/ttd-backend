# backend/config.py
# ========================================================
# TTD SMART CROWD SYSTEM - CONFIGURATION RULES
# ========================================================

# 1. QUEUE CAPACITIES (Real-world numbers)
VQC_MAX_CAPACITY = 14000
SILATHORANAM_MAX = 8000
TOTAL_SYSTEM_MAX = VQC_MAX_CAPACITY + SILATHORANAM_MAX # 22,000

# 2. WAIT TIME CALCULATOR SETTINGS (For the 50/50 feature)
# Time it takes per 1000 people to clear the temple
MINUTES_PER_1000_PEOPLE = {
    "FREE_DARSHAN": 45,     # 45 mins per 1000 people
    "RS_300_TICKET": 20,    # 20 mins per 1000 people (Faster)
    "VIP_BREAK": 10         # 10 mins per 1000 people (Fastest)
}

# 3. COMPARTMENT GRID (For the Heatmap)
VQC_COMPARTMENTS = {
    "VQC_1A": {"capacity": 2500, "row": 0, "col": 0},
    "VQC_1B": {"capacity": 2500, "row": 0, "col": 1},
    "VQC_1C": {"capacity": 2000, "row": 0, "col": 2},
    "VQC_2A": {"capacity": 2500, "row": 1, "col": 0},
    "VQC_2B": {"capacity": 2500, "row": 1, "col": 1},
    "VQC_2C": {"capacity": 2000, "row": 1, "col": 2},
}

# 4. OUTDOOR SPILLOVER (Silathoranam)
SILATHORANAM_TRACKS = {
    "TRACK_A": {"capacity": 2000, "row": 0, "col": 0},
    "TRACK_B": {"capacity": 2000, "row": 0, "col": 1},
    "TRACK_C": {"capacity": 2000, "row": 1, "col": 0},
    "TRACK_D": {"capacity": 2000, "row": 1, "col": 1},
}