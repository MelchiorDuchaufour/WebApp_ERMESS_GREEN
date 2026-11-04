# Webapp ERMESS Green (WP3.4)

Outil de calcul et plateforme de suivi des serres de démonstration
(COPIL n°3, diapositive 38 : versions base nov. 2026, suivi juin 2027,
contrôle nov. 2027, fonctionnement juin 2028).

| Dossier | Contenu |
|---|---|
| `app/` | **Version de travail.** Accueil carte, vue 3D de la serre avec onglets (Suivi, Potentiel PV, Énergie, Rénovation, Contrôle), visualisation Blender en direct |
| `reserve_v1/` | **Version de réserve figée** (état du 03/11/2026 avant les onglets et Blender). Pour revenir dessus en cas de bug |
| `Plan Sigrow.png` | Plan d'implantation des 15 capteurs du central 15353 |
| `170491_3_Verbale COPIL n.3(1).pptx` | Compte rendu du COPIL n°3 (cahier des charges de la webapp, p. 38) |

## Lancer
```bash
cd ~/doctorat/webapp/app && python3 serveur_3d.py                       # http://localhost:8766
cd ~/doctorat/webapp/reserve_v1 && python3 serveur_3d.py --port 8767    # réserve, http://localhost:8767
```
Les clés Sigrow sont dans `.cles_sigrow` de chaque dossier (chmod 600, **ne pas partager**).
Le dossier d'origine `~/doctorat/fresh/pao_reproduction/bocage/webapp3d/` existe toujours
mais n'est plus la version suivie.

## Blender en direct (première version, locale)
```bash
cd ~/doctorat/webapp/app
blender blender/serre_rigerie_detail.blend --python blender/blender_live.py
```
Vue 3D > barre latérale (N) > onglet « Serre live » > Démarrer le direct.
Écrans par nef, ouvrants de faîtage, chauffage et capteurs colorés, rafraîchis
depuis le serveur (onglet Contrôle de la webapp) ou pilotés à la main.
