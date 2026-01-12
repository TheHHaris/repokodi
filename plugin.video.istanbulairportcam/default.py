# -*- coding: utf-8 -*-
import sys
import re
import urllib.request
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

ADDON_NAME = "Istanbul Airport Live Cam"
PLAYER_URL = "https://play28.player.im/player/kamera/play.php?kamera=apron&uid=2&sid=1"

M3U8_RE = re.compile(
    r'(https?://[^\s"\']+?\.m3u8\?[^\s"\']*?\banahtar=[^&"\']+&sure=\d+[^\s"\']*)',
    re.IGNORECASE
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

    # 1) Pokušaj kao ranije: full URL u jednom komadu
    m = M3U8_RE.search(cleaned)
    if m:
        return m.group(1)

    # 2) Fallback: izvuci path + anahtar + sure, pa sastavi URL
    # Path do playlist-a (nekad je bez protokola i domene)
    path_m = re.search(r'(igaistanbul/[a-zA-Z0-9_-]+/playlist\.m3u8)', cleaned, re.IGNORECASE)
    if not path_m:
        # hard fallback ako path ne nađe (za tvoj slučaj znamo da je apron2)
        path = "igaistanbul/apron2/playlist.m3u8"
    else:
        path = path_m.group(1)

    # Tokeni (anahtar i sure) se često pojavljuju odvojeno u JS-u
    key_m = re.search(r'anahtar["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]+)', cleaned)
    sure_m = re.search(r'sure["\']?\s*[:=]\s*["\']?(\d+)', cleaned)

    if not (key_m and sure_m):
        # nekad je "anahtar=" već u tekstu, pa pokušaj i to
        key_m = key_m or re.search(r'anahtar=([A-Za-z0-9_-]+)', cleaned)
        sure_m = sure_m or re.search(r'sure=(\d+)', cleaned)

    if not (key_m and sure_m):
        return None

    anahtar = key_m.group(1)
    sure = sure_m.group(1)

    # Domen koji si već vidio u pravom linku
    return f"https://cdn-iga.yayin.com.tr/{path}?anahtar={anahtar}&sure={sure}"

def get_stream_url():
    html = http_get(PLAYER_URL)
    return extract_m3u8(html)


def list_root():
    handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(handle, ADDON_NAME)
    xbmcplugin.setContent(handle, "videos")

    li = xbmcgui.ListItem(label="Istanbul Airport – Apron (LIVE)")
    li.setInfo("video", {"title": "Istanbul Airport – Apron (LIVE)"})
    li.setProperty("IsPlayable", "true")

    url = sys.argv[0] + "?action=play"
    xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)
    xbmcplugin.endOfDirectory(handle)

def play():
    handle = int(sys.argv[1])

    stream_url = None
    try:
        stream_url = get_stream_url()
    except Exception as e:
        xbmc.log(f"[{ADDON_NAME}] Error fetching stream: {e}", xbmc.LOGERROR)

    if not stream_url:
        xbmcgui.Dialog().notification(ADDON_NAME, "Ne mogu pronaći live stream (m3u8).",
                                      xbmcgui.NOTIFICATION_ERROR, 4000)
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
        return

    xbmc.log(f"[{ADDON_NAME}] Resolved stream: {stream_url}", xbmc.LOGINFO)
    li = xbmcgui.ListItem(path=stream_url)
    li.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(handle, True, li)

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring.lstrip("?")))
    if params.get("action") == "play":
        play()
    else:
        list_root()

if __name__ == "__main__":
    router(sys.argv[2] if len(sys.argv) > 2 else "")
