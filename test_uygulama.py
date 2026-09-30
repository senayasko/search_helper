import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QTextBrowser
from uni_ara import AnaPencere, DetailDialog, CompareDialog, PreferenceDialog
from veri import load_data, SearchEngine, PreferenceStore, year_data, number


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.data, cls.atlas = load_data()
        cls.engine = SearchEngine(cls.data)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "tercihler.json"
        self.store = PreferenceStore(self.path)

    def tearDown(self):
        self.app.processEvents()
        self.temp.cleanup()

    def window(self):
        w = AnaPencere(self.data, self.atlas, self.store)
        self.addCleanup(w.close)
        return w

    def test_official_sources_match(self):
        self.assertEqual(len(self.data), 21493)
        self.assertEqual(set(self.engine.by_code), set(self.atlas["programlar"]))
        for item in self.data:
            source = self.atlas["programlar"][item["kod"]]
            self.assertEqual(item["uni"], source["universite"])
            self.assertEqual(item["bolum"], source["bolum"])
            a, b = item["puan"], number(source["gecmis"][0]["puan"])
            if a is not None and b is not None:
                self.assertAlmostEqual(a, b, places=5)

    def test_history_years_and_missing_rank(self):
        item = self.engine.by_code["102210277"]
        self.assertEqual([year_data(item, y)["sira"] for y in (2026, 2025, 2024, 2023)], [4560, 1448, 1008, 775])
        missing = next(d for d in self.data if not year_data(d).get("sira"))
        self.assertEqual(self.engine.search(missing["kod"], {"min_sira": 1}), [])

    def test_search_and_spelling(self):
        self.assertEqual([d["kod"] for d in self.engine.search("bogazici bilgisayar")],
                         [d["kod"] for d in self.engine.search("BOĞAZİÇİ BİLGİSAYAR")])
        self.assertTrue(self.engine.search("bogazici bilgisayar"))
        self.assertEqual(self.engine.correction("bogazci bilgisyar"), "bogazici bilgisayar")
        self.assertTrue(self.engine.suggest("bogazi"))

    def test_filters_combine_and_use_selected_year(self):
        results = self.engine.search("", {"puan_turu": "SAY", "sehir": "İSTANBUL", "dil": "İngilizce",
                                          "burs": "Burslu", "uni_turu": "VAKIF", "yil": 2025,
                                          "min_sira": 1, "max_sira": 20000})
        self.assertTrue(results)
        self.assertTrue(all(d["sehir"] == "İSTANBUL" and d["burs"] == "Burslu" and
                            1 <= year_data(d, 2025)["sira"] <= 20000 for d in results))

    def test_preferences_survive_restart_and_reorder(self):
        self.store.toggle("102210277")
        self.store.toggle("102210011")
        self.store.save(list(reversed(self.store.codes)))
        reopened = PreferenceStore(self.path)
        self.assertEqual(reopened.codes, ["102210011", "102210277"])
        reopened.toggle("102210277")
        self.assertEqual(PreferenceStore(self.path).codes, ["102210011"])

    def test_corrupt_preferences_are_not_overwritten(self):
        self.path.write_text("broken", encoding="utf-8")
        store = PreferenceStore(self.path)
        self.assertIsNotNone(store.error)
        with self.assertRaises(OSError):
            store.toggle("102210277")
        self.assertEqual(self.path.read_text(), "broken")

    def test_pagination_reaches_last_result_and_resets(self):
        w = self.window()
        w.search("bilgisayar")
        first = {c.code for c in w.cards}
        w.go_page(1)
        self.assertFalse(first & {c.code for c in w.cards})
        w.go_page(100000)
        self.assertEqual(w.cards[-1].code, w.results[-1]["kod"])
        self.assertFalse(w.next.isEnabled())
        w.search("102210277")
        self.assertEqual(w.page, 0)
        self.assertEqual(len(w.cards), 1)

    def test_student_rank_requires_type_then_filters(self):
        w = self.window()
        w.search("")
        w.near_rank.setChecked(True)
        w.student_rank.setValue(10000)
        with patch("uni_ara.QMessageBox.information") as message:
            w.apply_filters()
            message.assert_called_once()
        w.combos["puan_turu"].setCurrentText("SAY")
        w.apply_filters()
        self.assertTrue(w.results)
        self.assertTrue(all(7500 <= year_data(d)["sira"] <= 12500 and d["puan_turu"] == "SAY" for d in w.results))

    def test_comparison_limit_and_clear(self):
        w = self.window()
        w.search("bilgisayar")
        for card in w.cards[:4]:
            card.check.setChecked(True)
        with patch("uni_ara.QMessageBox.information"):
            w.cards[4].check.setChecked(True)
        self.assertEqual(len(w.comparison), 4)
        self.assertFalse(w.cards[4].check.isChecked())
        dialog = CompareDialog([w.engine.by_code[c] for c in w.comparison], w)
        self.assertEqual(dialog.table.columnCount(), 4)
        w.clear_comparison()
        self.assertFalse(any(c.check.isChecked() for c in w.cards))

    def test_detail_and_preference_dialog(self):
        w = self.window()
        self.store.save(["102210277", "102210011"])
        dialog = PreferenceDialog(w)
        dialog.list.setCurrentRow(1)
        dialog.move(-1)
        self.assertEqual(self.store.codes[0], "102210011")
        target = str(Path(self.temp.name) / "export.csv")
        with patch("uni_ara.QFileDialog.getSaveFileName", return_value=(target, "CSV")):
            dialog.export()
        self.assertIn("102210277", Path(target).read_text(encoding="utf-8-sig"))
        detail = DetailDialog(w.engine.by_code["102210277"], self.atlas, w)
        text = detail.findChild(QTextBrowser).toPlainText()
        self.assertIn("2023", text)
        self.assertIn("4.560", text)
        self.assertIn("Özel koşullar", text)

    def test_keyboard_autocomplete(self):
        w = self.window()
        w.show()
        w.home_search.setFocus()
        QTest.keyClicks(w.home_search, "bogazi")
        QTest.qWait(220)
        self.assertGreater(w.home_search.model.rowCount(), 0)
        popup = w.home_search.completion.popup()
        QTest.keyClick(popup, Qt.Key.Key_Down)
        QTest.keyClick(popup, Qt.Key.Key_Return)
        self.app.processEvents()
        self.assertEqual(w.stack.currentWidget(), w.result_page)
        self.assertTrue(w.results)


if __name__ == "__main__":
    unittest.main()
