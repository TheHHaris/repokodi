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
BASE = "https://kamerayayin.ibb.istanbul/turistikcam"

IBB_EMINONU_CHUNKLIST = f"{BASE}/eminonu.stream/playlist.m3u8"
IBB_BEYAZIT_CHUNKLIST = f"{BASE}/beyazitmeydan.stream/playlist.m3u8"
IBB_SAHMET_CHUNKLIST = f"{BASE}/sultanahmet2.stream/playlist.m3u8"
IBB_METROHAN_CHUNKLIST = f"{BASE}/metrohan.stream/playlist.m3u8"
IBB_KAPALICARSI_CHUNKLIST = f"{BASE}/misircarsisi.stream/playlist.m3u8"
IBB_BEYAZITKULESI_CHUNKLIST = f"{BASE}/beyazitkulesi2.stream/playlist.m3u8"
IBB_CAMLICA_CHUNKLIST = f"{BASE}/buyukcamlica.stream/playlist.m3u8"
IBB_KADIKOY_CHUNKLIST = f"{BASE}/kadikoy.stream/playlist.m3u8"
IBB_ORTAKOY_CHUNKLIST = f"{BASE}/ortakoy.stream/playlist.m3u8"
IBB_PIERELOTI_CHUNKLIST = f"{BASE}/pierreloti.stream/playlist.m3u8"
IBB_SAHMET1_CHUNKLIST = f"{BASE}/sultanahmet1.stream/playlist.m3u8"
IBB_TAKSIM_CHUNKLIST = f"{BASE}/taksim.stream/playlist.m3u8"
IBB_KIZKULESI_CHUNKLIST = f"{BASE}/kizkulesi.stream/playlist.m3u8"
IBB_ANADOLUHISARI_CHUNKLIST = f"{BASE}/anadoluhisari.stream/playlist.m3u8"
IBB_EYUPSULTAN_CHUNKLIST = f"{BASE}/eyupsultan.stream/playlist.m3u8"
IBB_HIDIVKASRI_CHUNKLIST = f"{BASE}/hidivkasri.stream/playlist.m3u8"
IBB_KUCUKCEKMECE_CHUNKLIST = f"{BASE}/kucukcekmece.stream/playlist.m3u8"
IBB_SALACAK_CHUNKLIST = f"{BASE}/salacak.stream/playlist.m3u8"
IBB_SARACHANE_CHUNKLIST = f"{BASE}/sarachane.stream/playlist.m3u8"
IBB_USKUDAR_CHUNKLIST = f"{BASE}/uskudar.stream/playlist.m3u8"

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
    "ibb_taksim": IBB_TAKSIM_CHUNKLIST,
    "ibb_kizkulesi": IBB_KIZKULESI_CHUNKLIST,
    "ibb_anadoluhisari": IBB_ANADOLUHISARI_CHUNKLIST,
    "ibb_eyupsultan": IBB_EYUPSULTAN_CHUNKLIST,
    "ibb_hidivkasri": IBB_HIDIVKASRI_CHUNKLIST,
    "ibb_kucukcekmece": IBB_KUCUKCEKMECE_CHUNKLIST,
    "ibb_salacak": IBB_SALACAK_CHUNKLIST,
    "ibb_sarachane": IBB_SARACHANE_CHUNKLIST,
    "ibb_uskudar": IBB_USKUDAR_CHUNKLIST
}

# Headers koje browser šalje (po tvom Network screenshotu)
IBB_HEADERS = (
    "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    "&Accept=*/*"
    "&Accept-Language=en-US,en;q=0.9,bs;q=0.8"
    "&Origin=https://istanbuluseyret.ibb.gov.tr"
    "&Referer=https://istanbuluseyret.ibb.gov.tr/"
    "&Sec-Fetch-Dest=empty"
    "&Sec-Fetch-Mode=cors"
    "&Sec-Fetch-Site=cross-site"
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

    # 6) IBB KCarsi
    li6 = xbmcgui.ListItem(label="Istanbul – Misir Carsi (IBB LIVE)")
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

    li14 = xbmcgui.ListItem(label="Istanbul – Kiz Kulesi (IBB LIVE)")
    li14.setInfo("video", {"title": "Istanbul – Kiz Kulesi (IBB LIVE)"})
    li14.setProperty("IsPlayable", "true")
    url14 = sys.argv[0] + "?action=play&cam=ibb_kizkulesi"
    xbmcplugin.addDirectoryItem(handle, url14, li14, isFolder=False)

    li15 = xbmcgui.ListItem(label="Istanbul – Anadolu Hisari (IBB LIVE)")
    li15.setInfo("video", {"title": "Istanbul – Anadolu Hisari (IBB LIVE)"})
    li15.setProperty("IsPlayable", "true")
    url15 = sys.argv[0] + "?action=play&cam=ibb_anadoluhisari"
    xbmcplugin.addDirectoryItem(handle, url15, li15, isFolder=False)

    li16 = xbmcgui.ListItem(label="Istanbul – Eyup Sultan (IBB LIVE)")
    li16.setInfo("video", {"title": "Istanbul – Eyup Sultan (IBB LIVE)"})
    li16.setProperty("IsPlayable", "true")
    url16 = sys.argv[0] + "?action=play&cam=ibb_eyupsultan"
    xbmcplugin.addDirectoryItem(handle, url16, li16, isFolder=False)

    li17 = xbmcgui.ListItem(label="Istanbul – Hidiv Kasri (IBB LIVE)")
    li17.setInfo("video", {"title": "Istanbul – Hidiv Kasri (IBB LIVE)"})
    li17.setProperty("IsPlayable", "true")
    url17 = sys.argv[0] + "?action=play&cam=ibb_hidivkasri"
    xbmcplugin.addDirectoryItem(handle, url17, li17, isFolder=False)

    li18 = xbmcgui.ListItem(label="Istanbul – Kucuk Cekmece (IBB LIVE)")
    li18.setInfo("video", {"title": "Istanbul – Kucuk Cekmece (IBB LIVE)"})
    li18.setProperty("IsPlayable", "true")
    url18 = sys.argv[0] + "?action=play&cam=ibb_kucukcekmece"
    xbmcplugin.addDirectoryItem(handle, url18, li18, isFolder=False)

    li19 = xbmcgui.ListItem(label="Istanbul – Salacak (IBB LIVE)")
    li19.setInfo("video", {"title": "Istanbul – Salacak (IBB LIVE)"})
    li19.setProperty("IsPlayable", "true")
    url19 = sys.argv[0] + "?action=play&cam=ibb_salacak"
    xbmcplugin.addDirectoryItem(handle, url19, li19, isFolder=False)

    li20 = xbmcgui.ListItem(label="Istanbul – Sarachane (IBB LIVE)")
    li20.setInfo("video", {"title": "Istanbul – Sarachane (IBB LIVE)"})
    li20.setProperty("IsPlayable", "true")
    url20 = sys.argv[0] + "?action=play&cam=ibb_sarachane"
    xbmcplugin.addDirectoryItem(handle, url20, li20, isFolder=False)

    li21 = xbmcgui.ListItem(label="Istanbul – Uskudar (IBB LIVE)")
    li21.setInfo("video", {"title": "Istanbul – Uskudar (IBB LIVE)"})
    li21.setProperty("IsPlayable", "true")
    url21 = sys.argv[0] + "?action=play&cam=ibb_uskudar"
    xbmcplugin.addDirectoryItem(handle, url21, li21, isFolder=False)

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
