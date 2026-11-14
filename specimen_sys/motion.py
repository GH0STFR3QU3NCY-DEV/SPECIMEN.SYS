"""Approved v1.0 motion contract, independent of Qt and rendering.

A2/B2, C1/D1, E3-B/P1/F2/I3, G1/H2/J2/K2,
T2/M2/N1/O2, R2. These numbers are authored animation parameters,
not biomedical measurements of a fictional species.
"""
from __future__ import annotations
from dataclasses import dataclass
from bisect import bisect_right
import random
import math

BREATH_RANGE=(4.6,5.4)
TENSION_REST=72
TENSION_PEAK=84
INTENSITIES={'subtle':0.60,'standard':1.0,'enhanced':1.25}
SIZES={'compact':0.4,'standard':0.5,'large':0.625}


def ease(x:float)->float:
    v=max(0.,min(1.,x))
    return v*v*(3-2*v)


def event_window(phase:float,start:float,end:float)->float:
    if phase < start or phase > end: return -1.0
    return (phase-start)/(end-start)


def envelope(progress:float)->float:
    if progress < 0: return 0.
    return max(0.,math.sin(math.pi*progress))


@dataclass(frozen=True)
class Sample:
    elapsed:float
    breath_number:int
    breath_duration:float
    breath_phase:float
    breath_amplitude:float
    abdomen_progress:float
    finger_progress:float
    tail_progress:float
    tail_amplitude:float
    tension_percent:int
    smoothed_bpm:int
    phase_thumbnail:int

class Biology:
    def __init__(self,seed=6401979):
        self.random=random.Random(seed)
        self.starts=[0.0]
        self.durations=[]
        self._extend(100)
    def _extend(self,n):
        for _ in range(n):
            # Stable, bounded variability avoids mechanically identical cycles.
            d=round(self.random.uniform(*BREATH_RANGE),3)
            self.durations.append(d)
            self.starts.append(self.starts[-1]+d)
    def at(self,elapsed:float)->Sample:
        t=max(0.,float(elapsed))
        while t>=self.starts[-1]:
            self._extend(100)
        idx=bisect_right(self.starts,t)-1
        d=self.durations[idx]
        p=(t-self.starts[idx])/d
        if p < .37:
            amp=ease(p/.37)
            thumb=1 if p<.26 else 2
        elif p < .90:
            amp=1.-ease((p-.37)/.53)
            thumb=2 if p<.44 else 3
        else:
            amp=0.0
            thumb=0
        # F2: all but one of five breaths; interval is mapped to inspiration.
        ab=event_window(p,.12,.55) if idx%5!=2 else -1.
        # N1: 2,3,2,3 breath spacing. Tail occurs in the later half of breath.
        tail=event_window(p,.59,.96) if idx%5 in (0,2) else -1.
        # J2: rare isometric tension, never coincident with tail N1 event.
        finger=event_window(p,.68,.91) if idx%8==4 and idx%5 not in (0,2) else -1.
        tailamp=envelope(tail)
        average=self.durations[max(0,idx-3):idx+1]
        bpm=round(60.0/(sum(average)/len(average)))
        return Sample(t,idx,d,p,amp,ab,finger,tail,tailamp,
                      round(TENSION_REST+(TENSION_PEAK-TENSION_REST)*tailamp),bpm,thumb)


class PausableClock:
    def __init__(self):
        self.started=None
        self.paused_at=None
        self.paused_total=0.
    def elapsed(self,now):
        if self.started is None:self.started=now
        point=self.paused_at if self.paused_at is not None else now
        return max(0.,point-self.started-self.paused_total)
    def pause(self,now):
        self.elapsed(now)
        if self.paused_at is None:self.paused_at=now
    def resume(self,now):
        if self.paused_at is not None:
            self.paused_total+=max(0.,now-self.paused_at)
            self.paused_at=None
    def toggle(self,now):
        if self.paused_at is None:self.pause(now)
        else:self.resume(now)
