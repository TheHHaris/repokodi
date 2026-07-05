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

# --- IBB cameras ---
BASE = "https://kamerayayin.ibb.istanbul/turistikcam"

IBB_CAMS = {
    "ibb_eminonu": f"{BASE}/eminonu.stream/playlist.m3u8",
    "ibb_beyazit": f"{BASE}/beyazitmeydan.stream/playlist.m3u8",
    "ibb_sahmet": f"{BASE}/sultanahmet2.stream/playlist.m3u8",
    "ibb_metrohan": f"{BASE}/metrohan.stream/playlist.m3u8",
    "ibb_kapalicarsi": f"{BASE}/misircarsisi.stream/playlist.m3u8",
    "ibb_bkulesi": f"{BASE}/beyazitkulesi2.stream/playlist.m3u8",
    "ibb_camlica": f"{BASE}/buyukcamlica.stream/playlist.m3u8",
    "ibb_kadikoy": f"{BASE}/kadikoy.stream/playlist.m3u8",
    "ibb_ortakoy": f"{BASE}/ortakoy.stream/playlist.m3u8",
    "ibb_piereloti": f"{BASE}/pierreloti.stream/playlist.m3u8",
    "ibb_sahmet1": f"{BASE}/sultanahmet1.stream/playlist.m3u8",
    "ibb_taksim": f"{BASE}/taksim.stream/playlist.m3u8",
    "ibb_kizkulesi": f"{BASE}/kizkulesi.stream/playlist.m3u8",
    "ibb_anadoluhisari": f"{BASE}/anadoluhisari.stream/playlist.m3u8",
    "ibb_eyupsultan": f"{BASE}/eyupsultan.stream/playlist.m3u8",
    "ibb_hidivkasri": f"{BASE}/hidivkasri.stream/playlist.m3u8",
    "ibb_kucukcekmece": f"{BASE}/kucukcekmece.stream/playlist.m3u8",
    "ibb_salacak": f"{BASE}/salacak.stream/playlist.m3u8",
    "ibb_sarachane": f"{BASE}/sarachane.stream/playlist.m3u8",
    "ibb_uskudar": f"{BASE}/uskudar.stream/playlist.m3u8",
}

IBB_ITEMS = [
    ("Istanbul - Eminonu (IBB LIVE)", "ibb_eminonu"),
    ("Istanbul - Beyazit (IBB LIVE)", "ibb_beyazit"),
    ("Istanbul - Sultanahmet 2 (IBB LIVE)", "ibb_sahmet"),
    ("Istanbul - Metrohan (IBB LIVE)", "ibb_metrohan"),
    ("Istanbul - Misir Carsi (IBB LIVE)", "ibb_kapalicarsi"),
    ("Istanbul - Beyazit Kulesi 2 (IBB LIVE)", "ibb_bkulesi"),
    ("Istanbul - Buyuk Camlica (IBB LIVE)", "ibb_camlica"),
    ("Istanbul - Kadikoy (IBB LIVE)", "ibb_kadikoy"),
    ("Istanbul - Ortakoy (IBB LIVE)", "ibb_ortakoy"),
    ("Istanbul - Pierre Lotti (IBB LIVE)", "ibb_piereloti"),
    ("Istanbul - Sultanahmet 1 (IBB LIVE)", "ibb_sahmet1"),
    ("Istanbul - Taksim (IBB LIVE)", "ibb_taksim"),
    ("Istanbul - Kiz Kulesi (IBB LIVE)", "ibb_kizkulesi"),
    ("Istanbul - Anadolu Hisari (IBB LIVE)", "ibb_anadoluhisari"),
    ("Istanbul - Eyup Sultan (IBB LIVE)", "ibb_eyupsultan"),
    ("Istanbul - Hidiv Kasri (IBB LIVE)", "ibb_hidivkasri"),
    ("Istanbul - Kucuk Cekmece (IBB LIVE)", "ibb_kucukcekmece"),
    ("Istanbul - Salacak (IBB LIVE)", "ibb_salacak"),
    ("Istanbul - Sarachane (IBB LIVE)", "ibb_sarachane"),
    ("Istanbul - Uskudar (IBB LIVE)", "ibb_uskudar"),
]


def airport_variant(stream_url, mount):
    # mijenja /igaistanbul/<nesto>/ u /igaistanbul/<mount>/
    return re.sub(
        r'(https://cdn-iga\.yayin\.com\.tr/igaistanbul/)[^/]+(/)',
        r'\1' + mount + r'\2',
        stream_url
    )


def http_get(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8"
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()

    return data.decode("utf-8", "ignore")


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


def get_ibb_chunklist_url(playlist_url):
    """
    IBB playlist radi preko curl-like requesta.
    Prvo uzmemo playlist.m3u8, iz njega izvucemo chunklist_w*.m3u8,
    pa Kodi pustamo direktno na chunklist.
    """
    headers = {
        "User-Agent": "curl/8.19.0",
        "Accept": "*/*"
    }

    xbmc.log(f"[{ADDON_NAME}] Fetching IBB playlist: {playlist_url}", xbmc.LOGINFO)

    req = urllib.request.Request(playlist_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        txt = resp.read().decode("utf-8", "ignore")

    xbmc.log(f"[{ADDON_NAME}] IBB PLAYLIST CONTENT: {txt}", xbmc.LOGINFO)

    for line in txt.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            chunklist_url = urllib.parse.urljoin(playlist_url, line)
            xbmc.log(f"[{ADDON_NAME}] IBB CHUNKLIST URL: {chunklist_url}", xbmc.LOGINFO)
            return chunklist_url

    xbmc.log(f"[{ADDON_NAME}] IBB chunklist not found, fallback to playlist", xbmc.LOGWARNING)
    return playlist_url


def list_root():
    handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(handle, ADDON_NAME)
    xbmcplugin.setContent(handle, "videos")

    airport_items = [
        ("Istanbul Airport - Apron 2 (LIVE)", "airport_apron2"),
        ("Istanbul Airport - Apron (LIVE)", "airport_apron"),
        ("Istanbul Airport - ApronG (LIVE)", "airport"),
    ]

    for label, cam in airport_items:
        li = xbmcgui.ListItem(label=label)
        li.setInfo("video", {"title": label})
        li.setProperty("IsPlayable", "true")
        url = sys.argv[0] + "?action=play&cam=" + cam
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)

    for label, cam in IBB_ITEMS:
        li = xbmcgui.ListItem(label=label)
        li.setInfo("video", {"title": label})
        li.setProperty("IsPlayable", "true")
        url = sys.argv[0] + "?action=play&cam=" + cam
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)

    xbmcplugin.endOfDirectory(handle)


def play(cam):
    handle = int(sys.argv[1])

    # IBB cams
    if cam in IBB_CAMS:
        playlist_url = IBB_CAMS[cam]

        try:
            chunklist_url = get_ibb_chunklist_url(playlist_url)
        except Exception as e:
            xbmc.log(f"[{ADDON_NAME}] IBB playlist error: {e}", xbmc.LOGERROR)
            chunklist_url = playlist_url

        headers = (
            "User-Agent=curl/8.19.0"
            "&Accept=*/*"
            "&Referer=" + urllib.parse.quote(playlist_url, safe="")
        )

        final_url = chunklist_url + "|" + headers
        xbmc.log(f"[{ADDON_NAME}] IBB FINAL URL: {final_url}", xbmc.LOGINFO)

        li = xbmcgui.ListItem(path=final_url)
        li.setProperty("IsPlayable", "true")
        li.setMimeType("application/vnd.apple.mpegurl")
        xbmcplugin.setResolvedUrl(handle, True, li)
        return

    # Airport cams (dynamic token)
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

    if cam == "airport_apron":
        stream_url = airport_variant(stream_url, "apron")
    else:
        stream_url = airport_variant(stream_url, "apron2")

    airport_headers = (
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
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
