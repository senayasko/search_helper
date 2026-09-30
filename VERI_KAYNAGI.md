# Veri kaynağı

`universite_verileri.csv`, ÖSYM'nin **2026-YKS merkezi yerleştirme** sonuçlarındaki genel kontenjan sütunlarından üretilmiştir:

- [Tablo 4 — lisans](https://cdn.osym.gov.tr/en-kucuk-ve-en-buyuk-puanlar-tablo-4-rps0lq-18092428.xlsx)
- [Tablo 3 — ön lisans](https://cdn.osym.gov.tr/en-kucuk-ve-en-buyuk-puanlar-tablo-3-0wptq7-18092428.xlsx)
- [ÖSYM duyuru sayfası](https://www.osym.gov.tr/2026-yks-yerlestirme-sonuclarina-iliskin-sayisal-bilgiler)

Alanlar: program kodu, üniversite türü ve adı, program adı, puan türü, genel kontenjan, genel kontenjana yerleşen, en küçük ve en büyük puan. Özel kontenjanlar dahil değildir. Puan oluşmamış programlarda puan alanı boştur.

`program_detaylari.json`, [YÖK Atlas](https://yokatlas.yok.gov.tr/) tarafından kendi arayüzünde kullanılan herkese açık `https://yokatlas.yok.gov.tr/api/tercih-kilavuz/search` servisinden alınmıştır. Şehir/ilçe, fakülte, eğitim dili, süre, öğretim türü, özel koşullar, akreditasyon ve başarı sıraları bu kaynaktan gelir. Kayıtlar **program koduyla** birleştirilir. 21.493 programın kodu, üniversite adı, program adı ve mevcut puanları iki kaynak arasında kontrol edilmiştir.

Atlas'ın `yil=2026` ve `sonuc-aciklandi=1` değerleri doğrulandı. Mevcut sıralama 2026'ya; geçmiş alanlar 2025, 2024 ve 2023'e aittir. Örnek olarak 102210277 kodlu programın 2025 ve 2024 değerleri ayrıca ÖSYM'nin 2026 ve 2025 tercih kılavuzlarıyla karşılaştırılmıştır. Sıralama hesaplanmaz veya puandan tahmin edilmez. Sıralaması olmayan kayıtlar sıralama aralığı filtrelerine dahil edilmez.

2026 sıralaması bulunan program sayısı 18.251'dir. Bazı programların dil, şehir veya geçmiş yıl alanları kaynakta boş olabilir; uygulama bunları bilinmeyen olarak gösterir. Burs/ücret filtresi resmî program adındaki `Burslu`, `%… İndirimli` ve `Ücretli` ifadelerinden çıkarılır. Başka bir ifade yoksa burs varsayılmaz.

Geçmiş yıl ekranı, **2026 program listesindeki kodların** geçmiş değerlerini gösterir; kapanmış tüm eski programları kapsayan ayrı bir katalog değildir. Ad, dil, burs ve koşullar güncel programa aittir. Geçmiş başarı sırası ve puan yıl etiketiyle gösterilir. Başarı sırasındaki küçük sayı daha üst sırayı ifade eder; farklı puan türleri ve yılların puanları doğrudan karşılaştırılmamalıdır. Sıralamaya yakınlık yüzdesi yalnızca araştırma aralığıdır, yerleşme olasılığı değildir.

Veriyi yeniden üretmek için gereksinimleri kurup sırasıyla `python resmi_veri_guncelle.py` ve `python atlas_guncelle.py` çalıştırın. Betikler sabit 2026 kaynaklarını kullanır; arayüz çalışırken ağ isteği yapılmaz. Atlas güncellemesi program kapsamı, kimliği veya puanı uyuşmazsa durur ve mevcut ayrıntı dosyasını korur. Yeni yıl için kaynak adresleri, alanlar ve yıl eşleştirmesi ayrıca doğrulanmalıdır.
