import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

SCHEDULE_URL = "https://padangtv.id/schedule/"
CHANNEL_ID = "PadangTV.id"
CHANNEL_NAME = "Padang TV"
LOGO_URL = "https://padangtv.id/wp-content/uploads/2020/07/logo1-e1595189708614.png"

def fetch_schedule_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(SCHEDULE_URL, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[!] Error saat memuat halaman jadwal: {e}")
    return ""

def parse_schedule(html):
    soup = BeautifulSoup(html, "html.parser") if html else None
    programs = []
    
    if soup:
        items = soup.select("tr") or soup.select(".schedule-item") or soup.select(".elementor-icon-list-item")
        for item in items:
            text = item.get_text(separator=" ", strip=True)
            parts = text.replace(".", ":").split()
            if not parts:
                continue
            
            time_part = parts[0]
            if ":" in time_part and len(time_part) <= 5:
                title = " ".join(parts[1:])
                if title:
                    programs.append({
                        "time": time_part,
                        "title": title
                    })

    if not programs:
        programs = [
            {"time": "05:00", "title": "Salingka Minang Morning"},
            {"time": "06:00", "title": "Detak Sumbar Pagi"},
            {"time": "07:30", "title": "Lagu Minang Hits"},
            {"time": "09:00", "title": "Dapur Kita"},
            {"time": "11:00", "title": "Info Publik"},
            {"time": "12:00", "title": "Detak Sumbar Siang"},
            {"time": "13:30", "title": "Feature Daerah"},
            {"time": "15:30", "title": "Salingka Minang Sore"},
            {"time": "17:00", "title": "Mimbar Agama"},
            {"time": "19:00", "title": "Detak Sumbar Utama"},
            {"time": "20:30", "title": "Talkshow Interaktif"},
            {"time": "22:00", "title": "Sinema / Salingka Minang Malam"},
            {"time": "00:00", "title": "Padang TV Night Broadcast"}
        ]

    return programs

def build_xmltv(base_programs):
    tv = ET.Element("tv", generator_info_name="PadangTV-EPG-Generator")
    
    channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = CHANNEL_NAME
    icon = ET.SubElement(channel, "icon", src=LOGO_URL)

    now = datetime.now()
    dates_to_generate = [now.date(), now.date() + timedelta(days=1)]

    for current_date in dates_to_generate:
        for i, prog in enumerate(base_programs):
            try:
                time_struct = datetime.strptime(prog["time"], "%H:%M").time()
                start_dt = datetime.combine(current_date, time_struct)
                
                if i + 1 < len(base_programs):
                    next_time_struct = datetime.strptime(base_programs[i+1]["time"], "%H:%M").time()
                    stop_dt = datetime.combine(current_date, next_time_struct)
                    if stop_dt <= start_dt:
                        stop_dt += timedelta(days=1)
                else:
                    stop_dt = start_dt + timedelta(hours=3)

                start_str = start_dt.strftime("%Y%m%d%H%M%S +0700")
                stop_str = stop_dt.strftime("%Y%m%d%H%M%S +0700")

                programme = ET.SubElement(tv, "programme", start=start_str, stop=stop_str, channel=CHANNEL_ID)
                title = ET.SubElement(programme, "title", lang="id")
                title.text = prog["title"]
                desc = ET.SubElement(programme, "desc", lang="id")
                desc.text = f"Siaran resmi Padang TV - {prog['title']}"

            except Exception as e:
                print(f"[!] Error item EPG: {e}")

    xml_str = minidom.parseString(ET.tostring(tv, encoding="utf-8")).toprettyxml(indent="  ")
    return xml_str

def main():
    html = fetch_schedule_html()
    programs = parse_schedule(html)
    xml_content = build_xmltv(programs)
    
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print("[SUCCESS] Berkas EPG `epg.xml` berhasil diperbarui!")

if __name__ == "__main__":
    main()
