"""Assemble site/index.html from tools/pages/index.html (stage 1: homepage only).

Placeholders in the page template:
  <!--@head Title|Description-->   (no | inside the title)
  <!--@header-->  <!--@footer-->  <!--@actionbar-->
  <!--@icon name-->                 inline SVG icon
  <!--@img name|alt|sizes|tag|cls|eager-->  responsive <img> from assets/img/name-<w>.webp; tag = stock | hugo | ""
  {{TEL}} {{SMS}} {{EMAIL}} {{MAILTO}} {{GOOGLE}} {{MAPS}} {{CURRENT}} {{FB}} {{YELP}} {{YT}} {{PHONE}}
Owner questions (data-note) and fact sources (data-source) stay in the template for review and are stripped
from the output; they are collected in pitch/review-notes.md.
Run: python tools/build.py
"""
import base64, hashlib, html, re
from pathlib import Path
from PIL import Image

SITE = Path(__file__).resolve().parent.parent
PHONE = "(210) 396-0922"
TEL = "tel:+12103960922"
SMS = "sms:+12103960922"
EMAIL = "hugoroofer8888@gmail.com"
GOOGLE = "https://maps.google.com/?cid=14612401134964218356"
MAPS = "https://www.google.com/maps/search/?api=1&query=HG+Roof+Repair+345+N+San+Gabriel+Ave+San+Antonio+TX+78237&query_place_id=ChIJo1TTmrxeXIYR9JkOlWmtyco"
CURRENT = "https://hugoroofer8888.wixsite.com/hgroofrepair"
FB = "https://www.facebook.com/HugoAdolfoGuerraROOFER/"
YELP = "https://www.yelp.com/biz/hg-roof-repair-san-antonio-2"
YT = "https://www.youtube.com/@hugoguerra-ey1ls"

NAV = [("#services", "What he fixes"), ("#why", "Why Hugo"), ("#reviews", "Reviews"), ("#estimate", "Free estimate")]  # page order

ICONS = {
    "arrow-ur": '<path d="M7 17L17 7M9 7h8v8"/>',
    "arrow-r": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "chev-l": '<path d="M15 6l-6 6 6 6"/>',
    "chev-r": '<path d="M9 6l6 6-6 6"/>',
    "home": '<path d="M4 11l8-6.5 8 6.5"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-4.5a2 2 0 0 1 4 0V20"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 10h8"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "star": '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8L3.5 9.7l5.9-.8z" fill="currentColor"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    "fb": '<path d="M14 8h3V4h-3a4 4 0 0 0-4 4v3H7v4h3v6h4v-6h3l1-4h-4V8z"/>',
    "google": '<path d="M20 12.2c0-.6 0-1.1-.1-1.7H12v3.3h4.5a3.9 3.9 0 0 1-1.7 2.5v2h2.7c1.6-1.4 2.5-3.6 2.5-6.1z"/><path d="M12 20.5c2.3 0 4.2-.8 5.5-2.1l-2.7-2a5 5 0 0 1-7.5-2.7H4.5v2.1A8.5 8.5 0 0 0 12 20.5z"/><path d="M7.3 13.7a5 5 0 0 1 0-3.4V8.2H4.5a8.5 8.5 0 0 0 0 7.6z"/><path d="M12 6.9c1.3 0 2.4.4 3.3 1.3l2.4-2.4A8.5 8.5 0 0 0 4.5 8.2l2.8 2.1A5 5 0 0 1 12 6.9z"/>',
    "yelp": '<path d="M12.5 3.5l.3 8.1-5.4-6.2c1.4-1.2 3.2-1.9 5.1-1.9z"/><path d="M13.8 13.4l5.6-1.6a7.7 7.7 0 0 1-.6 4.9z"/><path d="M12.6 14.6l1.5 5.6a7.6 7.6 0 0 1-4.6-1.1z"/><path d="M11.1 13.2l-5.6 1.4a7.6 7.6 0 0 1 .5-5z"/>',
    "yt": '<rect x="3" y="6" width="18" height="12" rx="4"/><path d="M10.5 9.5v5l4.2-2.5z" fill="currentColor"/>',
    # service + benefit line icons (orange on light cards, white on the dark band)
    "drop": '<path d="M12 3s6 6.4 6 10.5a6 6 0 0 1-12 0C6 9.4 12 3 12 3z"/><path d="M9.5 14.5a2.6 2.6 0 0 0 2.5 2.5"/>',
    "shingles": '<path d="M3 9l9-5 9 5"/><path d="M5 13h14M5 17h14"/><path d="M9 13v4M15 13v4M12 17v3M7 17v3M17 17v3"/>',
    "wind": '<path d="M3 9h11a3 3 0 1 0-3-3"/><path d="M3 13h15a3 3 0 1 1-3 3"/><path d="M3 17h7"/>',
    "tile": '<path d="M3 16c0-3 2-5 4.5-5S12 13 12 16"/><path d="M12 16c0-3 2-5 4.5-5S21 13 21 16"/><path d="M3 16v3h18v-3"/><path d="M7.5 11c0-3 2-5 4.5-5s4.5 2 4.5 5"/>',
    "flat": '<path d="M3 10h18v4H3z"/><path d="M5 14v5M19 14v5"/><path d="M7 7h10"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/><path d="M8 10.5l2 2 3-3.5"/>',
    "fan": '<circle cx="12" cy="12" r="2"/><path d="M12 10c0-4 1-6 3-6s2 4-3 6zM14 12c4 0 6 1 6 3s-4 2-6-3zM12 14c0 4-1 6-3 6s-2-4 3-6zM10 12c-4 0-6-1-6-3s4-2 6 3z"/>',
    "bolt": '<path d="M13 3L5 14h6l-1 7 8-11h-6z"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "clipboard": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9z"/><path d="M8.5 12h7M8.5 16h5"/>',
    "tag": '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/><path d="M8.5 14.5l2 2 4-4"/>',
    "house": '<path d="M3 11l9-7 9 7"/><path d="M5 9.5V20h14V9.5"/><path d="M9.5 20v-6h5v6"/>',
}


def icon(n, cls="", w=20, sw=1.6):
    return (f'<svg class="ico {cls}" viewBox="0 0 24 24" width="{w}" height="{w}" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[n]}</svg>')


def esc(s):
    return html.escape(str(s), quote=True)


def link(u):
    """A supplied link, escaped. Only web, email, sms and phone links get through (no javascript: or data:)."""
    u = str(u or "").strip()
    return esc(u) if re.match(r"(?i)(https?://|mailto:|tel:|sms:|#)", u) else "#"


# The one inline script (adds the "js" class). The policy allows it by hash, so no other inline script can run.
JS_FLAG = "document.documentElement.classList.add('js');setTimeout(function(){if(!window.HG)document.documentElement.classList.remove('js')},3000)"
CSP = ("default-src 'self'; script-src 'self' 'sha256-" + base64.b64encode(hashlib.sha256(JS_FLAG.encode()).digest()).decode() + "'; "
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; "
       "connect-src 'self'; frame-src 'none'; form-action 'self'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests")
FONTS = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,600;125,700&family=Hanken+Grotesk:wght@400;500;600&family=Inter+Tight:wght@500;600&display=swap"


def ver(rel):
    return int((SITE / rel).stat().st_mtime)


def head(title, desc):
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0B0B0C">
<meta name="color-scheme" content="light">
<meta name="robots" content="noindex, nofollow">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<script>{JS_FLAG}</script>
<link rel="icon" href="assets/img/favicon.ico?v={ver("assets/img/favicon.ico")}" sizes="any">
<link rel="icon" type="image/png" href="assets/img/favicon.png?v={ver("assets/img/favicon.png")}">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png?v={ver("assets/img/apple-touch-icon.png")}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="preload" as="image" href="assets/img/hero-1400.webp" imagesrcset="assets/img/hero-800.webp 800w, assets/img/hero-1400.webp 1400w, assets/img/hero-1670.webp 1670w" imagesizes="100vw">
<link rel="stylesheet" href="assets/css/site.css?v={ver("assets/css/site.css")}">
<script src="assets/js/site.js?v={ver("assets/js/site.js")}" defer></script>'''


def header():
    # Home starts highlighted; site.js moves the orange pill to whatever was clicked, and to the section on screen while scrolling
    links = f'<a class="is-active" href="#top" aria-current="true" data-spy>{icon("home", w=18)}<span>Home</span></a>' + "".join(
        f'<a href="{h}" data-spy>{t}</a>' for h, t in NAV)
    mlinks = '<a href="#top">Home</a>' + "".join(f'<a href="{h}">{t}</a>' for h, t in NAV)
    return f'''<a class="skip" href="#main">Skip to content</a>
<p class="concept-bar">Concept redesign for review. Not the official HG Roof Repair website. <a href="{CURRENT}">See the current site</a></p>
<header class="site-header" data-header>
  <a class="brand" href="#top" aria-label="HG Roof Repair, back to top"><span class="brand-mark">HG</span><span class="brand-word">Roof Repair</span></a>
  <nav class="nav-pill" aria-label="Main">{links}</nav>
  <a class="pill pill-white pill-sm header-cta" href="{TEL}" aria-label="Call or text Hugo at {PHONE}"><span>Call or text Hugo</span><span class="pill-ico orange">{icon("arrow-ur", w=16, sw=2)}</span></a>
  <button class="menu-btn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-nav">{icon("menu", w=22, sw=2)}</button>
</header>
<div class="mobile-nav" id="mobile-nav" role="dialog" aria-modal="true" aria-label="Site menu" hidden>
  <div class="mobile-top"><span class="brand"><span class="brand-mark">HG</span><span class="brand-word">Roof Repair</span></span><button class="close" type="button" aria-label="Close menu">{icon("x", w=22, sw=2)}</button></div>
  <nav aria-label="Mobile">{mlinks}</nav>
  <p class="mobile-meta"><a href="{TEL}">Call {PHONE}</a> · <a href="{SMS}">Text a photo</a><br>345 N San Gabriel Ave, San Antonio, TX 78237</p>
</div>'''


def action_bar():
    return f'''<div class="action-bar" aria-label="Quick actions">
  <a class="primary" href="{TEL}">{icon("phone", w=18, sw=2)} Call Hugo</a>
  <a href="{SMS}">{icon("chat", w=18, sw=2)} Text</a>
  <a href="#estimate">{icon("clipboard", w=18, sw=2)} Estimate</a>
</div>
<p id="sr-live" class="sr-only" aria-live="polite"></p>'''


def footer():
    nav = '<a href="#top">Home</a>' + "".join(f'<a href="{h}">{t}</a>' for h, t in NAV) 
    social = (f'<a class="sq" href="{FB}" aria-label="HG Roof Repair on Facebook">{icon("fb", w=18)}</a>'
              f'<a class="sq" href="{GOOGLE}" aria-label="HG Roof Repair on Google">{icon("google", w=18)}</a>'
              f'<a class="sq" href="{YELP}" aria-label="HG Roof Repair on Yelp">{icon("yelp", w=18)}</a>'
              f'<a class="sq" href="{YT}" aria-label="Hugo Guerra on YouTube">{icon("yt", w=18)}</a>')
    return f'''<footer class="site-footer">
  <div class="footer-top">
    <p class="footer-word">HG Roof Repair</p>
    <p class="footer-tag">Repair-only roofer in San Antonio, Texas. Call or text Hugo at <a href="{TEL}">{PHONE}</a>.</p>
    <div class="social">{social}</div>
  </div>
  <nav class="footer-nav" aria-label="Footer">{nav}</nav>
  <ul class="footer-facts">
    <li><a href="{MAPS}">345 N San Gabriel Ave, San Antonio, TX 78237</a></li>
    <li>Mon–Sun 8am–6pm · emergencies 24 hrs</li>
    <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
  </ul>
  <p class="footer-giant" aria-hidden="true">HG ROOF</p>
  <p class="footer-base">Concept redesign for review, not the official HG Roof Repair website. Photos tagged “Sample photo” are free Unsplash placeholders, not Hugo’s work.</p>
</footer>'''


_dims = {}


def img(spec):
    """name|alt|sizes|tag|cls|eager -> responsive <img> (+ a visible photo tag)."""
    parts = (spec.split("|") + [""] * 6)[:6]
    name, alt, sizes, tag, cls, eager = (p.strip() for p in parts)
    files = sorted(SITE.glob(f"assets/img/{name}-*.webp"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    if not files:
        raise SystemExit(f"missing image {name}")
    srcset = []
    for f in files:
        if f not in _dims:
            with Image.open(f) as im:
                _dims[f] = im.size
        srcset.append(f"assets/img/{f.name} {_dims[f][0]}w")
    mid = files[min(1, len(files) - 1)] if len(files) > 1 else files[0]
    w, h = _dims[mid]
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    label = {"stock": '<span class="ph-tag">Sample photo</span>', "hugo": '<span class="ph-tag is-real">Hugo’s photo</span>'}.get(tag, "")
    return (f'<img class="{cls}" src="assets/img/{mid.name}" srcset="{", ".join(srcset)}" sizes="{sizes or "100vw"}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" {load} decoding="async">{label}')


TOKENS = {"TEL": TEL, "SMS": SMS, "EMAIL": EMAIL, "MAILTO": "mailto:" + EMAIL, "GOOGLE": GOOGLE, "MAPS": MAPS,
          "CURRENT": CURRENT, "FB": FB, "YELP": YELP, "YT": YT, "PHONE": PHONE}


def build():
    for page in sorted((SITE / "tools" / "pages").glob("*.html")):
        t = page.read_text(encoding="utf-8")
        t = re.sub(r"<!--@head (.+?)\|(.+?)-->", lambda m: head(m.group(1), m.group(2)), t)
        t = t.replace("<!--@header-->", header()).replace("<!--@footer-->", footer()).replace("<!--@actionbar-->", action_bar())
        t = re.sub(r"<!--@icon ([\w-]+)(?: (\d+))?-->", lambda m: icon(m.group(1), w=int(m.group(2) or 20)), t)
        t = re.sub(r"<!--@bigicon ([\w-]+)-->", lambda m: icon(m.group(1), "big", w=56, sw=1.1), t)
        t = re.sub(r"<!--@img (.+?)-->", lambda m: img(m.group(1)), t)
        t = re.sub(r"\{\{(\w+)\}\}", lambda m: link(TOKENS[m.group(1)]) if m.group(1) != "PHONE" else PHONE, t)
        t = re.sub(r'\s+data-(?:note|source)="[^"]*"', "", t)
        assert "assets/css/site.css" in t and "assets/js/site.js" in t, "head lost its stylesheet or script"
        (SITE / page.name).write_text(t, encoding="utf-8")
        print("built", page.name, len(t), "bytes")


if __name__ == "__main__":
    build()
