from typing import List, Tuple


def _normalize_note_name(name: str) -> str:
    """Convert flats to equivalent sharps, keep sharps as-is."""
    flats = {
        "Db": "C#",
        "Eb": "D#",
        "Gb": "F#",
        "Ab": "G#",
        "Bb": "A#",
        "Cb": "B",
        "Fb": "E",
    }
    return flats.get(name, name)


class Note:
    """
    A single musical note.
    """

    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self, pitch: str, duration: float = 1.0, velocity: int = 80):
        self.pitch = pitch.strip() if isinstance(pitch, str) else "REST"
        self.duration = float(duration)
        self.velocity = max(1, min(127, int(velocity)))

    def is_rest(self) -> bool:
        return self.pitch.upper() == "REST"

    def midi_number(self) -> int:
        """
        Convert pitch to MIDI number. C4 = 60.
        REST returns -1.
        """
        if self.is_rest():
            return -1

        # Parse note name + octave
        # Valid examples: C4, D#5, Bb3
        if len(self.pitch) < 2:
            raise ValueError(f"Invalid pitch format: {self.pitch}")

        if self.pitch[1] in ("#", "b"):
            note_name = self.pitch[:2]
            octave_str = self.pitch[2:]
        else:
            note_name = self.pitch[:1]
            octave_str = self.pitch[1:]

        note_name = _normalize_note_name(note_name)
        if note_name not in self.NOTE_NAMES:
            raise ValueError(f"Invalid note name: {note_name}")

        try:
            octave = int(octave_str)
        except ValueError as exc:
            raise ValueError(f"Invalid octave in pitch: {self.pitch}") from exc

        return self.NOTE_NAMES.index(note_name) + (octave + 1) * 12

    @classmethod
    def from_midi(cls, midi: int, duration: float = 1.0, velocity: int = 80):
        if midi < 0:
            return cls("REST", duration, velocity)
        note_name = cls.NOTE_NAMES[midi % 12]
        octave = midi // 12 - 1
        return cls(f"{note_name}{octave}", duration, velocity)

    def transpose(self, semitones: int):
        if self.is_rest():
            return Note("REST", self.duration, self.velocity)
        new_midi = self.midi_number() + semitones
        return Note.from_midi(new_midi, self.duration, self.velocity)

    def to_dict(self) -> dict:
        return {
            "pitch": self.pitch,
            "duration": self.duration,
            "velocity": self.velocity,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            pitch=data.get("pitch", "REST"),
            duration=data.get("duration", 1.0),
            velocity=data.get("velocity", 80),
        )

    def __str__(self):
        symbol_map = {
            0.5: "♪",
            1.0: "♩",
            1.5: "♩.",
            2.0: "𝅗𝅥",
        }
        symbol = symbol_map.get(self.duration, "♩")
        return f"{'-' if self.is_rest() else self.pitch}({symbol})"

    def __eq__(self, other):
        return (
            isinstance(other, Note)
            and self.pitch == other.pitch
            and self.duration == other.duration
            and self.velocity == other.velocity
        )


class Scale:
    """
    A musical scale.
    """

    INTERVALS = {
        "major": [2, 2, 1, 2, 2, 2, 1],
        "minor": [2, 1, 2, 2, 1, 2, 2],
        "pentatonic": [2, 2, 3, 2, 3],
        "blues": [3, 2, 1, 1, 3, 2],
        "dorian": [2, 1, 2, 2, 2, 1, 2],
    }
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self, root: str = "C", mode: str = "major"):
        self.root = _normalize_note_name(root)
        self.mode = mode.lower()
        if self.mode not in self.INTERVALS:
            self.mode = "major"
        if self.root not in self.NOTE_NAMES:
            self.root = "C"
        self.notes = self._build_notes()

    def _build_notes(self) -> List[str]:
        intervals = self.INTERVALS[self.mode]
        idx = self.NOTE_NAMES.index(self.root)
        scale_notes = [self.root]
        for step in intervals[:-1]:  # last step closes octave
            idx = (idx + step) % 12
            scale_notes.append(self.NOTE_NAMES[idx])
        return scale_notes

    def get_note(self, degree: int) -> str:
        if degree <= 0:
            degree = 1
        return self.notes[(degree - 1) % len(self.notes)]

    def contains(self, note_name: str) -> bool:
        return _normalize_note_name(note_name) in self.notes

    def __len__(self):
        return len(self.notes)

    def __str__(self):
        return f"{self.root} {self.mode}: {' '.join(self.notes)}"


class Chord:
    """
    A chord.
    """

    PATTERNS = {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        "dom7": [0, 4, 7, 10],
        "min7": [0, 3, 7, 10],
    }
    NOTE_NAMES = Scale.NOTE_NAMES

    def __init__(self, root: str, quality: str = "major"):
        self.root = _normalize_note_name(root)
        self.quality = quality
        if self.quality not in self.PATTERNS:
            self.quality = "major"
        self.notes = self._build_notes()

    def _build_notes(self) -> List[str]:
        if self.root not in self.NOTE_NAMES:
            return []
        root_idx = self.NOTE_NAMES.index(self.root)
        return [self.NOTE_NAMES[(root_idx + i) % 12] for i in self.PATTERNS[self.quality]]

    def to_dict(self) -> dict:
        return {"root": self.root, "quality": self.quality, "notes": self.notes}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(root=data.get("root", "C"), quality=data.get("quality", "major"))

    def __str__(self):
        if self.quality == "major":
            return f"{self.root}"
        if self.quality == "minor":
            return f"{self.root}m"
        if self.quality == "dom7":
            return f"{self.root}7"
        if self.quality == "min7":
            return f"{self.root}m7"
        return f"{self.root}"


class Melody:
    """
    A sequence of notes.
    """

    def __init__(
        self,
        notes: List[Note] = None,
        title: str = "Untitled",
        key: str = "C major",
        bpm: int = 100,
        time_signature: Tuple[int, int] = (4, 4),
    ):
        self.notes = notes[:] if notes else []
        self.title = title
        self.key = key
        self.bpm = int(bpm)
        self.time_signature = tuple(time_signature)

    def add_note(self, note: Note):
        if isinstance(note, Note):
            self.notes.append(note)

    def transpose(self, semitones: int):
        transposed = [n.transpose(semitones) for n in self.notes]
        return Melody(
            notes=transposed,
            title=f"{self.title} (transposed)",
            key=self.key,
            bpm=self.bpm,
            time_signature=self.time_signature,
        )

    def retrograde(self):
        # RECURSION
        def _reverse_recursive(items):
            if len(items) <= 1:
                return items[:]
            return [items[-1]] + _reverse_recursive(items[:-1])

        reversed_notes = _reverse_recursive(self.notes)
        return Melody(
            notes=reversed_notes,
            title=f"{self.title} (retrograde)",
            key=self.key,
            bpm=self.bpm,
            time_signature=self.time_signature,
        )

    def get_contour(self) -> List[str]:
        contour = []
        for i in range(1, len(self.notes)):
            a = self.notes[i - 1]
            b = self.notes[i]
            if a.is_rest() or b.is_rest():
                contour.append("→")
                continue
            ma = a.midi_number()
            mb = b.midi_number()
            if mb > ma:
                contour.append("↑")
            elif mb < ma:
                contour.append("↓")
            else:
                contour.append("→")
        return contour

    def total_beats(self) -> float:
        return sum(n.duration for n in self.notes)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "key": self.key,
            "bpm": self.bpm,
            "time_signature": list(self.time_signature),
            "notes": [n.to_dict() for n in self.notes],
        }

    @classmethod
    def from_dict(cls, data: dict):
        notes = [Note.from_dict(n) for n in data.get("notes", [])]
        ts = data.get("time_signature", [4, 4])
        if isinstance(ts, list):
            ts = tuple(ts)
        return cls(
            notes=notes,
            title=data.get("title", "Untitled"),
            key=data.get("key", "C major"),
            bpm=data.get("bpm", 100),
            time_signature=ts,
        )

    def __str__(self):
        return " ".join(n.pitch if not n.is_rest() else "-" for n in self.notes)

    def __len__(self):
        return len(self.notes)

    def __add__(self, other):
        if not isinstance(other, Melody):
            raise TypeError("Can only concatenate Melody with Melody")
        return Melody(
            notes=self.notes + other.notes,
            title=f"{self.title} + {other.title}",
            key=self.key,
            bpm=self.bpm,
            time_signature=self.time_signature,
        )
