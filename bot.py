# bot.py
import os
import sys
import requests
from datetime import datetime, timezone, timedelta

# ============ ตั้งค่า ============
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# เมืองที่ต้องการ (เพิ่ม/ลบได้ตามชอบ)
CITIES = ["Bangkok", "Chiang Mai", "Phuket"]

# เวลาไทย UTC+7
TH_TZ = timezone(timedelta(hours=7))

# emoji ตามสภาพอากาศ
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

# สีตามสภาพอากาศ
COLORS = {
    "01": 0xFFD700,   # แจ่มใส = ทอง
    "02": 0x95A5A6,   # มีเมฆ = เทา
    "03": 0x95A5A6,
    "04": 0x7F8C8D,
    "09": 0x3498DB,   # ฝน = ฟ้า
    "10": 0x3498DB,
    "11": 0x8E44AD,   # พายุ = ม่วง
    "13": 0xFFFFFF,   # หิมะ = ขาว
    "50": 0xBDC3C7,   # หมอก = เทาอ่อน
}

# ชื่อเมืองภาษาไทย
THAI_NAMES = {
    "Bangkok": "กรุงเทพ",
    "Chiang Mai": "เชียงใหม่",
    "Phuket": "ภูเก็ต",
    "Pattaya": "พัทยา",
    "Hat Yai": "หาดใหญ่",
    "Khon Kaen": "ขอนแก่น",
    "Nakhon Ratchasima": "โคราช",
    "Udon Thani": "อุดรธานี",
}


def get_weather(city):
    """ดึงข้อมูลสภาพอากาศจาก API"""
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
        print(f"❌ ดึงข้อมูล {city} ไม่ได้: {e}")
        return None


def make_embed(data):
    """สร้าง embed สำหรับ Discord"""
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

    # สร้าง bar อุณหภูมิ
    temp_bar_count = max(0, min(10, int(temp / 45 * 10)))
    temp_bar = "🟥" * temp_bar_count + "⬜" * (10 - temp_bar_count)

    # สร้าง bar ความชื้น
    hum_bar_count = humidity // 10
    hum_bar = "🟦" * hum_bar_count + "⬜" * (10 - hum_bar_count)

    # ชื่อไทย
    thai = THAI_NAMES.get(city, city)
    country = data["sys"]["country"]

    # คำเตือน
    warning = ""
    if temp >= 40:
        warning = "\n\n🔴 **อันตราย!** ร้อนจัดมาก หลีกเลี่ยงกลางแจ้ง"
    elif temp >= 35 and humidity >= 70:
        warning = "\n\n🟠 **เตือน!** ร้อนชื้นมาก ดื่มน้ำเยอะๆ"
    elif temp >= 35:
        warning = "\n\n🟡 **ระวัง!** อากาศร้อนจัด"

    # ข้อมูลฝน
    rain_info = ""
    if "rain" in data:
        rain_1h = data["rain"].get("1h", 0)
        if rain_1h > 0:
            rain_info = f"\n🌧️ ฝน (1ชม.): {rain_1h} มม."

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
            "text": "📡 ข้อมูลจาก OpenWeatherMap"
        },
        "timestamp": datetime.now(TH_TZ).isoformat(),
    }

    if rain_info:
        embed["fields"].append({
            "name": "🌧️ ปริมาณฝน",
            "value": rain_info.strip(),
            "inline": True,
        })

    return embed


def send_to_discord(content=None, embeds=None):
    """ส่งข้อความไป Discord"""
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
            print("✅ ส่งสำเร็จ!")
            return True
        else:
            print(f"❌ ส่งไม่ได้ status={r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def report_weather():
    """รายงานสภาพอากาศทุกเมือง"""
    now = datetime.now(TH_TZ)
    header = (
        f"# 🌍 รายงานสภาพอากาศ\n"
        f"📆 {now.strftime('%d/%m/%Y')} | "
        f"🕐 {now.strftime('%H:%M')} น."
    )

    embeds = []
    for city in CITIES:
        print(f"📡 กำลังดึงข้อมูล {city}...")
        data = get_weather(city)
        if data:
            embed = make_embed(data)
            embeds.append(embed)
            print(f"  ✅ {city}: {data['main']['temp']}°C")
        else:
            print(f"  ❌ {city}: ดึงข้อมูลไม่ได้")

    if embeds:
        send_to_discord(content=header, embeds=embeds)
    else:
        print("❌ ไม่มีข้อมูลจะส่งเลย")


def test_webhook():
    """ทดสอบว่า webhook ใช้ได้"""
    send_to_discord(content="🧪 ทดสอบ Weather Bot สำเร็จ! บอทพร้อมทำงาน ✅")


# ============ จุดเริ่มต้น ============
if __name__ == "__main__":
    # ตรวจสอบ config
    if not WEBHOOK_URL:
        print("❌ ไม่มี DISCORD_WEBHOOK_URL")
        sys.exit(1)
    if not API_KEY:
        print("❌ ไม่มี OPENWEATHER_API_KEY")
        sys.exit(1)

    # เช็คคำสั่ง
    mode = sys.argv if len(sys.argv) > 1 else "current"

    if mode == "test":
        test_webhook()
    elif mode == "current":
        report_weather()
    else:
        report_weather()

    print("🎉 เสร็จสิ้น!")
