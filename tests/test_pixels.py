"""Viewport, alpha, simulation and shell-compositing regression tests."""
import sys,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from specimen_sys.compositor import Compositor,ASSETS,BOXES
from specimen_sys.motion import Biology

class PixelContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ASSETS/'layer_manifest.json').read_text())
    def test_boxes_within_specimen_window(self):
        for name,(x0,y0,x1,y1) in BOXES.items():
            with self.subTest(layer=name):
                self.assertTrue(25<=x0<x1<=805 and 260<=y0<y1<=990)
    def test_crop_edges_transparent_for_both_modes(self):
        for style in ['layers','layers_classic']:
            for name,n in self.manifest['counts'].items():
                for i in (0,n//2,n-1):
                    with Image.open(ASSETS/style/name/f'{i:02}.png') as image:
                        a=np.asarray(image.convert('RGBA'))[:,:,3]
                    with self.subTest(style=style,layer=name,frame=i):
                        self.assertFalse(a[0,:].any() or a[-1,:].any() or a[:,0].any() or a[:,-1].any())
    def test_biological_changes_are_confined_to_viewport(self):
        bio=Biology()
        for style in ['detailed','classic']:
            comp=Compositor(style)
            static=np.asarray(comp.base.convert('RGB'))
            for t in (0.8,1.9,3.7,6.7,11.7):
                dynamic=np.asarray(comp.compose(bio.at(t),telemetry=False,rolling_crt=False).convert('RGB'))
                changed=np.any(static!=dynamic,axis=2)
                self.assertEqual(int(changed[:280,:].sum()),0)
                self.assertEqual(int(changed[955:,:].sum()),0)
                self.assertEqual(int(changed[:,805:].sum()),0)
    def test_static_screens_are_identical_outside_viewport(self):
        a=np.asarray(Compositor('classic').base.convert('RGBA'))
        b=np.asarray(Compositor('detailed').base.convert('RGBA'))
        allowed=np.zeros(a.shape[:2],bool)
        x0,y0,x1,y1=self.manifest['specimen_viewport']
        allowed[y0:y1,x0:x1]=True
        changed=np.any(a!=b,axis=2)
        self.assertEqual(int((changed & ~allowed).sum()),0)
