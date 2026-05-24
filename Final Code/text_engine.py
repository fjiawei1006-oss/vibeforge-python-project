from models import Melody, Note, Scale, Chord


class TextEngine:
    """
    Converts text to music using mapping rules.
    """

    def __init__(self, root: str = "C"):
        self.root = root

    def _detect_mood(self, text: str) -> dict:
        t = text.lower()
        if any(k in t for k in ["angry", "fire", "storm"]):
            return {"mood": "intense", "scale_mode": "blues", "bpm": 140}
        if any(k in t for k in ["sad", "dark", "rain", "cry"]):
            return {"mood": "sad", "scale_mode": "minor", "bpm": 80}
        if any(k in t for k in ["dream", "float", "wonder"]):
            return {"mood": "dreamy", "scale_mode": "pentatonic", "bpm": 95}
        if any(k in t for k in ["happy", "love", "sun", "bright"]):
            return {"mood": "happy", "scale_mode": "major", "bpm": 110}
        return {"mood": "neutral", "scale_mode": "major", "bpm": 100}

    def _word_length_at(self, text: str, idx: int) -> int:
        if not text[idx].isalpha():
            return 0
        left = idx
        right = idx
        while left - 1 >= 0 and text[left - 1].isalpha():
            left -= 1
        while right + 1 < len(text) and text[right + 1].isalpha():
            right += 1
        return right - left + 1

    def _duration_by_word_length(self, length: int) -> float:
        if length <= 2:
            return 0.5
        if length <= 5:
            return 1.0
        return 1.5

    def _char_to_pitch(self, char: str, scale: Scale, default_octave: int) -> str:
        if char == " ":
            return "REST"

        degree = (ord(char) % len(scale)) + 1
        vowels = "aeiouAEIOU"

        if char in vowels:
            chord_degrees = [1, 3, 5]
            degree = chord_degrees[ord(char) % len(chord_degrees)]
            note_name = scale.get_note(degree)
        else:
            non_chord = [d for d in range(1, len(scale) + 1) if d not in [1, 3, 5]]
            if not non_chord:
                non_chord = list(range(1, len(scale) + 1))
            degree = non_chord[ord(char) % len(non_chord)]
            note_name = scale.get_note(degree)

        octave = 5 if char.isupper() else default_octave
        return f"{note_name}{octave}"

    def _generate_chords(self, scale: Scale, num_bars: int):
        # Very simple diatonic progression templates
        if scale.mode in ("major", "pentatonic", "dorian"):
            progression = [(1, "major"), (4, "major"), (5, "dom7"), (6, "minor")]
        else:
            progression = [(1, "minor"), (4, "minor"), (5, "dom7"), (6, "major")]

        chords = []
        for i in range(max(1, num_bars)):
            deg, q = progression[i % len(progression)]
            root = scale.get_note(deg)
            chords.append(Chord(root, q))
        return chords

    def generate(self, text: str):
        mood_info = self._detect_mood(text)
        scale = Scale(self.root, mood_info["scale_mode"])
        melody = Melody(
            title="Text Vibe",
            key=f"{scale.root} {scale.mode}",
            bpm=mood_info["bpm"],
            time_signature=(4, 4),
        )

        for i, ch in enumerate(text):
            if ch == " ":
                melody.add_note(Note("REST", duration=0.5, velocity=0))
                continue

            if ch == ",":
                melody.add_note(Note("REST", duration=0.5, velocity=0))
                continue

            if ch == ".":
                melody.add_note(Note("REST", duration=1.0, velocity=0))
                continue

            if ch == "!":
                if melody.notes:
                    melody.notes[-1].velocity = 127
                continue

            if ch == "?":
                # Raise last non-rest note by a 4th (5 semitones)
                for j in range(len(melody.notes) - 1, -1, -1):
                    if not melody.notes[j].is_rest():
                        melody.notes[j] = melody.notes[j].transpose(5)
                        break
                continue

            if not ch.isprintable():
                continue

            wl = self._word_length_at(text, i)
            duration = self._duration_by_word_length(wl if wl > 0 else 3)

            pitch = self._char_to_pitch(ch, scale, default_octave=4)
            velocity = 90 if ch.isupper() else 75
            melody.add_note(Note(pitch, duration=duration, velocity=velocity))

        total = melody.total_beats()
        bars = int(total // 4) + (1 if total % 4 > 0 else 0)
        chords = self._generate_chords(scale, num_bars=max(1, bars))
        return melody, chords, mood_info["mood"]
