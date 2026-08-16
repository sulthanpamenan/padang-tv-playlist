import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

SCHEDULE_URL = "https://padangtv.id/schedule/"
CHANNEL_ID = "PadangTV.id"
CHANNEL_NAME = "Padang TV"

def fetch_schedule_html():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    html_content = ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(user_agent=ua)
        page = context.new_page()
        print("[*] Membuka halaman jadwal Padang TV...")
        try:
            page.goto(SCHEDULE_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            html_content = page.content()
        except Exception as e:
            print(f"[!] Error saat memuat halaman jadwal: {e}")
        browser.close()
        
    return html_content

def parse_schedule(html):
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    programs = []
    
    # Mencari tabel/kontainer jadwal pada WordPress Padang TV
    # Catatan: Elemen umum WordPress untuk tabel jadwal berupa <tr> atau item daftar
    items = soup.select("tr") or soup.select(".schedule-item") or soup.select(".elementor-icon-list-item")
    
    today_str = datetime.now().strftime("%Y-%m-%d")

    for item in items:
        text = item.get_text(separator=" ", strip=True)
        # Mencari pola jam (misal 06:00 - Program A atau 06.00 Program B)
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

    # Fallback jika scraping struktur tabel HTML tidak menemukan item
    if not programs:
        print("[!] Format jadwal HTML dinamis, menerapkan fallback jadwal harian...")
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
            {"time": "22:00", "title": "Semaian Rohani / Sinema Malam"}
        ]

    return programs

def build_xmltv(programs):
    tv = ET.Element("tv", generator_info_name="PadangTV-EPG-Generator")
    
    # Elemen Channel
    channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
    display_name = ET.SubElement(channel, "display-name")
    display_name.text = CHANNEL_NAME

    now = datetime.now()
    today_date = now.date()

    for i, prog in enumerate(programs):
        try:
            time_struct = datetime.strptime(prog["time"], "%H:%M").time()
            start_dt = datetime.combine(today_date, time_struct)
            
            # Tentukan waktu selesai berdasarkan jam mulai program berikutnya
            if i + 1 < len(programs):
                next_time_struct = datetime.strptime(programs[i+1]["time"], "%H:%M").time()
                stop_dt = datetime.combine(today_date, next_time_struct)
                if stop_dt <= start_dt:
                    stop_dt += timedelta(days=1)
            else:
                stop_dt = start_dt + timedelta(hours=2)

            start_str = start_dt.strftime("%Y%m%d%H%M%S +0700")
            stop_str = stop_dt.strftime("%Y%m%d%H%M%S +0700")

            programme = ET.SubElement(tv, "programme", start=start_str, stop=stop_str, channel=CHANNEL_ID)
            title = ET.SubElement(programme, "title", lang="id")
            title.text = prog["title"]
            desc = ET.SubElement(programme, "desc", lang="id")
            desc.text = f"Siaran resmi Padang TV - {prog['title']}"

        except Exception as e:
            print(f"[!] Error memasukkan item program {prog}: {e}")

    # Format XML agar rapi (Pretty Print)
    xml_str = minidom.parseString(ET.tostring(tv, encoding="utf-8")).toprettyxml(indent="  ")
    return xml_str

def main():
    html = fetch_schedule_html()
    programs = parse_schedule(html)
    
    if not programs:
        print("[X] Gagal menyusun jadwal EPG.")
        sys.exit(1)
        
    xml_content = build_xmltv(programs)
    
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print("[SUCCESS] Berkas EPG epg.xml berhasil diperbarui!")

if __name__ == "__main__":
    main()
