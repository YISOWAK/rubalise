# Avancement

## 2026-09-06
- Solveur OR-Tools écrit et validé sur le jeu SwissPeaks : `solveur/solveur.py`, 50 créneaux × 75 bénévoles, optimal en 8 s. Arbitrages appliqués (plan 07) : effectif min souple (1000), responsable dur avec relance relâchée (10 000) si infaisable, refus de nuit = dispo, charge : 4 points par heure au-delà de 8 h, « pas avec X » dur (à coder), binômes +2.
- Découpe des postes longs en créneaux ajoutée au générateur de données (au-delà de 6 h).
- Outil « Traduire les dispos » écrit : `outils/traduire_dispos.py`, schéma JSON fermé, Claude Opus 4.6 sur Bedrock. Score sur 75 lignes : dispos 74/75, compétences 74/75, nuit 74/75, accompagnants, responsable, binôme 75/75. 36 questions à l'orga, 141 remarques étiquetées. Sortie : `outils/sortie/benevoles_traduits.json`.
- Formulaire en texte libre généré depuis le jeu de données : `data/formulaire_benevoles.csv` (entrée réelle du produit).
- AWS : budget 30 $ avec alertes créé. Claude 5 non disponible sur ce compte Bedrock (restriction de compte) : on utilise Opus 4.6 / Sonnet 4.6 / Haiku 4.5. Quota bas : appels séquentiels avec réessais.

## 2026-09-06, soir
- Vérificateur de règles : `outils/verifier.py`, 9 bloquantes (B1-B9) + 11 alertes (A1-A11), avec doublons par téléphone et remarques du traducteur. Sur le plan de référence : 15 bloquantes, 160 alertes ; il attrape Michel le coureur, les deux mineurs après 22h, les deux Pierre-Alain.
- Solveur : règles dures mineur (pas de poste route, pas après 22h), « pas avec X » dur, plan figé avec coûts de changement (20 prévenu, 100 en poste, 10 par ajout), créneaux terminés figés, options `--benevoles --plan-fige --absents --heure`.
- Pont formulaire -> solveur : `outils/pont.py`. Fusion des doublons, binômes retrouvés par nom, hypothèses notées, questions listées. 75 lignes -> 74 bénévoles, 47 décisions, 72 questions.
- Chaîne complète sans agent : formulaire texte libre -> traduction (Opus 4.6) -> pont -> solveur -> vérificateur. Plan optimal en 1,7 s, 13 bloquantes (toutes des trous de personnel, aucune erreur d'affectation).
- Batterie de scénarios : `solveur/scenarios.py` -> `solveur/sortie/scenarios.md` (10 scénarios : moins de monde, sans PSC1, sans nuit, course plus grosse, 4 incidents de jour J avec nombre de personnes déplacées).
- Traducteur : champ `editions_precedentes` ajouté, appels séquentiels avec reprise (quota Bedrock bas).

## 2026-09-06, nuit : serveur MCP
- `serveur/serveur_course.py` : 13 outils (etat_resume, charger_donnees, traduire_formulaire, resoudre, verifier, plan_par_poste, plan_par_personne, regles_lister, regle_modifier, deroger, journaliser, journal_lire, publier). État en JSON dans `etat/` (config, regles, plan, plan_publie, journal, violations, envoyes/). Transport stdio par défaut, `--http` pour AgentCore.
- Règles par défaut dans `serveur/regles_defaut.json` (B1-B9, A1-A11, paramètres modifiables : heure_limite_mineur, journee_longue_h).
- `serveur/test_serveur.py` : test par le vrai protocole (sous-processus stdio), scénario complet sans LLM : charger, résoudre, vérifier, lire, déroger, modifier une règle, publier (73 messages simulés), résoudre jour J avec 2 absents à 11h (0,13 s), journal.
- Attention : Strands épingle `mcp` en 1.x (FastMCP) ; le serveur gère les deux versions.

## 2026-09-09 : les agents
- `agents/orchestrateur.py` : orchestrateur Strands (Sonnet 4.6 sur Bedrock) branché sur le serveur MCP par stdio ; contradicteur (Opus 4.6, contexte vierge, outils en lecture seule) appelé automatiquement dans `calculer_plan` (résoudre + vérifier + relecture). Garde-fou dur : `publier`, `deroger`, `regle_modifier` demandent confirmation dans le terminal avant exécution.
- Prompts lisibles dans `agents/prompts/` (orchestrateur.md, contradicteur.md). Mode `--script fichier --oui` pour rejouer un dialogue sans taper. Premier dialogue complet réussi (`agents/demo_log.txt`) : état, plan avec priorités, Taney, dérogation, publication, jour J à 11h avec deux absents.
- Le contradicteur a vu seul : la chaîne serre-file cassée, la livraison 4x4 vide qui bloque 4 postes en cascade, une mineure déclarée responsable, les 3 accompagnants de Fabien comptés sur 3 postes.

## 2026-09-09, suite : la phase 1 complète
- `outils/lire_roadbook.py` : pages PDF en images -> fiche de course JSON (Opus 4.6, schéma fermé, doutes listés). Sur le roadbook SwissPeaks (pages 14, 18, 22-24) : 6 points de passage exacts (km, altitude, horaires, barrières), dossards et navettes trouvés ; seules erreurs : deux icônes de service confondues (bus/valise, repas chaud), signalées comme doutes.
- `gabarits/trail.json` + `outils/construire_postes.py` : fiche de course -> 60 créneaux (ravitos, pointages, barrières, arrivée, serre-files par tronçon, dossards, navettes, PC, réserve volante, livraisons, rangement), découpe et union des courses partagées. Un autre événement = un autre gabarit.
- Chaîne complète depuis le PDF : roadbook -> fiche -> postes -> formulaire traduit -> solveur (0,4 s) -> vérificateur.
- Serveur MCP : 16 outils (ajout de lire_roadbook, corriger_course, construire_postes). Solveur et serveur acceptent un fichier postes alternatif.

## 2026-09-09, soir : préparation AgentCore
- `agents/agentcore_app.py` : point d'entrée AgentCore Runtime (HTTP /invocations), une session = un dossier d'état + un orchestrateur + son serveur MCP ; garde-fou hébergé = confirmation explicite dans le message de l'orga, vérifiée par le code. Testé en local.
- Outil de déploiement : le starter toolkit Python est obsolète ; on utilise l'AgentCore CLI (npm `@aws/agentcore`, déploiement par CDK). Projet configuré (`agentcore/agentcore.json`), runtime `orchestrateur` en mode CodeZip Python 3.12 (pas de Docker sur la machine). `agentcore package` produit un zip de 108 Mo (ortools, pymupdf, numpy).
- Fichiers lourds sortis du projet (`../sources-privees/` : roadbook PDF, GPX brut). `pyproject.toml` ajouté (uv).
- Bloquant : le déploiement demande une identité admin. Un profil AWS admin séparé a été configuré sur la machine de développement, jamais dans le dépôt.

## 2026-09-09, nuit : dépôt public et vidéo
- README en anglais (nom de projet proposé : Rubalise), licence MIT, `.gitignore`, diagramme exporté en `docs/architecture.svg`, `pyproject.toml`.
- Script de la vidéo (`plan/08-video.md`) : découpage minute par minute, messages à taper, captures à préparer.
- Déploiement AgentCore réussi (CDK, zip 108 Mo, 5 minutes) : runtime `benevolestrail_orchestrateur-Oj5XvYFzfG`, région us-east-1, stack CloudFormation `AgentCore-benevolestrail-default`. Testé : « Où en est-on ? » puis « Calcule un plan » dans la même session, solveur + vérificateur + contradicteur exécutés dans le cloud. Appel : `AWS_PROFILE=admin agentcore invoke "..."` (ou `--session-id` pour continuer).

## 2026-09-09, nuit : page de démonstration en ligne
- `web/index.html` (style du Cockpit Prospection : Roboto, clair, sobre, sans emoji), `web/lambda_proxy.py` (relais en deux temps : POST /invoke lance, GET /result interroge ; résultats dans un bucket S3 purgé à 2 jours), `web/deployer.py` (rôle IAM, Lambda, API HTTP ; l'URL Lambda publique est bloquée sur ce compte, d'où l'API Gateway).
- Piège résolu : le client boto3 coupait à 60 s et relançait sur une session occupée ; délai 840 s et zéro réessai.
- Testé : plan complet en 83 s, question de suivi en 4 s dans la même session. Lien de démo avec clé dans `web/lien_demo.txt` (exclu du dépôt).

## Prochaines étapes
2. Outil « Feuilles de route » (LLM) à la place des messages simulés bruts.
3. Réduire le bruit des alertes A8 (remarques « autre » et éditions) avant de les donner au contradicteur.
4. AgentCore, README avec les scores, vidéo.
