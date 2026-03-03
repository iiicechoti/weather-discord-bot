import os, sys, requests
from datetime import datetime, timezone, timedelta

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
APIKEY = os.environ.get("OPENWEATHER_API_KEY", "")
TZ = timezone(timedelta(hours=7))
cities = ["Bangkok", "Chiang Mai", "Phuket"]
thainames = {"Bangkok": "กรุงเทพ", "Chiang Mai": "เชียงใหม่", "Phuket": "ภูเก็ต"}

if WEBHOOK == "":
    print("ERROR: No DISCORD_WEBHOOK_URL")
    sys.exit(1)
if APIKEY == "":
    print("ERROR: No OPENWEATHER_API_KEY")
    sys.exit(1)

now = datetime.now(TZ)
header = "# 🌍 รายงานสภาพอากาศ\n" + now.strftime("%d/%m/%Y %H:%M") + " น."
embeds = []

for city in cities:
    print("Fetching " + city)
    url = "https://api.openweathermap.org/data/2.5/weather?q=" + city + "&appid=" + APIKEY + "&units=metric&lang=th"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        d = r.json()
    except Exception as e:
        print("FAIL " + city + " " + str(e))
        continue

    wlist = d["weather"]
    w = wlist
    icon = w["icon"]
    desc = w["description"]
    temp = d["main"]["temp"]
    feels = d["main"]["feels_like"]
    hum = d["main"]["humidity"]
    wspeed = d["wind"]["speed"]
    cloud = d["clouds"]["all"]
    vis = d.get("visibility", 10000) / 1000
    country = d["sys"]["country"]
    name = d["name"]
    thai = thainames.get(city, name)
    emap = {"01d": "☀️", "01n": "🌙", "02d": "⛅", "02n": "☁️", "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️", "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️", "11d": "⛈️", "11n": "⛈️", "13d": "❄️", "13n": "❄️", "50d": "🌫️", "50n": "🌫️"}
    emoji = emap.get(icon, "🌡️")
    cmap = {"01": 0xFFD700, "02": 0x95A5A6, "03": 0x95A5A6, "04": 0x7F8C8D, "09": 0x3498DB, "10": 0x3498DB, "11": 0x8E44AD, "13": 0xFFFFFF, "50": 0xBDC3C7}
    color = cmap.get(icon[:2], 0x2ECC71)
    tc = max(0, min(10, int(temp / 45 * 10)))
    tbar = "🟥" * tc + "⬜" * (10 - tc)
    hc = max(0, min(10, hum // 10))
    hbar = "🟦" * hc + "⬜" * (10 - hc)
    title = emoji + " " + thai + " (" + name + ", " + country + ")"
    fields = []
    fields.append({"name": "🌡️ อุณหภูมิ", "value": str(round(temp, 1)) + "°C\n" + tbar + "\nรู้สึกเหมือน " + str(round(feels, 1)) + "°C", "inline": True})
    fields.append({"name": "💧 ความชื้น", "value": str(hum) + "%\n" + hbar, "inline": True})
    fields.append({"name": "💨 ลม", "value": str(wspeed) + " m/s", "inline": True})
    fields.append({"name": "🌥️ เมฆ", "value": str(cloud) + "%", "inline": True})
    fields.append({"name": "👁️ ทัศนวิสัย", "value": str(round(vis, 1)) + " กม.", "inline": True})
    embed = {"title": title, "description": desc, "color": color, "fields": fields, "thumbnail": {"url": "https://openweathermap.org/img/wn/" + icon + "@2x.png"}, "footer": {"text": "OpenWeatherMap"}, "timestamp": now.isoformat()}
    embeds.append(embed)
    print("OK " + city + " " + str(round(temp, 1)) + "C")

if len(embeds) == 0:
    print("No data")
    sys.exit(1)

print("Sending to Discord...")
payload = {"username": "Weather Bot", "content": header, "embeds": embeds}
r = requests.post(WEBHOOK, json=payload, timeout=15)
print("Discord: " + str(r.status_code))
if r.status_code in [200, 204]:
    print("DONE!")
else:
    print(r.text)
    sys.exit(1)
