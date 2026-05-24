# scene_engine.py
import json
import os
import random

from models import Melody, Note, Scale, Chord


class SceneEngine:
    """
    Generates music based on scene type and modifiers.
    """

    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "scene_presets.json")
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def list_scenes(self):
        return sorted(list(self.data.get("scenes", {}).keys()))

    def list_modifiers(self):
        return sorted(list(self.data.get("modifiers", {}).keys()))

    def _clamp(self, value, lo, hi):
        return max(lo, min(hi, value))

    def _build_params(self, scene: str, modifiers=None, intensity: int = 50):
        if modifiers is None:
            modifiers = []

        scenes = self.data.get("scenes", {})
        mods = self.data.get("modifiers", {})

        if scene not in scenes:
            raise ValueError(f"Unknown scene: {scene}")

        params = dict(scenes[scene])
        params["scene"] = scene
        params["modifiers_used"] = []

        for m in modifiers:
            if m not in mods:
                continue
            params["modifiers_used"].append(m)
            for k, v in mods[m].items():
                if k in ["velocity_adjust", "bpm_adjust", "octave_adjust"]:
                    params[k] = params.get(k, 0) + v
                else:
                    params[k] = v

        intensity = self._clamp(intensity, 1, 100)
        params["intensity"] = intensity

        bpm_lo, bpm_hi = params.get("bpm_range", [90, 120])
        bpm = int(bpm_lo + (bpm_hi - bpm_lo) * (intensity / 100.0))
        bpm += params.get("bpm_adjust", 0)
        params["bpm"] = self._clamp(bpm, 40, 220)

        vel_lo, vel_hi = params.get("velocity_range", [60, 100])
        vel_lo += params.get("velocity_adjust", 0)
        vel_hi += params.get("velocity_adjust", 0)
        params["velocity_range"] = [self._clamp(vel_lo, 1, 127), self._clamp(vel_hi, 1, 127)]

        return params

    def _recursive_arch(self, notes: list, peak_index: int) -> list:
        # RECURSION
        if len(notes) <= 1:
            return notes[:]

        if peak_index > 0:
            return [notes[0]] + self._recursive_arch(notes[1:], peak_index - 1)
        return [notes[-1]] + self._recursive_arch(notes[:-1], peak_index)

    def _apply_contour(self, pitches: list, contour: str) -> list:
        if not pitches:
            return []

        if contour == "ascending":
            return sorted(pitches)

        if contour == "descending":
            return sorted(pitches, reverse=True)

        if contour == "zigzag":
            s = sorted(pitches)
            out = []
            i, j = 0, len(s) - 1
            toggle = True
            while i <= j:
                if toggle:
                    out.append(s[i])
                    i += 1
                else:
                    out.append(s[j])
                    j -= 1
                toggle = not toggle
            return out

        if contour == "arch":
            s = sorted(pitches)
            peak = len(s) // 2
            return self._recursive_arch(s, peak)

        return pitches

    def _generate_melody(self, params: dict, scale: Scale, num_notes: int) -> Melody:
        density = params.get("note_density", "medium")
        if density == "low":
            duration_choices = [1.0, 1.5, 2.0]
        elif density == "high":
            duration_choices = [0.5, 0.5, 1.0]
        else:
            duration_choices = [0.5, 1.0, 1.0, 1.5]

        vel_lo, vel_hi = params.get("velocity_range", [60, 100])
        octave_adjust = params.get("octave_adjust", 0)
        base_octave = 4 + octave_adjust
        base_octave = max(2, min(6, base_octave))

        # generate degree stream
        degrees = [random.randint(1, len(scale))]
        intervals = params.get("preferred_intervals", [2, 3, 4])
        for _ in range(num_notes - 1):
            step = random.choice(intervals)
            direction = random.choice([-1, 1])
            next_deg = degrees[-1] + direction * (step % max(1, len(scale)))
            while next_deg < 1:
                next_deg += len(scale)
            while next_deg > len(scale):
                next_deg -= len(scale)
            degrees.append(next_deg)

        degrees = self._apply_contour(degrees, params.get("contour", "ascending"))

        notes = []
        for d in degrees:
            note_name = scale.get_note(d)
            duration = random.choice(duration_choices)
            velocity = random.randint(vel_lo, vel_hi)
            notes.append(Note(f"{note_name}{base_octave}", duration=duration, velocity=velocity))

        return Melody(
            notes=notes,
            title=f"Scene: {params.get('scene', 'unknown')}",
            key=f"{scale.root} {scale.mode}",
            bpm=params.get("bpm", 100),
            time_signature=(4, 4),
        )

    def _generate_chords(self, params: dict, scale: Scale, num_bars: int):
        mode = scale.mode
        if mode in ("minor", "blues"):
            pattern = [(1, "minor"), (6, "major"), (7, "dom7"), (4, "minor")]
        else:
            pattern = [(1, "major"), (5, "dom7"), (6, "minor"), (4, "major")]

        chords = []
        for i in range(max(1, num_bars)):
            deg, quality = pattern[i % len(pattern)]
            chords.append(Chord(scale.get_note(deg), quality))
        return chords

    def generate(self, scene: str, modifiers=None, intensity: int = 50):
        if modifiers is None:
            modifiers = []
        params = self._build_params(scene, modifiers, intensity)
        scale = Scale("C", params.get("scale_mode", "major"))

        density = params.get("note_density", "medium")
        if density == "low":
            num_notes = 8
        elif density == "high":
            num_notes = 16
        else:
            num_notes = 12

        melody = self._generate_melody(params, scale, num_notes)
        bars = int(melody.total_beats() // 4) + (1 if melody.total_beats() % 4 > 0 else 0)
        chords = self._generate_chords(params, scale, bars)
        return melody, chords, params
