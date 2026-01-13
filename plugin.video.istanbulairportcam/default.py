# -*- coding: utf-8 -*-
import sys
import re
import urllib.request
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

ADDON_NAME = "Istanbul Airport Live Cam"

# --- Airport (dynamic token) ---
PLAYER_URL = "https://play28.player.im/player/kamera/play.php?kamera=apron&uid=2&sid=1"

M3U8_RE = re.compile(
    r'(https?://[^\s"\']+?\.m3u8\?[^\s"\']*?\banahtar=[^&"\']+&sure=\d+[^\s"\']*)',
    re.IGNORECASE
)

# --- IBB (static HLS chunklist) ---
IBB_EMINONU_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_eminonu.stream/chunklist.m3u8"
IBB_BEYAZIT_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_beyazitmeydani.stream/chunklist.m3u8"
IBB_SAHMET_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_sultanahmet2.stream/chunklist.m3u8"
IBB_METROHAN_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_metrohan.stream/chunklist.m3u8"

IBB_CAMS = {
    "ibb_eminonu": IBB_EMINONU_CHUNKLIST,
    "ibb_beyazit": IBB_BEYAZIT_CHUNKLIST,
    "ibb_sahmet": IBB_SAHMET_CHUNKLIST,
    "ibb_metrohan": IBB_METROHAN_CHUNKLIST
}

# Headers koje browser šalje (po tvom Network screenshotu)
IBB_HEADERS = (
    "User-Agent=Mozilla/5.0"
    "&Referer=https://istanbuluseyret.ibb.gov.tr/"
    "&Origin=https://istanbuluseyret.ibb.gov.tr"
)

def http_get(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    try:
        return data.decode("utf-8", "ignore")
    except Exception:
        return data.decode("latin-1", "ignore")

def extract_m3u8(html):
    cleaned = html.replace("\\/", "/")

    # 1) Pokušaj: full URL u jednom komadu
    m = M3U8_RE.search(cleaned)
    if m:
        return m.group(1)

    # 2) Fallback: izvuci path + anahtar + sure
    path_m = re.search(r'(igaistanbul/[a-zA-Z0-9_-]+/playlist\.m3u8)', cleaned, re.IGNORECASE)
    if not path_m:
        path = "igaistanbul/apron2/playlist.m3u8"
    else:
        path = path_m.group(1)

    key_m = re.search(r'anahtar["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]+)', cleaned)
    sure_m = re.search(r'sure["\']?\s*[:=]\s*["\']?(\d+)', cleaned)

    if not (key_m and sure_m):
        key_m = key_m or re.search(r'anahtar=([A-Za-z0-9_-]+)', cleaned)
        sure_m = sure_m or re.search(r'sure=(\d+)', cleaned)

    if not (key_m and sure_m):
        return None

    anahtar = key_m.group(1)
    sure = sure_m.group(1)

    return f"https://cdn-iga.yayin.com.tr/{path}?anahtar={anahtar}&sure={sure}"

def get_airport_stream_url():
    html = http_get(PLAYER_URL)
    return extract_m3u8(html)

def list_root():
    handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(handle, ADDON_NAME)
    xbmcplugin.setContent(handle, "videos")

    # 1) Airport
    li1 = xbmcgui.ListItem(label="Istanbul Airport – Apron (LIVE)")
    li1.setInfo("video", {"title": "Istanbul Airport – Apron (LIVE)"})
    li1.setProperty("IsPlayable", "true")
    url1 = sys.argv[0] + "?action=play&cam=airport"
    xbmcplugin.addDirectoryItem(handle, url1, li1, isFolder=False)

    # 2) IBB Eminönü
    li2 = xbmcgui.ListItem(label="Istanbul – Eminönü (IBB LIVE)")
    li2.setInfo("video", {"title": "Istanbul – Eminönü (IBB LIVE)"})
    li2.setProperty("IsPlayable", "true")
    url2 = sys.argv[0] + "?action=play&cam=ibb_eminonu"
    xbmcplugin.addDirectoryItem(handle, url2, li2, isFolder=False)

    # 3) IBB Beyazit
    li3 = xbmcgui.ListItem(label="Istanbul – Beyazit (IBB LIVE)")
    li3.setInfo("video", {"title": "Istanbul – Beyazit (IBB LIVE)"})
    li3.setProperty("IsPlayable", "true")
    url3 = sys.argv[0] + "?action=play&cam=ibb_beyazit"
    xbmcplugin.addDirectoryItem(handle, url3, li3, isFolder=False)

    # 4) IBB SAhmet
    li4 = xbmcgui.ListItem(label="Istanbul – Sultanahmet (IBB LIVE)")
    li4.setInfo("video", {"title": "Istanbul – Sultanahmet (IBB LIVE)"})
    li4.setProperty("IsPlayable", "true")
    url4 = sys.argv[0] + "?action=play&cam=ibb_sahmet"
    xbmcplugin.addDirectoryItem(handle, url4, li4, isFolder=False)

    # 5) IBB Metrohan
    li5 = xbmcgui.ListItem(label="Istanbul – Metrohan (IBB LIVE)")
    li5.setInfo("video", {"title": "Istanbul – Metrohan (IBB LIVE)"})
    li5.setProperty("IsPlayable", "true")
    url5 = sys.argv[0] + "?action=play&cam=ibb_metrohan"
    xbmcplugin.addDirectoryItem(handle, url5, li5, isFolder=False)

    xbmcplugin.endOfDirectory(handle)

def play(cam):
    handle = int(sys.argv[1])

    # IBB cams (static)
    if cam in IBB_CAMS:
        url = IBB_CAMS[cam] + "|" + IBB_HEADERS
        xbmc.log(f"[{ADDON_NAME}] Playing {cam}: {url}", xbmc.LOGINFO)
        li = xbmcgui.ListItem(path=url)
        li.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(handle, True, li)
        return

    # default: airport (dynamic token)
    stream_url = None
    try:
        stream_url = get_airport_stream_url()
    except Exception as e:
        xbmc.log(f"[{ADDON_NAME}] Error fetching airport stream: {e}", xbmc.LOGERROR)

    if not stream_url:
        xbmcgui.Dialog().notification(
            ADDON_NAME,
            "Ne mogu pronaći live stream (m3u8).",
            xbmcgui.NOTIFICATION_ERROR,
            4000
        )
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return

    xbmc.log(f"[{ADDON_NAME}] Resolved airport stream: {stream_url}", xbmc.LOGINFO)

    airport_headers = (
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        "&Referer=https://play28.player.im/"
        "&Origin=https://play28.player.im"
    )

    li = xbmcgui.ListItem(path=stream_url + "|" + airport_headers)
    li.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(handle, True, li)


def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring.lstrip("?")))
    if params.get("action") == "play":
        play(params.get("cam", "airport"))
    else:
        list_root()

if __name__ == "__main__":
    router(sys.argv[2] if len(sys.argv) > 2 else "")
