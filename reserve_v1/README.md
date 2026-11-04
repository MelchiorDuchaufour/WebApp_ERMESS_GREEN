# webapp3d : capteurs Sigrow en 3D dans la serre Rigerie

Vue 3D en continu des capteurs du Bocage, placés sur la maquette Blender de la
serre Rigerie (= « Grande serre »), colorés par leur dernière mesure.
Seulement les points de mesure : pas de champ interpolé.

```bash
cd bocage/webapp3d
source ../env.sh                 # clé Bocage
python3 serveur_3d.py            # port 8766 -> http://localhost:8766
python3 serveur_3d.py --hote 0.0.0.0   # accessible depuis le réseau local
```

**Accueil** (`/`) : carte en relief de la zone franco-italienne (Alcotra), avec la
frontière en rouge et une mini-serre par site, placée d'après le champ `lieu` de
`sites.json`. Une serre grossit au survol et ouvre sa vue 3D au clic.
Le relief (tuiles Terrarium, AWS) et les frontières (Natural Earth via world-atlas)
sont chargés par le navigateur : il faut un accès Internet.

**Vue d'un site** : `/serre#bocage`.

Un site = une serre, dans `sites.json` : nom, `sources` (un ou plusieurs centrals,
chacun avec le nom de sa clé et un filtre sur le nom des capteurs), maquette `.glb`
facultative, fichier de positions, `lieu` (ville, pays, lat/lon pour la carte).
Un site sans source apparaît sur la carte (« pas encore de capteurs ») sans être
cliquable. Les clés viennent de l'environnement ou de `.cles_sigrow`
(`NOM=clé`, chmod 600, **ne pas partager**).

| Site | Centrals | Capteurs |
|---|---|---|
| `bocage` : Serre Rigerie, Chambéry | 28896 (PHENIX, filtre « Bocage ») + 15353 | 7 + 15 = 22 : 9 Air+, 2 AirPro+ (CO₂), 7 Pixel+, 4 SoilPro+ |
| `savona` : site pilote, Savona | aucun | carte seulement |

Logos : liens dans `logos/liens.js` (ERMESS Green → page projet du LOCIE ; le lien
Agrithermic est vide, à compléter).

| Fichier | Rôle |
|---|---|
| `serveur_3d.py` | Serveur (stdlib + requests). Tire toutes les variables, y compris CO₂ et sol |
| `accueil.html` | Carte d'accueil France–Italie |
| `index.html` | Vue d'un site : page Three.js + Plotly (CDN) : scène, liste, détail 48 h, mode édition |
| `sites.json`, `.cles_sigrow` | Sites suivis ; clés locales |
| `placer_selon_plan.py` | Place les 15 capteurs du central 15353 d'après `~/doctorat/webapp/Plan Sigrow.png` (détection des symboles, calage sur les tablettes, superposition = hauteurs différentes) |
| `logos/` | Logos ERMESS Green et partenaires (copiés de `~/doctorat/rapport`, Interreg depuis le poster JNES) |
| `serre.glb` | Maquette exportée. Régénérer : `blender -b ../plan_rigerie/serre_rigerie_detail.blend --python export_glb.py` |
| `capteurs_positions.json` | Positions des 22 capteurs dans le repère du plan Rigerie (m). Écrit par la page et par `placer_selon_plan.py` |

## Points à savoir
- Formes : Air+ = sphère, AirPro+ = losange, Pixel+ = cube, SoilPro+ = disque.
- **Central Bocage** : depuis l'automne 2026, les capteurs Bocage remontent via **PHENIX 28896**
  (37824 renvoie une erreur 500). On ne suit que les capteurs dont le nom contient
  « Bocage » (champ `filtre` de `sites.json`).
- **Positions provisoires** (`a_valider`) : déduites des noms Sigrow et de
  `greenhouse_map.py`. Le Nord n'est pas indiqué sur le plan 2012. Corriger avec
  « Placer les capteurs » : choisir un capteur, cliquer dans la scène pour (x, y),
  régler z, puis « Enregistrer ».
- Un capteur sans mesure depuis plus de 30 min apparaît en gris (« hors ligne »).
- Si l'API Sigrow ne répond pas, la page garde les dernières valeurs et l'indique
  dans le bandeau.
- Le repère : x le long du mur haut, y vers le mur haut, z vertical. La page
  convertit vers le repère Y-haut de glTF : (x, y, z) → (x, z, −y).

## Capteurs du central 15353 (plan Sigrow)
- Placés par `placer_selon_plan.py`. Le schéma n'est pas à l'échelle en hauteur
  d'image : le script cale x par rang sur les bords des tablettes et y par morceaux
  entre les bords de rangs.
- Deux symboles à moins de 55 px sur le schéma (moins de 2 symboles) sont supposés
  **superposés** : même (x, y), celui du capteur le plus bas, et au moins 0,4 m
  d'écart en z. Hauteurs de base : SoilPro+ 0,90 m (substrat sur tablette à 0,80 m),
  Pixel+ 1,10 m, Air+ 1,60 m, AirPro+ 2,20 m.
- Le schéma ne donne pas les identifiants : ils sont attribués par type, dans l'ordre
  de lecture du plan et par numéro croissant. **À vérifier sur place**, puis corriger
  dans la page (mode édition) ou en relançant le script.
- Le carré orange en haut à droite du schéma n'est pas dans la légende (central ?) : non placé.
