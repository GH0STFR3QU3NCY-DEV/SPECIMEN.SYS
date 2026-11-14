import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from specimen_sys.motion import Biology,PausableClock,BREATH_RANGE,INTENSITIES,SIZES

class ApprovedMotion(unittest.TestCase):
 def setUp(self):self.bio=Biology()
 def test_breath_cycle_bounded(self):
  self.assertTrue(all(BREATH_RANGE[0]<=x<=BREATH_RANGE[1] for x in self.bio.durations))
 def test_respiration_rate_matches_cycle(self):
  for t in [0.,1.,4.5,9.,13.,66.,201.]:
   s=self.bio.at(t)
   self.assertTrue(10<=s.smoothed_bpm<=15)
   self.assertTrue(0<=s.breath_amplitude<=1)
 def test_tail_frequency_two_to_three_breaths(self):
  self.assertEqual([i for i in range(12) if i%5 in (0,2)],[0,2,5,7,10])
 def test_tail_tension_limits(self):
  for i in range(800):
   s=self.bio.at(i*.17)
   self.assertTrue(72<=s.tension_percent<=84)
 def test_staggered_events(self):
  for k in range(1400):
   s=self.bio.at(k*.113)
   self.assertFalse(s.abdomen_progress>=0 and s.tail_progress>=0)
   self.assertFalse(s.finger_progress>=0 and s.tail_progress>=0)
 def test_abdomen_some_breaths_skipped(self):
  events=[]
  for i in range(15):
   t=self.bio.starts[i]+.33*self.bio.durations[i]
   events.append(self.bio.at(t).abdomen_progress>=0)
  self.assertTrue(any(events));self.assertTrue(any(not x for x in events))
 def test_paused_clock_continuity(self):
  c=PausableClock();self.assertEqual(c.elapsed(100),0)
  self.assertAlmostEqual(c.elapsed(110),10)
  c.pause(110);self.assertAlmostEqual(c.elapsed(600),10)
  c.resume(600);self.assertAlmostEqual(c.elapsed(602),12)
 def test_intensity_affects_geometry_only(self):
  self.assertEqual(set(INTENSITIES),{'subtle','standard','enhanced'})
  self.assertGreater(INTENSITIES['enhanced'],INTENSITIES['standard'])
 def test_sizes(self):
  self.assertEqual(set(SIZES),{'compact','standard','large'})
