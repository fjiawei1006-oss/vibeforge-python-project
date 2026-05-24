# evolve_engine.py
import random
from models import Melody, Note, Scale


class EvolveEngine:
    """
    Melody evolution through genetic-style operations.
    """

    def __init__(self, scale: Scale, population_size: int = 4, mutation_rate: float = 0.3):
        self.scale = scale
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.population = []
        self.generation = 0

    def _copy_melody(self, melody: Melody, title_suffix: str = "") -> Melody:
        copied = [Note(n.pitch, n.duration, n.velocity) for n in melody.notes]
        return Melody(
            notes=copied,
            title=f"{melody.title}{title_suffix}",
            key=melody.key,
            bpm=melody.bpm,
            time_signature=melody.time_signature,
        )

    def _random_melody(self, length: int = 8) -> Melody:
        notes = []
        for _ in range(length):
            deg = random.randint(1, len(self.scale))
            name = self.scale.get_note(deg)
            octave = random.choice([4, 4, 5])
            duration = random.choice([0.5, 1.0, 1.0, 1.5])
            velocity = random.randint(60, 110)
            notes.append(Note(f"{name}{octave}", duration, velocity))
        return Melody(
            notes=notes,
            title="Random Seed",
            key=f"{self.scale.root} {self.scale.mode}",
            bpm=100,
            time_signature=(4, 4),
        )

    def create_initial_population(self, seed: Melody = None):
        self.population = []
        if seed is None:
            for _ in range(self.population_size):
                self.population.append(self._random_melody())
        else:
            self.population.append(self._copy_melody(seed, " [seed]"))
            while len(self.population) < self.population_size:
                variant = self._copy_melody(seed, " [var]")
                variant = self._mutate(variant)
                self.population.append(variant)

        self.generation = 1
        return self.population

    def _crossover(self, parent_a: Melody, parent_b: Melody):
        a_notes = parent_a.notes
        b_notes = parent_b.notes
        if not a_notes and not b_notes:
            return Melody(title="Child", key=parent_a.key, bpm=parent_a.bpm)
        if not a_notes:
            return self._copy_melody(parent_b, " [child]")
        if not b_notes:
            return self._copy_melody(parent_a, " [child]")

        split_a = len(a_notes) // 2
        split_b = len(b_notes) // 2
        child_notes = a_notes[:split_a] + b_notes[split_b:]
        child_copy = [Note(n.pitch, n.duration, n.velocity) for n in child_notes]
        return Melody(
            notes=child_copy,
            title="Child Melody",
            key=parent_a.key,
            bpm=int((parent_a.bpm + parent_b.bpm) / 2),
            time_signature=parent_a.time_signature,
        )

    def _shift_note_by_scale_step(self, note: Note, direction: int):
        if note.is_rest():
            return Note("REST", note.duration, note.velocity)
        midi = note.midi_number()
        semitone_step = 2 * direction  # simple approximation
        return Note.from_midi(midi + semitone_step, note.duration, note.velocity)

    def _retrograde_fragment(self, notes: list):
        # RECURSION
        if len(notes) <= 1:
            return notes[:]
        return [notes[-1]] + self._retrograde_fragment(notes[:-1])

    def _mutate(self, melody: Melody):
        if len(melody.notes) == 0:
            return melody

        m = self._copy_melody(melody, " [mut]")
        mutation = random.choice(["pitch_shift", "rhythm_change", "swap", "retrograde_fragment"])

        if mutation == "pitch_shift":
            i = random.randint(0, len(m.notes) - 1)
            direction = random.choice([-1, 1])
            m.notes[i] = self._shift_note_by_scale_step(m.notes[i], direction)

        elif mutation == "rhythm_change":
            i = random.randint(0, len(m.notes) - 1)
            m.notes[i].duration = random.choice([0.5, 1.0, 1.5, 2.0])

        elif mutation == "swap":
            if len(m.notes) >= 2:
                i = random.randint(0, len(m.notes) - 2)
                m.notes[i], m.notes[i + 1] = m.notes[i + 1], m.notes[i]

        elif mutation == "retrograde_fragment":
            if len(m.notes) >= 3:
                start = random.randint(0, len(m.notes) - 3)
                end = random.randint(start + 2, len(m.notes) - 1)
                frag = m.notes[start : end + 1]
                rev = self._retrograde_fragment(frag)
                m.notes[start : end + 1] = rev

        return m

    def evolve(self, parent_indices: list):
        if len(self.population) == 0:
            self.create_initial_population()

        valid = [i for i in parent_indices if 0 <= i < len(self.population)]
        if len(valid) < 2:
            valid = [0, 1] if len(self.population) >= 2 else [0, 0]

        parents = [self.population[valid[0]], self.population[valid[1]]]
        new_population = []

        while len(new_population) < self.population_size:
            child = self._crossover(random.choice(parents), random.choice(parents))
            if random.random() < self.mutation_rate:
                child = self._mutate(child)
            new_population.append(child)

        self.population = new_population
        self.generation += 1
        return self.population

    def get_generation(self):
        return self.generation

    def get_population(self):
        return self.population
