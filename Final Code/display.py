import random
from models import Melody


class Display:
    COLORS = {
        "reset": "\033[0m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
    }

    @classmethod
    def color(cls, text: str, color: str) -> str:
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

    @classmethod
    def banner(cls):
        logo = r"""
 __      ___ _          _____                     
 \ \    / (_) |        |  ___|                    
  \ \  / / _| |__   ___| |_ ___  _ __ __ _  ___   
   \ \/ / | | '_ \ / _ \  _/ _ \| '__/ _` |/ _ \  
    \  /  | | |_) |  __/ || (_) | | | (_| |  __/  
     \/   |_|_.__/ \___\_| \___/|_|  \__, |\___|  
                                       __/ |       
                                      |___/        
"""
        print(cls.color(logo, "cyan"))
        print(cls.color("VibeForge", "magenta"))

    @classmethod
    def main_menu(cls):
        print("╔══════════════════════════════════╗")
        print("║           VibeForge              ║")
        print("╠══════════════════════════════════╣")
        print("║  [1]  Text Mode                  ║")
        print("║  [2]  Scene Mode                 ║")
        print("║  [3]  Evolve Mode                ║")
        print("║  [4]  My Works                   ║")
        print("║  [0]  Exit                       ║")
        print("╚══════════════════════════════════╝")

    @classmethod
    def loading(cls, message: str = ""):
        msgs = [
            "Channeling Mozart...",
            "Tuning the algorithm...",
            "Mixing vibes...",
            "Sprinkling musical magic...",
        ]
        print(cls.color(message or random.choice(msgs), "yellow"))

    @classmethod
    def show_melody(cls, melody: Melody):
        beat = 0.0
        bar = ["|"]
        for n in melody.notes:
            token = "-" if n.is_rest() else n.pitch
            bar.append(f"{token:>4}")
            beat += n.duration
            if beat >= 4.0:
                bar.append(" |")
                beat -= 4.0
        if bar[-1] != " |":
            bar.append(" |")
        print("".join(bar))

    @classmethod
    def show_piano_roll(cls, melody: Melody):
        pitches = [n.pitch for n in melody.notes if not n.is_rest()]
        if not pitches:
            print("(no notes)")
            return

        uniq = sorted(set(pitches), key=lambda p: (int(p[-1]), p[:-1]), reverse=True)
        grid = {p: [] for p in uniq}
        for n in melody.notes:
            for p in uniq:
                if n.is_rest():
                    grid[p].append("  ")
                else:
                    grid[p].append("██" if n.pitch == p else "  ")

        for p in uniq:
            print(f"{p:>3} | {''.join(grid[p])} |")

    @classmethod
    def show_chords(cls, chords: list):
        print("".join([f"| {str(c):<6} " for c in chords]) + "|")

    @classmethod
    def show_composition(cls, title: str, melody: Melody, chords: list, metadata: dict):
        print("\n" + "═" * 46)
        print(cls.color(f"🎼 {title}", "bold"))
        print(f"Key: {melody.key} | BPM: {melody.bpm} | Beats: {melody.total_beats():.1f}")
        if metadata:
            for k, v in metadata.items():
                print(f"- {k}: {v}")
        print("-" * 46)
        print("Melody:")
        cls.show_melody(melody)
        print("Chords:")
        cls.show_chords(chords)
        print("Piano Roll:")
        cls.show_piano_roll(melody)
        print("═" * 46 + "\n")

    @classmethod
    def show_generation(cls, gen_num: int, melodies: list):
        print(cls.color(f"\n🧬 Generation {gen_num}", "green"))
        for i, m in enumerate(melodies, start=1):
            print(f"[{i}] {m}")
