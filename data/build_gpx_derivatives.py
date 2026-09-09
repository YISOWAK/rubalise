"""Dérive du GPX de la course :
 - parcours.gpx : trace nettoyée (lat, lon, ele uniquement, pas d'horodatage ni de données perso)
 - parcours_profil.csv : profil tous les 100 m (km, altitude, D+ et D- cumulés)
 - points_de_passage_geo.csv : coordonnées des postes du roadbook, retrouvées sur la trace
   par la distance cumulée, avec l'écart d'altitude par rapport au roadbook comme contrôle
 - passages_reference.csv : temps de passage réels d'un coureur (l'auteur de la trace)
   à chaque poste, comparés à la fenêtre premier / dernier du roadbook

Source : enregistrement Strava d'un coureur du SwissPeaks Marathon 2025.
"""
from __future__ import annotations

import csv
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta, timezone

SRC = next((c for c in ("source/swisspeaks-marathon-2025.gpx", "../../sources-privees/swisspeaks-marathon-2025.gpx") if Path(c).exists()), "source/swisspeaks-marathon-2025.gpx")
NS = "http://www.topografix.com/GPX/1/1"
TZ = timezone(timedelta(hours=2))  # heure d'été Suisse


def hav(a, b):
    R = 6371000
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


root = ET.parse(SRC).getroot()
pts = []
for p in root.iter(f"{{{NS}}}trkpt"):
    ele = p.find(f"{{{NS}}}ele")
    tm = p.find(f"{{{NS}}}time")
    pts.append((float(p.get("lat")), float(p.get("lon")),
                float(ele.text) if ele is not None else None,
                datetime.fromisoformat(tm.text.replace("Z", "+00:00")).astimezone(TZ) if tm is not None else None))

# distance cumulée et dénivelé lissé (fenêtre de 5 points pour limiter le bruit GPS)
cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + hav(pts[i - 1][:2], pts[i][:2]))
eles = [p[2] for p in pts]
smooth = [sum(eles[max(0, i - 2):i + 3]) / len(eles[max(0, i - 2):i + 3]) for i in range(len(eles))]
dplus = [0.0]
dmoins = [0.0]
for i in range(1, len(pts)):
    d = smooth[i] - smooth[i - 1]
    dplus.append(dplus[-1] + max(d, 0))
    dmoins.append(dmoins[-1] + max(-d, 0))

# 1. trace nettoyée
gpx = ET.Element("gpx", version="1.1", creator="agents-for-humans-dataset", xmlns=NS)
meta = ET.SubElement(gpx, "metadata")
ET.SubElement(meta, "name").text = "SwissPeaks Marathon 2025, trace nettoyée"
trk = ET.SubElement(gpx, "trk")
ET.SubElement(trk, "name").text = "SwissPeaks Marathon 2025"
seg = ET.SubElement(trk, "trkseg")
for lat, lon, ele, _ in pts[::3]:  # 1 point sur 3 suffit pour la démo
    tp = ET.SubElement(seg, "trkpt", lat=f"{lat:.6f}", lon=f"{lon:.6f}")
    ET.SubElement(tp, "ele").text = f"{ele:.1f}"
ET.ElementTree(gpx).write("parcours.gpx", encoding="utf-8", xml_declaration=True)

# 2. profil tous les 100 m
with open("parcours_profil.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["km", "altitude_m", "dplus_cumul_m", "dmoins_cumul_m", "lat", "lon"])
    target = 0.0
    for i in range(len(pts)):
        if cum[i] >= target:
            w.writerow([f"{cum[i] / 1000:.1f}", f"{smooth[i]:.0f}", f"{dplus[i]:.0f}", f"{dmoins[i]:.0f}",
                        f"{pts[i][0]:.5f}", f"{pts[i][1]:.5f}"])
            target += 100

# 3. postes géolocalisés + 4. passages réels
course = json.load(open("course_marathon.json", encoding="utf-8"))
scale = cum[-1] / (course["distance_km"] * 1000)  # la trace fait un peu plus que 46 km officiels
geo_rows, pass_rows = [], []
t0 = pts[0][3]
for cp in course["points_de_passage"]:
    target = cp["km"] * 1000 * scale
    # parmi les points proches en distance, on prend celui dont l'altitude colle le mieux au roadbook
    window = [i for i in range(len(pts)) if abs(cum[i] - target) < 800]
    i = min(window, key=lambda k: abs(smooth[k] - cp["altitude_m"]) + abs(cum[k] - target) / 50)
    if cp["km"] == 0:
        i = 0
    if cp["km"] == course["distance_km"]:
        i = len(pts) - 1
    lat, lon, _, tm = pts[i]
    geo_rows.append({"nom": cp["nom"], "km_roadbook": cp["km"], "km_trace": f"{cum[i] / 1000:.1f}",
                     "lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "altitude_roadbook_m": cp["altitude_m"],
                     "altitude_trace_m": f"{smooth[i]:.0f}", "dplus_cumul_trace_m": f"{dplus[i]:.0f}"})
    premier = datetime.fromisoformat(cp["premier"]).replace(tzinfo=TZ)
    dernier = datetime.fromisoformat(cp["dernier"]).replace(tzinfo=TZ)
    pass_rows.append({"nom": cp["nom"], "km": cp["km"],
                      "premier_roadbook": premier.strftime("%H:%M"), "dernier_roadbook": dernier.strftime("%H:%M"),
                      "passage_coureur_reference": tm.strftime("%H:%M"),
                      "temps_course_reference": str(tm - t0).split(".")[0],
                      "position_dans_la_fenetre": f"{(tm - premier) / (dernier - premier):.0%}" if dernier > premier else "depart",
                      "dans_la_fenetre": premier <= tm <= dernier})

for name, rows in [("points_de_passage_geo.csv", geo_rows), ("passages_reference.csv", pass_rows)]:
    with open(name, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)

print(f"trace : {cum[-1] / 1000:.1f} km, D+ lissé {dplus[-1]:.0f} m, D- {dmoins[-1]:.0f} m, "
      f"départ {t0.strftime('%H:%M')} arrivée {pts[-1][3].strftime('%H:%M')} (durée {str(pts[-1][3] - t0).split('.')[0]})")
for r in geo_rows:
    print(f"  {r['nom']:<20} km rb {r['km_roadbook']:>2} / trace {r['km_trace']:>4}  alt rb {r['altitude_roadbook_m']} / trace {r['altitude_trace_m']}")
for r in pass_rows:
    print(f"  {r['nom']:<20} {r['premier_roadbook']} < {r['passage_coureur_reference']} < {r['dernier_roadbook']}  ({r['position_dans_la_fenetre']}) ok={r['dans_la_fenetre']}")
