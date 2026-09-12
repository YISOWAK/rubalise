"""Filme les scènes du site (3, 3 bis, 4) en pilotant Chrome, avec un curseur visible, calé sur le minutage de la voix.

Lit video/voix_synth/{s3,s3bis,s4}.json pour placer les clics au moment où la voix en parle.
Écrit video/captures/site.webm, video/captures/evenements.json (bornes de chaque scène dans la vidéo) et mesures.png.
Coûte un calcul de plan et un message du jour J sur Bedrock.
"""
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parents[1]
VOIX = RACINE / "video" / "voix_synth"
SORTIE = RACINE / "video" / "captures"
LIEN = (RACINE / "web" / "lien_demo.txt").read_text(encoding="utf-8").strip()
BASE, CLE = LIEN.split("?")[0], urllib.parse.parse_qs(urllib.parse.urlparse(LIEN).query)["k"][0]

CURSEUR = """
(() => {
  const st = document.createElement('style');
  st.textContent = '#curseur-demo{position:fixed;left:0;top:0;width:28px;height:28px;pointer-events:none;z-index:2147483647;transform:translate(-3px,-2px);filter:drop-shadow(0 1px 2px rgba(0,0,0,.5))}'
    + '#curseur-demo.clic svg{animation:cd .28s ease-out}@keyframes cd{from{transform:scale(.72)}to{transform:scale(1)}}';
  const svg = '<svg viewBox="0 0 24 24" width="28" height="28"><path d="M5 3l14 9-6 1.5L16.5 21l-3-1.5-3.5-7L5 15z" fill="#fff" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  function init(){ if (document.getElementById('curseur-demo')) return;
    document.head.appendChild(st);
    const d = document.createElement('div'); d.id = 'curseur-demo'; d.innerHTML = svg; document.documentElement.appendChild(d);
    document.addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
    document.addEventListener('mousedown', () => { d.classList.remove('clic'); void d.offsetWidth; d.classList.add('clic'); }, true); }
  if (document.readyState !== 'loading') init(); else document.addEventListener('DOMContentLoaded', init);
})();
"""


class Tournage:
    def __init__(self, page):
        self.page, self.souris = page, (960, 540)
        self.t_video0 = time.time()
        self.segments, self.journal = {}, []

    # --- le temps
    def note(self, quoi):
        self.journal.append((round(time.time() - self.t_video0, 2), quoi)); print(f"  {self.journal[-1][0]:7.2f}  {quoi}")

    def maintenant(self):
        return time.time() - self.t_video0

    def jusqua(self, t_scene, t0):
        reste = t0 + t_scene - time.time()
        if reste > 0:
            time.sleep(reste)

    # --- la souris
    def glisser(self, x, y, duree=0.6):
        x0, y0 = self.souris
        n = max(8, int(duree * 60))
        for i in range(1, n + 1):
            e = 0.5 - math.cos(math.pi * i / n) / 2      # accélère puis freine
            self.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
            time.sleep(duree / n)
        self.souris = (x, y)

    def centre(self, sel):
        b = self.page.locator(sel).first.bounding_box()
        if not b:
            raise RuntimeError(f"introuvable : {sel}")
        return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

    def aller(self, sel, duree=0.6):
        self.glisser(*self.centre(sel), duree)

    def cliquer(self, sel, duree=0.6):
        self.aller(sel, duree)
        time.sleep(0.12)
        self.page.mouse.down(); time.sleep(0.08); self.page.mouse.up()

    def defiler_vers(self, sel, bloc="center"):
        self.page.evaluate("([s, b]) => { const e = document.querySelector(s); if (e) e.scrollIntoView({behavior: 'smooth', block: b}); }", [sel, bloc])


def phrases(scene):
    d = json.loads((VOIX / f"{scene}.json").read_text(encoding="utf-8"))
    return d["duree"], [p["debut"] for p in d["phrases"]], [p["fin"] for p in d["phrases"]]


def etat(session):
    with urllib.request.urlopen(f"{BASE}etat?k={CLE}&session={urllib.parse.quote(session)}", timeout=300) as r:
        return json.load(r)["etat"]


def absents(e):
    """Le responsable et une autre personne d'un créneau qui commence à 11h le jour J, le plus serré possible."""
    jc = e["course"]["depart"]["date_heure"][:10]
    cands = []
    for p in e["postes"]:
        if p["debut"][:10] != jc or p["debut"][11:16] > "11:00" or p["fin"][11:16] <= "11:30":
            continue
        eq = p.get("equipe", [])
        resp = [m for m in eq if m["role"] == "responsable"]
        autres = [m for m in eq if m["role"] != "responsable"]
        if resp and autres:
            couverture = sum(1 + m.get("accompagnants", 0) for m in eq)
            cands.append((couverture - p["min"], 0 if p["site"] == "Le Grand Pré" else 1, p, resp[0]["nom"], autres[0]["nom"]))
    cands.sort(key=lambda c: (c[1], c[0]))
    if not cands:
        raise RuntimeError("aucun créneau de 11h avec responsable et équipe")
    _, _, p, r, a = cands[0]
    lieu = "au ravitaillement du Grand Pré" if p["site"] == "Le Grand Pré" else f"sur le poste « {p['nom']} »"
    return f"Il est 11h. {r} et {a}, {lieu}, viennent d'appeler, ils ne viennent pas. On fait quoi ?", p["site"], p["nom"], r, a


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    for f in SORTIE.glob("*.webm"):
        f.unlink()
    T3, d3, f3 = phrases("s3")
    T3b, d3b, f3b = phrases("s3bis")
    T4, d4, f4 = phrases("s4")

    with sync_playwright() as pw:
        nav = pw.chromium.launch(channel="chrome", headless=True)
        ctx = nav.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1, locale="fr-FR",
                              record_video_dir=str(SORTIE), record_video_size={"width": 1920, "height": 1080})
        ctx.add_init_script(CURSEUR)
        ctx.add_init_script("document.addEventListener('DOMContentLoaded', () => { document.documentElement.style.zoom = '1.45'; });")
        page = ctx.new_page()
        t = Tournage(page)
        page.goto(LIEN, wait_until="load", timeout=90_000)
        page.evaluate("localStorage.removeItem('rubalise.session')")
        page.reload(wait_until="load", timeout=90_000)
        page.wait_for_selector("#calculer", timeout=60_000)
        time.sleep(2.0)
        t.note("page chargée, session neuve")
        page.mouse.move(960, 540); t.souris = (960, 540)

        # ---- le plan : le bouton n'est actif qu'une fois l'état de la session lu
        page.wait_for_function("() => !document.getElementById('calculer').disabled && document.getElementById('course-travail').hidden", timeout=120_000)
        time.sleep(0.5)
        for essai in range(3):
            t.cliquer("#calculer", 0.8)
            time.sleep(2.0)
            if page.evaluate("document.querySelectorAll('#fil .msg.orga').length") > 0:
                break
            t.note(f"le clic n'a pas pris, nouvel essai {essai + 2}")
        t.note("calcul du plan demandé")
        page.wait_for_function("() => document.querySelectorAll('.frise .pt.ok, .frise .pt.partiel, .frise .pt.critique').length > 0 && document.getElementById('course-travail').hidden",
                               timeout=420_000)
        time.sleep(1.5)
        session = page.evaluate("localStorage.getItem('rubalise.session')")
        t.note(f"plan affiché, session {session[9:17]}")
        e = etat(session)
        message, site, poste, r, a = absents(e)
        t.note(f"absents choisis : {r} (responsable) et {a}, {site}")

        # ---- scène 3 : la course, Blancsex, la barre rouge, le panneau
        t.glisser(960, 300, 0.5)
        t0 = time.time(); t.segments["s3"] = [t.maintenant()]
        t.jusqua(d3[1], t0); x0, _ = t.centre('.frise .pt[data-point="Morgins"]'); x1, y1 = t.centre('.frise .pt[data-point="Le Bouveret"]')
        t.glisser(x0, y1, 0.5); t.glisser(x1, y1, max(1.5, f3[1] - d3[1] - 1.2))
        t.jusqua(d3[2], t0); t.glisser(700, 720, 1.0); t.glisser(1200, 820, 1.4)
        t.jusqua(d3[3] + 0.4, t0); t.cliquer('.frise .pt[data-point="Chalet de Blancsex"]', 0.9); t.note("clic Blancsex")
        t.jusqua(d3[5] + 0.3, t0); page.wait_for_selector(".barre.critique", timeout=10_000); t.aller(".barre.critique", 1.0)
        t.jusqua(d3[6] + 0.5, t0); t.cliquer(".barre.critique", 0.3); t.note("clic barre rouge")
        t.jusqua(d3[7] + 0.4, t0); t.defiler_vers("#detail .viol.proche"); t.aller("#detail .viol.proche", 1.0)
        t.jusqua(d3[8], t0); t.aller("#detail .viol.proche li:nth-child(1)", 0.6)
        t.jusqua(d3[9], t0); t.aller("#detail .viol.proche li:nth-child(3)", 0.8)
        t.jusqua(T3, t0); t.segments["s3"].append(t.maintenant()); t.note("fin scène 3")

        # ---- scène 3 bis : la conversation, la relecture du contradicteur
        page.evaluate("""() => { const f = document.getElementById('fil'); const ms = [...f.querySelectorAll('.msg.agent .corps')];
            const m = ms.filter(x => /ontradict/i.test(x.textContent)).pop() || ms.pop(); if (m) m.id = 'msg-contradicteur'; }""")
        t.cliquer("#toute-la-course", 0.7)
        t0 = time.time(); t.segments["s3bis"] = [t.maintenant()]
        t.jusqua(0.3, t0); t.glisser(*t.centre("#fil"), 1.2)
        t.jusqua(d3b[1], t0); t.defiler_vers("#msg-contradicteur", "start")
        t.jusqua(d3b[2], t0); page.evaluate("() => { const m = document.getElementById('msg-contradicteur'); if (m) { const i = [...m.querySelectorAll('p,li')].find(x => /accompagn|trois|3 personne/i.test(x.textContent)); if (i) i.scrollIntoView({behavior:'smooth', block:'center'}); } }")
        t.jusqua(d3b[3], t0); page.evaluate("() => document.getElementById('fil').scrollBy({top: 160, behavior: 'smooth'})")
        t.jusqua(T3b, t0); t.segments["s3bis"].append(t.maintenant()); t.note("fin scène 3 bis")

        # ---- scène 4, partie A : le message du jour J
        t0 = time.time(); t.segments["s4a"] = [t.maintenant()]
        t.jusqua(0.4, t0); t.cliquer("#entree", 1.0)
        t.jusqua(d4[1], t0); page.keyboard.type(message, delay=26); t.note("message tapé")
        t.jusqua(max(f4[2] - 0.6, d4[2]), t0); t.cliquer("#envoyer", 0.5); t.note("message envoyé")
        t.jusqua(d4[3], t0); t.segments["s4a"].append(t.maintenant()); t.note("fin scène 4 A, attente de l'agent")

        page.wait_for_function("() => !document.querySelector('.msg.agent.pending') && document.getElementById('course-travail').hidden && document.querySelectorAll('.msg.agent').length >= 2",
                               timeout=480_000)
        time.sleep(1.0); t.note("réponse reçue")
        page.evaluate("() => { const ms = document.querySelectorAll('#fil .msg.agent'); ms[ms.length-1].id = 'msg-jourj'; ms[ms.length-1].scrollIntoView({block:'start'}); }")

        # ---- scène 4, partie B : la réponse
        t0 = time.time(); t.segments["s4b"] = [t.maintenant()]
        t.jusqua(0.5, t0); t.glisser(*t.centre("#msg-jourj"), 1.0)
        reste = T4 - d4[3]
        for k in range(1, 5):
            t.jusqua(reste * k / 5, t0); page.evaluate("() => document.getElementById('fil').scrollBy({top: 220, behavior: 'smooth'})")
        t.jusqua(reste, t0); t.segments["s4b"].append(t.maintenant()); t.note("fin scène 4 B")

        # ---- la capture des mesures pour la scène 5
        page.click('nav.onglets button[data-vue="archi"]'); time.sleep(0.8)
        page.evaluate("() => { const h = [...document.querySelectorAll('#archi h3')].find(x => /measured/i.test(x.textContent)); if (h) { h.nextElementSibling.id = 'tbl-mesures'; h.scrollIntoView(); } }")
        page.locator("#tbl-mesures").screenshot(path=str(SORTIE / "mesures.png"), scale="device")
        t.note("mesures capturées")

        chemin = page.video.path()
        ctx.close(); nav.close()
        Path(chemin).replace(SORTIE / "site.webm")

    (SORTIE / "evenements.json").write_text(json.dumps({"video": "site.webm", "segments": t.segments, "message": message,
                                                         "absents": [r, a], "poste": poste, "site": site, "session": session,
                                                         "journal": t.journal}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("segments :", {k: [round(a, 1), round(b, 1)] for k, (a, b) in t.segments.items()})


if __name__ == "__main__":
    main()
