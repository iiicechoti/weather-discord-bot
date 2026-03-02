import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
APIKEY = os.environ.get("OPENWEATHER_API_KEY", "")
CITIES = ["Bangkok", "Chiang Mai", "Phuket"]
TZ = timezone(timedelta(hours=7))

def fetch(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    p = {"q": city, "appid": APIKEY, "units": "metric", "lang": "th"}
    r = requests.get(url, params=p, timeout=15)
    r.raise_for_status()
    return r.json()

def build(d):
    wlist = d["weather"]
    wfirst = wlist
    icon = wfirst["icon"]
    desc = wfirst["description"]

    temp = d["main"]["temp"]
    feels = d["main"]["feels_like"]
    hum = d["main"]["humidity"]
    wspeed = d["wind"]["speed"]
    cloud = d["clouds"]["all"]
    vis = d.get("visibility", 10000) / 1000
    country = d["sys"]["country"]
    name = d["name"]

    emojimap = {"01d":"☀️","01n":"🌙","02d":"⛅","02n":"☁️","03d":"☁️","03n":"☁️","04d":"☁️","04n":"☁️","09d":"🌧️","09n":"🌧️","10d":"🌦️","10n":"🌧️","11d":"⛈️","11n":"⛈️","13d":"❄️","13n":"❄️","50d":"🌫️","50n":"🌫️"}
    emoji = emojimap.get(icon, "🌡️")

    colormap = {"01":0xFFD700,"02":0x95A5A6,"03":0x95A5A6,"04":0x7F8C8D,"09":0x3498DB,"10":0x3498DB,"11":0x8E44AD,"13":0xFFFFFF,"50":0xBDC3C7}
    color = colormap.get(icon[:2], 0x2ECC71)

    thaimap = {"Bangkok":"กรุงเทพ","Chiang Mai":"เชียงใหม่","Phuket":"ภูเก็ต","Pattaya":"พัทยา","Khon Kaen":"ขอนแก่น"}
    thai = thaimap.get(name, name)

    tc = max(0, min(10, int(temp / 45 * 10)))
    tbar = "🟥" * tc + "⬜" * (10 - tc)
    hc = max(0, min(10, hum // 10))
    hbar = "🟦" * hc + "⬜" * (10 - hc)

    warn = ""
    if temp >= 40:
        warn = "\n🔴 **อันตราย!** ร้อนจัดมาก"
    elif temp >= 35 and hum >= 70:
        warn = "\n🟠 **เตือน!** ร้อนชื้นมาก"
    elif temp >= 35:
        warn = "\n🟡 **ระวัง!** อากาศร้อนจัด"

    now = datetime.now(TZ)

    embed = {
        "title": emoji + " " + thai + " (" + name + ", " + country + ")",
        "description": "**" + desc + "**" + warn,
        "color": color,
        "thumbnail": {"url": "https://openweathermap.org/img/wn/" + icon + "@2x.png"},
        "fields": [
            {"name": "🌡️ อุณหภูมิ", "value": "**" + str(round(temp, 1)) + "°C**\n" + tbar + "\nรู้สึกเหมือน " + str(round(feels, 1)) + "°C", "inline": True},
            {"name": "💧 ความชื้น", "value": "**" + str(hum) + "%**\n" + hbar, "inline": True},
            {"name": "💨 ลม", "value": str(wspeed) + " m/s", "inline": True},
            {"name": "🌥️ เมฆ", "value": str(cloud) + "%", "inline": True},
            {"name": "👁️ ทัศนวิสัย", "value": str(round(vis, 1)) + " กม.", "inline": True},
        ],
        "footer": {"text": "OpenWeatherMap"},
        "timestamp": now.isoformat()
    }
    return embed

def send(content, embeds):
    payload = {"username": "Weather Bot", "content": content, "embeds": embeds}
    r = requests.post(WEBHOOK, json=payload, timeout=15)
    print("Discord: " + str(r.status_code))
    return r.status_code in [200, 204]

def main():
    if WEBHOOK == "":
        print("ERROR: No DISCORD_WEBHOOK_URL")
        sys.exit(1)
    if APIKEY == "":
        print("ERROR: No OPENWEATHER_API_KEY")
        sys.exit(1)

    now = datetime.now(TZ)
    header = "# 🌍 รายงานสภาพอากาศ\n📆 " + now.strftime("%d/%m/%Y") + " 🕐 " + now.strftime("%H:%M") + " น."

    embeds = []
    for city in CITIES:
        print("Fetching " + city + "...")
        try:
            d = fetch(city)
            e = build(d)
            embeds.append(e)
            print("  OK " + city + " " + str(d["main"]["temp"]) + "C")
        except Exception as ex:
            print("  FAIL " + city + " " + str(ex))

    if len(embeds) == 0:
        print("No data")
        sys.exit(1)

    ok = send(header, embeds)
    if ok:
        print("Done!")
    else:
        print("Send failed")
        sys.exit(1)

main()
