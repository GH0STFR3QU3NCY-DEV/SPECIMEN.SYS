"""Automated Qt rendering test on a Windows runner.

This exercises real QWidget painting but NOT the user's desktop, taskbar
compositor, DPI settings, or physical multi-monitor behaviour.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication
from specimen_sys.app import Controller
from specimen_sys.plates import EquipmentPlate


def capture(widget, path: Path, transparent_corner: bool = True) -> str:
    widget.show()
    QApplication.processEvents()
    image = widget.grab().toImage()
    assert not image.isNull(), f"Empty Qt render: {path}"
    assert image.width() >= 300 and image.height() >= 150
    if transparent_corner:
        assert image.pixelColor(0, 0).alpha() == 0, f"Widget corner not transparent: {path}"
    assert image.pixelColor(image.width() // 2, image.height() // 2).alpha() > 0
    assert image.save(str(path), "PNG"), f"Could not save verification screenshot: {path}"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="specimen-qt-review-") as directory:
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
        settings = QSettings("SpecimenSystems", "SpecimenSysPublic")
        settings.setValue("splash_enabled", False)
        settings.setValue("visible", False)
        settings.setValue("size", "standard")
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        ctl = Controller(app)
        assert ctl.window.windowFlags() & Qt.WindowType.Tool
        assert ctl.window.windowFlags() & Qt.WindowType.FramelessWindowHint
        assert not ctl.tray.icon().isNull()
        ctl._set_option("display_style", "detailed")
        detailed = capture(ctl.window, Path(directory) / "detailed.png")
        ctl._set_option("display_style", "classic")
        classic = capture(ctl.window, Path(directory) / "classic.png")
        assert detailed != classic, "Display style switching did not change rendered pixels"
        ctl._set_option("size", "compact")
        assert ctl.window.width() == 449 and ctl.window.height() == 561
        capture(ctl.window, Path(directory) / "compact.png")
        for kind, size in (("boot", (620, 176)), ("about", (420, 156))):
            plaque = EquipmentPlate(kind)
            assert plaque.windowFlags() & Qt.WindowType.FramelessWindowHint
            assert plaque.windowFlags() & Qt.WindowType.Tool
            assert (plaque.width(), plaque.height()) == size
            capture(plaque, Path(directory) / f"{kind}.png", transparent_corner=False)
            plaque.close()
        ctl.quit()
        print("Windows Qt offscreen UI render: PASS (not an interactive desktop test)")


if __name__ == "__main__":
    main()
