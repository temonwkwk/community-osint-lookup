#!/usr/bin/env python3
"""Community OSINT & Multi-Community Intelligence (`community_osint.py`)

Input Format (Excel / CSV):
  Nama Komunitas | Deskripsi Komunitas | Nama PIC Komunitas | Email PIC | Nomor HP PIC

Structured Excel Output Columns:
  1. Wilayah Terdeteksi (Kota & Provinsi)
  2. Sosmed Resmi Komunitas (IG, FB Page, Linktree, Web)
  3. Komunitas Lain Milik PIC (Multi-community portfolio)
  4. Jejaring Chapter & Induk Paguyuban (Federation / Chapter network)
  5. Agenda / Event Terdekat (Outreach Timing Trigger: Anniversary, Touring, Cup, Gathering)
  6. Komunitas Sejenis di Daerah (Beserta IG @handle & Kontak CP/WA)
  7. Kontak Siap Hubungi (WA, DM IG/FB, Email)
  8. Community Intelligence Summary (Catatan ringkas lengkap)

Usage:
  python3 community_osint.py input.xlsx [--search-cache cache.json] [--dump-queries q.json] [--no-live-search]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from indonesian_regions import CITY_TO_PROVINCE_MAP
except ImportError:
    CITY_TO_PROVINCE_MAP = {
        "jakarta": ("Jakarta", "DKI Jakarta"),
        "bandung": ("Bandung", "Jawa Barat"),
        "surabaya": ("Surabaya", "Jawa Timur"),
        "yogyakarta": ("Yogyakarta", "DI Yogyakarta"),
        "semarang": ("Semarang", "Jawa Tengah"),
        "medan": ("Medan", "Sumatera Utara"),
        "makassar": ("Makassar", "Sulawesi Selatan"),
        "bali": ("Denpasar", "Bali"),
        "kuningan": ("Kuningan", "Jawa Barat"),
        "cirebon": ("Cirebon", "Jawa Barat"),
    }

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

COMMUNITY_NICHE_KEYWORDS = [
    # Olahraga & Hobi
    "tennis", "tenis", "lari", "running", "marathon", "sepeda", "cycling", "gowes",
    "motor", "motoran", "touring", "riding", "otomotif", "kopi", "coffee", "barista",
    "fotografi", "photography", "hiking", "gunung", "backpacker", "traveler", "kuliner",
    "badminton", "bulutangkis", "futsal", "basket", "gym", "fitness", "yoga", "diving", "surfing",
    # Event & Hiburan
    "event", "organizer", "eo", "wedding", "mice", "gathering", "party", "hiburan", "entertainment", "pameran", "expo",
    # Lingkungan & Sosial
    "lingkungan", "sampah", "plastik", "hutan", "relawan", "volunteer", "baksos", "charity",
    "sosial", "donasi", "peduli", "kemanusiaan", "pemberdayaan", "yayasan",
    # Teknologi & Bisnis
    "programming", "developer", "coding", "python", "javascript", "golang", "flutter",
    "devops", "cloud", "data science", "ai", "artificial intelligence", "cybersecurity",
    "startup", "umkm", "bisnis", "investasi", "saham", "crypto", "marketing", "digital marketing",
    # Edukasi, Anak & Keluarga
    "parenting", "ibu", "anak", "edukasi", "pendidikan", "beasiswa", "mahasiswa", "pelajar",
    # Seni & Kreatif
    "desain", "design", "ui ux", "animasi", "film", "musik", "teater", "tari",
]

SOCIAL_PATTERNS = {
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)/?", re.I),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/@([A-Za-z0-9_.]+)", re.I),
    "facebook_page": re.compile(r"https?://(?:www\.|web\.|m\.)?facebook\.com/(?:pages/|p/)?([A-Za-z0-9_.\-]+)/?", re.I),
    "facebook_group": re.compile(r"https?://(?:www\.|web\.|m\.)?facebook\.com/groups/([A-Za-z0-9_.\-]+)", re.I),
    "twitter": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/([A-Za-z0-9_]+)", re.I),
    "threads": re.compile(r"https?://(?:www\.)?threads\.net/@([A-Za-z0-9_.]+)", re.I),
    "linkedin": re.compile(r"https?://(?:[a-z]{2}\.)?linkedin\.com/(?:company|school)/([A-Za-z0-9\-_%]+)", re.I),
    "linktree": re.compile(r"https?://(?:www\.)?(?:linktr\.ee|campsite\.bio|taplink\.cc|biolinky\.co)/([A-Za-z0-9_.\-]+)", re.I),
    "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/@([A-Za-z0-9_.\-]+)", re.I),
    "website": re.compile(r"https?://(?:www\.)?([A-Za-z0-9\-]+\.(?:org|id|com|net|io|co\.id|or\.id))(?:/[^\s]*)?", re.I),
}

RESERVED = {
    "p", "reel", "reels", "explore", "stories", "tv", "accounts", "about", "privacy",
    "help", "legal", "developer", "directory", "share", "profile.php", "pages", "groups",
    "watch", "events", "marketplace", "hashtag", "story", "i", "home",
    "search", "login", "signup", "policies", "terms", "settings", "notifications",
    "intent", "status", "people", "photo", "media", "tag", "discover",
}


# --------------------------------------------------------------------------- search engine

class SearchEngine:
    """Cache-first search engine."""

    def __init__(self, cache_path: Path | None, live: bool, delay: float):
        self.cache_path = cache_path
        self.live = live
        self.delay = delay
        self.cache: dict[str, list] = {}
        self.missing: list[str] = []
        if cache_path and cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[warn] cache unreadable ({e}); starting empty", file=sys.stderr)

    def search(self, query: str) -> list[tuple[str, str]]:
        if query in self.cache:
            return [(u, t) for u, t in self.cache[query]]
        if query not in self.missing:
            self.missing.append(query)
        if not self.live:
            return []
        res = self._ddg(query)
        if res:
            self.cache[query] = [list(x) for x in res]
            self._flush()
        time.sleep(self.delay)
        return res

    def _flush(self) -> None:
        if self.cache_path:
            self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1), encoding="utf-8")

    def _ddg(self, query: str, retries: int = 2) -> list[tuple[str, str]]:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
                body = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
                if "result__a" not in body:
                    time.sleep(5 + attempt * 5)
                    continue
                out = []
                for m in re.finditer(
                        r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                        body, re.S):
                    href, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
                    if "uddg=" in href:
                        uddg_m = re.search(r"uddg=([^&]+)", href)
                        href = urllib.parse.unquote(uddg_m.group(1)) if uddg_m else href
                    out.append((href, html.unescape(title).strip()))
                return out
            except Exception:
                time.sleep(3 + attempt * 3)
        return []


# --------------------------------------------------------------------------- analyzers

def extract_bio_contact_signals(text: str) -> list[str]:
    """Extract WhatsApp, Contact Person (CP/Admin/PIC), email, and bio links from community snippet."""
    signals = []
    # WhatsApp / Phone
    wa_match = re.search(r"(?:WA|WhatsApp|Contact|Hubungi|Phone|Telp|Call|Hotline)[\s:]*([+\d\s-]{9,16})", text, re.I)
    if wa_match:
        clean_num = re.sub(r"[^\d+]", "", wa_match.group(1).strip())
        signals.append(f"WA: {clean_num}")
    # Contact Person Name
    cp_match = re.search(r"\b(?:CP|Contact Person|Admin|PIC|Narahubung)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text, re.I)
    if cp_match:
        signals.append(f"CP: {cp_match.group(1).strip()}")
    # Email in bio
    email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b", text)
    if email_match:
        signals.append(f"Email: {email_match.group(1)}")
    # Contact Links
    link_match = re.search(r"((?:https?://)?(?:wa\.me|linktr\.ee|biolinky\.co|campsite\.bio|taplink\.cc)/\S+)", text, re.I)
    if link_match:
        signals.append(f"Link: {link_match.group(1).strip().rstrip('.,;')}")
    return signals


def extract_community_socials(results: list[tuple[str, str]], comm_name: str) -> dict[str, dict]:
    """Extract social links dedicated to the community itself."""
    tally: dict[str, dict] = {}
    comm_clean = re.sub(r"[^a-zA-Z0-9]+", "", comm_name.lower())

    for url, title in results:
        for platform, pat in SOCIAL_PATTERNS.items():
            m = pat.search(url)
            if not m:
                continue
            handle = m.group(1).strip("/").lower()
            if not handle or handle in RESERVED or handle.startswith("profile.php"):
                continue

            sig = []
            f_match = re.search(r"([\d.,]+[KkMm]?\+?\s*(?:followers?|members?|pengikut|anggota))", title, re.I)
            if f_match:
                sig.append(f_match.group(1).strip())

            contacts = extract_bio_contact_signals(title)
            if contacts:
                sig.extend(contacts)

            score = 1.0
            handle_clean = re.sub(r"[^a-zA-Z0-9]+", "", handle)
            if comm_clean in handle_clean or handle_clean in comm_clean:
                score += 1.5
            if comm_name.lower() in title.lower():
                score += 1.0

            if platform not in tally or score > tally[platform]["score"]:
                tally[platform] = {
                    "handle": handle,
                    "url": url,
                    "title": title,
                    "score": score,
                    "signals": sig
                }

    return tally


def detect_community_region_structured(
    comm_texts: list[str],
    pic_texts: list[str] | None = None,
    phone: str = ""
) -> tuple[str, str]:
    """Identify City/Regency and Province in a structured hierarchy (Kota, Provinsi)."""
    scores: dict[str, int] = {}

    def score_corpus(texts: list[str], multiplier: int = 1):
        combined = " ".join(texts).lower()
        for key in sorted(CITY_TO_PROVINCE_MAP.keys(), key=len, reverse=True):
            pat = rf"\b{re.escape(key)}\b"
            matches = re.findall(pat, combined)
            if matches:
                scores[key] = scores.get(key, 0) + (len(matches) * multiplier)

    # 1. Score community text (highest weight)
    score_corpus(comm_texts, multiplier=3)

    # 2. Score PIC text (secondary weight for grassroots communities)
    if pic_texts:
        score_corpus(pic_texts, multiplier=2)

    # Pick the highest scoring specific city/region
    if scores:
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        best_key = ranked[0][0]
        city_name, prov_name = CITY_TO_PROVINCE_MAP[best_key]
        return (city_name, prov_name)

    # 3. Fallback to phone HLR area if available
    if phone:
        p_clean = re.sub(r"[^\d]", "", phone)
        if p_clean.startswith("021") or p_clean.startswith("6221"):
            return ("Jakarta", "DKI Jakarta")
        elif p_clean.startswith("022") or p_clean.startswith("6222"):
            return ("Bandung", "Jawa Barat")
        elif p_clean.startswith("024") or p_clean.startswith("6224"):
            return ("Semarang", "Jawa Tengah")
        elif p_clean.startswith("0274") or p_clean.startswith("62274"):
            return ("Yogyakarta", "DI Yogyakarta")
        elif p_clean.startswith("031") or p_clean.startswith("6231"):
            return ("Surabaya", "Jawa Timur")
        elif p_clean.startswith("0361") or p_clean.startswith("62361"):
            return ("Denpasar", "Bali")
        elif p_clean.startswith("061") or p_clean.startswith("6261"):
            return ("Medan", "Sumatera Utara")
        elif p_clean.startswith("0411") or p_clean.startswith("62411"):
            return ("Makassar", "Sulawesi Selatan")

    return ("Indonesia", "Cakupan Nasional")


def extract_community_niche(name: str, desc: str) -> list[str]:
    """Extract key themes/niches from community name and description."""
    # Skip deskripsi jika hanya berisi group order / order pekerja
    clean_desc = desc
    if re.search(r"\bgroup\s+order(?:\s+pekerja)?\b", desc, re.I):
        clean_desc = ""

    combined = (name + " " + clean_desc).strip().lower()
    found = []
    for kw in COMMUNITY_NICHE_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", combined, re.I):
            found.append(kw)
    if not found and clean_desc:
        # Fallback to description words (excluding generic/order words)
        words = [
            w for w in re.findall(r"\b[a-z]{4,}\b", combined)
            if w not in ("komunitas", "group", "official", "indonesia", "order", "pekerja", "karyawan", "member")
        ]
        found = words[:2]
    return found[:4]


GLOBAL_ORGANIZATIONS_BLACKLIST = {
    # Diving & Water Safety Bodies
    "divers alert network", "dan", "padi", "ssi", "naui", "cmas", "scuba schools international",
    "professional association of diving instructors",
    # Sports & Global Federations
    "fifa", "fiba", "atp", "wta", "bwf", "fim", "fia", "ittf", "ioc", "koni", "imi",
    # Tech Giants & Social Platforms
    "google", "microsoft", "apple", "amazon", "meta", "facebook", "instagram",
    "twitter", "tiktok", "youtube", "linkedin", "spotify", "telegram", "whatsapp",
    # International & Government Agencies
    "unesco", "unicef", "who", "united nations", "pbb", "red cross", "palang merah",
    "kemenpora", "kemenparekraf", "kementerian", "pemerintah", "pemprov", "pemda",
}


def extract_other_pic_communities(
    results: list[tuple[str, str]],
    pic_name: str,
    current_comm: str,
    main_comm_handle: str = ""
) -> list[str]:
    """Find other projects, sister brands, festivals, networks, and communities initiated/managed by the PIC/entity (excluding global bodies)."""
    discovered = []
    seen = set()
    current_clean = re.sub(r"[^a-zA-Z0-9]+", "", current_comm.lower())

    org_patterns = [
        re.compile(
            r"\b(?:Founder|Co-Founder|Inisiator|Ketua|Leader|Presiden|Pimpinan|CEO|Owner|Direktur|Aktivis|Penggagas|Penyelenggara|Persembahan)\s+(?:of\s+|di\s+|dari\s+|oleh\s+)?([A-Z0-9][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){1,3})\b",
            re.I
        ),
        re.compile(
            r"\b([A-Z0-9][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){0,2}\s+(?:Festival|Network|Agency|Movement|Initiative|Collective|Project|Foundation|Group|Media))\b",
            re.I
        ),
    ]

    # Stopwords to filter out sentence fragments
    blacklist_words = {
        "the", "a", "an", "is", "are", "and", "or", "in", "on", "at", "to", "for", "with",
        "official", "photos", "videos", "reels", "posts", "facebook", "instagram", "tiktok"
    }

    for url, title in results:
        ig_handle = ""
        ig_m = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", url, re.I)
        if ig_m and ig_m.group(1).lower() not in RESERVED:
            ig_handle = f"@{ig_m.group(1)}"

        contacts = extract_bio_contact_signals(title)
        contact_suffix = f" [{', '.join(contacts)}]" if contacts else ""

        for p in org_patterns:
            for m in p.finditer(title):
                cand = m.group(1).strip(" -–—|·,:")
                cand_clean = re.sub(r"[^a-zA-Z0-9]+", "", cand.lower())
                cand_lower = cand.lower().strip()
                words = cand_lower.split()

                if len(cand) < 4 or cand_clean in seen:
                    continue
                # Skip global bodies and tech platforms
                if cand_lower in GLOBAL_ORGANIZATIONS_BLACKLIST or any(gb in cand_lower for gb in GLOBAL_ORGANIZATIONS_BLACKLIST):
                    continue
                if any(w in blacklist_words for w in words[:1]) and len(words) > 2:
                    continue
                if current_clean and (current_clean in cand_clean and len(cand_clean) - len(current_clean) < 3):
                    continue
                seen.add(cand_clean)

                if ig_handle:
                    discovered.append(f"{cand} ({ig_handle}){contact_suffix}")
                elif main_comm_handle:
                    discovered.append(f"{cand} (IG sama dengan induk: @{main_comm_handle}){contact_suffix}")
                else:
                    discovered.append(f"{cand}{contact_suffix}")

    return discovered[:5]


def extract_similar_communities(results: list[tuple[str, str]], current_comm: str) -> list[str]:
    """Extract names, handles, and contacts of peer/similar communities with direct Instagram handles."""
    discovered = []
    seen = set()
    current_clean = re.sub(r"[^a-zA-Z0-9]+", "", current_comm.lower())

    comm_pat = re.compile(
        r"\b((?:Komunitas|Grup|Forum|Yayasan|Perkumpulan|Paguyuban|Club|Community|Society|Movement|Alliance|Kolektif|Chapter)\s+[A-Z][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){1,3})\b",
        re.I
    )
    comm_pat_en = re.compile(
        r"\b([A-Z][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){1,3}\s+(?:Community|Club|Group|Forum|Movement|Foundation|Network|Chapter|Collective))\b",
        re.I
    )

    for url, title in results:
        ig_handle = ""
        ig_m = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", url, re.I)
        if ig_m and ig_m.group(1).lower() not in RESERVED:
            ig_handle = f" (@{ig_m.group(1)})"

        contacts = extract_bio_contact_signals(title)
        contact_suffix = f" [{', '.join(contacts)}]" if contacts else ""

        for p in (comm_pat, comm_pat_en):
            for m in p.finditer(title):
                cand = m.group(1).strip(" -–—|·,:")
                cand_clean = re.sub(r"[^a-zA-Z0-9]+", "", cand.lower())
                if len(cand) < 5 or cand.lower() in seen:
                    continue
                if current_clean and (current_clean in cand_clean or cand_clean in current_clean):
                    continue
                seen.add(cand.lower())
                discovered.append(f"{cand}{ig_handle}{contact_suffix}")

    return discovered[:6]


def extract_chapter_federation_network(
    results: list[tuple[str, str]],
    comm_name: str,
    city: str,
    province: str
) -> list[str]:
    """Discover federation affiliations (Paguyuban/Induk) and sibling regional chapters."""
    discovered = []
    seen = set()
    comm_clean = re.sub(r"[^a-zA-Z0-9]+", "", comm_name.lower())

    fed_pat = re.compile(
        r"\b((?:Paguyuban|Ikatan|Asosiasi|Federasi|Aliansi|Pengda|Pengcab|Korwil|Forum Komunikasi|Induk)\s+[A-Z][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){1,3})\b",
        re.I
    )
    chapter_pat = re.compile(
        r"\b([A-Z][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){0,2}\s+(?:Chapter\s+[A-Z][\w&'\-]+|Korwil\s+[A-Z][\w&'\-]+))\b",
        re.I
    )

    for url, title in results:
        ig_handle = ""
        ig_m = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", url, re.I)
        if ig_m and ig_m.group(1).lower() not in RESERVED:
            ig_handle = f" (@{ig_m.group(1)})"

        for p in (fed_pat, chapter_pat):
            for m in p.finditer(title):
                cand = m.group(1).strip(" -–—|·,:")
                cand_clean = re.sub(r"[^a-zA-Z0-9]+", "", cand.lower())
                if len(cand) < 6 or cand.lower() in seen:
                    continue
                if comm_clean in cand_clean and len(cand_clean) - len(comm_clean) < 3:
                    continue
                seen.add(cand.lower())
                discovered.append(f"{cand}{ig_handle}")

    return discovered[:5]


def extract_event_agenda_triggers(results: list[tuple[str, str]], city: str = "") -> list[str]:
    """Detect community's upcoming events or regional festivals with date/article link, filtering out past events."""
    triggers = []
    seen = set()
    current_year = 2026

    # Past date indicators
    past_years = [str(y) for y in range(2015, current_year)]  # 2015..2025

    event_patterns = [
        re.compile(r"\b((?:Anniversary|Deklarasi|Milad|HUT)\s+(?:ke-?\d+|\d+th|\d+)?(?:\s+[A-Z][\w&'\-]+){0,2})\b", re.I),
        re.compile(r"\b((?:Touring|Tour de|Sunmori|Night Ride|Rolling Thunder|Kopdargab|Kopdar Akbar|Gathering|Family Gathering)\s+[A-Z0-9][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){0,2})\b", re.I),
        re.compile(r"\b((?:Turnamen|Cup|Championship|Liga|Sparring|Fun Match|Festival|Fun Run|Marathon|Exhibition|Expo|Summit|Baksos|Bakti Sosial)\s+[A-Z0-9][\w&'\-]*(?:\s+[A-Z0-9][\w&'\-]*){0,2})\b", re.I),
    ]

    for url, title in results:
        # Filter out past events (e.g. 2019, 2020, 2021, 2022, 2023, 2024, 2025)
        combined_text = f"{title} {url}"
        if any(re.search(rf"\b{py}\b", combined_text) for py in past_years):
            continue

        # Extract date indicator if present (e.g. 2026, 2027, 'Oktober 2026', '14-15 Oktober 2026')
        date_match = re.search(r"\b(?:\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+)?(?:202[6-9]|203[0-9])\b", title, re.I)
        date_str = f" [{date_match.group(0)}]" if date_match else ""

        # Filter: require explicit future year or relevant upcoming keyword if it's a general article
        has_future_signal = bool(date_match) or any(k in title.lower() for k in ("mendatang", "siap digelar", "jadwal", "2026", "2027"))
        if not has_future_signal:
            continue

        for p in event_patterns:
            for m in p.finditer(title):
                cand = m.group(1).strip(" -–—|·,:")
                cand_clean = cand.lower()
                if len(cand) < 6 or cand_clean in seen:
                    continue
                seen.add(cand_clean)
                triggers.append(f"{cand}{date_str} - Sumber: {url}")

    return triggers[:4]


# --------------------------------------------------------------------------- query generators

def generate_community_queries(comm_name: str) -> list[str]:
    """Generate search queries to find the community's official social media presence and sister projects."""
    qs = []
    seen = set()

    def add(q: str):
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            qs.append(q)

    add(f'"{comm_name}"')
    add(f'"{comm_name}" site:instagram.com OR site:tiktok.com')
    add(f'"{comm_name}" site:facebook.com -site:facebook.com/groups')
    add(f'"{comm_name}" (festival OR project OR network OR yayasan OR inisiatif OR event OR agency)')
    add(f'"{comm_name}" site:linktr.ee OR site:campsite.bio OR site:taplink.cc')
    add(f'"{comm_name}" instagram')
    add(f'"{comm_name}" (facebook page OR facebook profil)')

    return qs


def generate_pic_queries(pic_name: str, current_comm: str) -> list[str]:
    """Generate search queries to track PIC personal profile, domicile, and other organizations."""
    qs = []
    seen = set()

    def add(q: str):
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            qs.append(q)

    if pic_name:
        is_single_word = len(pic_name.strip().split()) < 2
        if is_single_word:
            # Single-word names must be bound to community name to avoid generic homonym noise
            add(f'"{pic_name}" "{current_comm}"')
            add(f'"{pic_name}" "{current_comm}" (founder OR ketua OR leader OR direktur OR inisiator)')
            add(f'"{pic_name}" "{current_comm}" site:linkedin.com/in')
            add(f'"{pic_name}" "{current_comm}" site:facebook.com OR site:instagram.com')
        else:
            add(f'"{pic_name}" (founder OR inisiator OR ketua OR leader OR pimpinan OR penggagas) -"{current_comm}"')
            add(f'"{pic_name}" (komunitas OR yayasan OR project OR "movement" OR perkumpulan) -"{current_comm}"')
            add(f'"{pic_name}" site:linkedin.com/in')
            add(f'"{pic_name}" site:facebook.com -site:facebook.com/groups')
            add(f'"{pic_name}" site:instagram.com')

    return qs


def generate_peer_comm_queries(niches: list[str], city: str, province: str) -> list[str]:
    """Generate search queries to discover peer/similar communities with direct Instagram handles."""
    qs = []
    seen = set()

    def add(q: str):
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            qs.append(q)

    for n in niches[:2]:
        if city and city != "Indonesia":
            add(f'site:instagram.com "{city}" "komunitas {n}" OR "{n} club"')
            add(f'site:instagram.com "{city} chapter" "{n}"')
            add(f'komunitas "{n}" "{city}" site:instagram.com')
            add(f'daftar komunitas {n} {city}')
        if province and province != "Cakupan Nasional":
            add(f'site:instagram.com "paguyuban {n}" "{province}"')
            add(f'komunitas {n}" "{province}"')

    return qs


def generate_federation_chapter_queries(comm_name: str, niches: list[str], city: str, province: str) -> list[str]:
    """Generate queries for parent federation, regional chapters, and upcoming events in the region."""
    qs = []
    seen = set()

    def add(q: str):
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            qs.append(q)

    if niches:
        n = niches[0]
        if province and province != "Cakupan Nasional":
            add(f'site:instagram.com "paguyuban {n}" "{province}"')
            add(f'site:instagram.com "ikatan {n}" "{province}"')
        if city and city != "Indonesia":
            add(f'site:instagram.com "{comm_name}" chapter OR korwil OR paguyuban')
            add(f'site:instagram.com event "{n}" "{city}" OR festival OR tournament OR gathering')
            add(f'jadwal event "{n}" "{city}" 2026')

    return qs


# --------------------------------------------------------------------------- io

def normalize_community_headers(headers: list[str]) -> dict[str, int]:
    idx = {}
    for i, h in enumerate(headers):
        key = (h or "").strip().lower()
        if any(k in key for k in ("pic", "pengurus", "ketua", "founder", "leader", "penanggung jawab")):
            if any(e in key for e in ("email", "mail")):
                idx["pic_email"] = i
            elif any(p in key for p in ("nomor", "no", "hp", "phone", "telepon", "wa")):
                idx["pic_phone"] = i
            else:
                idx["pic_name"] = i
        elif any(k in key for k in ("email", "mail", "e-mail")):
            idx["pic_email"] = i
        elif any(k in key for k in ("nomor", "no hp", "nohp", "phone", "telepon", "wa", "whatsapp")):
            idx["pic_phone"] = i
        elif any(k in key for k in ("deskripsi", "description", "kegiatan", "tentang", "about")):
            idx["description"] = i
        elif any(k in key for k in ("nama komunitas", "nama", "komunitas", "community", "nama group", "nama grup", "organisasi")):
            idx["community_name"] = i
    return idx


def load_rows(path: Path, sheet: str | None):
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True)
        ws = wb[sheet] if sheet else (wb.active or wb.create_sheet())
        rows = [[(c if c is not None else "") for c in r]
                for r in ws.iter_rows(values_only=True)]
        return rows[0], rows[1:]
    import csv
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def main() -> int:
    ap = argparse.ArgumentParser(description="Community OSINT & Multi-Community Intelligence Mapping")
    ap.add_argument("input", help="Input file (.xlsx or .csv)")
    ap.add_argument("--sheet", default=None, help="Sheet name for Excel file")
    ap.add_argument("--search-cache", default=None, help="Path to JSON search cache")
    ap.add_argument("--dump-queries", default=None, help="Dump missing queries to JSON for batch retrieval")
    ap.add_argument("--no-live-search", action="store_true", help="Disable live DuckDuckGo/Google search")
    ap.add_argument("--delay", type=float, default=4.0, help="Delay between search requests in seconds")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of rows processed")
    args = ap.parse_args()

    src = Path(args.input).expanduser()
    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        return 1

    headers, rows = load_rows(src, args.sheet)
    headers = [str(h) for h in headers]
    idx = normalize_community_headers(headers)

    if "community_name" not in idx:
        print(f"Header 'Nama Komunitas' tidak ditemukan di: {headers}", file=sys.stderr)
        return 1

    if args.limit:
        rows = rows[: args.limit]

    eng = SearchEngine(Path(args.search_cache) if args.search_cache else None,
                       live=not args.no_live_search, delay=args.delay)

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active or wb.create_sheet()
    ws.title = "community_osint_result"

    # Define Structured Output Columns
    structured_new_cols = [
        "Wilayah Terdeteksi",
        "Sosmed Resmi Komunitas",
        "Komunitas Lain Milik PIC",
        "Jejaring Chapter & Induk",
        "Agenda / Event Terdekat",
        "Komunitas Sejenis di Daerah",
    ]

    out_headers = list(headers)
    for col in structured_new_cols:
        if col.lower() not in [h.lower() for h in headers]:
            out_headers.append(col)

    ws.append(out_headers)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    col_map = {col: out_headers.index(col) for col in structured_new_cols}

    for n, row in enumerate(rows, 1):
        row = list(row) + [""] * (len(headers) - len(row))
        comm_name = str(row[idx["community_name"]]).strip() if "community_name" in idx else ""
        desc = str(row[idx["description"]]).strip() if "description" in idx else ""
        pic_name = str(row[idx["pic_name"]]).strip() if "pic_name" in idx else ""
        pic_email = str(row[idx["pic_email"]]).strip() if "pic_email" in idx else ""
        pic_phone = str(row[idx["pic_phone"]]).strip() if "pic_phone" in idx else ""

        if not comm_name:
            continue

        print(f"\n[{n}/{len(rows)}] 🏢 Memproses Komunitas: {comm_name} (PIC: {pic_name or '-'})", flush=True)

        # -------------------------------------------------------------
        # STEP 1: Community Official Socials & Bio Contact Discovery
        # -------------------------------------------------------------
        comm_queries = generate_community_queries(comm_name)
        print(f"  [Step 1] Mencari Sosmed & Bio Kontak Komunitas ({len(comm_queries)} query)...", flush=True)
        comm_results = []
        for q in comm_queries:
            print(f"           -> Q: {q}", flush=True)
            comm_results += eng.search(q)

        socials = extract_community_socials(comm_results, comm_name)
        main_handle = socials.get("instagram", {}).get("handle", "")

        # -------------------------------------------------------------
        # STEP 2: PIC Multi-Organization & Domicile Discovery
        # -------------------------------------------------------------
        pic_results = []
        pic_other_comms = []
        if pic_name:
            pic_queries = generate_pic_queries(pic_name, comm_name)
            print(f"  [Step 3] Melacak Profil & Organisasi Lain PIC ({len(pic_queries)} query)...", flush=True)
            for q in pic_queries:
                print(f"           -> Q: {q}", flush=True)
                pic_results += eng.search(q)
            pic_other_comms = extract_other_pic_communities(pic_results + comm_results, pic_name, comm_name, main_comm_handle=main_handle)
            print(f"           Komunitas/Project Lain: {', '.join(pic_other_comms) if pic_other_comms else '-'}", flush=True)

        # -------------------------------------------------------------
        # STEP 4: Structured Geographic Resolution (Kota & Provinsi)
        # -------------------------------------------------------------
        comm_snippets = [t for _, t in comm_results] + [desc, comm_name]
        pic_snippets = [t for _, t in pic_results]
        city, province = detect_community_region_structured(comm_snippets, pic_snippets, phone=pic_phone)
        region_display = f"{city}, {province}" if city != province and city != "Indonesia" else f"{city} ({province})"
        print(f"  [Step 4] Wilayah Terdeteksi: {region_display}", flush=True)

        # -------------------------------------------------------------
        # STEP 5: Event Trigger Discovery (Future/Upcoming Events Only)
        # -------------------------------------------------------------
        niches = extract_community_niche(comm_name, desc)
        event_queries = []
        if niches and city and city != "Indonesia":
            event_queries.append(f'jadwal event "{niches[0]}" "{city}" 2026')
            event_queries.append(f'festival "{niches[0]}" "{city}" 2026')
        
        event_results = []
        for q in event_queries:
            event_results += eng.search(q)

        all_event_pool = comm_results + event_results
        event_triggers = extract_event_agenda_triggers(all_event_pool, city=city)
        pic_other_comms = extract_other_pic_communities(pic_results + comm_results, pic_name, comm_name, main_comm_handle=main_handle)

        # -------------------------------------------------------------
        # STEP 6: Peer / Similar Communities in the Specific Region
        # -------------------------------------------------------------
        similar_comms = []
        if niches:
            peer_queries = generate_peer_comm_queries(niches, city, province)
            print(f"  [Step 6] Mencari Komunitas Sejenis di {region_display} (Niche: {', '.join(niches)})...", flush=True)
            peer_results = []
            for q in peer_queries:
                print(f"           -> Q: {q}", flush=True)
                peer_results += eng.search(q)
            similar_comms = extract_similar_communities(peer_results, comm_name)
            print(f"           Komunitas Sejenis: {', '.join(similar_comms) if similar_comms else '-'}", flush=True)

        # -------------------------------------------------------------
        # STEP 7: Format Structured Data Values for Output
        # -------------------------------------------------------------
        # 1. Official Social Media
        comm_socmed_list = []
        for plat, label in (
            ("instagram", "IG"), ("facebook_page", "FB Page / Profil"),
            ("tiktok", "TikTok"), ("threads", "Threads"), ("linktree", "Linktree/Biolink"),
            ("website", "Web Resmi"), ("linkedin", "LinkedIn"), ("facebook_group", "FB Group")
        ):
            if plat in socials:
                d = socials[plat]
                sig_str = f" ({', '.join(d['signals'])})" if d.get("signals") else ""
                comm_socmed_list.append(f"{label}: {d['url']}{sig_str}")
        val_socmed = "\n".join(comm_socmed_list) if comm_socmed_list else "Belum ditemukan publik"

        # 2. Other Communities of PIC
        val_other_pic = "\n".join(pic_other_comms) if pic_other_comms else "Tidak terdeteksi / hanya komunitas ini"

        # 3. Chapter & Federation Network (Skipped)
        val_federation = "-"

        # 4. Event / Agenda Triggers
        val_events = "\n".join(event_triggers) if event_triggers else "Tidak terdeteksi agenda mendatang"

        # 5. Similar Peer Communities
        val_peers = "\n".join(similar_comms) if similar_comms else f"Belum terdeteksi direktori komunitas sejenis di {city}"

        # Assemble Output Row
        out_row = [""] * len(out_headers)
        for i, v in enumerate(row):
            out_row[i] = str(v)

        out_row[col_map["Wilayah Terdeteksi"]] = region_display
        out_row[col_map["Sosmed Resmi Komunitas"]] = val_socmed
        out_row[col_map["Komunitas Lain Milik PIC"]] = val_other_pic
        out_row[col_map["Jejaring Chapter & Induk"]] = val_federation
        out_row[col_map["Agenda / Event Terdekat"]] = val_events
        out_row[col_map["Komunitas Sejenis di Daerah"]] = val_peers

        ws.append(out_row)

    # Format Column Widths & Alignment
    col_widths = {
        "Wilayah Terdeteksi": 25,
        "Sosmed Resmi Komunitas": 40,
        "Komunitas Lain Milik PIC": 30,
        "Jejaring Chapter & Induk": 32,
        "Agenda / Event Terdekat": 30,
        "Komunitas Sejenis di Daerah": 45,
    }

    for i, h in enumerate(out_headers, 1):
        letter = get_column_letter(i)
        ws.column_dimensions[letter].width = col_widths.get(h, 25)

    for r in ws.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(vertical="top", wrap_text=True)

    dest = src.with_name(src.stem + "_result.xlsx")
    wb.save(dest)
    print(f"\n✅ Hasil investigasi komunitas selesai disimpan ke: {dest}")

    if eng.missing:
        print(f"[cache] {len(eng.missing)} query belum ada di cache")
        if args.dump_queries:
            Path(args.dump_queries).write_text(
                json.dumps(eng.missing, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[cache] Daftar query berhasil ditulis ke {args.dump_queries}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
