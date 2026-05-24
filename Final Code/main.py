from models import Melody, Note, Chord, Scale
from text_engine import TextEngine
from scene_engine import SceneEngine
from evolve_engine import EvolveEngine
from file_manager import FileManager
from display import Display


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nInput interrupted. Returning to menu.")
        return ""


def parse_int(prompt: str, default: int = 0, lo: int = None, hi: int = None) -> int:
    s = safe_input(prompt).strip()
    try:
        value = int(s)
    except ValueError:
        print(f"Invalid number. Using default: {default}")
        return default
    if lo is not None and value < lo:
        print(f"Too small. Clamped to {lo}.")
        value = lo
    if hi is not None and value > hi:
        print(f"Too large. Clamped to {hi}.")
        value = hi
    return value


def ask_yes_no(prompt: str) -> bool:
    s = safe_input(prompt).strip().lower()
    return s in ("y", "yes", "1")


def parse_melody_line(line: str) -> Melody:
    notes = []
    for tok in line.strip().split():
        tok = tok.strip()
        if not tok:
            continue
        if tok.upper() == "REST" or tok == "-":
            notes.append(Note("REST", 1.0, 0))
        else:
            notes.append(Note(tok, 1.0, 80))
    if not notes:
        notes = [Note("C4"), Note("E4"), Note("G4"), Note("A4")]
    return Melody(notes=notes, title="User Seed", key="C major", bpm=100)


def handle_text_mode(file_manager: FileManager):
    engine = TextEngine()
    Display.loading()
    text = safe_input("Enter text: ")
    if not text.strip():
        print("No text entered.")
        return

    melody, chords, mood = engine.generate(text)
    meta = {"mode_used": "text", "mood": mood, "source_text": text}
    Display.show_composition("Text Mode Output", melody, chords, meta)

    if ask_yes_no("Save this composition? (y/n): "):
        title = safe_input("Title: ").strip() or "text_vibe"
        fn = file_manager.save(title, melody, chords, meta)
        if fn:
            print(f"Saved as: {fn}")


def handle_scene_mode(file_manager: FileManager):
    engine = SceneEngine()
    scenes = engine.list_scenes()
    mods = engine.list_modifiers()

    print("\nAvailable scenes:")
    for i, s in enumerate(scenes, start=1):
        print(f"[{i}] {s}")

    idx = parse_int("Pick a scene number: ", default=1, lo=1, hi=len(scenes))
    scene = scenes[idx - 1]

    print("\nAvailable modifiers (pick up to 2, comma-separated numbers, or empty):")
    for i, m in enumerate(mods, start=1):
        print(f"[{i}] {m}")

    raw = safe_input("Modifiers: ").strip()
    chosen_mods = []
    if raw:
        parts = [p.strip() for p in raw.split(",")]
        for p in parts[:2]:
            try:
                mi = int(p)
                if 1 <= mi <= len(mods):
                    chosen_mods.append(mods[mi - 1])
            except ValueError:
                print(f"Skipping invalid modifier: {p}")

    intensity = parse_int("Intensity (1-100): ", default=50, lo=1, hi=100)

    try:
        Display.loading()
        melody, chords, params = engine.generate(scene, chosen_mods, intensity)
        meta = {"mode_used": "scene", "params": params}
        Display.show_composition("Scene Mode Output", melody, chords, meta)

        if ask_yes_no("Save this composition? (y/n): "):
            title = safe_input("Title: ").strip() or f"scene_{scene}"
            fn = file_manager.save(title, melody, chords, meta)
            if fn:
                print(f"Saved as: {fn}")
    except ValueError as e:
        print(f"Scene error: {e}")


def handle_evolve_mode(file_manager: FileManager):
    scale = Scale("C", "major")
    engine = EvolveEngine(scale=scale, population_size=4, mutation_rate=0.35)

    start_choice = safe_input("Start with random or custom melody? (r/c): ").strip().lower()
    seed = None
    if start_choice == "c":
        line = safe_input("Enter short melody (example: C4 E4 G4 A4): ")
        try:
            seed = parse_melody_line(line)
        except Exception as e:
            print(f"Could not parse melody, using random. ({e})")

    population = engine.create_initial_population(seed)

    for _ in range(5):
        Display.show_generation(engine.get_generation(), population)
        pick = safe_input("Pick 2 favorites (e.g. 1,3) or 'done': ").strip().lower()
        if pick == "done":
            break
        try:
            a, b = [int(x.strip()) for x in pick.split(",")]
            parent_indices = [a - 1, b - 1]
        except Exception:
            print("Invalid input. Using defaults 1 and 2.")
            parent_indices = [0, 1]
        population = engine.evolve(parent_indices)

    Display.show_generation(engine.get_generation(), population)
    final_choice = parse_int("Choose final melody number to keep: ", default=1, lo=1, hi=len(population))
    final_melody = population[final_choice - 1]
    final_chords = [Chord("C", "major"), Chord("G", "dom7"), Chord("Am".replace("m", ""), "minor"), Chord("F", "major")]
    meta = {"mode_used": "evolve", "generation": engine.get_generation(), "scale": str(scale)}
    Display.show_composition("Evolve Mode Final", final_melody, final_chords, meta)

    if ask_yes_no("Save this composition? (y/n): "):
        title = safe_input("Title: ").strip() or "evolved_vibe"
        fn = file_manager.save(title, final_melody, final_chords, meta)
        if fn:
            print(f"Saved as: {fn}")


def handle_my_works(file_manager: FileManager):
    works = file_manager.list_saved()
    if not works:
        print("No saved works yet.")
        return

    print("\nSaved compositions:")
    for i, w in enumerate(works, start=1):
        print(f"[{i}] {w['title']} ({w['filename']}) {w.get('date', '')}")

    idx = parse_int("Open which one? (0 to back): ", default=0, lo=0, hi=len(works))
    if idx == 0:
        return

    item = works[idx - 1]
    data = file_manager.load(item["filename"])
    if not data:
        return

    melody = Melody.from_dict(data.get("melody", {}))
    chords = [Chord.from_dict(c) for c in data.get("chords", [])]
    metadata = data.get("metadata", {})
    title = data.get("title", "Untitled")
    Display.show_composition(title, melody, chords, metadata)


def main():
    file_manager = FileManager()
    Display.banner()

    while True:
        Display.main_menu()
        choice = safe_input("Choose an option: ").strip()

        if choice == "1":
            handle_text_mode(file_manager)
        elif choice == "2":
            handle_scene_mode(file_manager)
        elif choice == "3":
            handle_evolve_mode(file_manager)
        elif choice == "4":
            handle_my_works(file_manager)
        elif choice == "0":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid option. Please enter 0-4.")


if __name__ == "__main__":
    main()
