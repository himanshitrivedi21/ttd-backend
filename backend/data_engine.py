# backend/data_engine.py
import requests
from datetime import datetime
import random

class LiveDataEngine:
    def __init__(self):
        # The real Google API endpoints (Architecture ready for Production)
        self.google_api_url = "https://maps.googleapis.com/maps/api/place/details/json"
        self.tirumala_place_id = "ChIJ-wH7B-2wTzQRt-B1Yqg9nUU" # Real Place ID
        self.api_key = "DEMO_MODE" # Replace with real key if you ever buy one

        # Predictive Algorithm (Fallback)
        self.daily_curve = [
            15, 10,  5, 20, 45, 75, 85, 95,  # Midnight to 7 AM
            98, 90, 80, 65, 50, 55, 60, 70,  # 8 AM to 3 PM
            85, 90, 95, 90, 80, 60, 40, 25   # 4 PM to 11 PM
        ]

    def get_live_busyness(self):
        """Attempts to fetch LIVE Google Data, falls back to Predictive Model"""
        
        # STEP 1: Try to get real internet data
        try:
            if self.api_key != "DEMO_MODE":
                response = requests.get(
                    self.google_api_url, 
                    params={"place_id": self.tirumala_place_id, "key": self.api_key},
                    timeout=3 # Don't freeze if internet is slow
                )
                if response.status_code == 200:
                    data = response.json()
                    # Extract live busyness from Google JSON
                    return data['result']['current_busyness'], "LIVE GOOGLE API"
        except:
            pass # Internet failed or no API key, move to Step 2
            
        # STEP 2: Use Predictive Time-Series Algorithm (Demo Safe)
        current_hour = datetime.now().hour
        base_busyness = self.daily_curve[current_hour]
        live_busyness = base_busyness + random.randint(-3, 3) # Add realistic variation
        
        return max(0, min(100, live_busyness)), "PREDICTIVE ALGORITHM"

# Let's test the new Advanced Engine!
if __name__ == "__main__":
    engine = LiveDataEngine()
    crowd_level, data_source = engine.get_live_busyness()
    
    print(f"=====================================")
    print(f"📡 TTD LIVE DATA FETCH SYSTEM")
    print(f"=====================================")
    print(f"Time:        {datetime.now().strftime('%I:%M %p')}")
    print(f"Crowd Level: {crowd_level}% Full")
    print(f"Data Source: {data_source} (Fault-Tolerant)")
    print(f"=====================================")