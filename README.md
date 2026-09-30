# Üni-Ara

Üniversite ve programları yerel CSV verisiyle keşfetmek için hazırlanmış Electron masaüstü uygulaması.

## Çalıştırma

Node.js ve npm kurulu olmalı. Proje klasöründe:

```bash
npm install
npm run dev
```

`npm run dev`, Vite geliştirme sunucusunu ve Electron penceresini birlikte açar. Uygulama internet bağlantısı olmadan da verileri ve fontları kullanır.

## Derleme ve Windows paketi

```bash
npm run build
npm run dist:win
```

Windows yükleyicisi `release/` klasöründe oluşur. `npm start` derlenmiş `dist/` sürümünü Electron içinde açar.

## Kullanım

- Ana ekranda üniversite, bölüm veya şehir ara. Önerilerde ok tuşlarıyla gez, Enter ile seç, Escape ile kapat.
- Sonuçları şehir, puan türü, taban puan ve başarı sırası ile filtrele; sıralamayı değiştir.
- Kalp simgesiyle favori kaydet. Favoriler, son aramalar ve tema bu bilgisayarda saklanır.
- `Ctrl+K` veya `⌘+K` ve `/` aramaya odaklanır.
- Üst sağdan açık/koyu tema ve animasyon düzeyi değiştirilebilir.

Veri kaynağı yalnızca `universite_verileri.csv` dosyasıdır. Canlı YÖK Atlas bağlantısı veya otomatik veri güncellemesi yoktur. Eski PyQt6 uygulaması `uni_ara.py` içinde referans olarak durur.

Tasarım ve kapsam kararları için [UI_REDESIGN_PLAN.md](UI_REDESIGN_PLAN.md) dosyasına bakın.
