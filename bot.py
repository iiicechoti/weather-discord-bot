import os
import sys
import requests
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

CITIES = ["Bangkok", "Chiang Mai", "Phuket"]

TH_TZ = timezone(timedelta(hours=7))

EMOJIS = {
    "01d": "☀️", "01n": "🌙",
    "02d": "⛅", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
}

COLORS = {
    "01": 0xFFD700,
    "02": 0x95A5A6,
    "03": 0x95A5A6,
    "04": 0x7F8C8D,
    "09": 0x3498DB,
    "10": 0x3498DB,
    "11": 0x8E44AD,
    "13": 0xFFFFFF,
    "50": 0xBDC3C7,
}

THAI_NAMES = {
    "Bangkok": "กรุงเทพ",
    "Chiang Mai": "เชียงใหม่",
    "Phuket": "ภูเก็ต",
    "Pattaya": "พัทยา",
    "Hat Yai": "หาดใหญ่",
    "Khon Kaen": "ขอนแก่น",
}


def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "th",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error fetching {city}: {e}")
        return None


def make_embed(data):
    city = data["name"]
    icon = data["weather"]["icon"]
    emoji = EMOJIS.get(icon, "🌡️")
    color = COLORS.get(icon[:2], 0x2ECC71)
    desc = data["weather"]["description"]
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility", 0) / 1000
    thai = THAI_NAMES.get(city, city)
    country = data["sys"]["country"]

    temp_bar_count = max(0, min(10, int(temp / 45 * 10)))
    temp_bar = "🟥" * temp_bar_count + "⬜" * (10 - temp_bar_count)

    hum_bar_count = humidity // 10
    hum_bar = "🟦" * hum_bar_count + "⬜" * (10 - hum_bar_count)

    warning = ""
    if temp >= 40:
        warning = "\n\n🔴 **อันตราย!** ร้อนจัดมาก หลีกเลี่ยงกลางแจ้ง"
    elif temp >= 35 and humidity >= 70:
        warning = "\n\n🟠 **เตือน!** ร้อนชื้นมาก ดื่มน้ำเยอะๆ"
    elif temp >= 35:
        warning = "\n\n🟡 **ระวัง!** อากาศร้อนจัด"

    embed = {
        "title": f"{emoji} {thai} ({city}, {country})",
        "description": f"**{desc}**{warning}",
        "color": color,
        "thumbnail": {
            "url": f"https://openweathermap.org/img/wn/{icon}@2x.png"
        },
        "fields": [
            {
                "name": "🌡️ อุณหภูมิ",
                "value": f"**{temp:.1f}°C**\n{temp_bar}\nรู้สึกเหมือน {feels:.1f}°C",
                "inline": True,
            },
            {
                "name": "💧 ความชื้น",
                "value": f"**{humidity}%**\n{hum_bar}",
                "inline": True,
            },
            {
                "name": "💨 ลม",
                "value": f"**{wind} m/s**",
                "inline": True,
            },
            {
                "name": "🌥️ เมฆ",
                "value": f"{clouds}%",
                "inline": True,
            },
            {
                "name": "👁️ ทัศนวิสัย",
                "value": f"{visibility:.1f} กม.",
                "inline": True,
            },
        ],
        "footer": {
            "text": "ข้อมูลจาก OpenWeatherMap"
        },
        "timestamp": datetime.now(TH_TZ).isoformat(),
    }

    if "rain" in data:
        rain_1h = data["rain"].get("1h", 0)
        if rain_1h > 0:
            embed["fields"].append({
                "name": "🌧️ ฝน (1ชม.)",
                "value": f"{rain_1h} มม.",
                "inline": True,
            })

    return embed


def send_to_discord(content=None, embeds=None):
    payload = {
        "username": "🌤️ Weather Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/1779/1779940.png",
    }
    if content:
        payload["content"] = content
    if embeds:
        payload["embeds"] = embeds

    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 204:
            print("Sent to Discord!")
            return True
        else:
            print(f"Discord error {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"Send error: {e}")
        return False


def report_weather():
    now = datetime.now(TH_TZ)
    header = (
        f"# 🌍 รายงานสภาพอากาศ\n"
        f"📆 {now.strftime('%d/%m/%Y')} | "
        f"🕐 {now.strftime('%H:%M')} น."
    )

    embeds = []
    for city in CITIES:
        print(f"Fetching {city}...")
        data = get_weather(city)
        if data:
            embed = make_embed(data)
            embeds.append(embed)
            print(f"  OK: {city} {data['main']['temp']}C")
        else:
            print(f"  FAIL: {city}")

    if embeds:
        send_to_discord(content=header, embeds=embeds)
    else:
        print("No data to send")


def test_webhook():
    send_to_discord(content="🧪 ทดสอบ Weather Bot สำเร็จ! ✅")


if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("ERROR: No DISCORD_WEBHOOK_URL")
        sys.exit(1)
    if not API_KEY:
        print("ERROR: No OPENWEATHER_API_KEY")
        sys.exit(1)

    mode = sys.argv if len(sys.argv) > 1 else "current"

    if mode == "test":
        test_webhook()
    else:
        report_weather()

    print("Done!")
