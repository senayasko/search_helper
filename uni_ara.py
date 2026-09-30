# -*- coding: utf-8 -*-
"""Üni-Ara: resmî program araması ve kişisel tercih araştırması."""
import csv
import html
import math
import sys
from PyQt6.QtCore import Qt, QTimer, QStringListModel, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QScrollArea, QStackedWidget, QComboBox, QFrame,
    QSpinBox, QCheckBox, QDialog, QTextBrowser, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QListWidget, QListWidgetItem, QMessageBox,
    QCompleter, QFileDialog,
)
from veri import SearchEngine, PreferenceStore, load_data, year_data

LOGO_HTML = ('<span style="color:#4285f4">Ü</span><span style="color:#ea4335">n</span>'
             '<span style="color:#fbbc05">i</span><span style="color:#4285f4">-</span>'
             '<span style="color:#34a853">A</span><span style="color:#ea4335">r</span>'
             '<span style="color:#4285f4">a</span>')
GUIDE = "https://www.osym.gov.tr/2026-yuksekogretim-kurumlari-sinavi-yks-yuksekogretim-programlari-ve-kontenjanlari-kilavuzu"
STYLE = """
QWidget { font-family:'Segoe UI'; font-size:13px; color:#202124; background:#f7f9fc; }
QLineEdit,QComboBox,QSpinBox { border:1px solid #d5dce8; border-radius:8px; padding:7px; background:#ffffff; }
QLineEdit:focus,QComboBox:focus,QSpinBox:focus { border:1px solid #5b7cfa; }
QPushButton { background:#ffffff; border:1px solid #d5dce8; border-radius:8px; padding:8px 12px; }
QPushButton:hover { background:#eef2ff; border-color:#7188ee; }
QPushButton:disabled { color:#9aa0a6; background:#f2f4f8; }
QPushButton#primary { color:white; background:#596ee8; border-color:#596ee8; }
QFrame#card { background:#ffffff; border:1px solid #e2e7f0; border-radius:12px; margin:5px 2px; }
QFrame#filterPanel { background:#eef2ff; border:1px solid #dce3ff; border-radius:12px; }
QLabel#sectionTitle { color:#3949ab; font-size:15px; font-weight:600; }
QLabel#muted { color:#5f6368; }
QScrollArea { border:0; background:transparent; }
QScrollBar:vertical { width:10px; background:#edf0f7; border-radius:5px; }
QScrollBar::handle:vertical { background:#b7c0d5; border-radius:5px; min-height:28px; }
QHeaderView::section { background:#e7ebff; border:0; padding:8px; }
QTableWidget { gridline-color:#e8eaed; border:1px solid #e8eaed; }
QListWidget { border:1px solid #dadce0; }
QListWidget::item { padding:10px; }
QListWidget::item:selected { background:#d2e3fc; color:#202124; }
"""


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()


def esc(value):
    return html.escape(str(value if value is not None else "Belirtilmemiş"))


def fmt(value, decimals=0):
    if value is None:
        return "Veri yok"
    if decimals:
        return f"{float(value):.{decimals}f}".replace(".", ",")
    return f"{int(value):,}".replace(",", ".")


def label(text, muted=False):
    widget = QLabel(str(text))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    if muted:
        widget.setObjectName("muted")
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


def open_url(url):
    QDesktopServices.openUrl(QUrl(url))


class SearchBox(QLineEdit):
    def __init__(self, engine, search):
        super().__init__()
        self.engine = engine
        self.setPlaceholderText("Üniversite, bölüm, şehir veya program kodu ara…")
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(44)
        self.model = QStringListModel(self)
        self.completion = QCompleter(self.model, self)
        self.completion.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.completion.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(self.completion)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.textEdited.connect(lambda _: self.timer.start())
        self.timer.timeout.connect(self.suggest)
        self.returnPressed.connect(lambda: search(self.text()))
        self.completion.activated.connect(lambda text: search(text))

    def suggest(self):
        if not self.hasFocus():
            return
        suggestions = self.engine.suggest(self.text())
        self.model.setStringList(suggestions)
        if suggestions:
            self.completion.complete()
        else:
            self.completion.popup().hide()


class DetailDialog(QDialog):
    def __init__(self, item, atlas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Program ayrıntıları")
        self.resize(900, 690)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setStyleSheet("QTextBrowser {border:0; padding:12px;}")
        fields = [("Program kodu", item["kod"]), ("Puan türü", item["puan_turu"]),
                  ("Fakülte / yüksekokul", item["fakulte"]),
                  ("Program ili / ilçesi", " / ".join(str(item[k]) for k in ("sehir", "ilce") if item[k])),
                  ("Üniversite türü", item["uni_turu"]), ("Eğitim dili", item["dil"]),
                  ("Süre (hazırlık hariç)", f"{item['sure']} yıl" if item["sure"] else None),
                  ("Öğretim türü", item["ogretim"]), ("Burs / ücret", item["burs"]),
                  ("Akreditasyon", item["akreditasyon"]), ("2026 genel kontenjan", fmt(item["kontenjan"])),
                  ("2026 yerleşen", fmt(item["yerlesen"])), ("2026 en büyük puan", fmt(item["tavan"], 5))]
        rows = [f"<tr><td><b>{esc(name)}</b></td><td>{esc(value or 'Belirtilmemiş')}</td></tr>" for name, value in fields]
        history_rows = []
        for h in sorted(item["gecmis"], key=lambda h: h["yil"], reverse=True):
            previous, rank = year_data(item, h["yil"] - 1).get("sira"), h.get("sira")
            change = "—"
            if rank and previous:
                delta = previous - rank
                change = f"{fmt(abs(delta))} basamak " + ("iyileşme" if delta > 0 else "gerileme" if delta < 0 else "değişim")
            history_rows.append(f"<tr><td>{h['yil']}</td><td>{fmt(rank)}</td>"
                                f"<td>{fmt(h.get('puan'), 5)}</td><td>{fmt(h.get('kontenjan'))}</td><td>{change}</td></tr>")
        conditions = []
        for code in (item.get("kosullar") or "").replace(" ", "").split(","):
            if code:
                text = atlas["kosullar"].get(code, "Açıklama yerel veride yok; ÖSYM kılavuzunu açın.")
                conditions.append(f"<p><b>{esc(code)}.</b> {esc(text).replace(chr(10), '<br>')}</p>")
        browser.setHtml(f"<h2>{esc(item['bolum'])}</h2><p>{esc(item['uni'])}</p>"
            f"<table cellpadding='6'>{''.join(rows)}</table><h3>Yıllara göre yerleştirme</h3>"
            "<p>Başarı sırasında küçük sayı daha üst sırayı gösterir. Yıllar arasındaki puanlar doğrudan karşılaştırılmamalıdır.</p>"
            "<table border='1' cellspacing='0' cellpadding='7'><tr><th>Yıl</th><th>Başarı sırası</th>"
            f"<th>En küçük puan</th><th>Kontenjan</th><th>Önceki yıla göre</th></tr>{''.join(history_rows)}</table>"
            "<h3>Özel koşullar ve açıklamalar · 2026</h3>"
            + ("".join(conditions) or "<p>Yerel veride koşul açıklaması bulunmuyor.</p>")
            + "<p>Kaynak: ÖSYM 2026 yerleştirme tabloları ve YÖK Atlas. Geçmiş değerler yerleşme garantisi vermez.</p>")
        layout.addWidget(browser)
        actions = QHBoxLayout()
        actions.addWidget(button("YÖK Atlas’ta aç", lambda: open_url(f"https://yokatlas.yok.gov.tr/detay/{item['kod']}")))
        actions.addWidget(button("ÖSYM kılavuzu", lambda: open_url(GUIDE)))
        actions.addStretch()
        actions.addWidget(button("Kapat", self.accept))
        layout.addLayout(actions)


class CompareDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Programları karşılaştır")
        self.resize(1050, 660)
        layout = QVBoxLayout(self)
        layout.addWidget(label("Her sütun bir programdır. Farklı puan türlerinin sıralamaları birbirleriyle karşılaştırılmaz.", True))
        fields = [("Program", lambda d: d["bolum"]), ("Üniversite", lambda d: d["uni"]),
                  ("Program kodu", lambda d: d["kod"]), ("Puan türü", lambda d: d["puan_turu"]),
                  ("Şehir", lambda d: d["sehir"]), ("Üniversite türü", lambda d: d["uni_turu"]),
                  ("Burs / ücret", lambda d: d["burs"]), ("Eğitim dili", lambda d: d["dil"]),
                  ("Süre", lambda d: f"{d['sure']} yıl" if d["sure"] else None),
                  ("2026 kontenjan", lambda d: fmt(d["kontenjan"])), ("2026 yerleşen", lambda d: fmt(d["yerlesen"]))]
        for year in (2026, 2025, 2024, 2023):
            fields.append((f"{year} başarı sırası", lambda d, y=year: fmt(year_data(d, y).get("sira"))))
            fields.append((f"{year} en küçük puan", lambda d, y=year: fmt(year_data(d, y).get("puan"), 5)))
        self.table = QTableWidget(len(fields), len(items))
        self.table.setHorizontalHeaderLabels([f"Program {i+1}" for i in range(len(items))])
        self.table.setVerticalHeaderLabels([name for name, _ in fields])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(180)
        for row, (_, getter) in enumerate(fields):
            for col, item in enumerate(items):
                value = getter(item)
                cell = QTableWidgetItem(str(value if value is not None else "Belirtilmemiş"))
                cell.setToolTip(cell.text())
                self.table.setItem(row, col, cell)
        self.table.resizeRowsToContents()
        layout.addWidget(self.table)
        layout.addWidget(button("Kapat", self.accept))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.table.resizeRowsToContents)


class PreferenceDialog(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Tercih listem")
        self.resize(850, 570)
        layout = QVBoxLayout(self)
        layout.addWidget(label("Araştırma listeniz bu bilgisayarda saklanır. Bu liste ÖSYM’ye gönderilmez. Karşılaştırmak için Ctrl ile 2–4 program seçin.", True))
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.itemDoubleClicked.connect(lambda _: self.details())
        layout.addWidget(self.list)
        actions = QHBoxLayout()
        for text, callback in [("Yukarı", lambda: self.move(-1)), ("Aşağı", lambda: self.move(1)),
                               ("Kaldır", self.remove), ("Ayrıntılar", self.details),
                               ("Karşılaştır", self.compare), ("CSV olarak kaydet", self.export)]:
            actions.addWidget(button(text, callback))
        layout.addLayout(actions)
        self.reload()

    def reload(self):
        self.list.clear()
        for n, code in enumerate(self.window.store.codes, 1):
            d = self.window.engine.by_code.get(code)
            text = f"{n}. {d['uni']} — {d['bolum']}" if d else f"{n}. {code} — güncel veride bulunmuyor"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setToolTip(text)
            self.list.addItem(item)

    def persist(self, codes):
        try:
            self.window.store.save(codes)
        except OSError as exc:
            QMessageBox.warning(self, "Liste kaydedilemedi", str(exc))
            return False
        self.window.update_actions()
        self.reload()
        return True

    def move(self, step):
        selected = self.list.selectedItems()
        if len(selected) != 1:
            QMessageBox.information(self, "Program seçin", "Sırasını değiştirmek için bir program seçin.")
            return
        row = self.list.row(selected[0])
        target = row + step
        if 0 <= target < len(self.window.store.codes):
            codes = self.window.store.codes.copy()
            codes[row], codes[target] = codes[target], codes[row]
            if self.persist(codes):
                self.list.setCurrentRow(target)

    def remove(self):
        selected = {i.data(Qt.ItemDataRole.UserRole) for i in self.list.selectedItems()}
        if selected:
            self.persist([c for c in self.window.store.codes if c not in selected])

    def selected(self):
        return [self.window.engine.by_code[i.data(Qt.ItemDataRole.UserRole)]
                for i in self.list.selectedItems() if i.data(Qt.ItemDataRole.UserRole) in self.window.engine.by_code]

    def details(self):
        items = self.selected()
        if len(items) == 1:
            self.window.details(items[0])
        else:
            QMessageBox.information(self, "Program seçin", "Ayrıntıları görmek için bir program seçin.")

    def compare(self):
        self.window.compare(self.selected())

    def export(self):
        if not self.window.store.codes:
            QMessageBox.information(self, "Liste boş", "Önce listenize program ekleyin.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Tercih listesini kaydet", "tercih_listem.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Tercih", "Program Kodu", "Üniversite", "Program", "Puan Türü", "2026 Başarı Sırası"])
                for n, code in enumerate(self.window.store.codes, 1):
                    d = self.window.engine.by_code.get(code, {})
                    writer.writerow([n, code, d.get("uni", ""), d.get("bolum", ""), d.get("puan_turu", ""),
                                     year_data(d, 2026).get("sira", "") if d else ""])
        except OSError as exc:
            QMessageBox.warning(self, "Dosya kaydedilemedi", str(exc))


class ResultCard(QFrame):
    def __init__(self, item, window, year):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 18)
        layout.addWidget(label(f"{item['duzey']} · {item['puan_turu']} · {item['sehir'] or 'Şehir belirtilmemiş'} · {item['kod']}", True))
        title = QLabel(f'<a style="color:#1a0dab;text-decoration:none;" href="detail">{esc(item["uni"])} — {esc(item["bolum"])}</a>')
        title.setWordWrap(True)
        title.setStyleSheet("font-size:17px;")
        title.linkActivated.connect(lambda _: window.details(item))
        layout.addWidget(title)
        layout.addWidget(label(f"{item['uni_turu']} · {item['burs']} · {item['dil'] or 'Dil belirtilmemiş'}", True))
        h = year_data(item, year)
        layout.addWidget(label(f"{year} başarı sırası: {fmt(h.get('sira'))}     En küçük puan: {fmt(h.get('puan'), 5)}     Kontenjan: {fmt(h.get('kontenjan'))}"))
        actions = QHBoxLayout()
        self.save = button("", lambda: window.toggle_preference(item["kod"]))
        self.code = item["kod"]
        actions.addWidget(self.save)
        actions.addWidget(button("Ayrıntılar", lambda: window.details(item)))
        self.check = QCheckBox("Karşılaştır")
        self.check.setChecked(item["kod"] in window.comparison)
        self.check.toggled.connect(lambda checked: window.toggle_compare(item["kod"], checked, self.check))
        actions.addWidget(self.check)
        actions.addStretch()
        layout.addLayout(actions)


class AnaPencere(QMainWindow):
    PAGE_SIZE = 25

    def __init__(self, data=None, atlas=None, store=None):
        super().__init__()
        if data is None:
            data, atlas = load_data()
        self.data, self.atlas = data, atlas
        self.engine = SearchEngine(data)
        self.store = store or PreferenceStore()
        self.comparison, self.results, self.cards = [], [], []
        self.query, self.page, self.filters = "", 0, {}
        self.setWindowTitle("Üni-Ara · Üniversite ve tercih araştırması")
        self.resize(1180, 780)
        self.setMinimumSize(860, 600)
        self.setStyleSheet(STYLE)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.create_home()
        self.create_results()
        self.update_actions()
        if self.store.error:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Tercih dosyası okunamadı", str(self.store.path) + "\n" + self.store.error))

    def create_home(self):
        self.home = QWidget()
        layout = QVBoxLayout(self.home)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.addStretch(2)
        logo = QLabel(LOGO_HTML)
        logo.setStyleSheet("font-size:80px; font-weight:700;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        subtitle = label("Üniversiteni keşfet, seçeneklerini karşılaştır.", True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        self.home_search = SearchBox(self.engine, self.search)
        self.home_search.setMaximumWidth(700)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.home_search, 6)
        row.addStretch()
        layout.addLayout(row)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button("Ara", lambda: self.search(self.home_search.text()), True))
        actions.addWidget(button("Tüm programlar ve filtreler", lambda: self.search("")))
        self.home_saved = button("Tercih listem", self.preferences)
        actions.addWidget(self.home_saved)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch(2)
        footer = label(f"{fmt(len(self.data))} program · ÖSYM 2026 ve YÖK Atlas · 2023–2026 geçmiş verileri", True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        self.stack.addWidget(self.home)

    def create_results(self):
        self.result_page = QWidget()
        layout = QVBoxLayout(self.result_page)
        top = QHBoxLayout()
        top.addWidget(button("Üni-Ara", lambda: self.stack.setCurrentWidget(self.home)))
        self.search_box = SearchBox(self.engine, self.search)
        top.addWidget(self.search_box, 1)
        top.addWidget(button("Ara", lambda: self.search(self.search_box.text()), True))
        self.saved_button = button("Tercih listem", self.preferences)
        top.addWidget(self.saved_button)
        self.compare_button = button("Karşılaştır", lambda: self.compare([self.engine.by_code[c] for c in self.comparison]))
        top.addWidget(self.compare_button)
        clear_compare = button("×", self.clear_comparison)
        clear_compare.setToolTip("Karşılaştırma seçimlerini temizle")
        clear_compare.setAccessibleName("Karşılaştırma seçimlerini temizle")
        top.addWidget(clear_compare)
        layout.addLayout(top)
        body = QHBoxLayout()
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setFixedWidth(235)
        panel = QFrame()
        panel.setObjectName("filterPanel")
        fl = QVBoxLayout(panel)
        fl.setContentsMargins(5, 12, 14, 12)
        heading = label("Aramanı daralt")
        heading.setObjectName("sectionTitle")
        fl.addWidget(heading)
        self.combos = {}
        for key, text in [("duzey", "Öğrenim düzeyi"), ("puan_turu", "Puan türü"), ("sehir", "Programın ili"),
                          ("uni_turu", "Üniversite türü"), ("burs", "Burs / ücret"), ("dil", "Eğitim dili")]:
            fl.addWidget(label(text, True))
            combo = NoWheelComboBox()
            combo.addItems(["Tümü"] + sorted({str(d.get(key) or "Belirtilmemiş") for d in self.data}))
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(10)
            self.combos[key] = combo
            fl.addWidget(combo)
        fl.addWidget(label("Sıralama ve puan yılı", True))
        self.year_combo = NoWheelComboBox()
        self.year_combo.addItems(["2026", "2025", "2024", "2023"])
        fl.addWidget(self.year_combo)
        fl.addWidget(label("Başarı sırası aralığı (0 = sınır yok)", True))
        self.rank_min, self.rank_max = self.rank_box(), self.rank_box()
        self.rank_min.setPrefix("En az: ")
        self.rank_max.setPrefix("En çok: ")
        fl.addWidget(self.rank_min)
        fl.addWidget(self.rank_max)
        self.near_rank = QCheckBox("Sıralamama yakın programlar")
        fl.addWidget(self.near_rank)
        self.student_rank = self.rank_box()
        self.student_rank.setPrefix("Sıram: ")
        fl.addWidget(self.student_rank)
        self.band = NoWheelSpinBox()
        self.band.setRange(5, 100)
        self.band.setValue(25)
        self.band.setPrefix("Aralık: ±%")
        fl.addWidget(self.band)
        self.near_rank.toggled.connect(self.rank_mode)
        self.rank_mode(False)
        fl.addStretch()
        filter_scroll.setWidget(panel)
        filter_column = QVBoxLayout()
        filter_column.addWidget(filter_scroll, 1)
        filter_column.addWidget(button("Filtreleri uygula", self.apply_filters, True))
        filter_column.addWidget(button("Filtreleri temizle", self.reset_filters))
        body.addLayout(filter_column)
        right = QVBoxLayout()
        toolbar = QHBoxLayout()
        self.count_label = label("", True)
        toolbar.addWidget(self.count_label, 1)
        self.sort_combo = NoWheelComboBox()
        self.sort_combo.addItems(["Başarı sırası", "Puan (yüksekten)", "Üniversite adı"])
        self.sort_combo.currentTextChanged.connect(self.change_sort)
        toolbar.addWidget(self.sort_combo)
        right.addLayout(toolbar)
        self.context_label = label("", True)
        right.addWidget(self.context_label)
        self.correction_button = button("", self.use_correction)
        self.correction_button.hide()
        right.addWidget(self.correction_button)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        right.addWidget(self.scroll, 1)
        paging = QHBoxLayout()
        self.prev = button("← Önceki", lambda: self.go_page(self.page - 1))
        self.next = button("Sonraki →", lambda: self.go_page(self.page + 1))
        self.page_spin = NoWheelSpinBox()
        self.page_spin.setPrefix("Sayfa ")
        self.page_spin.valueChanged.connect(lambda n: self.go_page(n - 1))
        self.page_count = label("")
        paging.addWidget(self.prev)
        paging.addStretch()
        paging.addWidget(self.page_spin)
        paging.addWidget(self.page_count)
        paging.addStretch()
        paging.addWidget(self.next)
        right.addLayout(paging)
        body.addLayout(right, 1)
        layout.addLayout(body, 1)
        self.stack.addWidget(self.result_page)

    @staticmethod
    def rank_box():
        spin = NoWheelSpinBox()
        spin.setRange(0, 10000000)
        spin.setGroupSeparatorShown(True)
        return spin

    def rank_mode(self, enabled):
        self.student_rank.setEnabled(enabled)
        self.band.setEnabled(enabled)
        self.rank_min.setEnabled(not enabled)
        self.rank_max.setEnabled(not enabled)

    def apply_filters(self):
        f = {key: combo.currentText() for key, combo in self.combos.items()}
        f.update(yil=int(self.year_combo.currentText()), min_sira=self.rank_min.value(),
                 max_sira=self.rank_max.value(), sirala=self.sort_combo.currentText())
        if self.near_rank.isChecked():
            rank = self.student_rank.value()
            if not rank:
                QMessageBox.information(self, "Sıralamanı gir", "Yakın programları bulmak için başarı sıranı gir.")
                return
            margin = self.band.value() / 100
            f.update(min_sira=max(1, math.ceil(rank * (1 - margin))), max_sira=math.floor(rank * (1 + margin)))
        if (f["min_sira"] or f["max_sira"]) and f["puan_turu"] == "Tümü":
            QMessageBox.information(self, "Puan türünü seç", "Başarı sırası araması için SAY, EA, SÖZ, DİL veya TYT puan türünü seç.")
            return
        if f["max_sira"] and f["min_sira"] > f["max_sira"]:
            QMessageBox.information(self, "Aralığı kontrol et", "En az sıra değeri, en çok sıra değerinden büyük olamaz.")
            return
        self.filters = f
        self.search(self.search_box.text())

    def reset_filters(self):
        for combo in self.combos.values():
            combo.setCurrentIndex(0)
        self.year_combo.setCurrentIndex(0)
        self.rank_min.setValue(0)
        self.rank_max.setValue(0)
        self.near_rank.setChecked(False)
        self.student_rank.setValue(0)
        self.filters = {"sirala": self.sort_combo.currentText()}
        self.search(self.search_box.text())

    def change_sort(self, text):
        self.filters["sirala"] = text
        self.search(self.query)

    def search(self, query):
        self.query = query.strip()
        self.search_box.setText(self.query)
        self.home_search.completion.popup().hide()
        self.search_box.completion.popup().hide()
        self.results = self.engine.search(self.query, self.filters)
        self.correction = self.engine.correction(self.query) if not self.results and self.query else None
        self.correction_button.setVisible(bool(self.correction))
        if self.correction:
            self.correction_button.setText(f"Şunu mu demek istedin: {self.correction}?")
        self.stack.setCurrentWidget(self.result_page)
        self.page = 0
        self.render_results()

    def use_correction(self):
        if self.correction:
            self.search(self.correction)

    def go_page(self, page):
        count = max(1, math.ceil(len(self.results) / self.PAGE_SIZE))
        self.page = max(0, min(page, count - 1))
        self.render_results()

    def render_results(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(5, 0, 12, 10)
        year = self.filters.get("yil", 2026)
        start = self.page * self.PAGE_SIZE
        visible = self.results[start:start + self.PAGE_SIZE]
        self.cards = []
        for item in visible:
            card = ResultCard(item, self, year)
            self.cards.append(card)
            layout.addWidget(card)
        if not visible:
            layout.addWidget(label("Sonuç bulunamadı. Daha kısa bir arama deneyin veya filtreleri temizleyin."))
        layout.addStretch()
        old = self.scroll.takeWidget()
        if old:
            old.deleteLater()
        self.scroll.setWidget(content)
        self.scroll.verticalScrollBar().setValue(0)
        total = len(self.results)
        self.count_label.setText(f"{fmt(total)} sonuç · {start+1 if total else 0}–{min(start+self.PAGE_SIZE, total)} gösteriliyor")
        text = f"{year} sıralama ve puanları · Kaynak: ÖSYM / YÖK Atlas"
        if self.filters.get("min_sira") or self.filters.get("max_sira"):
            text += f"\nSıra aralığı: {fmt(self.filters.get('min_sira') or 1)}–{fmt(self.filters.get('max_sira')) if self.filters.get('max_sira') else 'sınırsız'}. Geçmiş sonuçlar yerleşme garantisi değildir."
        self.context_label.setText(text)
        count = max(1, math.ceil(total / self.PAGE_SIZE))
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, count)
        self.page_spin.setValue(self.page + 1)
        self.page_spin.blockSignals(False)
        self.page_count.setText(f"/ {count}")
        self.prev.setEnabled(self.page > 0)
        self.next.setEnabled(self.page < count - 1)
        self.update_actions()

    def update_actions(self):
        count = len(self.store.codes)
        for widget in (self.home_saved, self.saved_button):
            widget.setText(f"Tercih listem ({count})")
        self.compare_button.setText(f"Karşılaştır ({len(self.comparison)}/4)")
        self.compare_button.setEnabled(len(self.comparison) >= 2)
        for card in self.cards:
            card.save.setText("Listeden çıkar" if card.code in self.store.codes else "Listeme ekle")

    def toggle_preference(self, code):
        try:
            self.store.toggle(code)
        except OSError as exc:
            QMessageBox.warning(self, "Liste kaydedilemedi", str(exc))
        self.update_actions()

    def toggle_compare(self, code, checked, checkbox):
        if checked and code not in self.comparison:
            if len(self.comparison) >= 4:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
                QMessageBox.information(self, "Karşılaştırma sınırı", "Aynı anda en fazla dört program karşılaştırabilirsiniz.")
                return
            self.comparison.append(code)
        elif not checked and code in self.comparison:
            self.comparison.remove(code)
        self.update_actions()

    def details(self, item):
        DetailDialog(item, self.atlas, self).exec()

    def clear_comparison(self):
        self.comparison.clear()
        for card in self.cards:
            card.check.blockSignals(True)
            card.check.setChecked(False)
            card.check.blockSignals(False)
        self.update_actions()

    def compare(self, items):
        if not 2 <= len(items) <= 4:
            QMessageBox.information(self, "Program seçin", "Karşılaştırmak için 2–4 program seçin.")
            return
        CompareDialog(items, self).exec()

    def preferences(self):
        PreferenceDialog(self).exec()
        self.update_actions()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    try:
        window = AnaPencere()
    except (OSError, ValueError, KeyError) as error:
        QMessageBox.critical(None, "Veri yüklenemedi", f"Program veri dosyalarını kontrol edin.\n{error}")
        sys.exit(1)
    window.show()
    sys.exit(app.exec())
