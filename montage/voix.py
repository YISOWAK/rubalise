"""La voix off avec Amazon Polly, phrase par phrase, pour avoir le minutage exact de chaque sous-titre.

Sortie, par scène, dans video/voix_synth/ : <scene>.mp3, <scene>.json (durée, phrases avec début et fin), <scene>.srt.
Usage : python montage/voix.py [--voix Matthew] [--moteur generative] [--scenes s1,s3] [--test]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import boto3

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))
from textes import ORDRE, phrases  # noqa: E402

SORTIE = RACINE / "video" / "voix_synth"
BIN = next(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin"))
FFMPEG, FFPROBE = str(BIN / "ffmpeg.exe"), str(BIN / "ffprobe.exe")
PAUSE_PHRASE = 0.35      # silence entre deux phrases d'un même sous-titre
PAUSE_SOUS_TITRE = 0.55  # silence entre deux sous-titres


def decouper(texte: str) -> list[str]:
    return [m for m in re.split(r"(?<=[.!?])\s+", texte.strip()) if m]


def duree_audio(chemin: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(chemin)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def srt_temps(s: float) -> str:
    h, r = divmod(s, 3600)
    m, r = divmod(r, 60)
    return f"{int(h):02}:{int(m):02}:{int(r):02},{int(round((r - int(r)) * 1000)):03}"


def silence(duree: float, chemin: Path):
    if not chemin.exists():
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{duree:.3f}",
                        "-c:a", "libmp3lame", "-b:a", "64k", str(chemin)], check=True)


def synthese(polly, scene: str, items: list[tuple[str, str]], voix: str, moteur: str) -> dict:
    """items : (texte lu, texte affiché) par sous-titre. Chaque phrase lue est synthétisée à part."""
    dossier = SORTIE / "morceaux" / scene
    dossier.mkdir(parents=True, exist_ok=True)
    silence(PAUSE_PHRASE, SORTIE / "morceaux" / "pause_phrase.mp3")
    silence(PAUSE_SOUS_TITRE, SORTIE / "morceaux" / "pause_sous_titre.mp3")

    liste, sous_titres, t = [], [], 0.0
    for i, (lu, affiche) in enumerate(items):
        debut = t
        for j, phrase in enumerate(decouper(lu)):
            mp3 = dossier / f"{i:02}_{j}.mp3"
            if not mp3.exists():
                r = polly.synthesize_speech(Text=phrase, VoiceId=voix, Engine=moteur, OutputFormat="mp3", SampleRate="24000")
                mp3.write_bytes(r["AudioStream"].read())
            if j:
                liste.append(SORTIE / "morceaux" / "pause_phrase.mp3"); t += PAUSE_PHRASE
            liste.append(mp3); t += duree_audio(mp3)
        sous_titres.append({"debut": round(debut, 3), "fin": round(t, 3), "texte": affiche})
        if i + 1 < len(items):
            liste.append(SORTIE / "morceaux" / "pause_sous_titre.mp3"); t += PAUSE_SOUS_TITRE

    concat = dossier / "liste.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in liste), encoding="utf-8")
    mp3 = SORTIE / f"{scene}.mp3"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "libmp3lame", "-b:a", "96k", str(mp3)], check=True)
    duree = duree_audio(mp3)

    res = {"scene": scene, "duree": round(duree, 3), "voix": voix, "moteur": moteur, "phrases": sous_titres}
    (SORTIE / f"{scene}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    srt = "".join(f"{i + 1}\n{srt_temps(p['debut'])} --> {srt_temps(p['fin'])}\n{p['texte']}\n\n" for i, p in enumerate(sous_titres))
    (SORTIE / f"{scene}.srt").write_text(srt, encoding="utf-8")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voix", default="Matthew")
    ap.add_argument("--moteur", default="generative", choices=["generative", "neural"])
    ap.add_argument("--scenes", default=",".join(ORDRE))
    ap.add_argument("--test", action="store_true", help="deux phrases factices, pour vérifier la chaîne")
    args = ap.parse_args()
    SORTIE.mkdir(parents=True, exist_ok=True)
    polly = boto3.Session(region_name="us-east-1").client("polly")

    if args.test:
        res = synthese(polly, "test", [("This is a test of the voice.", "This is a test of the voice."),
                                       ("It has two subtitles. And a second sentence.", "It has two subtitles. And a second sentence.")], args.voix, args.moteur)
        print(json.dumps(res, indent=1))
        return

    total = 0.0
    for scene in args.scenes.split(","):
        res = synthese(polly, scene, phrases(scene), args.voix, args.moteur)
        total += res["duree"]
        print(f"{scene:6} {res['duree']:6.1f} s  {len(res['phrases'])} sous-titres")
    print(f"total  {total:6.1f} s  soit {int(total // 60)} min {int(total % 60):02d}")


if __name__ == "__main__":
    main()
