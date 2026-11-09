"""Make the site's WebP images from the originals in research/ (originals never ship).
Each entry: (output name, source path relative to the project, crop box or None, sizes, credit/source).
Writes site/assets/img/<name>-<w>.webp and research/image-manifest.json (source URL + licence per file)."""
import json
from pathlib import Path
from PIL import Image, ImageFilter

PROJ = Path(__file__).resolve().parents[2]
OUT = PROJ / "site" / "assets" / "img"
U = "https://unsplash.com/photos/"
# kind: "hugo" = his own photo (from his Wix site), "stock" = free Unsplash placeholder (Unsplash License)
IMAGES = [
    # hero chosen by Khubaib (6 Nov 2026): 1670x942 copy of the Freepik-style roof photo he pasted in chat (replaces the 740px one)
    ("hero", "research/stock/user-supplied/hero-hires.webp", None, (800, 1400, 1670), "user-stock", "Supplied by Khubaib in chat: same image as modern-roofing-cladding-design-homes_29120-54525 (looks like Freepik 29120-54525; check the licence/attribution)"),
    ("about-main", "research/stock/p-1633759593085-1eaeb724fc88.jpg", (380, 0, 1640, 1333), (800, 1200), "stock", "https://images.unsplash.com/photo-1633759593085-1eaeb724fc88"),
    ("hugo-roof", "research/raw/img/9a65d3_69bfe30a89e4441d9ce7b338fec2f33a_mv2.png", (0, 745, 720, 1215), (720,), "hugo", "https://static.wixstatic.com/media/9a65d3_69bfe30a89e4441d9ce7b338fec2f33a~mv2.png (his Wix site)"),
    ("hugo-tile-job", "research/raw/img/9a65d3_4980da72ab60437a9d1fa20c95933ccf_mv2.png", None, (720,), "hugo", "https://static.wixstatic.com/media/9a65d3_4980da72ab60437a9d1fa20c95933ccf~mv2.png (his Wix site)"),
    ("type-shingle", "research/stock/p-1635424825057-7fb6dcd651ef.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1635424825057-7fb6dcd651ef (Raze Solar)"),
    ("type-tile", "research/stock/p-1726589004565-bedfba94d3a2.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1726589004565-bedfba94d3a2"),
    ("type-tile-close", "research/stock/p-1605450099279-533bd3ce379a.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1605450099279-533bd3ce379a"),
    ("type-metal", "research/stock/p-1602193230480-7840a38eb0c3.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1602193230480-7840a38eb0c3"),
    ("type-storm", "research/stock/p-1634750009079-6bf7bede038b.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1634750009079-6bf7bede038b"),
    ("type-brick", "research/stock/p-1635424710918-d5c138981922.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1635424710918-d5c138981922 (Raze Solar)"),
    ("svc-leak", "research/stock/p-1635424824800-692767998d07.jpg", (330, 0, 1330, 1333), (800,), "stock", "https://images.unsplash.com/photo-1635424824800-692767998d07 (Raze Solar)"),
    ("svc-shingle", "research/stock/p-1635424709961-f3a150459ad4.jpg", (380, 0, 1380, 1333), (800,), "stock", "https://images.unsplash.com/photo-1635424709961-f3a150459ad4 (Raze Solar)"),
    ("svc-storm", "research/stock/p-1635424709870-cdc6e64f0e20.jpg", (500, 0, 1500, 1333), (800,), "stock", "https://images.unsplash.com/photo-1635424709870-cdc6e64f0e20 (Raze Solar)"),
    ("svc-tile", "research/stock/p-1681049400158-0ff6249ac315.jpg", (700, 0, 1700, 1325), (800,), "stock", "https://images.unsplash.com/photo-1681049400158-0ff6249ac315"),
    ("svc-flat", "research/stock/p-1780445392484-5fb7d5610708.jpg", (500, 0, 1500, 1333), (800,), "stock", "https://images.unsplash.com/photo-1780445392484-5fb7d5610708"),
    ("svc-inspect", "research/stock/p-1566071634551-224a639a1c7d.jpg", (0, 300, 2000, 2967), (800,), "stock", "https://images.unsplash.com/photo-1566071634551-224a639a1c7d"),
    ("svc-vents", "research/stock/p-1643509867448-57001e0c333d.jpg", (0, 600, 2000, 2667), (800,), "stock", "https://images.unsplash.com/photo-1643509867448-57001e0c333d"),
    ("svc-emergency", "research/stock/p-1635424709845-3a85ad5e1f5e.jpg", (500, 0, 1500, 1333), (800,), "stock", "https://images.unsplash.com/photo-1633759593085-1eaeb724fc88"),
    ("svc-insurance", "research/stock/p-1786295866839-d17f879c65cd.jpg", (500, 0, 1500, 1333), (800, 1000), "stock", "https://images.unsplash.com/photo-1786295866839-d17f879c65cd"),
    ("cta-house", "research/stock/p-1632759145351-1d592919f522.jpg", None, (800, 1400), "stock", "https://images.unsplash.com/photo-1632759145351-1d592919f522"),
]

manifest = []
for name, src, crop, sizes, kind, source in IMAGES:
    im = Image.open(PROJ / src).convert("RGB")
    if crop:
        im = im.crop(crop)
    files = {}
    for w in sizes:
        if im.width > w:
            x = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        elif im.width < w and kind == "user-stock":  # the only image allowed to be enlarged (see the hero note)
            x = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
        else:
            x = im
        out = OUT / f"{name}-{w}.webp"
        x.save(out, "WEBP", quality=84, method=6)
        files[w] = [out.name, x.width, x.height]
    licence = {"stock": "Unsplash License (free placeholder, not Hugo's work)", "hugo": "Hugo's own photo from his website; ask before publishing",
               "user-stock": "Stock placeholder supplied by Khubaib, not Hugo's work; confirm licence/attribution before publishing"}[kind]
    manifest.append({"name": name, "kind": kind, "source": source, "licence": licence, "files": files})
    print(name, files)
(PROJ / "research" / "image-manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
