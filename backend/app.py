# app.py — TTD COMPLETE API + BUILT-IN PAGES (single file, cloud-proof!)
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import time

from scraper import TTDLiveScraper
from engine import TTDCrowdEngine

app = Flask(__name__)
CORS(app)

cache = {"data": None, "result": None, "last_fetch": 0, "CACHE_MINUTES": 15}
scraper = TTDLiveScraper()
engine = TTDCrowdEngine()

def get_fresh_result(your_location=None):
    now = time.time()
    age = (now - cache["last_fetch"]) / 60
    if cache["result"] is None or age > cache["CACHE_MINUTES"]:
        print("Fetching FRESH data...")
        real_data = scraper.get_live_data()
        cache["data"] = real_data
        cache["last_fetch"] = now
        cache["result"] = engine.process(real_data)
    if your_location:
        return engine.process(cache["data"], your_location=your_location)
    return cache["result"]

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "service": "TTD API",
                    "time": datetime.now().strftime('%d-%m-%Y %I:%M %p')})

@app.route('/api/live', methods=['GET'])
def live():
    try:
        result = get_fresh_result()
        data = result["scraped"]
        free = data['wait_times'].get('free_darshan', {})
        ssd = data['wait_times'].get('ssd_token', {})
        rs300 = data['wait_times'].get('rs300', {})
        return jsonify({
            "status": "success", "timestamp": data["timestamp"], "source": data["source"],
            "queue_starts_at": result["new_devotee"]["joins_at"],
            "wait_if_join_now": result["new_devotee"]["display"],
            "wait_times": {"free_darshan": free.get('display', 'N/A'),
                           "ssd_token": ssd.get('display', 'N/A'),
                           "rs300": rs300.get('display', 'N/A')},
            "location_guide": result["new_devotee"]["guide"],
            "journey_route": result["new_devotee"]["route"],
            "crowd_status": result["status"], "crowd_level": data["crowd_level"],
            "pilgrims_waiting": data["pilgrims_waiting"],
            "darshan_completed": data["darshan_completed"],
            "active_compartments": data["active_compartments"],
            "total_compartments": data["total_compartments"],
            "weather": data["weather"], "outdoor": result["outdoor"],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/journey', methods=['GET'])
def journey():
    try:
        your_location = request.args.get('location', None)
        if not your_location:
            result = get_fresh_result()
            tail = result["scraped"]["queue_location"]
            valid = engine.get_valid_positions(tail)
            return jsonify({"status": "success", "queue_tail": tail,
                "valid_positions": [{"id": loc, "name": engine.DISPLAY_NAMES[loc]} for loc, d in valid]})
        result = get_fresh_result(your_location=your_location)
        return jsonify({"status": "success", "your_position": your_location,
            "position_name": engine.DISPLAY_NAMES.get(your_location, your_location),
            "queue_tail": result["scraped"]["queue_location"],
            "remaining_wait": result["your_wait"]["display"],
            "route_forward": result["your_wait"]["route"],
            "spot_guide": result["your_wait"]["guide"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/compartments', methods=['GET'])
def compartments():
    try:
        result = get_fresh_result()
        return jsonify({"status": "success", "active": result["active_comp"],
            "total": result["total_comp"], "compartments": result["compartments"],
            "heatmap_grid": result["vqc_grid"].tolist()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/outdoor', methods=['GET'])
def outdoor():
    try:
        result = get_fresh_result()
        od = result["outdoor"]
        return jsonify({"status": "success", "total_in_system": od["total_in_system"],
            "inside_vqc": od["inside_vqc"], "outside_line": od["outside_line"],
            "tail_location": od["tail_location"],
            "segments": {
                "krishnateja": {"people": od["krishnateja_fill"], "status": "ACTIVE" if od["krishnateja_fill"] > 0 else "EMPTY"},
                "octopus": {"people": od["octopus_fill"], "status": "ACTIVE" if od["octopus_fill"] > 0 else "EMPTY"},
                "silathoranam": {"people": od["silathoranam_fill"], "status": "OPEN" if od["silathoranam_open"] else "CLOSED"}}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/forecast', methods=['GET'])
def forecast():
    try:
        result = get_fresh_result()
        bt = result["best_time"]
        return jsonify({"status": "success", "is_weekend": bt["is_weekend"],
                        "best_time": bt["best_time"], "hourly": bt["hourly_predictions"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "<h1 style='background:#0f1419;color:#00FF88;padding:40px;font-family:Arial'>🛕 TTD API LIVE! 🙏<br><small style='color:#FFD700'>Pages: /dashboard /places /rooms /phrases</small></h1>"

# ==================== BUILT-IN HTML PAGES ====================

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Heatmap</title>
<style>body{background:#0f1419;color:#fff;font-family:Arial;padding:12px;margin:0}
.hd{background:linear-gradient(135deg,#FF6B00,#FF8C00);padding:16px;border-radius:12px;text-align:center;margin-bottom:12px}
.hd b{color:#00FF88;font-size:22px}
.info{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.box2{background:#1a2332;padding:12px;border-radius:10px;text-align:center}
.box2 .n{color:#FF6B00;font-size:20px;font-weight:bold}
#grid{display:grid;grid-template-columns:repeat(11,1fr);gap:4px;background:#1a2332;padding:10px;border-radius:12px}
.fl{grid-column:1/-1;color:#FFD700;font-size:12px;font-weight:bold;margin-top:6px}
.box{aspect-ratio:1;border-radius:5px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:10px;font-weight:bold}
.full{background:#FF0000}.almost{background:#FF6B00}.part{background:#FFD700;color:#000}.low{background:#88FF00;color:#000}.empty{background:#2D3561;color:#777}
.leg{text-align:center;font-size:12px;color:#888;margin-top:10px}
#upd{text-align:center;color:#00FF88;font-size:12px;margin-top:8px}</style></head><body>
<div class="hd">🛕 VQC LIVE HEATMAP<br>Queue starts at: <b id="qs">...</b><br>Wait now: <b id="wait" style="color:#FFD700">...</b></div>
<div class="info">
<div class="box2"><div class="n" id="pil">...</div>👥 In VQC</div>
<div class="box2"><div class="n" id="comp">...</div>🚪 Rooms Active</div>
</div>
<div id="grid"></div>
<div class="leg">🔴 FULL 🟠 ALMOST 🟡 PARTIAL ⬛ EMPTY</div>
<div id="upd">Loading...</div>
<script>
function cls(s){if(s==='FULL')return 'full';if(s==='ALMOST FULL')return 'almost';if(s==='PARTIAL')return 'part';if(s==='LOW')return 'low';return 'empty'}
async function load(){try{
const[live,comps]=await Promise.all([fetch('/api/live').then(r=>r.json()),fetch('/api/compartments').then(r=>r.json())]);
document.getElementById('qs').textContent=live.queue_starts_at;
document.getElementById('wait').textContent=live.wait_if_join_now;
document.getElementById('pil').textContent=live.pilgrims_waiting.toLocaleString();
document.getElementById('comp').textContent=live.active_compartments+'/'+live.total_compartments;
const g=document.getElementById('grid');g.innerHTML='';let f='';
comps.compartments.forEach(c=>{if(c.floor!==f){f=c.floor;const l=document.createElement('div');l.className='fl';l.textContent='📌 '+f;g.appendChild(l)}
const b=document.createElement('div');b.className='box '+cls(c.status);b.innerHTML=c.number+'<br><small>'+c.percent+'%</small>';g.appendChild(b)});
document.getElementById('upd').textContent='Updated: '+live.timestamp;
}catch(e){document.getElementById('upd').textContent='Loading...'}}
load();setInterval(load,60000);
</script></body></html>"""

PLACES_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Places</title>
<style>body{background:#0f1419;color:#fff;font-family:Arial;padding:12px;margin:0}
.hd{background:linear-gradient(135deg,#FF6B00,#FF8C00);padding:16px;border-radius:12px;text-align:center;margin-bottom:12px}
.c{background:#1a2332;border-radius:12px;margin-bottom:14px;overflow:hidden;border-left:4px solid #FF6B00}
.i{padding:12px}.n{color:#FFD700;font-size:17px;font-weight:bold}.m{color:#00FF88;font-size:12px;margin:5px 0}.d{color:#ccc;font-size:13px;line-height:1.5}
a{display:inline-block;background:#FF6B00;color:#fff;padding:8px 16px;border-radius:16px;text-decoration:none;font-size:13px;font-weight:bold;margin-top:6px}
iframe{width:100%;height:200px;border:0}</style></head><body>
<div class="hd"><h1 style="margin:0">🗺️ Sacred Places</h1>Tirumala & Tirupati</div>
<div class="c"><div class="i"><div class="n">🛕 Sri Venkateswara Temple</div><div class="m">📍 Main Temple</div><div class="d">The divine Ananda Nilayam. Free Annaprasadam nearby all day.</div><a href="https://www.google.com/maps/dir/?api=1&destination=Sri+Venkateswara+Temple+Tirumala">🧭 Navigate (3D)</a></div><iframe loading="lazy" src="https://maps.google.com/maps?q=Sri+Venkateswara+Temple+Tirumala&z=16&output=embed"></iframe></div>
<div class="c"><div class="i"><div class="n">🌿 Silathoranam</div><div class="m">📍 1 km • Natural Rock Arch</div><div class="d">Millions of years old natural arch. Best at sunset!</div><a href="https://www.google.com/maps/dir/?api=1&destination=Silathoranam+Tirumala">🧭 Navigate (3D)</a></div><iframe loading="lazy" src="https://maps.google.com/maps?q=Silathoranam+Tirumala&z=16&output=embed"></iframe></div>
<div class="c"><div class="i"><div class="n">💧 Papavinasam</div><div class="m">📍 5 km • Holy Waterfall</div><div class="d">Sacred falls — a bath here washes away sins. Changing rooms available.</div><a href="https://www.google.com/maps/dir/?api=1&destination=Papavinasam+Tirumala">🧭 Navigate (3D)</a></div><iframe loading="lazy" src="https://maps.google.com/maps?q=Papavinasam+Tirumala&z=16&output=embed"></iframe></div>
<div class="c"><div class="i"><div class="n">💧 Akasa Ganga</div><div class="m">📍 3 km • Temple Water Source</div><div class="d">Holy falls supplying water for the Lord's abhishekam. Serene, less crowded.</div><a href="https://www.google.com/maps/dir/?api=1&destination=Akasa+Ganga+Tirumala">🧭 Navigate (3D)</a></div><iframe loading="lazy" src="https://maps.google.com/maps?q=Akasa+Ganga+Tirumala&z=16&output=embed"></iframe></div>
<div class="c"><div class="i"><div class="n">🐒 Japali Hanuman</div><div class="m">📍 5 km • Forest Temple</div><div class="d">Where Hanuman meditated. Quiet escape from crowds.</div><a href="https://www.google.com/maps/dir/?api=1&destination=Japali+Hanuman+Tirumala">🧭 Navigate (3D)</a></div><iframe loading="lazy" src="https://maps.google.com/maps?q=Japali+Hanuman+Temple+Tirumala&z=16&output=embed"></iframe></div>
<div class="c"><div class="i"><div class="n">💧 Kapila Theertham</div><div class="m">📍 Tirupati • Waterfall + Shiva Temple</div><div class="d">Waterfall beside a Shiva temple. Best in monsoon!</div><a href="https://www.google.com/maps/dir/?api=1&destination=Kapila+Theertham+Tirupati">🧭 Navigate (3D)</a></div><iframe loading="lazy" src="https://maps.google.com/maps?q=Kapila+Theertham+Tirupati&z=16&output=embed"></iframe></div>
<p style="text-align:center;color:#555;font-size:12px">🙏 Tap Navigate for full 3D in Google Maps 🙏</p>
</body></html>"""

ROOMS_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rooms</title>
<style>body{background:#0f1419;color:#fff;font-family:Arial;padding:12px;margin:0}
.hd{background:linear-gradient(135deg,#FF6B00,#FF8C00);padding:16px;border-radius:12px;text-align:center;margin-bottom:12px}
.tip{background:#16213E;border-left:4px solid #FFD700;padding:12px;border-radius:8px;margin-bottom:12px;font-size:13px;line-height:1.5}
.c{background:#1a2332;border-radius:12px;padding:14px;margin-bottom:12px;border-left:4px solid #00FF88}
.n{color:#FFD700;font-size:17px;font-weight:bold}.p{color:#00FF88;font-size:15px;font-weight:bold;margin:5px 0}.d{color:#ccc;font-size:13px;line-height:1.5}.l{color:#888;font-size:12px;margin-top:4px}
.b{display:block;background:#FF6B00;color:#fff;text-align:center;padding:14px;border-radius:10px;text-decoration:none;font-size:15px;font-weight:bold;margin-top:6px}</style></head><body>
<div class="hd"><h1 style="margin:0">🏨 TTD Rooms</h1>Guest Houses & Cottages</div>
<div class="tip">💡 <b>Tip:</b> Book 60 days early on the official portal — weekend rooms sell out FAST!</div>
<div class="c"><div class="n">🛏️ Padmavathi Guest House</div><div class="p">₹50 – ₹500/night</div><div class="d">Budget dorms & rooms, walking distance to temple.</div><div class="l">📍 Tirumala</div></div>
<div class="c"><div class="n">🛏️ Vishnu Nivasam</div><div class="p">₹100 – ₹1,000/night</div><div class="d">Huge complex, canteen inside, free bus to temple every 15 min.</div><div class="l">📍 Tirupati • Near Railway Station</div></div>
<div class="c"><div class="n">🛏️ Srinivasam Complex</div><div class="p">₹200 – ₹2,000/night</div><div class="d">AC & non-AC rooms, luggage counter, medical aid, restaurants.</div><div class="l">📍 Tirupati • Bus Stand</div></div>
<div class="c"><div class="n">🛏️ Kousthubham Rest House</div><div class="p">₹300 – ₹1,500/night</div><div class="d">On the hill itself — wake up and walk to the queue!</div><div class="l">📍 Tirumala</div></div>
<div class="c"><div class="n">🛏️ TTD Cottages (Premium)</div><div class="p">₹1,000 – ₹3,500/night</div><div class="d">Private cottages, hot water, some with temple views. Best for elders.</div><div class="l">📍 Tirumala</div></div>
<a class="b" href="https://ttdsevaonline.com">🔖 CHECK AVAILABILITY & BOOK (Official Portal)</a>
<p style="text-align:center;color:#555;font-size:12px;margin-top:10px">📞 TTD Helpline: 0877-2277777</p>
</body></html>"""

PHRASES_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Translator</title>
<style>body{background:#0f1419;color:#fff;font-family:Arial;padding:12px;margin:0}
.hd{background:linear-gradient(135deg,#FF6B00,#FF8C00);padding:16px;border-radius:12px;text-align:center;margin-bottom:12px}
.c{background:#1a2332;border-radius:12px;padding:14px;margin-bottom:10px;border-left:4px solid #00BFFF}
.c:active{background:#24314a}
.en{font-size:16px;font-weight:bold}.te{color:#FFD700;font-size:21px;font-weight:bold;margin-top:6px;line-height:1.4}
.la{color:#888;font-size:12px;font-style:italic;margin-top:3px}.h{color:#00FF88;font-size:11px;margin-top:6px}
a{display:block;background:#4285F4;color:#fff;text-align:center;padding:14px;border-radius:12px;text-decoration:none;font-weight:bold;margin-bottom:12px}</style></head><body>
<div class="hd"><h1 style="margin:0">🗣️ Seva Translator</h1>Tap phrase → phone SPEAKS Telugu!</div>
<a href="https://translate.google.com">🌐 Full Google Translate</a>
<div id="list"></div>
<script>
const P=[["Where is drinking water?","తాగే నీళ్ళు ఎక్కడ ఉన్నాయి?","Thaage nillu ekkada unnayi?"],
["I need a doctor. Emergency!","నాకు డాక్టర్ కావాలి. అత్యవసరం!","Naaku doctor kavali!"],
["Where is free food (Annaprasadam)?","ఉచిత అన్నప్రసాదం ఎక్కడ?","Uchita annaprasadam ekkada?"],
["Where is the toilet?","టాయిలెట్ ఎక్కడ ఉంది?","Toilet ekkada undi?"],
["How long is the darshan wait?","దర్శనానికి ఎంత సేపు?","Darshananiki enta sepu?"],
["Where does the queue start?","క్యూ ఎక్కడ మొదలవుతుంది?","Queue ekkada modalavutundi?"],
["Please help me, I am lost.","దయచేసి సహాయం చేయండి, దారి తప్పాను.","Dayachesi sahaayam cheyandi."],
["Where is the medical room?","వైద్య గది ఎక్కడ ఉంది?","Vaidya gadi ekkada undi?"],
["Where can I keep my luggage?","నా సామాను ఎక్కడ ఉంచాలి?","Naa saamanu ekkada unchali?"],
["My child is missing!","నా పిల్లవాడు కనిపించడం లేదు!","Naa pillavadu kanipinchadam ledu!"],
["Where is the free bus to Tirupati?","తిరుపతికి ఉచిత బస్సు ఎక్కడ?","Tirupatiki uchita bus ekkada?"],
["Thank you very much.","చాలా ధన్యవాదాలు.","Chaala dhanyavaadalu."]];
const L=document.getElementById('list');
P.forEach(p=>{const c=document.createElement('div');c.className='c';
c.innerHTML='<div class="en">'+p[0]+'</div><div class="te">'+p[1]+'</div><div class="la">'+p[2]+'</div><div class="h">🔊 Tap to speak Telugu</div>';
c.onclick=()=>{try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(p[1]);u.lang='te-IN';u.rate=0.85;speechSynthesis.speak(u)}catch(e){}};
L.appendChild(c)});
</script></body></html>"""

@app.route('/dashboard')
def dashboard_page():
    return DASHBOARD_HTML

@app.route('/places')
def places_page():
    return PLACES_HTML

@app.route('/rooms')
def rooms_page():
    return ROOMS_HTML

@app.route('/phrases')
def phrases_page():
    return PHRASES_HTML

if __name__ == "__main__":
    print("🛕 TTD API + PAGES RUNNING")
    app.run(host="0.0.0.0", port=5000, debug=True)
