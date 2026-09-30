# Üni-Ara

ÖSYM ve YÖK Atlas verileriyle üniversite programı arama ve kişisel tercih araştırması uygulaması.

## Çalıştırma

Python 3.10 veya daha yeni sürümle:

```powershell
python -m pip install -r requirements.txt
python uni_ara.py
```

Mevcut sanal ortamla `venv\Scripts\python.exe uni_ara.py` çalıştırılabilir.

## Kullanım

- Üniversite, bölüm, şehir veya program koduyla arayın. `bogazici bilgisayar` gibi Türkçe karaktersiz sorgular desteklenir. Sonuçsuz yazım hatalarında düzeltme önerisi çıkar.
- Sol panelden puan türü, öğrenim düzeyi, şehir, devlet/vakıf, burs ve dil seçip **Filtreleri uygula** düğmesine basın.
- 2023–2026 arasından bir sıralama yılı seçin. Başarı sırası aralığı veya kendi sıranızın çevresindeki yüzde aralığıyla arayın. Sıralama filtresi için puan türü seçilmelidir.
- Sonuç sayfalarında ileri/geri gidin veya doğrudan sayfa numarasını girin.
- **Listeme ekle** ile programları saklayın. **Tercih listem** ekranında sıralarını değiştirin, kaldırın veya CSV olarak dışa aktarın. Liste `%APPDATA%\UniAra\tercihler.json` dosyasında saklanır; ÖSYM'ye gönderilmez.
- Sonuçlarda 2–4 programın **Karşılaştır** kutusunu seçin. Üst çubuk karşılaştırmayı açar; `×` seçimleri temizler. Tercih listesinde Ctrl ile birden fazla program seçerek de karşılaştırabilirsiniz.
- **Ayrıntılar** bölümünde dört yıllık sıralama/puan/kontenjan, yıllık sıralama değişimi, fakülte, süre, dil, özel koşullar ve resmî kaynak bağlantıları bulunur.

## Veriler ve kontrol

Kapsam, eksik değerler ve güncelleme adımları için [VERI_KAYNAGI.md](VERI_KAYNAGI.md) dosyasına bakın. Programda tahmin edilmiş puan veya sıralama kullanılmaz.

```powershell
python -m unittest test_uygulama -v
```

Testler resmî kaynakların eşleşmesini, geçmiş yıl verilerini, aramayı, filtreleri, tercihlerin korunmasını, sayfalamayı, karşılaştırmayı, ayrıntıları ve klavye önerilerini kontrol eder. Testler gerçek tercih dosyasına yazmaz.
