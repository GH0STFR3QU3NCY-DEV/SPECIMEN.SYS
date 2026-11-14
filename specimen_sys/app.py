"""SPECIMEN.SYS: self-contained layered desktop observation instrument.

The static source image is never regenerated at runtime.  Five separate
pre-rendered RGBA anatomical layers and small diagnostic regions are painted
from one deterministic biological simulation. Qt paints only; no asset
synthesis, external processes, downloads, or network requests at runtime.
"""
from __future__ import annotations
import logging
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from PySide6.QtCore import QPoint, QRect, Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QCursor, QGuiApplication, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon, QWidget

from . import motion
from .plates import EquipmentPlate

APP_ID='SPECIMEN.SYS'
BASE_W,BASE_H=1122,1402
DEFAULTS={'size':'standard','intensity':'standard','paused':False,'reduced_motion':False,
          'always_on_top':False,'lock_position':False,'click_through':False,
          'x':-99999,'y':-99999,'visible':True,'theme':'amber','rolling_crt':True,
          'display_style':'detailed','splash_enabled':True}
THEMES={
    'amber':('#e4b669','#111812','#c9c8b7'),
    'phosphor':('#a3d68e','#0b180f','#e2f3cb'),
    'red':('#f07f6b','#1b1112','#f5cbbe'),
    'mono':('#bdcac4','#111615','#e4ebe6'),
}
ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
ASSETS=(ASSETS/'specimen_sys'/'assets') if getattr(sys,'_MEIPASS',None) else Path(__file__).parent/'assets'


class Config:
    def __init__(self):self.q=QSettings('SpecimenSystems','SpecimenSysPublic')
    def get(self,k):
        d=DEFAULTS[k]
        value=self.q.value(k,d,type=type(d))
        if k=='size' and value not in motion.SIZES:return d
        if k=='intensity' and value not in motion.INTENSITIES:return d
        if k=='theme' and value not in THEMES:return d
        if k=='display_style' and value not in ('classic','detailed'):return d
        return value
    def set(self,k,v):self.q.setValue(k,v)

class SpriteCache:
    """PNG decoding occurs once. Rendering tick never opens a file."""
    def __init__(self):
        import json
        self.manifest=json.loads((ASSETS/'layer_manifest.json').read_text('utf-8'))
        self.counts=self.manifest['counts']
        self.boxes={k:tuple(v) for k,v in self.manifest['boxes'].items()}
        self.bases={
            'detailed':self.load(ASSETS/'detailed_static_rgba.png'),
            'classic':self.load(ASSETS/'classic_static_rgba.png'),
        }
        self.layers={}
        self.ensure_mode('detailed')
        self.texts={}
        self.highlights=[self.load(ASSETS/'thumbnails'/f'active_{i}.png') for i in range(4)]
    def ensure_mode(self,style):
        if style in self.layers:return
        directory='layers' if style=='detailed' else 'layers_classic'
        self.layers[style]={name:[self.load(ASSETS/directory/name/f'{i:02d}.png')
                                  for i in range(n)]
                            for name,n in self.counts.items()}
    def base_for(self,style):
        return self.bases[style]
    def load(self,path):
        im=QImage(str(path))
        if im.isNull():raise FileNotFoundError(f'Cannot read widget image asset: {path}')
        return im
    def sprite(self,name,position,style='detailed'):
        self.ensure_mode(style)
        n=self.counts[name]
        return self.layers[style][name][max(0,min(n-1,round(position*(n-1))))]
    def text(self,kind,value):
        key=(kind,value)
        if key not in self.texts:
            safe=value.replace(' ','_').replace('%','pct').replace('.','p')
            self.texts[key]=self.load(ASSETS/'readouts'/f'{kind}_{safe}.png')
        return self.texts[key]

class Instrument(QWidget):
    def __init__(self,controller):
        super().__init__()
        self.c=controller
        self._moving_offset=None
        self._position_ready=False
        self._clamping=False
        self.setObjectName('SPECIMEN.SYS')
        self.setWindowTitle('SPECIMEN.SYS')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground,True)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating,True)
        self.setMouseTracking(True)
        self.apply_flags(False)
        self.resize_preset()
        self.restore_location()
        self._position_ready=True
    def apply_flags(self,show=True):
        cfg=self.c.cfg
        was_visible=self.isVisible()
        pos=self.pos()
        flags=(Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.NoDropShadowWindowHint)
        if cfg.get('always_on_top'):flags |= Qt.WindowType.WindowStaysOnTopHint
        if cfg.get('click_through'):flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setAutoFillBackground(False)
        self.move(pos)
        if show and was_visible:self.show()
    def resize_preset(self):
        factor=motion.SIZES[self.c.cfg.get('size')]
        self.setFixedSize(round(BASE_W*factor),round(BASE_H*factor))
        self.clamp_to_screen()
        self.update()
    def _screen(self):
        screens=QGuiApplication.screens()
        if not screens:return None
        center=self.frameGeometry().center()
        return next((s for s in screens if s.availableGeometry().contains(center)),
                    QGuiApplication.primaryScreen())
    def restore_location(self):
        x=self.c.cfg.get('x');y=self.c.cfg.get('y')
        if x==-99999 or y==-99999:
            screen=QGuiApplication.primaryScreen()
            if screen:
                g=screen.availableGeometry()
                self.move(g.right()-self.width()-36,g.top()+56)
        else:self.move(int(x),int(y))
        self.clamp_to_screen()
    def clamp_to_screen(self):
        if self._clamping:return
        self._clamping=True
        try:
            screen=self._screen()
            if screen is None:return
            a=screen.availableGeometry()
            # Keep the entire instrument within its current monitor if possible.
            x=min(max(self.x(),a.left()),max(a.left(),a.right()-self.width()+1))
            y=min(max(self.y(),a.top()),max(a.top(),a.bottom()-self.height()+1))
            self.move(x,y)
        finally:self._clamping=False
    def rect_scaled(self,x,y,w,h):
        fx=self.width()/BASE_W;fy=self.height()/BASE_H
        return QRect(round(x*fx),round(y*fy),round(w*fx)+2,round(h*fy)+2)
    def paintEvent(self,event):
        c=self.c
        p=QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(),QColor(0,0,0,0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,False)
        p.setRenderHint(QPainter.RenderHint.Antialiasing,False)
        p.scale(self.width()/BASE_W,self.height()/BASE_H)
        p.drawImage(QPoint(0,0),c.assets.base_for(c.cfg.get('display_style')))
        s=c.sample
        power=motion.INTENSITIES[c.cfg.get('intensity')]
        choices={'host':min(1.,s.breath_amplitude*power),
                 'sacs':min(1.,s.breath_amplitude*power),
                 'abdomen':s.abdomen_progress,
                 'fingers':s.finger_progress,
                 'tail':s.tail_progress}
        for name,v in choices.items():
            if v<0:continue
            x,y,_,_=c.assets.boxes[name]
            p.drawImage(QPoint(x,y),c.assets.sprite(name,v,c.cfg.get('display_style')))
        # Restore the dynamic readout glyphs over tiny cleaned HUD regions.
        for name,value,xy in (('resp',f'{s.smoothed_bpm} BPM',(992,553)),
                              ('tail',f'{s.tension_percent}%',(1009,695)),
                              ('cycle',f'{s.breath_duration:.1f} S',(961,981))):
            p.drawImage(QPoint(*xy),c.assets.text(name,value))
        # TC2: value updates with tail tension; bar is damped by a short lag.
        slots=max(0,min(3,round((c.bar_tension-72)*3/12)))
        for idx in range(slots):
            p.fillRect(QRect(round(1015+idx*14.4),768,11,17),QColor(137,221,121,214))
        # W2: stationary sine-like respiratory waveform, live small phosphor cursor.
        wp=s.breath_phase
        wx=round(777+wp*272)
        wy=round(635+16*math.sin(2*math.pi*(wx-777)*3/272+.04))
        p.fillRect(QRect(wx-2,wy-2,5,5),QColor(196,255,173,195))
        # BC2: indicate active respiratory keyframe, without animating thumbnails.
        thumb=s.phase_thumbnail
        thumb_origins=((97,1033),(336,1033),(570,1033),(801,1033))
        p.drawImage(QPoint(*thumb_origins[thumb]),c.assets.highlights[thumb])
        if c.cfg.get('rolling_crt') and not c.cfg.get('reduced_motion'):
            y_sweep=282 + int((s.elapsed * 52.0) % 671)
            p.fillRect(QRect(77,y_sweep,626,2),QColor(170,221,165,24))
            p.fillRect(QRect(77,y_sweep+2,626,9),QColor(5,22,12,11))
        p.end()
    def _can_drag(self,pos):
        x=pos.x()*BASE_W/max(1,self.width())
        y=pos.y()*BASE_H/max(1,self.height())
        # Metal chassis only: internal biological window is intentionally inert.
        return y<271 or y>1245 or x<29 or x>1085
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.RightButton:
            self.c.show_menu(event.globalPosition().toPoint())
        elif event.button()==Qt.MouseButton.LeftButton and not self.c.cfg.get('lock_position') and self._can_drag(event.position().toPoint()):
            self._moving_offset=event.globalPosition().toPoint()-self.frameGeometry().topLeft()
        event.accept()
    def mouseMoveEvent(self,event):
        if self._moving_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint()-self._moving_offset)
        event.accept()
    def mouseReleaseEvent(self,event):
        if self._moving_offset is not None:
            self._moving_offset=None
            self.clamp_to_screen()
            self.c.save_position()
        event.accept()
    def moveEvent(self,event):
        # Save only when not carrying out initial positioning/monitor recovery.
        if self._position_ready and not self._clamping and self._moving_offset is None:
            self.c.save_position()
        super().moveEvent(event)

class Controller:
    def __init__(self,app):
        self.app=app
        self.cfg=Config()
        self.assets=SpriteCache()
        self.biology=motion.Biology()
        self.clock=motion.PausableClock()
        self.sample=self.biology.at(0)
        self.bar_tension=72.
        self.previous_elapsed=0.
        self.window=Instrument(self)
        icon=QIcon(str(ASSETS.parent.parent/'branding'/'specimen.ico'))
        if icon.isNull():
            icon=QIcon(str(ASSETS.parent.parent/'branding'/'specimen-tray-32.png'))
        self.window.setWindowIcon(icon)
        self.app.setWindowIcon(icon)
        self.tray=QSystemTrayIcon(icon,self.window)
        self.tray.setToolTip('SPECIMEN.SYS | Biological Observation')
        self.tray.activated.connect(self._tray_activation)
        if QSystemTrayIcon.isSystemTrayAvailable():self.tray.show()
        self._tray_menu=self._build_menu(tray=True)
        self.tray.setContextMenu(self._tray_menu)
        self._popup=None
        self._splash=None
        self.timer=QTimer(self.window)
        self.timer.setInterval(70)  # ~14Hz, enough for restrained pixel movement
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        if self.cfg.get('paused'):self.clock.pause(time.monotonic())
        self._wire_monitors()
        if self.cfg.get('visible'):
            if self.cfg.get('splash_enabled'):
                self._splash=EquipmentPlate('boot',self.cfg.get('theme'))
                self._splash.show()
                QTimer.singleShot(2000,self._finish_splash)
            else:self.window.show()
    def _finish_splash(self):
        if self._splash is not None:
            self._splash.close()
            self._splash=None
        if self.cfg.get('visible'):self.window.show()
    def _wire_monitors(self):
        q=QGuiApplication.instance()
        q.screenAdded.connect(lambda s:self._monitor_changed())
        q.screenRemoved.connect(lambda s:self._monitor_changed())
        for s in QGuiApplication.screens():
            s.availableGeometryChanged.connect(lambda _g:self._monitor_changed())
    def _monitor_changed(self):
        self.window.clamp_to_screen()
        self.save_position()
    def _tray_icon(self):
        return QIcon(str(ASSETS.parent.parent/'branding'/'specimen.ico'))
    def tick(self):
        if self.cfg.get('paused') or self.cfg.get('reduced_motion'):
            return  # no needless event-loop repaint while appearance is frozen
        now=time.monotonic()
        elapsed=self.clock.elapsed(now)
        current=self.biology.at(elapsed)
        dt=max(0.,min(1.0,elapsed-self.previous_elapsed))
        self.previous_elapsed=elapsed
        if not self.cfg.get('paused'):
            # Damp the bar display only; the value reports actual simulated tension.
            tau=.37
            self.bar_tension+=(current.tension_percent-self.bar_tension)*(1-math.exp(-dt/tau))
        last=self.sample
        self.sample=current
        if self.window.isVisible():
            if self.cfg.get('rolling_crt') and not self.cfg.get('reduced_motion'):
                self.window.update(self.window.rect_scaled(75,281,639,675))
            # Partial dirty-area updates; QPainter clips the static shell image.
            if (round(last.breath_amplitude*27)!=round(current.breath_amplitude*27) or
                int(last.abdomen_progress*24)!=int(current.abdomen_progress*24) or
                int(last.tail_progress*24)!=int(current.tail_progress*24) or
                int(last.finger_progress*16)!=int(current.finger_progress*16)):
                self.window.update(self.window.rect_scaled(67,295,646,654))
            if (last.smoothed_bpm!=current.smoothed_bpm or
                round(last.breath_duration,1)!=round(current.breath_duration,1) or
                last.phase_thumbnail!=current.phase_thumbnail):
                self.window.update(self.window.rect_scaled(960,978,118,39))
                self.window.update(self.window.rect_scaled(985,549,97,50))
                self.window.update(self.window.rect_scaled(86,1019,933,176))
            if last.tension_percent!=current.tension_percent or abs(self.bar_tension-current.tension_percent)>.12:
                self.window.update(self.window.rect_scaled(767,688,310,102))
            if not self.cfg.get('reduced_motion'):
                self.window.update(self.window.rect_scaled(768,598,293,73))
    def _tray_activation(self,reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,QSystemTrayIcon.ActivationReason.DoubleClick):self.show()
    def can_recover(self):
        return bool(self.tray.isVisible())
    def save_position(self):
        if self.window._position_ready:
            self.cfg.set('x',self.window.x());self.cfg.set('y',self.window.y())
    def show(self):
        if self.cfg.get('click_through') and not self.can_recover():return
        self.window.clamp_to_screen()
        self.window.show()
        self.window.raise_()
        self.cfg.set('visible',True)
    def hide(self):
        if not self.can_recover():return
        self.window.hide();self.cfg.set('visible',False)
    def toggle_paused(self):
        n=not self.cfg.get('paused')
        self.cfg.set('paused',n)
        self.clock.pause(time.monotonic()) if n else self.clock.resume(time.monotonic())
        self.window.update()
        self._tray_menu=self._build_menu(tray=True)
        self.tray.setContextMenu(self._tray_menu)
    def set_flag(self,name,value):
        if name=='click_through' and value and not self.can_recover():return
        self.cfg.set(name,bool(value))
        if name=='reduced_motion' and value:
            self.sample=self.biology.at(0.)
            self.bar_tension=72.
        if name in ('click_through','always_on_top'):self.window.apply_flags()
        self.window.update()
        self._tray_menu=self._build_menu(tray=True)
        self.tray.setContextMenu(self._tray_menu)
    def _action(self,menu,title,fn=None,checked=None,enabled=True):
        a=QAction(title,menu)
        if checked is not None:
            a.setCheckable(True);a.setChecked(bool(checked))
        a.setEnabled(enabled)
        if fn:a.triggered.connect(lambda _checked=False,fn=fn:fn())
        menu.addAction(a)
        return a
    def _options(self,menu,label,choices,current,callback):
        sub=menu.addMenu(label)
        group=QActionGroup(sub);group.setExclusive(True)
        for value,text in choices:
            a=QAction(text,sub);a.setCheckable(True);a.setChecked(value==current)
            group.addAction(a)
            a.triggered.connect(lambda _checked=False,v=value:callback(v))
            sub.addAction(a)
        return sub
    def _set_option(self,key,value):
        self.cfg.set(key,value)
        if key=='size':self.window.resize_preset()
        if key=='display_style':self.assets.ensure_mode(value)
        self.window.update()
        self._tray_menu=self._build_menu(tray=True)
        self.tray.setContextMenu(self._tray_menu)
    def _build_menu(self,tray=False):
        menu=QMenu(self.window)
        accent,bg,fg=THEMES[self.cfg.get('theme')]
        menu.setStyleSheet('QMenu { background:'+bg+'; color:'+fg+'; border: 1px solid '+accent+';'
                           ' font: 12px Consolas; padding:4px; }'
                           'QMenu::item{padding:7px 24px;}'
                           'QMenu::item:selected{background:'+accent+';color:#071009;}'
                           'QMenu::separator{height:1px;background:#334236;margin:4px 8px;}')
        if tray:self._action(menu,'Show SPECIMEN.SYS',self.show)
        if not tray:
            anim=menu.addMenu('Animation')
            self._action(anim,'Resume' if self.cfg.get('paused') else 'Pause',self.toggle_paused)
            self._options(anim,'Intensity',[(x,x.title()) for x in motion.INTENSITIES],
                          self.cfg.get('intensity'),lambda v:self._set_option('intensity',v))
            self._action(anim,'Reduced motion',lambda:self.set_flag('reduced_motion',not self.cfg.get('reduced_motion')),
                         checked=self.cfg.get('reduced_motion'))
            display=menu.addMenu('Display')
            self._action(display,'Rolling CRT refresh',lambda:self.set_flag('rolling_crt',not self.cfg.get('rolling_crt')),checked=self.cfg.get('rolling_crt'))
            self._options(display,'Widget size',[(k,k.title()) for k in motion.SIZES],
                          self.cfg.get('size'),lambda v:self._set_option('size',v))
            self._options(display,'Display style',
                          [('detailed','Detailed'),('classic','Classic v1.0')],
                          self.cfg.get('display_style'),lambda v:self._set_option('display_style',v))
            for attr,text in [('always_on_top','Always on top'),('lock_position','Lock position'),
                              ('click_through','Click-through')]:
                self._action(display,text,lambda a=attr:self.set_flag(a,not self.cfg.get(a)),
                             checked=self.cfg.get(attr),enabled=(attr!='click_through' or self.can_recover()))
            prefs=menu.addMenu('Preferences')
            self._options(prefs,'Theme (menus only)',[(k,k.title()) for k in THEMES],
                          self.cfg.get('theme'),lambda v:self._set_option('theme',v))
            if os.name=='nt':
                self._action(prefs,'Start with Windows',self._toggle_startup,checked=self._startup_enabled())
            self._action(prefs,'Show splash screen',
                         lambda:self.set_flag('splash_enabled',not self.cfg.get('splash_enabled')),
                         checked=self.cfg.get('splash_enabled'))
            self._action(prefs,'Reset window position',self.reset_position)
            menu.addSeparator()
        else:
            self._action(menu,'Resume' if self.cfg.get('paused') else 'Pause',self.toggle_paused)
            self._action(menu,'Disable click-through',lambda:self.set_flag('click_through',False),
                         enabled=self.cfg.get('click_through'))
            self._action(menu,'Reset window position',self.reset_position)
            menu.addSeparator()
        self._action(menu,'Hide widget',self.hide,enabled=self.can_recover())
        self._action(menu,'About SPECIMEN.SYS',self.about)
        self._action(menu,'Exit',self.quit)
        return menu
    def show_menu(self,position):
        menu=self._build_menu()
        menu.exec(position)
    def reset_position(self):
        self.cfg.set('x',-99999);self.cfg.set('y',-99999)
        self.window.restore_location()
        self.save_position();self.show()
    def about(self):
        if self._popup is None:
            self._popup=EquipmentPlate('about',self.cfg.get('theme'))
        self._popup.theme=self.cfg.get('theme')
        self._popup.show()
        self._popup.raise_()
    def _run_command(self):
        exe=Path(sys.executable)
        if not getattr(sys,'frozen',False):
            pythonw=exe.with_name('pythonw.exe')
            if pythonw.exists():exe=pythonw
            script=Path(__file__).resolve().parents[1]/'specimen.pyw'
            return subprocess.list2cmdline([str(exe),str(script)])
        return subprocess.list2cmdline([str(exe)])
    def _startup_enabled(self):
        if os.name!='nt':return False
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                 r'Software\Microsoft\Windows\CurrentVersion\Run') as k:
                return winreg.QueryValueEx(k,'SpecimenSys')[0]==self._run_command()
        except OSError:return False
    def _toggle_startup(self):
        if os.name!='nt':return
        import winreg
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                 r'Software\Microsoft\Windows\CurrentVersion\Run') as k:
                if self._startup_enabled():
                    winreg.DeleteValue(k,'SpecimenSys')
                else:winreg.SetValueEx(k,'SpecimenSys',0,winreg.REG_SZ,self._run_command())
        except OSError as e:
            QMessageBox.warning(self.window,'Startup preference',str(e))
    def quit(self):
        self.cfg.set('visible',self.window.isVisible())
        self.save_position()
        self.tray.hide()
        self.app.quit()

def _logging():
    # Private diagnostics are opt-in. Normal startup writes no persistent log.
    # A user can explicitly enable it for local troubleshooting only.
    if os.environ.get('SPECIMEN_DEBUG_LOGS') != '1':
        logging.basicConfig(level=logging.CRITICAL)
        return
    path=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) /'SpecimenSys'/'logs'
    try:
        path.mkdir(parents=True,exist_ok=True)
        logging.basicConfig(filename=path/'specimen.log',level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s')
    except OSError:logging.basicConfig(level=logging.WARNING)

def main():
    _logging()
    try:
        app=QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName('SPECIMEN.SYS')
        ctl=Controller(app)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logging.warning('No system tray; click-through and hide are disabled.')
        return app.exec()
    except Exception:
        logging.exception('Fatal SPECIMEN.SYS startup error')
        raise

if __name__=='__main__':raise SystemExit(main())
