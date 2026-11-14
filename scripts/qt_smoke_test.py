"""Headless Windows CI smoke test of actual Qt widget and control wiring.

This is not a substitute for a visible desktop, multi-monitor or tray test.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import QApplication
from specimen_sys.app import Controller
from specimen_sys.plates import EquipmentPlate

app=QApplication([])
q=QSettings('SpecimenSystems','SpecimenSysPublic')
q.setValue('splash_enabled',False)
q.setValue('visible',False)
ctl=Controller(app)
assert ctl.window.windowFlags() & Qt.WindowType.Tool
assert ctl.window.windowFlags() & Qt.WindowType.FramelessWindowHint
assert ctl.tray.icon().isNull() is False
assert ctl.assets.base_for('detailed').width()==1122
assert ctl.assets.base_for('classic').width()==1122
ctl._set_option('display_style','classic')
assert ctl.cfg.get('display_style')=='classic'
ctl.about();assert ctl._popup is not None
assert isinstance(ctl._popup,EquipmentPlate)
assert ctl._popup.windowFlags() & Qt.WindowType.FramelessWindowHint
ctl._popup.close()
boot=EquipmentPlate('boot')
assert boot.size().width()==620 and boot.size().height()==176
boot.close()
ctl._set_option('display_style','detailed')
ctl.quit()
print('Qt offscreen smoke test: PASS (no real desktop compositor checked)')
