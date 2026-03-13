# Dessinator

Un outil de dessin moderne inspiré de Microsoft Paint, écrit en Python pour Linux.

## Fonctionnalités

### Outils de dessin
| Icône | Outil | Description |
|-------|-------|-------------|
| ✏ | Crayon | Dessin pixel par pixel (algorithme de Bresenham) |
| 🖌 | Pinceau | Pinceau avec tailles et formes configurables (1/3/5/8 px, rond/carré) |
| ⌫ | Gomme | Efface vers la couleur d'arrière-plan (8/16/32 px) |
| ✦ | Aérographe | Spray avec rayon et densité configurables |
| ▣ | Remplissage | Seau de remplissage performant (flood-fill via Pillow) |
| ⊕ | Pipette | Sélecteur de couleur depuis le canvas |
| A | Texte | Insertion de texte rasterisé avec choix de police |
| ⬚ | Sélection | Sélection rectangulaire (copier/couper/coller) |
| / | Ligne | Trait droit (Shift = horizontal/vertical) |
| ▭ | Rectangle | Contour, rempli ou les deux (épaisseur configurable) |
| ○ | Ellipse | Ellipse / cercle (Shift = cercle parfait) |
| ⬡ | Polygone | Polygone libre (clic droit = fermer la forme) |

### Autres fonctionnalités
- **Zoom** : 10 % à 800 % (9 niveaux) avec grille pixel optionnelle (activée ≥ 200 %)
- **Annulation/Rétablissement** : 3 niveaux (Ctrl+Z / Ctrl+Y), pile circulaire
- **Palette** : 28 couleurs inspirées de Paint, personnalisable et sauvegardable en JSON
- **Formats** : lecture et écriture PNG / JPEG uniquement (via Pillow)
- **Opérations image** : inversion des couleurs, retournement horizontal/vertical, redimensionnement
- **Copier / Couper / Coller** sur la sélection rectangulaire
- **Preview en direct** pour les formes géométriques (ligne, rectangle, ellipse, polygone)
- **Shift** pour contraindre les formes (carré parfait, cercle parfait, ligne droite)

## Installation

### Prérequis

- Python 3.11+
- Linux (Ubuntu 22.04+ recommandé)

### Dépendances Python

```bash
pip install PyQt6 Pillow
```

### Bibliothèques système (si absentes)

```bash
sudo apt install libegl1 libxcb-cursor0
```

## Lancement

```bash
cd paint95
python main.py

# Ouvrir directement un fichier image :
python main.py monimage.png
```

## Raccourcis clavier

| Action | Raccourci |
|--------|-----------|
| Nouveau | Ctrl+N |
| Ouvrir | Ctrl+O |
| Enregistrer | Ctrl+S |
| Enregistrer sous | Ctrl+Shift+S |
| Annuler | Ctrl+Z |
| Rétablir | Ctrl+Y |
| Copier | Ctrl+C |
| Couper | Ctrl+X |
| Coller | Ctrl+V |
| Supprimer sélection | Suppr |
| Zoom + | Ctrl++ |
| Zoom - | Ctrl+- |
| Grille pixels | Ctrl+G |
| Quitter | Ctrl+Q |

### Interactions souris
- **Clic gauche** : dessiner / sélectionner la couleur avant-plan
- **Clic droit** : dessiner avec l'arrière-plan / sélectionner la couleur arrière-plan / fermer un polygone
- **Shift** maintenu : contrainte géométrique (carré, cercle, ligne droite)
- **Échap** : annuler la sélection

## Architecture

```
paint95/
├── main.py                    # Point d'entrée (supporte fichier en argument)
├── canvas/
│   └── canvas_widget.py      # Widget de dessin (QImage + zoom + preview shapes)
├── tools/
│   ├── base_tool.py          # Classe abstraite de base
│   ├── pencil.py             # Crayon (Bresenham)
│   ├── brush.py              # Pinceau multi-tailles
│   ├── eraser.py             # Gomme
│   ├── spray.py              # Aérographe
│   ├── fill.py               # Remplissage (Pillow ImageDraw.floodfill)
│   ├── pipette.py            # Pipette / color picker
│   ├── text_tool.py          # Texte rasterisé (Qt FontDialog)
│   ├── selection_tool.py     # Sélection rectangulaire
│   └── shapes.py             # Ligne, Rectangle, Ellipse, Polygone
├── ui/
│   ├── main_window.py        # Fenêtre principale, menus, raccourcis
│   ├── toolbar.py            # Boîte à outils + panneau d'options
│   └── palette.py            # Palette couleurs (FG/BG + 28 swatches)
├── color/
│   └── palette_manager.py    # Gestion palette et persistance JSON
├── file_io/
│   ├── image_loader.py       # Chargement PNG/JPEG → QImage (ARGB32)
│   └── image_saver.py        # Sauvegarde QImage → PNG/JPEG via Pillow
└── history/
    └── undo_manager.py       # Stack circulaire d'annulation (3 niveaux max)
```

## Technologies

| Bibliothèque | Usage |
|---|---|
| **PyQt6** | Interface graphique, canvas QImage, rendu, dialogs |
| **Pillow** | Flood-fill performant, export PNG/JPEG |
| **Python 3.11+** | Type hints modernes, `from __future__ import annotations` |

## Spécifications techniques

- Canvas raster RGB/ARGB en mémoire (`QImage.Format_ARGB32`)
- Dessin direct sur QImage via `QPainter` (formes) ou `setPixelColor` (pixel art)
- Algorithme de Bresenham pour le crayon
- Flood-fill optimisé via `PIL.ImageDraw.floodfill` (C natif)
- Preview des formes par snapshot+restore (sans double-buffer séparé)
- Consommation mémoire maîtrisée : 3 snapshots undo maximum en RAM
- Canvas supporté jusqu'à 4096×4096 px
