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
IBB_KAPALICARSI_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_kapalicarsi.stream/chunklist.m3u8"
IBB_BEYAZITKULESI_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_beyazitkule.stream/chunklist.m3u8"
IBB_CAMLICA_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_buyukcaml%C4%B1ca.stream/chunklist.m3u8"
IBB_KADIKOY_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_kadikoy.stream/chunklist.m3u8"
IBB_ORTAKOY_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_ortakoy.stream/chunklist.m3u8"
IBB_PIERELOTI_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_pierreloti.stream/chunklist.m3u8"
IBB_SAHMET1_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_sultanahmet.stream/chunklist.m3u8"
IBB_TAKSIM_CHUNKLIST = "https://livestream.ibb.gov.tr/cam_turistik/b_taksim_meydan.stream/chunklist.m3u8"

IBB_CAMS = {
    "ibb_eminonu": IBB_EMINONU_CHUNKLIST,
    "ibb_beyazit": IBB_BEYAZIT_CHUNKLIST,
    "ibb_sahmet": IBB_SAHMET_CHUNKLIST,
    "ibb_metrohan": IBB_METROHAN_CHUNKLIST,
    "ibb_kapalicarsi": IBB_KAPALICARSI_CHUNKLIST,
    "ibb_bkulesi": IBB_BEYAZITKULESI_CHUNKLIST,
    "ibb_camlica": IBB_CAMLICA_CHUNKLIST,
    "ibb_kadikoy": IBB_KADIKOY_CHUNKLIST,
    "ibb_ortakoy": IBB_ORTAKOY_CHUNKLIST,
    "ibb_piereloti": IBB_PIERELOTI_CHUNKLIST,
    "ibb_sahmet1": IBB_SAHMET1_CHUNKLIST,
    "ibb_taksim": IBB_TAKSIM_CHUNKLIST
}

# Headers koje browser šalje (po tvom Network screenshotu)
IBB_HEADERS = (
    "User-Agent=Mozilla/5.0"
    "&Referer=https://istanbuluseyret.ibb.gov.tr/"
    "&Origin=https://istanbuluseyret.ibb.gov.tr"
)

def airport_variant(stream_url, mount):
    # mijenja /igaistanbul/<nesto>/ u /igaistanbul/<mount>/
    return re.sub(r'(https://cdn-iga\.yayin\.com\.tr/igaistanbul/)[^/]+(/)', r'\1' + mount + r'\2', stream_url)


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

    liA = xbmcgui.ListItem(label="Istanbul Airport – Apron 2 (LIVE)")
    liA.setInfo("video", {"title": "Istanbul Airport – Apron 2 (LIVE)"})
    liA.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(handle, sys.argv[0] + "?action=play&cam=airport_apron2", liA, False)

    liB = xbmcgui.ListItem(label="Istanbul Airport – Apron (LIVE)")
    liB.setInfo("video", {"title": "Istanbul Airport – Apron (LIVE)"})
    liB.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(handle, sys.argv[0] + "?action=play&cam=airport_apron", liB, False)


    # 1) Airport
    li1 = xbmcgui.ListItem(label="Istanbul Airport – ApronG (LIVE)")
    li1.setInfo("video", {"title": "Istanbul Airport – ApronG (LIVE)"})
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

    # 6) IBB KCarsi
    li6 = xbmcgui.ListItem(label="Istanbul – KapaliCarsi (IBB LIVE)")
    li6.setInfo("video", {"title": "Istanbul – KapaliCarsi (IBB LIVE)"})
    li6.setProperty("IsPlayable", "true")
    url6 = sys.argv[0] + "?action=play&cam=ibb_kapalicarsi"
    xbmcplugin.addDirectoryItem(handle, url6, li6, isFolder=False)

    li7 = xbmcgui.ListItem(label="Istanbul – Beyazit kulesi (IBB LIVE)")
    li7.setInfo("video", {"title": "Istanbul – Beyazit kulesi (IBB LIVE)"})
    li7.setProperty("IsPlayable", "true")
    url7 = sys.argv[0] + "?action=play&cam=ibb_bkulesi"
    xbmcplugin.addDirectoryItem(handle, url7, li7, isFolder=False)

    li8 = xbmcgui.ListItem(label="Istanbul – Buyuk camlica (IBB LIVE)")
    li8.setInfo("video", {"title": "Istanbul – Buyuk camlica (IBB LIVE)"})
    li8.setProperty("IsPlayable", "true")
    url8 = sys.argv[0] + "?action=play&cam=ibb_camlica"
    xbmcplugin.addDirectoryItem(handle, url8, li8, isFolder=False)

    li9 = xbmcgui.ListItem(label="Istanbul – Kadikoy (IBB LIVE)")
    li9.setInfo("video", {"title": "Istanbul – Kadikoy (IBB LIVE)"})
    li9.setProperty("IsPlayable", "true")
    url9 = sys.argv[0] + "?action=play&cam=ibb_kadikoy"
    xbmcplugin.addDirectoryItem(handle, url9, li9, isFolder=False)

    li10 = xbmcgui.ListItem(label="Istanbul – Ortakoy (IBB LIVE)")
    li10.setInfo("video", {"title": "Istanbul – Ortakoy (IBB LIVE)"})
    li10.setProperty("IsPlayable", "true")
    url10 = sys.argv[0] + "?action=play&cam=ibb_ortakoy"
    xbmcplugin.addDirectoryItem(handle, url10, li10, isFolder=False)

    li11 = xbmcgui.ListItem(label="Istanbul – Pierre lotti (IBB LIVE)")
    li11.setInfo("video", {"title": "Istanbul – Pierre lotti (IBB LIVE)"})
    li11.setProperty("IsPlayable", "true")
    url11 = sys.argv[0] + "?action=play&cam=ibb_piereloti"
    xbmcplugin.addDirectoryItem(handle, url11, li11, isFolder=False)

    li12 = xbmcgui.ListItem(label="Istanbul – Sultanahmet1 (IBB LIVE)")
    li12.setInfo("video", {"title": "Istanbul – Sultanahmet1 (IBB LIVE)"})
    li12.setProperty("IsPlayable", "true")
    url12 = sys.argv[0] + "?action=play&cam=ibb_sahmet1"
    xbmcplugin.addDirectoryItem(handle, url12, li12, isFolder=False)

    li13 = xbmcgui.ListItem(label="Istanbul – Taksim (IBB LIVE)")
    li13.setInfo("video", {"title": "Istanbul – Taksim (IBB LIVE)"})
    li13.setProperty("IsPlayable", "true")
    url13 = sys.argv[0] + "?action=play&cam=ibb_taksim"
    xbmcplugin.addDirectoryItem(handle, url13, li13, isFolder=False)

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

    # Biramo mount po odabiru
    if cam == "airport_apron":
        stream_url = airport_variant(stream_url, "apron")
    else:
        # default neka bude apron2
        stream_url = airport_variant(stream_url, "apron2")

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
