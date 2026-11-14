"""Minimal equipment-label splash and About windows for the standalone release.

Design inspired by industrial identification plates: solid colour field,
precise dark compartments, restrained typography, no simulated diagnostics.
Independent implementation with no external application linkage.
"""
from __future__ import annotations

import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

REVISION = "1.6.1"
COLOURS = {
    "amber": ("#d8ab5c", "#0a110e", "#b3a88c"),
    "phosphor": ("#a9cc8b", "#0a110e", "#9ea994"),
    "red": ("#d98a77", "#100d0d", "#ab9691"),
    "mono": ("#c2c9c2", "#0d100e", "#989f99"),
}


def _font(size: int, bold: bool = False) -> QFont:
    f = QFont("Consolas")
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setPixelSize(size)
    f.setBold(bold)
    return f


class EquipmentPlate(QWidget):
    """Exactly two public displays: a 2-second boot plate or a click-to-close About plaque."""
    def __init__(self, kind: str = "boot", theme: str = "amber"):
        if kind not in ("boot", "about"):
            raise ValueError("Unknown plate type")
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.NoDropShadowWindowHint)
        self.kind = kind
        self.theme = theme if theme in COLOURS else "amber"
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedSize(620, 176) if kind == "boot" else self.setFixedSize(420, 156)
        self.setToolTip("Click to close" if kind == "about" else "")
        self.started = time.monotonic()
        self._timer = None
        if kind == "boot":
            self._timer = QTimer(self)
            self._timer.setInterval(40)
            self._timer.timeout.connect(self._tick)
            self._timer.start()

    def _tick(self):
        elapsed = min(1.0,max(0.0,(time.monotonic()-self.started)/2.0))
        if elapsed > .875:
            self.setWindowOpacity(max(0.0,(1.0-elapsed)/.125))
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        screen = QGuiApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.move(rect.center() - QPoint(self.width() // 2, self.height() // 2))
        self.started = time.monotonic()

    def closeEvent(self, event):
        if self._timer:
            self._timer.stop()
        super().closeEvent(event)

    def mouseReleaseEvent(self, event):
        if self.kind == "about":
            self.close()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.close()
        else:
            super().keyPressEvent(event)

    def _write(self, p, rect, label, size, colour, bold=False, flags=None):
        p.setFont(_font(size, bold))
        p.setPen(colour)
        p.drawText(rect, flags if flags is not None else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)

    def _mark(self, p, rect, colour):
        """A compact, original segmented specimen symbol, not a copied corporate logo."""
        x,y,w,h = rect.x(),rect.y(),rect.width(),rect.height()
        # Four symmetrical clamp arms plus an aperture. No fine line work at small scales.
        for side in (0,1):
            a = x + (w*.16 if side == 0 else w*.69)
            p.fillRect(QRectF(a,y+h*.12,w*.15,h*.25),colour)
            p.fillRect(QRectF(a,y+h*.63,w*.15,h*.25),colour)
        p.fillRect(QRectF(x+w*.39,y+h*.33,w*.22,h*.34),colour)

    def _boot(self, p, accent, dark, low):
        p.fillRect(self.rect(),accent)
        p.fillRect(QRectF(10,10,94,101),dark)
        p.fillRect(QRectF(112,10,320,101),dark)
        p.fillRect(QRectF(440,10,170,101),dark)
        p.fillRect(QRectF(10,119,422,47),dark)
        p.fillRect(QRectF(440,119,170,47),dark)
        self._mark(p,QRectF(23,22,67,76),accent)
        self._write(p,QRectF(130,16,285,47),"SPECIMEN.SYS",26,accent,True)
        self._write(p,QRectF(130,64,280,26),"BIOLOGICAL OBSERVATION",13,accent)
        self._write(p,QRectF(130,89,260,17),"INSTRUMENT  /  REV " + REVISION,10,low)
        self._write(p,QRectF(450,25,149,47),"SYS  01",22,dark,True,Qt.AlignmentFlag.AlignCenter)
        self._write(p,QRectF(450,72,149,21),"LOCAL  /  OFFLINE",11,dark,True,Qt.AlignmentFlag.AlignCenter)
        self._write(p,QRectF(22,122,390,38),"SELF-CONTAINED OBSERVATION DISPLAY",12,accent,True)
        elapsed = min(1.0,max(0.0,(time.monotonic()-self.started)/2.0))
        self._write(p,QRectF(450,120,152,20),"READY" if elapsed >= .94 else "STARTUP",11,accent,True)
        # Progress indicates the splash duration, not a fabricated system check.
        p.setPen(QPen(accent,1))
        p.drawRect(QRectF(449,149,152,7))
        p.fillRect(QRectF(451,151,148*elapsed,3),accent)

    def _about(self, p, accent, dark, low):
        p.fillRect(self.rect(),dark)
        p.setPen(QPen(accent,2))
        p.drawRect(1,1,self.width()-3,self.height()-3)
        self._write(p,QRectF(17,10,380,28),"INDEPENDENT  /  OBSERVATION SYSTEM",11,low)
        self._write(p,QRectF(17,35,382,45),"SPECIMEN.SYS",28,accent,True)
        self._write(p,QRectF(18,82,375,25),f"REV {REVISION}  /  DESKTOP INSTRUMENT",12,accent)
        p.setPen(QPen(QColor("#354137"),1))
        p.drawLine(2,117,self.width()-3,117)
        self._write(p,QRectF(18,122,250,26),"OFFLINE  ·  CODE: MIT",11,low)
        self._write(p,QRectF(245,122,157,26),"CLICK TO CLOSE",10,accent,False,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing,False)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing,True)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(),QColor(0,0,0,0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        a,b,c=COLOURS[self.theme]
        accent,dark,low=QColor(a),QColor(b),QColor(c)
        if self.kind=="boot":self._boot(p,accent,dark,low)
        else:self._about(p,accent,dark,low)
        p.end()
