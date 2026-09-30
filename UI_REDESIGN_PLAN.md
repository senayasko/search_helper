# Üni-Ara — masaüstü uygulaması yeniden tasarım planı

## 1. Hedef ve sınırlar

Üni-Ara, mevcut `universite_verileri.csv` dosyasındaki programları hızlı ve keyifli biçimde keşfetmeye yarayan bir masaüstü uygulaması olacak. Hedef; arama işlevini korurken görsel kaliteyi, etkileşimleri ve kullanım hızını belirgin biçimde yükseltmek.

- Platform: Windows öncelikli Electron masaüstü uygulaması.
- Veri: Yalnızca repodaki CSV. Canlı veri servisi, hesap sistemi veya veri güncelleme akışı yok.
- Korunacak işlevler: Üniversite, bölüm ve şehir araması; arama önerileri; şehir filtresi; taban/tavan puan, başarı sırası ve kontenjan bilgileri.
- Eklenecek işlevler: Puan türü filtresi, puan ve başarı sırası aralıkları, sıralama, favoriler, son aramalar ve klavye kısayolları.
- Başarı ölçüsü: Görsel beğeni öznel olsa da aşağıdaki kabul ölçütlerinin tamamı sağlanacak; uygulama yalnızca maket olarak kalmayacak.

## 2. Teknoloji ve yapı

| Katman | Karar |
| --- | --- |
| Masaüstü kabuğu | Electron |
| Arayüz | React + TypeScript + Vite |
| Stil | Tasarım tokenlarıyla yazılmış CSS; bileşenlere özel efektler |
| Hareket | Motion for React ve gerektiğinde CSS geçişleri |
| Veri | Paketle birlikte gelen CSV; açılışta tek kez ayrıştırılıp tipli kayıtlara dönüştürülür |
| Yerel tercihler | Favoriler, son aramalar, tema ve hareket tercihi için yerel depolama |

Electron ana süreç ile arayüz ayrı tutulacak; `contextIsolation` açık, `nodeIntegration` kapalı olacak. Arayüze yalnızca gereken dar API sunulacak. Bu yapı [Electron güvenlik önerileri](https://www.electronjs.org/docs/latest/tutorial/security) ile uyumlu. Hareket azaltma tercihi [Motion for React desteği](https://motion.dev/docs/react-accessibility) üzerinden uygulanacak.

Eski Python dosyası geçiş sırasında referans olarak korunacak. Yeni uygulama tamamlanıp doğrulandıktan sonra repodaki rolü belirlenecek; çalışan bir sürüm olmadan mevcut işlev kaldırılmayacak.

## 3. Görsel yön: canlı, kontrollü, kendine ait

Arayüz güçlü bir masaüstü ürün hissi verecek. Ana kompozisyon büyük bir arama alanı, veri odaklı yuvarlatılmış kartlar ve seçili yerlerde katmanlı cam yüzeylerden oluşacak. Dekoratif hareket işlevi gölgelemeyecek; etkileşimi açıklayacak.

### Renk ve tema

- Koyu tema ilk açılışta varsayılan: derin mürekkep arka plan, açık metin, elektrik mavisi ve turkuaz vurgu; sıcak mercan yalnızca seçili çağrılar ve durumlar için.
- Açık tema da eksiksiz tasarlanacak; koyu temanın basit renk terslemesi olmayacak.
- Ana metin, ikincil metin, sınır ve durum renkleri token olarak tanımlanacak. Kritik metinlerde en az WCAG AA kontrastı hedeflenecek.
- Aktif filtre ve seçili durumlar yalnızca renkle anlatılmayacak; şekil, ikon veya metinle de belirtilecek.

### Tipografi ve biçim

- Başlıklar karakterli ama okunaklı bir yazı tipi; arayüz metni ve sayılar temiz bir sans serif ile kurulacak. Yerel ya da paketlenmiş font kullanılacak; çevrimdışı çalışacak.
- Veri rakamlarında tabular numerals kullanılacak; puan ve sıra değerleri hizalı okunacak.
- Köşe yarıçapları bileşenin işlevine göre 10–24 px aralığında; kartlarda tutarlı bir aile oluşturacak.
- Glassmorphism üst bar, arama yüzeyi ve seçili panellerde kullanılacak. Neumorphism yalnızca küçük, basılabilir kontrollerde hafif bir dokunuş olarak kalacak; kontrastı düşüren iç içe gölgeler kullanılmayacak.
- Görsel motif, üniversite keşfi ve veri haritası fikrinden üretilecek: ince çizgiler, koordinat hissi ve yumuşak ışık alanları. Rastgele 3B objeler, stok illüstrasyonlar ve klişe yapay zekâ görselleri kullanılmayacak.

## 4. Ekranlar ve bileşenler

### Karşılama / arama ekranı

- Kısa ve net bir ürün başlığı ile büyük, odak noktası olan arama alanı.
- CSV'den hesaplanan toplam program, üniversite ve şehir sayılarını gösteren **yuvarlatılmış KPI/flashcard kartları**. Kartlarda büyük sayı, küçük açıklama ve ilgili keşif eylemi bulunacak; dekoratif sayaçlardan ibaret olmayacak.
- Arama yazarken üniversite, bölüm ve şehir önerileri türlerine göre ayrılacak. Eşleşen bölüm vurgulanacak; ok tuşları, Enter ve Escape ile yönetilecek.
- Son aramalar ve favorilere hızlı erişim. İlk kullanımda boş durumlar özenle tasarlanacak.
- Ctrl/Cmd+K aramayı odaklayacak; `/` kısayolu da aramayı açabilecek.

### Sonuç / keşif ekranı

- Üstte arama ve sonuç sayısı; solda veya dar pencere düzeninde açılır filtre paneli.
- Filtreler: şehir, puan türü (SAY/EA/SÖZ), taban puan aralığı, başarı sırası aralığı. Seçilen filtreler kaldırılabilir etiketler olarak görünecek; tek hamlede temizlenebilecek.
- Sıralama: taban puan yüksek/düşük, başarı sırası iyi/kötü, üniversite veya bölüm adına göre alfabetik.
- Sonuçlar, taranması kolay **yuvarlatılmış bilgi kartları** olacak. Üniversite ve bölüm adı birincil; puan, sıralama, kontenjan ve şehir ikincil bilgi olarak belirgin hiyerarşiyle gösterilecek.
- Kartın tamamı klavye ve fare ile açılabilecek. Detay yüzeyi tüm CSV alanlarını gösterecek: puan türü ve yerleşen sayısı dahil. Veri kaynağı yalnızca “Yerel CSV” şeklinde küçük bir bilgi olarak belirtilecek.
- Favoriye ekleme kart üzerinde doğrudan yapılabilecek. Uzun listelerde sanallaştırma veya sayfalama uygulanacak; 6.258 DOM kartı aynı anda oluşturulmayacak.
- Sıfır sonuç, yükleme, bozuk CSV ve boş favoriler için açıklayıcı ekranlar olacak.

### Pencere davranışı

- Özel başlık çubuğu ve standart küçült/büyüt/kapat davranışı.
- En az 800×560 boyutunda kullanılabilir düzen; genişlik azaldıkça filtre ve kart yerleşimi yeniden akacak.
- Pencere boyutu, tema ve kullanıcının son tercihleri yerel olarak hatırlanacak.
- Çevrimdışı kullanım temel senaryo. Arayüzde işlevsiz bağlantı veya gerçek URL izlenimi veren sahte metin bulunmayacak.

## 5. Hareket ve hover sistemi

Hareket bu projenin ana kalite hedeflerinden biri. Bütün etkileşimler aynı ritim, eğri ve mesafe sistemini kullanacak; her bileşen rastgele animasyon almayacak.

| Etkileşim | Hedef davranış |
| --- | --- |
| Açılış | Başlık, arama ve KPI kartları kısa bir sıralı giriş yapar; toplam süre kullanımı geciktirmez. |
| Arama odağı | Alanın çerçevesi ve ışığı yumuşak değişir; öneri paneli kökene bağlı açılır. |
| Öneri hover/klavye seçimi | Satır arka planı, ikon ve eşleşme vurgusu birlikte tepki verir; seçili öğe net kalır. |
| KPI hover | Kart hafif yükselir, katman ışığı ve kenar çizgisi yer değiştirir; tıklama eylemi açıkça anlaşılır. |
| Sonuç kartı hover | Hafif yükselme, gölge/kenar vurgusu ve içindeki eylemlerin ortaya çıkması; metin yerinden oynamaz. |
| Filtre değişimi | Sonuç sayısı ve liste geçişi akıcıdır; eski/yeninin konumu anlaşılır. |
| Favori | Küçük ölçek/renk geri bildirimi ve kalıcı durum değişimi. |
| Detay paneli | Arka plan hafif kararır; panel kenardan veya kart bağlamından açılır, kapanış yönü tutarlıdır. |
| Basma/odak | Butonlar kısa basma tepkisi verir; klavye odak halkası hover kadar özenli ve görünürdür. |

- Mikro etkileşimler çoğunlukla 120–220 ms, panel geçişleri yaklaşık 240–360 ms aralığında tasarlanacak. Yay eğrileri kontrollü kullanılacak; sürekli zıplayan öğeler olmayacak.
- Animasyonlar mümkün olduğunca `transform` ve `opacity` üzerinde çalışacak; büyük blur alanları ve sürekli parallax performans testinden geçmeden eklenmeyecek.
- İşletim sistemindeki **reduced motion** tercihi karşılanacak: büyük hareketler sade solma veya anlık durum değişimine dönüşecek. Uygulama içinde hareket düzeyi ayarı da bulunacak.
- Hover olmayan girişlerde (dokunmatik/klavye) hiçbir eylem gizli kalmayacak.

## 6. Arama ve veri kuralları

- CSV sütunları: `Universite`, `Bolum`, `Sehir`, `Puan Turu`, `Taban Puan`, `Tavan Puan`, `Kontenjan`, `Yerlesen`, `Basari Sirasi`.
- Türkçe karakterlere duyarlı doğru küçük harf/karşılaştırma kullanılacak. Büyük/küçük harf aramayı engellemeyecek; eşleşmeler üniversite, bölüm ve şehirde aranacak.
- Sonuç ve KPI sayıları sabit kodlanmayacak; CSV'den hesaplanacak.
- Eksik veya hatalı satır uygulamayı kapatmayacak; geçerli kayıtlar görüntülenecek ve sorun açıklanacak.
- Filtreleme/sıralama tek bir veri katmanında test edilebilir saf fonksiyonlarla yapılacak.
- Favoriler için kayıt anahtarı, aynı isimli programları karıştırmayacak biçimde alan birleşiminden üretilecek.

## 7. Kabul ölçütleri

1. Mevcut CSV ile arama, öneri, şehir filtresi ve bütün mevcut veri alanları yeni uygulamada çalışır.
2. Puan türü, aralık filtreleri, sıralama, favoriler, son aramalar ve klavye kısayolları çalışır; yeniden açınca yerel tercihler korunur.
3. Arama önerisi, kart, filtre, buton, favori ve detay panelinin hover, odak ve basma durumları tutarlı biçimde tamamlanır.
4. Koyu ve açık temada metin okunur; klavyeyle temel akış tamamlanır; reduced motion ayarı etkili olur.
5. 6.258 satırlık mevcut veriyle arama ve filtreleme akıcıdır; liste aynı anda binlerce kart çizmez.
6. Geliştirme modunda çalıştırma ve paketlenmiş Windows uygulaması açılışı doğrulanır.
7. Boş sonuç, bozuk veri ve küçük pencere durumları gözle kontrol edilir; yatay taşma veya kırık düzen kalmaz.
8. README, kurulum, geliştirme ve paketleme komutlarını kısa ve doğru biçimde açıklar.

## 8. Uygulama sırası

1. Electron/React/TypeScript iskeleti, CSV veri katmanı ve mevcut arama işlevini taşıma.
2. Tasarım tokenları, iki tema, pencere çerçevesi, karşılama ve KPI kartları.
3. Sonuç ekranı, filtreler, sıralama, detay paneli ve sanallaştırılmış liste.
4. Favoriler, son aramalar, klavye akışı ve kalıcı tercihler.
5. Hover/animasyon sistemi, reduced motion, performans ve erişilebilirlik düzeltmeleri.
6. Paketleme, görsel kontrol, işlev testi ve README.

Bu belge implementasyon için kararlaştırılmış kapsamdır. Uygulama sırasında tasarım ayrıntıları değişebilir; yukarıdaki işlev ve kalite ölçütleri korunur.
electron.js in tum ssinirlarini ui ux tasarimi olarak.
