"""Le montage : chaque scène en vidéo à la durée exacte de sa voix, puis tout bout à bout, voix et sous-titres.

Entrées : video/voix_synth/*.mp3 et *.json, video/brut/*.jpg et *.png, video/captures/site.webm et evenements.json, docs/architecture.png.
Sortie : video/rendu/rubalise-demo.mp4
"""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = Path(__file__).resolve().parents[1]
VOIX, BRUT, CAPT, RENDU = RACINE / "video" / "voix_synth", RACINE / "video" / "brut", RACINE / "video" / "captures", RACINE / "video" / "rendu"
BIN = next(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin"))
FFMPEG = str(BIN / "ffmpeg.exe")
W, H, FPS = 1920, 1080, 30
TOILE = (3840, 2160)          # les images fixes sont posées sur une toile double, pour zoomer sans perdre de netteté
PAUSE = 0.5                   # respiration entre deux scènes
FOND, ENCRE, ACCENT, GRIS = "#F3F5F4", "#1E2429", "#D9530B", "#5C6670"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def ff(*args):
    subprocess.run([FFMPEG, "-v", "error", "-y", *args], check=True)


def voix(scene):
    d = json.loads((VOIX / f"{scene}.json").read_text(encoding="utf-8"))
    return d["duree"], [p["debut"] for p in d["phrases"]], [p["fin"] for p in d["phrases"]]


# ------------------------------------------------------------------ images fixes
def toile(fond=FOND):
    return Image.new("RGB", TOILE, fond)


def poser(im, canevas, hauteur=None, largeur=None):
    """Pose une image centrée sur la toile, à la hauteur ou à la largeur voulue."""
    if hauteur:
        im = im.resize((round(im.width * hauteur / im.height), hauteur), Image.LANCZOS)
    elif largeur:
        im = im.resize((largeur, round(im.height * largeur / im.width)), Image.LANCZOS)
    canevas.paste(im, ((canevas.width - im.width) // 2, (canevas.height - im.height) // 2))
    return canevas


def photo_composee(chemin, sortie):
    im = Image.open(chemin).convert("RGB")
    fond = im.resize((TOILE[0], round(im.height * TOILE[0] / im.width)), Image.LANCZOS)
    fond = fond.crop((0, (fond.height - TOILE[1]) // 2, TOILE[0], (fond.height - TOILE[1]) // 2 + TOILE[1]))
    fond = fond.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * 0.62))
    poser(im, fond, hauteur=int(TOILE[1] * 0.92)).save(sortie, quality=92)


def image_sur_fond(chemin, sortie, fond=FOND, marge=0.94, largeur_max=None):
    im = Image.open(chemin).convert("RGB")
    c = toile(fond)
    if im.width / im.height > TOILE[0] / TOILE[1]:
        poser(im, c, largeur=int(TOILE[0] * (largeur_max or marge)))
    else:
        poser(im, c, hauteur=int(TOILE[1] * marge))
    c.save(sortie, quality=92)
    return im.size


def carte_fin(sortie):
    c = toile()
    d = ImageDraw.Draw(c)
    gras = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 210)
    normal = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 84)
    petit = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 62)
    d.rectangle((0, 0, 44, TOILE[1]), fill=ACCENT)
    d.text((300, 640), "Rubalise", font=gras, fill=ENCRE)
    d.text((300, 920), "Volunteer planning for trail races", font=normal, fill=GRIS)
    d.text((300, 1220), "github.com/YISOWAK/rubalise", font=normal, fill=ACCENT)
    d.text((300, 1560), "Strands Agents  ·  Amazon Bedrock AgentCore  ·  OR-Tools CP-SAT  ·  MCP", font=petit, fill=GRIS)
    c.save(sortie, quality=92)


def zoom(image, sortie, duree, cible1, cible0=None, glisse=1.2, derive=0.04):
    """Une image fixe en vidéo : glisse de cible0 vers cible1 en `glisse` secondes, puis dérive lente.
    Une cible : (cx, cy, z) en fractions de la toile et facteur de zoom, z=1 montre toute la toile."""
    cx1, cy1, z1 = cible1
    cx0, cy0, z0 = cible0 or cible1
    n, k = max(2, round(duree * FPS)), max(1, round(glisse * FPS))
    if cible0 is None:
        k = 1
    def borne(c, z):        # le cadre reste dans la toile
        return min(max(c, 0.5 / z), 1 - 0.5 / z)
    cx0, cy0, cx1, cy1 = borne(cx0, z0), borne(cy0, z0), borne(cx1, z1), borne(cy1, z1)
    e = f"min(on/{k},1)"
    z = f"({z0}+({z1}-{z0})*{e})*(1+{derive}*max(on-{k},0)/{n})"
    cx = f"({cx0}+({cx1}-{cx0})*{e})"
    cy = f"({cy0}+({cy1}-{cy0})*{e})"
    filtre = (f"zoompan=z='{z}':x='iw*{cx}-iw/zoom/2':y='ih*{cy}-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},"
              f"trim=duration={duree:.3f},setpts=PTS-STARTPTS")
    ff("-loop", "1", "-framerate", str(FPS), "-t", f"{duree + 0.2:.3f}", "-i", str(image), "-vf", filtre, "-an", *ENC, str(sortie))


def fondu(clips, durees, sortie, d=0.5):
    """Enchaîne des clips par fondu croisé. La durée totale vaut somme des clips moins (n-1)·d."""
    if len(clips) == 1:
        Path(clips[0]).replace(sortie); return
    entrees = [a for c in clips for a in ("-i", str(c))]
    fc, prev, offset = [], "[0:v]", 0.0
    for i in range(1, len(clips)):
        offset += durees[i - 1] - d
        out = f"[v{i}]" if i < len(clips) - 1 else "[v]"
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={d}:offset={offset:.3f}{out}")
        prev = out
    ff(*entrees, "-filter_complex", ";".join(fc), "-map", "[v]", "-an", *ENC, str(sortie))


def extrait(source, debut, duree, sortie):
    ff("-i", str(source), "-ss", f"{debut:.3f}", "-t", f"{duree:.3f}", "-vf", f"scale={W}:{H},fps={FPS}", "-an", *ENC, str(sortie))


def caler(clip, duree, sortie):
    """Force un clip à la durée voulue : coupe, ou gèle la dernière image."""
    ff("-i", str(clip), "-vf", f"tpad=stop_mode=clone:stop_duration={duree + 1:.3f},trim=duration={duree:.3f},setpts=PTS-STARTPTS", "-an", *ENC, str(sortie))


# ------------------------------------------------------------------ les scènes
def scene_s1(T, deb, fin):
    """Trois photos, fondu entre elles."""
    d = (T + 2 * 0.6) / 3
    clips = []
    for i, nom in enumerate(["photo1_depart_morgins.jpg", "photo2_arche_finisher.jpg", "photo3_medaille.jpg"]):
        comp = RENDU / f"s1_{i}.jpg"; photo_composee(BRUT / nom, comp)
        clip = RENDU / f"s1_{i}.mp4"
        zoom(comp, clip, d, (0.5, 0.48, 1.10), (0.5, 0.5, 1.0), glisse=d, derive=0.0)
        clips.append(clip)
    fondu(clips, [d] * 3, RENDU / "s1.mp4", 0.6)


def scene_s2a(T, deb, fin):
    """La page du roadbook, le tableau en gros plan, le formulaire."""
    b1, b2 = deb[2], deb[3]
    dA, dB, dC = b1 + 0.25, (b2 - b1) + 0.5, (T - b2) + 0.25
    page = RENDU / "s2a_page.jpg"; image_sur_fond(BRUT / "img_roadbook_page.png", page, marge=0.96)
    tableau = RENDU / "s2a_tableau.jpg"; image_sur_fond(BRUT / "img_roadbook_tableau.png", tableau, marge=0.92)
    form = RENDU / "s2a_form.jpg"; image_sur_fond(BRUT / "img_formulaire.png", form, marge=0.90)
    zoom(page, RENDU / "s2a_0.mp4", dA, (0.5, 0.30, 1.35), (0.5, 0.5, 1.0), glisse=dA * 0.8, derive=0.0)
    zoom(tableau, RENDU / "s2a_1.mp4", dB, (0.5, 0.5, 1.06), (0.5, 0.5, 1.0), glisse=dB, derive=0.0)
    zoom(form, RENDU / "s2a_2.mp4", dC, (0.57, 0.56, 1.14), (0.5, 0.5, 1.0), glisse=dC * 0.9, derive=0.0)
    fondu([RENDU / "s2a_0.mp4", RENDU / "s2a_1.mp4", RENDU / "s2a_2.mp4"], [dA, dB, dC], RENDU / "s2a.mp4", 0.5)


def scene_s2b(T, deb, fin):
    """Le schéma, bloc par bloc, au rythme des phrases."""
    schema = RENDU / "s2b_schema.jpg"
    lw, lh = image_sur_fond(RACINE / "docs" / "architecture.png", schema, marge=0.96)
    # le PNG (2400x1700) posé à 96 % de hauteur : on convertit les coordonnées du schéma (1200x850) en fractions de toile
    h = int(TOILE[1] * 0.96); w = round(lw * h / lh); x0, y0 = (TOILE[0] - w) / 2, (TOILE[1] - h) / 2
    def cible(px, py, z):
        return ((x0 + px / 1200 * w) / TOILE[0], (y0 + py / 850 * h) / TOILE[1], z)
    tout = (0.5, 0.5, 1.0)
    etapes = [(0, tout), (1, cible(315, 524, 2.4)), (3, cible(505, 524, 2.4)), (4, cible(885, 524, 2.4)),
              (7, cible(600, 295, 1.9)), (10, cible(1025, 295, 1.9)), (13, cible(600, 85, 1.7)), (14, tout)]
    clips, durees, prec = [], [], tout
    for i, (ph, c) in enumerate(etapes):
        t_deb = deb[ph] if ph else 0.0
        t_fin = deb[etapes[i + 1][0]] if i + 1 < len(etapes) else T
        clip = RENDU / f"s2b_{i}.mp4"
        zoom(schema, clip, t_fin - t_deb, c, prec, glisse=1.1, derive=0.03)
        clips.append(clip); durees.append(t_fin - t_deb); prec = c
    liste = RENDU / "s2b_liste.txt"
    liste.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", str(liste), "-c", "copy", str(RENDU / "s2b.mp4"))


def scene_site(scene, T, seg):
    """Une scène filmée sur le site : on découpe l'enregistrement aux bornes notées."""
    src = CAPT / "site.webm"
    if scene == "s4":
        a, b = seg["s4a"], seg["s4b"]
        extrait(src, a[0], a[1] - a[0], RENDU / "s4_a.mp4")
        extrait(src, b[0], b[1] - b[0], RENDU / "s4_b.mp4")
        liste = RENDU / "s4_liste.txt"
        liste.write_text(f"file '{(RENDU / 's4_a.mp4').as_posix()}'\nfile '{(RENDU / 's4_b.mp4').as_posix()}'\n", encoding="utf-8")
        ff("-f", "concat", "-safe", "0", "-i", str(liste), "-c", "copy", str(RENDU / "s4_brut.mp4"))
        caler(RENDU / "s4_brut.mp4", T, RENDU / "s4.mp4")
    else:
        a = seg[scene]
        extrait(src, a[0], a[1] - a[0], RENDU / f"{scene}_brut.mp4")
        caler(RENDU / f"{scene}_brut.mp4", T, RENDU / f"{scene}.mp4")


def scene_s5(T, deb, fin):
    """Le tableau des mesures, puis la carte de fin."""
    b = deb[2]
    dA, dB = b + 0.25, (T - b) + 0.25
    mes = RENDU / "s5_mesures.jpg"; image_sur_fond(CAPT / "mesures.png", mes, marge=0.88)
    carte = RENDU / "s5_carte.jpg"; carte_fin(carte)
    zoom(mes, RENDU / "s5_0.mp4", dA, (0.5, 0.5, 1.08), (0.5, 0.5, 1.0), glisse=dA, derive=0.0)
    zoom(carte, RENDU / "s5_1.mp4", dB, (0.5, 0.5, 1.04), (0.5, 0.5, 1.0), glisse=dB, derive=0.0)
    fondu([RENDU / "s5_0.mp4", RENDU / "s5_1.mp4"], [dA, dB], RENDU / "s5.mp4", 0.5)


# ------------------------------------------------------------------ l'assemblage
def srt_temps(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h):02}:{int(m):02}:{int(r):02},{int(round((r - int(r)) * 1000)):03}"


def main():
    RENDU.mkdir(parents=True, exist_ok=True)
    seg = json.loads((CAPT / "evenements.json").read_text(encoding="utf-8"))["segments"]
    ordre = ["s1", "s2a", "s2b", "s3", "s3bis", "s4", "s5"]
    fabriques = {"s1": scene_s1, "s2a": scene_s2a, "s2b": scene_s2b, "s5": scene_s5}

    videos, audios, srt, offset, n = [], [], [], 0.0, 0
    for scene in ordre:
        T, deb, fin = voix(scene)
        print(f"{scene:6} {T:6.1f} s")
        if scene in fabriques:
            fabriques[scene](T, deb, fin)
        else:
            scene_site(scene, T, seg)
        cale = RENDU / f"{scene}_cale.mp4"
        caler(RENDU / f"{scene}.mp4", T + PAUSE, cale)
        videos.append(cale)
        wav = RENDU / f"{scene}.wav"
        ff("-i", str(VOIX / f"{scene}.mp3"), "-af", f"apad=pad_dur={PAUSE},atrim=duration={T + PAUSE:.3f}", "-ar", "48000", "-ac", "2", str(wav))
        audios.append(wav)
        for p in json.loads((VOIX / f"{scene}.json").read_text(encoding="utf-8"))["phrases"]:
            n += 1
            srt.append(f"{n}\n{srt_temps(offset + p['debut'])} --> {srt_temps(offset + p['fin'])}\n{p['texte']}\n")
        offset += T + PAUSE

    (RENDU / "videos.txt").write_text("".join(f"file '{v.as_posix()}'\n" for v in videos), encoding="utf-8")
    (RENDU / "audios.txt").write_text("".join(f"file '{a.as_posix()}'\n" for a in audios), encoding="utf-8")
    (RENDU / "tout.srt").write_text("\n".join(srt) + "\n", encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", str(RENDU / "videos.txt"), "-c", "copy", str(RENDU / "tout_video.mp4"))
    ff("-f", "concat", "-safe", "0", "-i", str(RENDU / "audios.txt"), "-c", "copy", str(RENDU / "tout.wav"))

    style = "FontName=Segoe UI,FontSize=17,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=44,Alignment=2"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", "tout_video.mp4", "-i", "tout.wav",
                    "-vf", f"subtitles=tout.srt:force_style='{style}'", *ENC, "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", "-shortest", "rubalise-demo.mp4"], cwd=RENDU, check=True)
    print(f"\nvidéo : {RENDU / 'rubalise-demo.mp4'}  ({offset:.0f} s, soit {int(offset // 60)} min {int(offset % 60):02d})")


if __name__ == "__main__":
    main()
