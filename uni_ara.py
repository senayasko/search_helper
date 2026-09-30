# -*- coding: utf-8 -*-
import sys
import re
import csv
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QStackedWidget,
    QGraphicsDropShadowEffect, QComboBox, QFrame, QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor

# ── Veri Yükle ────────────────────────────────────────────────────────────────
def veri_yukle():
    csv_path = os.path.join(os.path.dirname(__file__), "universite_verileri.csv")
    data = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "uni":       row["Universite"],
                "bolum":     row["Bolum"],
                "sehir":     row["Sehir"],
                "puan":      float(row["Taban Puan"]),
                "tavan":     float(row["Tavan Puan"]),
                "kontenjan": int(row["Kontenjan"]),
                "sira":      int(row["Basari Sirasi"]),
            })
    return data

DATA = veri_yukle()

ONERI_HAVUZU = sorted(set(
    [d["uni"]   for d in DATA] +
    [d["bolum"] for d in DATA] +
    [d["sehir"] for d in DATA]
))

def tr_lower(s):
    return s.replace("İ", "i").replace("I", "ı").lower()

def oneri_getir(metin, limit=7):
    q = tr_lower(metin.strip())
    if not q:
        return []
    sonuclar = [s for s in ONERI_HAVUZU if q in tr_lower(s)]
    bastanlar = [s for s in sonuclar if tr_lower(s).startswith(q)]
    ortalar   = [s for s in sonuclar if not tr_lower(s).startswith(q)]
    return (bastanlar + ortalar)[:limit]

def ara(sorgu, sehir_filtre="Tümü"):
    q = tr_lower(sorgu.strip())
    sonuclar = []
    for d in DATA:
        eslesti = (
            not q or
            q in tr_lower(d["uni"]) or
            q in tr_lower(d["bolum"]) or
            q in tr_lower(d["sehir"])
        )
        sehir_eslesti = (sehir_filtre == "Tümü" or d["sehir"] == sehir_filtre)
        if eslesti and sehir_eslesti:
            sonuclar.append(d)
    return sorted(sonuclar, key=lambda x: x["puan"], reverse=True)

SEHIRLER = ["Tümü"] + sorted(set(d["sehir"] for d in DATA))

LOGO_HTML = (
    '<span style="color:#4285F4;">Ü</span>'
    '<span style="color:#EA4335;">n</span>'
    '<span style="color:#FBBC05;">i</span>'
    '<span style="color:#4285F4;">-</span>'
    '<span style="color:#34A853;">A</span>'
    '<span style="color:#EA4335;">r</span>'
    '<span style="color:#4285F4;">a</span>'
)

# ── Öneri Listesi (Overlay) ───────────────────────────────────────────────────
class OneriDropdown(QFrame):
    """Ana sayfanın üstüne overlay olarak çizilen öneri kutusu."""
    oneri_secildi = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #dfe1e5;
                border-top: none;
                border-bottom-left-radius: 24px;
                border-bottom-right-radius: 24px;
            }
        """)
        g = QGraphicsDropShadowEffect()
        g.setBlurRadius(12)
        g.setColor(QColor(32, 33, 36, 40))
        g.setOffset(0, 4)
        self.setGraphicsEffect(g)

        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(0, 4, 0, 10)
        duzen.setSpacing(0)

        self.liste = QListWidget()
        self.liste.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 24px;
                font-size: 14px;
                color: #202124;
            }
            QListWidget::item:hover { background: #f1f3f4; }
            QListWidget::item:selected { background: #f1f3f4; color: #202124; }
        """)
        self.liste.setFont(QFont("Segoe UI", 12))
        self.liste.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.liste.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.liste.itemClicked.connect(self._tikla)
        duzen.addWidget(self.liste)
        self.hide()

    def guncelle(self, oneriler, x, y, genislik):
        self.liste.clear()
        satir_yuksekligi = 42
        for o in oneriler:
            item = QListWidgetItem(o)
            item.setData(Qt.ItemDataRole.UserRole, o)
            self.liste.addItem(item)
        toplam_yukseklik = len(oneriler) * satir_yuksekligi + 14
        self.liste.setFixedHeight(len(oneriler) * satir_yuksekligi)
        self.setGeometry(x, y, genislik, toplam_yukseklik)
        self.show()
        self.raise_()

    def _tikla(self, item):
        self.oneri_secildi.emit(item.data(Qt.ItemDataRole.UserRole))
        self.hide()

    def asagi(self):
        r = self.liste.currentRow()
        self.liste.setCurrentRow(min(r + 1, self.liste.count() - 1))
        item = self.liste.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def yukari(self):
        r = self.liste.currentRow()
        self.liste.setCurrentRow(max(r - 1, -1))
        item = self.liste.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None


# ── Arama Kutusu ─────────────────────────────────────────────────────────────
class AramaKutusu(QLineEdit):
    keyPressed = pyqtSignal(object)

    def __init__(self, placeholder="", yuvarlak=True):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(48)
        self.setFont(QFont("Segoe UI", 13))
        self._yuvarlak = yuvarlak
        self._oneri_acik = False
        self._stil()

    def _stil(self):
        if self._oneri_acik:
            self.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #dfe1e5;
                    border-bottom: none;
                    border-top-left-radius: 24px;
                    border-top-right-radius: 24px;
                    border-bottom-left-radius: 0;
                    border-bottom-right-radius: 0;
                    padding: 0 20px;
                    color: #202124;
                    background: #ffffff;
                    font-size: 14px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #dfe1e5;
                    border-radius: 24px;
                    padding: 0 20px;
                    color: #202124;
                    background: #ffffff;
                    font-size: 14px;
                }
            """)
        g = QGraphicsDropShadowEffect()
        g.setBlurRadius(10)
        g.setColor(QColor(32, 33, 36, 35))
        g.setOffset(0, 1)
        self.setGraphicsEffect(g)

    def set_oneri_acik(self, acik):
        self._oneri_acik = acik
        self._stil()

    def keyPressEvent(self, e):
        self.keyPressed.emit(e.key())
        super().keyPressEvent(e)


# ── Ana Sayfa ─────────────────────────────────────────────────────────────────
class AnaSayfa(QWidget):
    def __init__(self, aramaya_git):
        super().__init__()
        self.aramaya_git = aramaya_git
        self._goster_oneriler = True
        self.setStyleSheet("background:#ffffff;")

        # Overlay dropdown — bu widget'ın child'ı
        self.dropdown = OneriDropdown(self)
        self.dropdown.oneri_secildi.connect(self._oneri_sec)

        duzen = QVBoxLayout(self)
        duzen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        duzen.setSpacing(0)

        # Logo
        logo = QLabel(LOGO_HTML)
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 64, QFont.Weight.Bold))
        logo.setStyleSheet("margin-bottom:8px; background:transparent;")
        duzen.addWidget(logo)

        alt = QLabel("YÖK Atlas Veritabanı")
        alt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt.setStyleSheet("color:#70757a; font-size:14px; margin-bottom:28px;")
        duzen.addWidget(alt)

        # Arama kutusu (sabit genişlik, ortada)
        self.arama = AramaKutusu("Üniversite, bölüm veya şehir ara...")
        self.arama.setFixedWidth(580)
        self.arama.textChanged.connect(self._metin_degisti)
        self.arama.returnPressed.connect(self._ara)
        self.arama.keyPressed.connect(self._tus)

        satir = QHBoxLayout()
        satir.setAlignment(Qt.AlignmentFlag.AlignCenter)
        satir.addWidget(self.arama)
        duzen.addLayout(satir)

        duzen.addSpacing(20)

        btn = QPushButton("Ara")
        btn.setFixedSize(100, 36)
        btn.setFont(QFont("Segoe UI", 12))
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background:#f8f9fa; border:1px solid #f8f9fa;
                border-radius:4px; color:#3c4043; font-size:13px;
            }
            QPushButton:hover { border-color:#dadce0; color:#202124; }
            QPushButton:pressed { background:#e8eaed; }
        """)
        btn.clicked.connect(self._ara)

        btn_satir = QHBoxLayout()
        btn_satir.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_satir.addWidget(btn)
        duzen.addLayout(btn_satir)

        duzen.addSpacing(40)
        istatistik = QLabel(
            f"{len(DATA)} program  |  "
            f"{len(set(d['uni'] for d in DATA))} üniversite  |  "
            f"{len(set(d['sehir'] for d in DATA))} şehir"
        )
        istatistik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        istatistik.setStyleSheet("color:#bdc1c6; font-size:12px;")
        duzen.addWidget(istatistik)

        self.arama.setFocus()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._dropdown_konumla()

    def _dropdown_konumla(self):
        """Dropdown'ı arama kutusunun tam altına hizala."""
        if not self.dropdown.isVisible():
            return
        pos = self.arama.mapTo(self, self.arama.rect().bottomLeft())
        self.dropdown.move(pos.x(), pos.y())

    def _metin_degisti(self, metin):
        if not self._goster_oneriler:
            return
        oneriler = oneri_getir(metin)
        if oneriler and metin.strip():
            pos = self.arama.mapTo(self, self.arama.rect().bottomLeft())
            self.dropdown.guncelle(oneriler, pos.x(), pos.y(), self.arama.width())
            self.arama.set_oneri_acik(True)
        else:
            self.dropdown.hide()
            self.arama.set_oneri_acik(False)

    def _tus(self, key):
        if not self.dropdown.isVisible():
            return
        if key == Qt.Key.Key_Down:
            deger = self.dropdown.asagi()
            if deger:
                self._goster_oneriler = False
                self.arama.setText(deger)
                self._goster_oneriler = True
        elif key == Qt.Key.Key_Up:
            deger = self.dropdown.yukari()
            if deger:
                self._goster_oneriler = False
                self.arama.setText(deger)
                self._goster_oneriler = True
        elif key == Qt.Key.Key_Escape:
            self.dropdown.hide()
            self.arama.set_oneri_acik(False)

    def _oneri_sec(self, deger):
        self._goster_oneriler = False
        self.arama.setText(deger)
        self._goster_oneriler = True
        self.arama.set_oneri_acik(False)
        self.aramaya_git(deger)

    def _ara(self):
        self.dropdown.hide()
        self.arama.set_oneri_acik(False)
        q = self.arama.text().strip()
        if q:
            self.aramaya_git(q)

    def temizle(self):
        self.arama.clear()
        self.dropdown.hide()
        self.arama.set_oneri_acik(False)
        self.arama.setFocus()


# ── Sonuç Kartı ───────────────────────────────────────────────────────────────
class SonucKarti(QWidget):
    def __init__(self, veri, sorgu):
        super().__init__()
        self.setStyleSheet("background:transparent;")
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 26)
        duzen.setSpacing(3)

        q = sorgu.strip().lower()

        def vurgula(metin):
            if not q:
                return metin
            return re.sub(
                f"({re.escape(q)})",
                r'<b style="color:#202124;">\1</b>',
                metin, flags=re.IGNORECASE
            )

        url = QLabel(
            f'<span style="font-size:13px; color:#5f6368;">'
            f'{veri["uni"].lower().replace(" ", "-")}.edu.tr'
            f' &rsaquo; Bölümler &rsaquo; {veri["bolum"]}</span>'
        )
        url.setTextFormat(Qt.TextFormat.RichText)
        duzen.addWidget(url)

        baslik = QLabel(
            f'<span style="color:#1a0dab; font-size:19px;">'
            f'{vurgula(veri["uni"])} &mdash; {vurgula(veri["bolum"])}</span>'
        )
        baslik.setTextFormat(Qt.TextFormat.RichText)
        baslik.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        duzen.addWidget(baslik)

        aciklama = QLabel(
            f'<span style="color:#4d5156; font-size:13px;">'
            f'{vurgula(veri["bolum"])} bölümü <b>{vurgula(veri["sehir"])}</b> '
            f'kampüsünde eğitim vermektedir. '
            f'Kontenjan: <b>{veri["kontenjan"]}</b></span>'
        )
        aciklama.setTextFormat(Qt.TextFormat.RichText)
        aciklama.setWordWrap(True)
        duzen.addWidget(aciklama)

        chip_satir = QHBoxLayout()
        chip_satir.setSpacing(8)
        chip_satir.setContentsMargins(0, 4, 0, 0)
        chip_satir.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sira_fmt = f"{veri['sira']:,}".replace(",", ".")
        chiplar = [
            ("Taban Puan", f"{veri['puan']:.2f}"),
            ("Tavan Puan", f"{veri['tavan']:.2f}"),
            ("Başarı Sırası", sira_fmt),
            ("Kontenjan", str(veri["kontenjan"])),
            ("Şehir", veri["sehir"]),
        ]
        for etiket, deger in chiplar:
            chip = QLabel(
                f'<span style="color:#70757a;">{etiket}: </span>'
                f'<b style="color:#202124;">{deger}</b>'
            )
            chip.setTextFormat(Qt.TextFormat.RichText)
            chip.setStyleSheet(
                "background:#f8f9fa; border:1px solid #e8eaed; border-radius:4px;"
                "padding:3px 10px; font-size:12px;"
            )
            chip_satir.addWidget(chip)

        chip_satir.addStretch()
        duzen.addLayout(chip_satir)


# ── Sonuç Sayfası ─────────────────────────────────────────────────────────────
class SonucSayfasi(QWidget):
    def __init__(self, anaya_don):
        super().__init__()
        self.anaya_don = anaya_don
        self._sorgu = ""
        self._sehir = "Tümü"
        self.setStyleSheet("background:#ffffff;")

        ana = QVBoxLayout(self)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        ustbar = QWidget()
        ustbar.setFixedHeight(64)
        ustbar.setStyleSheet("background:#ffffff; border-bottom:1px solid #ebebeb;")
        ust = QHBoxLayout(ustbar)
        ust.setContentsMargins(24, 0, 24, 0)
        ust.setSpacing(16)

        logo_etiket = QLabel(LOGO_HTML)
        logo_etiket.setTextFormat(Qt.TextFormat.RichText)
        logo_etiket.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        logo_etiket.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        logo_etiket.mousePressEvent = lambda _: self.anaya_don()
        ust.addWidget(logo_etiket)

        self.ust_arama = AramaKutusu("Ara...")
        self.ust_arama.setFixedWidth(460)
        self.ust_arama.returnPressed.connect(self._ara)
        ust.addWidget(self.ust_arama)

        self.sehir_combo = QComboBox()
        self.sehir_combo.addItems(SEHIRLER)
        self.sehir_combo.setFixedHeight(36)
        self.sehir_combo.setFixedWidth(140)
        self.sehir_combo.setStyleSheet("""
            QComboBox {
                border:1px solid #dfe1e5; border-radius:18px;
                padding:0 14px; font-size:13px; color:#202124;
                background:#ffffff;
            }
            QComboBox::drop-down { border:none; }
            QComboBox:hover { border-color:#bdc1c6; }
        """)
        self.sehir_combo.currentTextChanged.connect(self._filtre_degisti)
        ust.addWidget(self.sehir_combo)
        ust.addStretch()

        ana.addWidget(ustbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{border:none; background:#ffffff;}"
            "QScrollBar:vertical{width:8px; background:#f1f3f4; border-radius:4px;}"
            "QScrollBar::handle:vertical{background:#dadce0; border-radius:4px;}"
        )

        self.icerik = QWidget()
        self.icerik.setStyleSheet("background:#ffffff;")
        self.icerik_duzen = QVBoxLayout(self.icerik)
        self.icerik_duzen.setContentsMargins(180, 20, 60, 60)
        self.icerik_duzen.setSpacing(0)
        self.icerik_duzen.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.icerik)
        ana.addWidget(scroll)

    def _ara(self):
        self._sorgu = self.ust_arama.text().strip()
        self._goster()

    def _filtre_degisti(self, sehir):
        self._sehir = sehir
        self._goster()

    def sonuclari_goster(self, sorgu):
        self._sorgu = sorgu
        self._sehir = "Tümü"
        self.sehir_combo.setCurrentText("Tümü")
        self.ust_arama.setText(sorgu)
        self._goster()

    def _goster(self):
        while self.icerik_duzen.count():
            item = self.icerik_duzen.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sonuclar = ara(self._sorgu, self._sehir)

        sayac = QLabel(
            f"Yaklaşık <b>{len(sonuclar)}</b> sonuç bulundu" if sonuclar
            else f'"{self._sorgu}" için sonuç bulunamadı.'
        )
        sayac.setTextFormat(Qt.TextFormat.RichText)
        sayac.setStyleSheet("color:#70757a; font-size:13px; margin-bottom:16px;")
        self.icerik_duzen.addWidget(sayac)

        for veri in sonuclar:
            self.icerik_duzen.addWidget(SonucKarti(veri, self._sorgu))

        self.icerik_duzen.addStretch()


# ── Ana Pencere ───────────────────────────────────────────────────────────────
class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Üni-Ara")
        self.resize(1100, 720)
        self.setMinimumSize(800, 560)
        self.setStyleSheet("background:#ffffff;")

        self.yigin = QStackedWidget()
        self.setCentralWidget(self.yigin)

        self.ana_sayfa = AnaSayfa(self._sonuca_git)
        self.sonuc_sayfasi = SonucSayfasi(self._anaya_don)

        self.yigin.addWidget(self.ana_sayfa)
        self.yigin.addWidget(self.sonuc_sayfasi)

    def _sonuca_git(self, sorgu):
        if not sorgu:
            return
        self.sonuc_sayfasi.sonuclari_goster(sorgu)
        self.yigin.setCurrentWidget(self.sonuc_sayfasi)

    def _anaya_don(self):
        self.ana_sayfa.temizle()
        self.yigin.setCurrentWidget(self.ana_sayfa)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palet = QPalette()
    palet.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    palet.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    app.setPalette(palet)
    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec())