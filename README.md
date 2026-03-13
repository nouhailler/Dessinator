# Dessinator

Un outil de dessin moderne inspiré de Microsoft Paint, écrit en Python 3 avec PyQt6.

## Fonctionnalités

- **Outils de dessin** : Crayon (Bresenham), Pinceau (rond/carré, 4 tailles), Gomme, Aérographe, Seau de remplissage (scanline flood fill), Pipette
- **Formes** : Ligne, Rectangle, Ellipse, Polygone, Courbe de Bézier
- **Texte** : Insertion de texte rasterisé avec sélection de police
- **Sélection** : Rectangle de sélection (copier/couper/coller/supprimer)
- **Zoom** : 10 % à 800 %, grille pixel visible à partir de ×4
- **Historique** : 3 niveaux d'annulation (Ctrl+Z / Ctrl+Y)
- **Palette** : 28 couleurs style Paint 95, personnalisable et sauvegardable (JSON)
- **Formats** : Lecture/écriture PNG et JPEG (via Pillow)
- **Opérations image** : Inverser les couleurs, retourner (H/V), redimensionner

## Installation

```bash
pip install -r requirements.txt
```

### Dépendances

| Paquet   | Rôle                        |
|----------|-----------------------------|
| PyQt6    | Interface graphique (Qt 6)  |
| Pillow   | Lecture/écriture PNG/JPEG   |
| numpy    | Optionnel (performances)    |

## Lancement

```bash
python main.py
```

ou

```bash
python -m paint95.main
```

## Architecture

```
paint95/
├── main.py                  # Point d'entrée
├── ui/
│   ├── main_window.py       # Fenêtre principale + menus
│   ├── toolbar.py           # Barre d'outils verticale
│   ├── palette.py           # Palette de couleurs
│   └── statusbar.py         # Barre d'état
├── canvas/
│   ├── canvas_widget.py     # Widget de dessin (zoom, grid, événements)
│   ├── drawing_engine.py    # Moteur de dessin + buffer QImage
│   └── selection_manager.py # Gestion des sélections
├── tools/
│   ├── base.py              # Classe abstraite outil
│   ├── pencil.py            # Crayon (algorithme de Bresenham)
│   ├── brush.py             # Pinceau
│   ├── eraser.py            # Gomme
│   ├── spray.py             # Aérographe
│   ├── fill.py              # Seau (scanline flood fill)
│   ├── pipette.py           # Pipette couleur
│   └── shapes.py            # Ligne, Rectangle, Ellipse, Polygone, Courbe, Texte
├── io/
│   ├── image_loader.py      # Chargement PNG/JPEG via Pillow
│   └── image_saver.py       # Sauvegarde PNG/JPEG via Pillow
├── color/
│   ├── palette_manager.py   # Gestion palette + persistance JSON
│   └── color_dialog.py      # Sélecteur de couleur
└── history/
    └── undo_manager.py      # Pile circulaire d'annulation (3 niveaux)
```

## Raccourcis clavier

| Action             | Raccourci      |
|--------------------|----------------|
| Nouveau            | Ctrl+N         |
| Ouvrir             | Ctrl+O         |
| Enregistrer        | Ctrl+S         |
| Enregistrer sous   | Ctrl+Shift+S   |
| Annuler            | Ctrl+Z         |
| Rétablir           | Ctrl+Y         |
| Copier             | Ctrl+C         |
| Couper             | Ctrl+X         |
| Coller             | Ctrl+V         |
| Supprimer          | Suppr          |
| Tout sélectionner  | Ctrl+A         |
| Zoom +             | Ctrl++         |
| Zoom -             | Ctrl+-         |
| Zoom 100%          | Ctrl+0         |
| Grille pixel       | Ctrl+G         |
| Quitter            | Ctrl+Q         |

### Sélection rapide d'outil (touche unique)

| Touche | Outil       |
|--------|-------------|
| P      | Crayon      |
| B      | Pinceau     |
| E      | Gomme       |
| A      | Aérographe  |
| F      | Remplissage |
| I      | Pipette     |
| L      | Ligne       |
| R      | Rectangle   |
| O      | Ellipse     |
| G      | Polygone    |
| U      | Courbe      |
| X      | Texte       |
| S      | Sél. rect.  |
| W      | Sél. libre  |

## Utilisation du polygone

1. Cliquez pour ajouter chaque sommet
2. Double-cliquez pour fermer et valider le polygone

## Utilisation de la courbe

1. Faites un cliquer-glisser pour définir le début et la fin
2. Cliquez une seconde fois pour placer le point de contrôle

## Palette personnalisée

La palette peut être sauvegardée et rechargée via **Palette → Sauvegarder/Charger palette** (format JSON).
Double-cliquez sur une couleur de la palette pour la modifier.

## Performances

- Canvas jusqu'à 4096×4096 px
- Dessin fluide à 60 FPS (visé)
- Consommation mémoire < 200 MB pour un canvas standard
