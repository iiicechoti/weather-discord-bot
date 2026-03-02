import os, sys, requests, json
from datetime import datetime, timezone, timedelta

WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
APIKEY = os.environ.get("OPENWEATHER_API_KEY", "")
CITIES = ["Bangkok", "Chiang Mai", "Phuket"]
TZ = timezone(timedelta(hours=7))

def run():
    if WEBHOOK == "" or APIKEY == "":
        print("ERROR: Missing secrets")
        sys.exit(1)

    now = datetime.now(TZ)
    header = "# 🌍 รายงานสภาพอากาศ\n📆 " + now.strftime("%d/%m/%Y") + " 🕐 " + now.strftime("%H:%M") + " น."

    embeds = []

    for city in CITIES:
        print("Fetching " + city)
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            resp = requests.get(url, params={"q": city, "appid": APIKEY, "units": "metric", "lang": "th"}, timeout=15)
            resp.raise_for_status()
            d = resp.json()
        except Exception as e:
            print("FAIL " + city + ": " + str(e))
            continue

        w = d.get("weather", [{}])
        m = d.get("main", {})
        wi = d.get("wind", {})
        cl = d.get("clouds", {})
        sy = d.get("sys", {})
        rn = d.get("rain", {})

        icon = w.get("icon", "01d")
        desc = w.get("description", "N/A")
        temp = m.get("temp", 0)
        feels = m.get("feels_like", 0)
        hum = m.get("humidity", 0)
        wspeed = wi.get("speed", 0)
        cloud = cl.get("all", 0)
        vis = d.get("visibility", 10000) / 1000
        country = sy.get("country", "")
        rain1h = rn.get("1h", 0)

        emojimap = {"01d":"☀️","01n":"🌙","02d":"⛅","02n":"☁️","03d":"☁️","03n":"☁️","04d":"☁️","04n":"☁️","09d":"🌧️","09n":"🌧️","10d":"🌦️","10n":"🌧️","11d":"⛈️","11n":"⛈️","13d":"❄️","13n":"❄️","50d":"🌫️","50n":"🌫️"}
        emoji = emojimap.get(icon, "🌡️")

        colormap = {"01":0xFFD700,"02":0x95A5A6,"03":0x95A5A6,"04":0x7F8C8D,"09":0x3498DB,"10":0x3498DB,"11":0x8E44AD,"13":0xFFFFFF,"50":0xBDC3C7}
        color = colormap.get(icon[:2], 0x2ECC71)

        thaimap = {"Bangkok":"กรุงเทพ","Chiang Mai":"เชียงใหม่","Phuket":"ภูเก็ต","Pattaya":"พัทยา","Khon Kaen":"ขอนแก่น","Hat Yai":"หาดใหญ่"}
        thai = thaimap.get(d.get("name", city), d.get("name", city))

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

        fields = [
            {"name": "🌡️ อุณหภูมิ", "value": "**" + str(round(temp,1)) + "°C**\n" + tbar + "\nรู้สึกเหมือน " + str(round(feels,1)) + "°C", "inline": True},
            {"name": "💧 ความชื้น", "value": "**" + str(hum) + "%**\n" + hbar, "inline": True},
            {"name": "💨 ลม", "value": str(wspeed) + " m/s", "inline": True},
            {"name": "🌥️ เมฆ", "value": str(cloud) + "%", "inline": True},
            {"name": "👁️ ทัศนวิสัย", "value": str(round(vis,1)) + " กม.", "inline": True},
        ]

        if rain1h > 0:
            fields.append({"name": "🌧️ ฝน", "value": str(rain1h) + " มม.", "inline": True})

        embed = {
            "title": emoji + " " + thai + " (" + d.get("name", city) + ", " + country + ")",
            "description": "**" + desc + "**" + warn,
            "color": color,
            "thumbnail": {"url": "https://openweathermap.org/img/wn/" + icon + "@2x.png"},
            "fields": fields,
            "footer": {"text": "OpenWeatherMap"},
            "timestamp": now.isoformat()
        }

        embeds.append(embed)
        print("OK: " + city + " " + str(round(temp,1)) + "C")

    if len(embeds) == 0:
        print("No data")
        sys.exit(1)

    payload = {"username": "Weather Bot", "content": header, "embeds": embeds}
    try:
        r = requests.post(WEBHOOK, json=payload, timeout=15)
        print("Discord response: " + str(r.status_code))
        if r.status_code not in [200, 204]:
            print(r.text)
            sys.exit(1)
    except Exception as e:
        print("Discord error: " + str(e))
        sys.exit(1)

    print("Done!")

if __name__ == "__main__":
    run()
