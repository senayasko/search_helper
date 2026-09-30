"""YÖK Atlas'ın herkese açık arama servisinden doğrulanabilir program ayrıntıları."""
import json
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://yokatlas.yok.gov.tr/api"


def request(path, body=None):
    req = Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                  headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=45) as response:
                return json.load(response)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def main():
    year = int(request("/parameters/yil"))
    announced = int(request("/parameters/sonuc-aciklandi"))
    if year != 2026 or announced != 1:
        raise ValueError("Yıl/dönem değişti; ÖSYM verisi ile eşleştirmeyi kontrol edin.")
    programs, conditions = {}, {}
    page = 0
    while True:
        result = request("/tercih-kilavuz/search", {
            "filters": {}, "page": page, "size": 500,
            "sortBy": "kilavuzKodu", "direction": "ASC"})
        if int(result["yil"]) != year:
            raise ValueError("Sayfalar arasında yıl değişti")
        for item in result["content"]:
            code = str(item["kilavuzKodu"])
            if code in programs:
                raise ValueError(f"Yinelenen program: {code}")
            for condition in item.get("kosulList") or []:
                conditions.update(condition)
            programs[code] = {
                "sehir": item.get("ilAdi"), "ilce": item.get("ilceAdi"),
                "fakulte": item.get("fymkAdi"), "dil": item.get("ogrenimDiliAdi"),
                "sure": item.get("ogrenimSuresi"), "ogretim": item.get("ogrenimTuruAdi"),
                "kosullar": item.get("kosul"), "sinir_sira": item.get("minBasariSirasi"),
                "akreditasyon": item.get("akreditasyonAck"),
                "universite": item.get("universiteAdi"), "bolum": item.get("birimAdi"),
                "gecmis": [{"yil": year - i,
                            "sira": item.get("basariSirasi" + (str(i) if i else "")),
                            "puan": item.get("minPuan" + (str(i) if i else "")),
                            "kontenjan": item.get("gk" + str(i)) if i else item.get("kontenjan")}
                           for i in range(4)],
            }
        print(f"YÖK Atlas: {len(programs)} / {result['totalElements']}", flush=True)
        if result["last"]:
            if len(programs) != result["totalElements"]:
                raise ValueError("Eksik kayıt")
            break
        page += 1
        time.sleep(0.25)
    payload = {"yil": year, "kaynak": BASE + "/tercih-kilavuz/search",
               "alinma_zamani": datetime.now(timezone.utc).isoformat(),
               "programlar": programs, "kosullar": conditions}
    # Farklı yıl veya güncelleme dönemlerine ait dosyaları karıştırma.
    with Path(__file__).with_name("universite_verileri.csv").open(encoding="utf-8-sig") as source:
        official = {r["Program Kodu"]: r for r in csv.DictReader(source)}
    if set(official) != set(programs):
        raise ValueError("ÖSYM ile YÖK Atlas program kapsamı uyuşmuyor; mevcut ayrıntı dosyası korundu.")
    for code, row in official.items():
        item = programs[code]
        if row["Universite"] != item["universite"] or row["Bolum"] != item["bolum"]:
            raise ValueError(f"Program kimliği uyuşmuyor: {code}")
        point = item["gecmis"][0]["puan"]
        if row["Taban Puan"] and point not in (None, "", "--"):
            if abs(float(row["Taban Puan"]) - float(point)) > 0.00001:
                raise ValueError(f"Kaynakların güncel puanları uyuşmuyor: {code}")
    target = Path(__file__).with_name("program_detaylari.json")
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temp.replace(target)


if __name__ == "__main__":
    main()
