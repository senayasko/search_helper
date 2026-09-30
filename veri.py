"""Arama, resmî veri birleştirme ve yerel tercih listesi."""
import csv
import difflib
import json
import math
import os
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def normalize(text):
    text = str(text).replace("İ", "i").replace("I", "ı").lower().replace("ı", "i")
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def number(value, integer=False):
    if value in (None, "", "--", "---"):
        return None
    try:
        result = float(str(value).replace(",", "."))
        if not math.isfinite(result) or result < 0:
            return None
        return int(result) if integer else result
    except ValueError:
        return None


def burs(name, uni_type):
    if "(Burslu)" in name:
        return "Burslu"
    match = re.search(r"\(%(\d+) İndirimli\)", name)
    if match:
        return f"%{match[1]} İndirimli"
    if "(Ücretli)" in name:
        return "Ücretli"
    if uni_type == "DEVLET":
        return "Devlet / burs belirtilmemiş"
    return "Belirtilmemiş"


def load_data(root=ROOT):
    with (root / "program_detaylari.json").open(encoding="utf-8") as file:
        atlas = json.load(file)
    if atlas["yil"] != 2026:
        raise ValueError("YÖK Atlas ve ÖSYM veri yılları uyuşmuyor")
    data = []
    with (root / "universite_verileri.csv").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = row["Program Kodu"]
            detail = atlas["programlar"].get(code, {})
            history = []
            for h in detail.get("gecmis", []):
                history.append({"yil": int(h["yil"]), "sira": number(h.get("sira"), True) or None,
                                "puan": number(h.get("puan")), "kontenjan": number(h.get("kontenjan"), True)})
            current = next((h for h in history if h["yil"] == 2026), None)
            if current is None:
                current = {"yil": 2026, "sira": None}
                history.insert(0, current)
            current.update(puan=number(row["Taban Puan"]), kontenjan=number(row["Kontenjan"], True))
            item = {"kod": code, "uni": row["Universite"], "bolum": row["Bolum"],
                    "puan_turu": row["Puan Turu"], "duzey": row["Ogrenim Duzeyi"],
                    "uni_turu": row["Universite Turu"], "puan": current["puan"],
                    "tavan": number(row["Tavan Puan"]), "kontenjan": current["kontenjan"],
                    "yerlesen": number(row["Yerlesen"], True), "gecmis": history,
                    "burs": burs(row["Bolum"], row["Universite Turu"])}
            for key in ("sehir", "ilce", "fakulte", "dil", "sure", "ogretim", "kosullar", "sinir_sira", "akreditasyon"):
                item[key] = detail.get(key) or None
            item["arama"] = normalize(" ".join(str(item.get(k) or "") for k in
                                              ("uni", "bolum", "kod", "sehir", "fakulte", "puan_turu")))
            data.append(item)
    if not data or len({d["kod"] for d in data}) != len(data):
        raise ValueError("Program dosyası boş veya tekrarlanan program kodları var")
    return data, atlas


def year_data(item, year=2026):
    return next((h for h in item["gecmis"] if h["yil"] == year), {})


class SearchEngine:
    def __init__(self, data):
        self.data = data
        self.by_code = {d["kod"]: d for d in data}
        self.suggestions = sorted({d[k] for d in data for k in ("uni", "bolum", "sehir") if d.get(k)})
        self.normal_suggestions = [(s, normalize(s)) for s in self.suggestions]
        self.words = sorted({w for d in data for w in re.findall(r"[a-z]{4,}", d["arama"])})

    def suggest(self, query, limit=7):
        q = normalize(query.strip())
        if len(q) < 2:
            return []
        matches = [(not n.startswith(q), s) for s, n in self.normal_suggestions if q in n]
        return [s for _, s in sorted(matches)[:limit]]

    def correction(self, query):
        tokens = normalize(query).split()
        fixed = []
        for token in tokens:
            if len(token) >= 4 and token.isalpha() and token not in self.words:
                alternatives = difflib.get_close_matches(token, self.words, n=1, cutoff=0.78)
                fixed.append(alternatives[0] if alternatives else token)
            else:
                fixed.append(token)
        result = " ".join(fixed)
        return result if result != " ".join(tokens) else None

    def search(self, query, filters=None):
        f = filters or {}
        tokens = normalize(query).split()
        year = int(f.get("yil", 2026))
        results = []
        for item in self.data:
            if not all(t in item["arama"] for t in tokens):
                continue
            if any(f.get(k) not in (None, "", "Tümü") and (item.get(k) or "Belirtilmemiş") != f[k]
                   for k in ("duzey", "puan_turu", "sehir", "uni_turu", "burs", "dil")):
                continue
            rank = year_data(item, year).get("sira")
            low, high = f.get("min_sira", 0), f.get("max_sira", 0)
            if (low or high) and (rank is None or (low and rank < low) or (high and rank > high)):
                continue
            results.append(item)
        sort = f.get("sirala", "Başarı sırası")
        if sort == "Üniversite adı":
            results.sort(key=lambda d: (normalize(d["uni"]), normalize(d["bolum"]), d["kod"]))
        elif sort == "Puan (yüksekten)":
            results.sort(key=lambda d: (-(year_data(d, year).get("puan") or 0), d["kod"]))
        else:
            results.sort(key=lambda d: (year_data(d, year).get("sira") or float("inf"), d["kod"]))
        return results


class PreferenceStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(os.environ.get("APPDATA", str(Path.home()))) / "UniAra" / "tercihler.json"
        self.error = None
        self.codes = []
        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(payload, list) or any(not isinstance(c, str) or not c.isdigit() for c in payload):
                    raise ValueError("Beklenmeyen tercih dosyası biçimi")
                self.codes = list(dict.fromkeys(payload))
            except (OSError, ValueError) as exc:
                self.error = str(exc)

    def save(self, codes):
        if self.error:
            raise OSError(f"Tercih dosyası okunamadı; mevcut dosya korunuyor: {self.path}")
        unique = list(dict.fromkeys(codes))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)
        self.codes = unique

    def toggle(self, code):
        codes = self.codes.copy()
        if code in codes:
            codes.remove(code)
        else:
            codes.append(code)
        self.save(codes)
        return code in codes
