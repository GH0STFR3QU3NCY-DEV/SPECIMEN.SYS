"""Pure-Python release contract; does not require a GUI at test time."""
import sys, unittest, json, ast
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from specimen_sys import motion
from specimen_sys.compositor import Compositor
from scripts.check_public import audit

class PublicReleaseTests(unittest.TestCase):
    def test_privacy_scan(self):self.assertEqual(audit(),[])
    def test_standalone_distribution_has_allowlisted_roots(self):
        # No companion applications, unpublished references, or local tooling.
        from scripts.check_public import ALLOWED_ROOT
        unexpected={p.name for p in ROOT.iterdir() if p.name not in ALLOWED_ROOT and p.name not in {'__pycache__','.pytest_cache','.git'}}
        self.assertEqual(unexpected,set())
    def test_only_public_source_images_are_distributed(self):
        folder=ROOT/'specimen_sys'/'assets'
        expected={'classic_static_rgba.png','detailed_static_rgba.png','layer_manifest.json',
                  'layers','layers_classic','readouts','thumbnails'}
        self.assertEqual({p.name for p in folder.iterdir()}, expected)
    def test_both_display_styles_have_transparent_shell(self):
        a=ROOT/'specimen_sys'/'assets'
        for style in ['detailed','classic']:
            with self.subTest(style=style):
                im=Image.open(a/f'{style}_static_rgba.png').convert('RGBA')
                self.assertEqual(im.size,(1122,1402))
                self.assertEqual(im.getpixel((0,0))[3],0)
                self.assertEqual(im.getpixel((320,390))[3],255)
    def test_two_styles_render_different_specimen_art(self):
        sample=motion.Biology().at(2.0)
        a=Compositor('detailed').compose(sample,rolling_crt=False)
        b=Compositor('classic').compose(sample,rolling_crt=False)
        self.assertNotEqual(a.crop((85,390,705,940)).tobytes(),b.crop((85,390,705,940)).tobytes())
    def test_240_sprite_files(self):
        a=ROOT/'specimen_sys'/'assets'
        m=json.loads((a/'layer_manifest.json').read_text())
        self.assertEqual(sum(m['counts'].values()),120)
        for style in ['layers','layers_classic']:
            self.assertEqual(sum(len(list((a/style/k).glob('*.png'))) for k in m['counts']),120)
    def test_movement_contract(self):
        bio=motion.Biology()
        samples=[bio.at(t/10) for t in range(0,800)]
        self.assertTrue(all(4.6<=s.breath_duration<=5.4 for s in samples))
        self.assertTrue(all(72<=s.tension_percent<=84 for s in samples))
        self.assertEqual(motion.SIZES,{'compact':0.4,'standard':0.5,'large':0.625})
    def test_icon_contains_native_tray_and_exe_sizes(self):
        with Image.open(ROOT/'branding'/'specimen.ico') as ico:
            self.assertTrue({(16,16),(32,32),(48,48),(256,256)}.issubset(ico.ico.sizes()))
        with Image.open(ROOT/'branding'/'specimen-icon-1024.png') as im:
            self.assertEqual(im.size,(1024,1024))
    def test_readme_assets_exist(self):
        for name in ['github-header.png','social-preview.png','classic-standard.png','detailed-standard.png','classic-animation.webp','detailed-animation.webp']:
            self.assertTrue((ROOT/'docs'/'images'/name).is_file(),name)
    def test_social_preview_under_one_mb(self):
        im=ROOT/'docs'/'images'/'social-preview.png'
        self.assertLess(im.stat().st_size,1000000)
        with Image.open(im) as pic:
            self.assertEqual(pic.size,(1280,640))
    def test_gui_source_features(self):
        text=(ROOT/'specimen_sys'/'app.py').read_text()
        ast.parse(text)
        self.assertIn('FramelessWindowHint',text)
        self.assertIn('QSystemTrayIcon',text)
        self.assertIn("QTimer.singleShot(2000,self._finish_splash)",text)
        self.assertIn("Display style",text)
        self.assertIn("EquipmentPlate",text)
        self.assertNotIn("StaticPanel",text)
        self.assertNotIn('QMessageBox.information(',text)
    def test_minimal_borderless_plates(self):
        source=(ROOT/'specimen_sys'/'plates.py').read_text()
        ast.parse(source)
        self.assertIn('Qt.WindowType.FramelessWindowHint',source)
        self.assertIn('Qt.WindowType.Tool',source)
        self.assertIn('Qt.WidgetAttribute.WA_TranslucentBackground',source)
        self.assertIn('620, 176',source)
        self.assertIn('420, 156',source)
        self.assertIn('"boot", "about"',source)
        self.assertFalse((ROOT/'branding'/'splash.png').exists())
        self.assertFalse((ROOT/'branding'/'about.png').exists())

    def test_release_workflow_installs_and_smoke_tests(self):
        text=(ROOT/'.github/workflows/release.yml').read_text()
        self.assertIn('run: |\n          python -m pip install -r requirements.txt',text)
        self.assertIn('python scripts/qt_smoke_test.py',text)

    def test_pngs_free_of_embedded_author_metadata(self):
        for p in ROOT.rglob('*.png'):
            with Image.open(p) as im:
                keys={k.lower() for k in im.info}
                self.assertFalse(keys.intersection({'exif','author','comment','description','software','usercomment','icc_profile'}),str(p))

if __name__=='__main__':unittest.main()
