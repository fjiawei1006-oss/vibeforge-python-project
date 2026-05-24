import os
import unittest

from models import Note, Scale, Melody, Chord
from text_engine import TextEngine
from scene_engine import SceneEngine
from evolve_engine import EvolveEngine
from file_manager import FileManager


class TestNote(unittest.TestCase):
    def test_midi_number(self):
        self.assertEqual(Note("C4").midi_number(), 60)
        self.assertEqual(Note("A4").midi_number(), 69)

    def test_transpose(self):
        self.assertEqual(Note("C4").transpose(4).pitch, "E4")

    def test_rest(self):
        self.assertTrue(Note("REST").is_rest())

    def test_to_from_dict(self):
        n = Note("D#4", 0.5, 99)
        data = n.to_dict()
        n2 = Note.from_dict(data)
        self.assertEqual(n, n2)


class TestScale(unittest.TestCase):
    def test_major_notes(self):
        self.assertEqual(Scale("C", "major").notes, ["C", "D", "E", "F", "G", "A", "B"])

    def test_minor_notes(self):
        self.assertEqual(Scale("A", "minor").notes, ["A", "B", "C", "D", "E", "F", "G"])

    def test_pentatonic_length(self):
        self.assertEqual(len(Scale("C", "pentatonic")), 5)

    def test_get_degree(self):
        self.assertEqual(Scale("C", "major").get_note(3), "E")

    def test_contains(self):
        self.assertFalse(Scale("C", "major").contains("F#"))


class TestMelody(unittest.TestCase):
    def test_retrograde(self):
        m = Melody([Note("C4"), Note("D4"), Note("E4")])
        r = m.retrograde()
        self.assertEqual([n.pitch for n in r.notes], ["E4", "D4", "C4"])

    def test_retrograde_uses_recursion(self):
        for length in [1, 2, 5, 8]:
            notes = [Note("C4") for _ in range(length)]
            m = Melody(notes)
            r = m.retrograde()
            self.assertEqual(len(r.notes), length)

    def test_transpose(self):
        m = Melody([Note("C4"), Note("D4")])
        t = m.transpose(2)
        self.assertEqual([n.pitch for n in t.notes], ["D4", "E4"])

    def test_concatenate(self):
        m1 = Melody([Note("C4"), Note("D4")])
        m2 = Melody([Note("E4")])
        m3 = m1 + m2
        self.assertEqual(len(m3.notes), 3)

    def test_total_beats(self):
        m = Melody([Note("C4", 0.5), Note("D4", 1.5), Note("E4", 2.0)])
        self.assertAlmostEqual(m.total_beats(), 4.0)


class TestTextEngine(unittest.TestCase):
    def test_space_creates_rest(self):
        engine = TextEngine()
        melody, _, _ = engine.generate("a b")
        self.assertTrue(any(n.is_rest() for n in melody.notes))

    def test_happy_mood(self):
        engine = TextEngine()
        _, _, mood = engine.generate("happy day")
        self.assertEqual(mood, "happy")

    def test_sad_mood(self):
        engine = TextEngine()
        _, _, mood = engine.generate("sad rain")
        self.assertEqual(mood, "sad")

    def test_output_has_notes(self):
        engine = TextEngine()
        melody, _, _ = engine.generate("hello")
        self.assertTrue(len(melody.notes) > 0)


class TestSceneEngine(unittest.TestCase):
    def test_chase_bpm(self):
        engine = SceneEngine()
        melody, _, _ = engine.generate("chase", intensity=100)
        self.assertGreaterEqual(melody.bpm, 140)

    def test_romance_bpm(self):
        engine = SceneEngine()
        melody, _, _ = engine.generate("romance", intensity=1)
        self.assertLessEqual(melody.bpm, 80)

    def test_invalid_scene(self):
        engine = SceneEngine()
        with self.assertRaises(ValueError):
            engine.generate("not_a_scene")


class TestEvolveEngine(unittest.TestCase):
    def test_initial_population_size(self):
        e = EvolveEngine(Scale("C", "major"), population_size=4)
        pop = e.create_initial_population()
        self.assertEqual(len(pop), 4)

    def test_evolve_returns_new_gen(self):
        e = EvolveEngine(Scale("C", "major"), population_size=4)
        e.create_initial_population()
        pop2 = e.evolve([0, 1])
        self.assertEqual(len(pop2), 4)

    def test_generation_counter(self):
        e = EvolveEngine(Scale("C", "major"), population_size=4)
        e.create_initial_population()
        g1 = e.get_generation()
        e.evolve([0, 1])
        g2 = e.get_generation()
        self.assertEqual(g2, g1 + 1)


class TestFileManager(unittest.TestCase):
    def test_save_and_load(self):
        fm = FileManager()
        melody = Melody([Note("C4"), Note("E4"), Note("G4")], title="Test Song")
        chords = [Chord("C", "major"), Chord("G", "dom7")]
        meta = {"mode_used": "test"}

        fn = fm.save("unit_test_song", melody, chords, meta)
        self.assertTrue(fn.endswith(".json"))

        data = fm.load(fn)
        self.assertEqual(data.get("title"), "unit_test_song")

        # cleanup
        fm.delete(fn)

    def test_load_nonexistent(self):
        fm = FileManager()
        data = fm.load("definitely_not_exists_12345.json")
        self.assertEqual(data, {})

    def test_list_saved(self):
        fm = FileManager()
        entries = fm.list_saved()
        self.assertIsInstance(entries, list)


if __name__ == "__main__":
    unittest.main()
