import requests
import re


def is_live(username):
    try:
        url = f"https://www.tiktok.com/@{username}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)

        if resp.status_code != 200:
            return False, None

        html = resp.text

        # Host-Live: klassische roomId
        match = re.search(r'"roomId":"(\d+)"', html)
        if match:
            return True, match.group(1)

        # Gast-Live: neue TikTok Live URL
        live_url_pattern = fr'https://www\.tiktok\.com/@{username}/live[^"\' ]*'
        match2 = re.search(live_url_pattern, html)

        if match2:
            return True, "LIVE"

        return False, None

    except Exception as e:
        print("Fehler in is_live:", e)
        return False, None
