import sys
import os
from playwright.sync_api import sync_playwright

TARGET_URL = "https://padangtv.id/livestreaming/"
EPG_URL = "https://sulthanpamenan.github.io/padang-tv-playlist/epg.xml"
LOGO_URL = "https://raw.githubusercontent.com/sulthanpamenan/IPTV/main/Logos/Local/Padang%20TV.png"

def run_scraper():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    stream_url = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"]
        )
        context = browser.new_context(user_agent=ua)
        page = context.new_page()

        def handle_request(request):
            nonlocal stream_url
            req_url = request.url
            # PERBAIKAN: Tangkap semua URL .m3u8 tanpa membatasi domain Twitch/ttvnw
            if ".m3u8" in req_url and not stream_url:
                print(f"[✓] Stream m3u8 ditemukan: {req_url}")
                stream_url = req_url

        page.on("request", handle_request)

        print("[*] Membuka halaman Padang TV Live Streaming...")
        try:
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Coba klik player jika memerlukan interaksi tombol play
            for frame in page.frames:
                try:
                    play_btn = frame.locator("video, .play-button, iframe, #player")
                    if play_btn.count() > 0:
                        play_btn.first.click(timeout=1000)
                except Exception:
                    pass

            for _ in range(10):
                if stream_url:
                    break
                page.wait_for_timeout(1000)

        except Exception as e:
            print(f"[!] Error saat memuat halaman: {e}")

        browser.close()

    return stream_url

def main():
    stream_url = run_scraper()

    if not stream_url:
        print("[X] Gagal menangkap stream M3U8 dari Padang TV.")
        sys.exit(1)

    print(f"[✓] Stream M3U8 Berhasil Ditemukan!")

    # Format header EXTM3U dengan url-tvg menuju EPG GitHub Pages
    m3u_content = (
        f'#EXTM3U url-tvg="{EPG_URL}"\n\n'
        f'#EXTINF:-1 tvg-id="PadangTV.id" tvg-name="Padang TV" tvg-logo="{LOGO_URL}" group-title="Local",Padang TV\n'
        f"{stream_url}\n"
    )

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    with open("playlist.txt", "w", encoding="utf-8") as f:
        f.write(stream_url)

    print("[SUCCESS] Berkas `playlist.m3u` dan `playlist.txt` berhasil diperbarui.")

if __name__ == "__main__":
    main()
