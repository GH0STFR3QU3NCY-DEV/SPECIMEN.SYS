"""Pure-Pillow reference compositor for acceptance tests and previews.
The Windows runtime uses the same prebaked sprites, boxes, and motion.sample,
but draws them with cached QImages rather than decoding PNGs every tick.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageDraw
from . import motion
import json
import math

ASSETS=Path(__file__).parent/'assets'
MANIFEST=json.loads((ASSETS/'layer_manifest.json').read_text())
BOXES={k:tuple(v) for k,v in MANIFEST['boxes'].items()}
THUMBS=[(88,1023,314,1190),(327,1023,548,1190),(560,1023,778,1190),(792,1023,1014,1190)]

class Compositor:
    def __init__(self,display_style='detailed'):
        if display_style not in ('detailed','classic'):raise ValueError('Invalid display style')
        self.display_style=display_style
        self.base=Image.open(ASSETS/f'{display_style}_static_rgba.png').convert('RGBA')
        self.counts=MANIFEST['counts']
        self.cache={}
    def _image(self,layer,index):
        key=(layer,index)
        if key not in self.cache:
            self.cache[key]=Image.open(ASSETS/('layers' if self.display_style=='detailed' else 'layers_classic')/layer/f'{index:02d}.png').convert('RGBA')
        return self.cache[key]
    def _readout(self,key,value):
        safe=value.replace(' ','_').replace('%','pct').replace('.','p')
        path=ASSETS/'readouts'/f'{key}_{safe}.png'
        if path.exists():return Image.open(path).convert('RGBA')
        return None
    def compose(self,sample:motion.Sample,intensity='standard',telemetry=True,rolling_crt=True):
        out=self.base.copy()
        power=motion.INTENSITIES[intensity]
        # Anatomical layers: each patch is an independently authored soft-masked
        # displacement with a zero-displacement edge. Layer order is intentional.
        activities={'host':sample.breath_amplitude,
                    'sacs':sample.breath_amplitude,
                    'abdomen':sample.abdomen_progress,
                    'fingers':sample.finger_progress,
                    'tail':sample.tail_progress}
        for name,value in activities.items():
            if value<0:continue
            v=value*power if name in ('host','sacs') else value
            v=min(v,1.)
            idx=min(self.counts[name]-1,max(0,round(v*(self.counts[name]-1))))
            if idx==0 and name in ('abdomen','fingers','tail'):continue
            out.alpha_composite(self._image(name,idx),BOXES[name][:2])
        if telemetry:
            pairs=[('resp',f'{sample.smoothed_bpm} BPM',(992,553)),
                   ('tail',f'{sample.tension_percent}%',(1009,695)),
                   ('cycle',f'{sample.breath_duration:.1f} S',(961,981))]
            for name,value,xy in pairs:
                im=self._readout(name,value)
                if im:out.alpha_composite(im,xy)
            d=ImageDraw.Draw(out,'RGBA')
            # Bar: add only the originally unlit 3 slots at rising tension.
            slots=max(0,min(3,round((sample.tension_percent-72)*3/12)))
            for i in range(slots):
                x=1015+i*14.4
                d.rectangle((round(x),768,round(x+10),784),fill=(137,221,121,215))
            # Stationary waveform; small moving phosphor cursor.
            x=round(777+sample.breath_phase*272)
            # Follow the reference waveform geometry (approx 3 cycles across 272 px).
            y=round(635+16*math.sin(2*math.pi*(x-777)*3/272 + .04))
            d.rectangle((x-2,y-2,x+2,y+2),fill=(192,255,176,180))
            x0,y0,x1,y1=((97,1033,305,1182),(336,1033,541,1182),
                           (570,1033,771,1182),(801,1033,1007,1182))[sample.phase_thumbnail]
            overlay=Image.open(ASSETS/'thumbnails'/f'active_{sample.phase_thumbnail}.png').convert('RGBA')
            out.alpha_composite(overlay,(x0,y0))
        if rolling_crt:
            ys=282+int((sample.elapsed*52.0)%671)
            overlay=Image.new('RGBA',out.size,(0,0,0,0))
            line=ImageDraw.Draw(overlay)
            line.rectangle((77,ys,702,ys+1),fill=(170,221,165,24))
            line.rectangle((77,ys+2,702,ys+10),fill=(5,22,12,11))
            out.alpha_composite(overlay)
        return out
