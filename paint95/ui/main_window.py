"""
Main application window.
Wires together: canvas, toolbar, palette, statusbar, menus.
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFileDialog, QDialog, QDialogButtonBox,
    QLabel, QSpinBox, QFormLayout, QMessageBox, QInputDialog,
    QComboBox, QSlider, QGroupBox, QRadioButton, QCheckBox,
)
from PyQt6.QtGui import (
    QAction, QKeySequence, QColor, QIcon, QCloseEvent,
)
from PyQt6.QtCore import Qt, QSize

from ..canvas.canvas_widget import CanvasWidget
from ..canvas.drawing_engine import DrawingEngine
from ..color.palette_manager import PaletteManager
from ..color.color_dialog import ColorPickerDialog
from ..ui.toolbar import ToolBar
from ..ui.palette import PaletteWidget
from ..ui.statusbar import StatusBar
from ..io.image_loader import load_image
from ..io.image_saver import save_image
from ..tools.shapes import FillMode


DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600


# ── New canvas dialog ─────────────────────────────────────────────────────────

class NewCanvasDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouveau document")
        layout = QFormLayout(self)

        self._w = QSpinBox()
        self._w.setRange(1, 8192)
        self._w.setValue(DEFAULT_WIDTH)
        self._h = QSpinBox()
        self._h.setRange(1, 8192)
        self._h.setValue(DEFAULT_HEIGHT)

        layout.addRow("Largeur (px):", self._w)
        layout.addRow("Hauteur (px):", self._h)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def size_px(self):
        return self._w.value(), self._h.value()


# ── Tool options panel ────────────────────────────────────────────────────────

class ToolOptionsPanel(QWidget):
    """A small panel below the menu that shows options for the active tool."""

    def __init__(self, canvas: CanvasWidget, parent=None) -> None:
        super().__init__(parent)
        self._canvas = canvas
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(8)
        self._widgets: list[QWidget] = []
        self.setFixedHeight(36)

    def update_for_tool(self, tool_name: str) -> None:
        # Clear previous widgets
        for w in self._widgets:
            self._layout.removeWidget(w)
            w.deleteLater()
        self._widgets.clear()

        if tool_name == "brush":
            self._add_size_combo(
                "Taille:", [1, 3, 5, 8],
                lambda v: setattr(self._canvas.get_brush(), "size", v)
            )
            self._add_shape_radio(
                lambda round_: setattr(self._canvas.get_brush(), "round_shape", round_)
            )

        elif tool_name == "eraser":
            self._add_size_combo(
                "Taille:", [8, 16, 32],
                lambda v: setattr(self._canvas.get_eraser(), "size", v)
            )

        elif tool_name == "spray":
            self._add_size_combo(
                "Rayon:", [5, 10, 15, 25, 40],
                lambda v: setattr(self._canvas.get_spray(), "radius", v)
            )
            self._add_size_combo(
                "Densité:", [10, 20, 30, 50, 80],
                lambda v: setattr(self._canvas.get_spray(), "density", v)
            )

        elif tool_name in ("line", "rectangle", "ellipse", "polygon", "curve"):
            self._add_size_combo(
                "Épaisseur:", [1, 2, 3, 5, 8],
                lambda v: self._set_thickness(tool_name, v)
            )
            if tool_name in ("rectangle", "ellipse"):
                self._add_fill_mode_combo(tool_name)

    def _add_size_combo(self, label: str, values: list[int], callback) -> None:
        lbl = QLabel(label)
        combo = QComboBox()
        for v in values:
            combo.addItem(str(v), v)
        combo.currentIndexChanged.connect(
            lambda _: callback(combo.currentData())
        )
        self._layout.addWidget(lbl)
        self._layout.addWidget(combo)
        self._widgets += [lbl, combo]

    def _add_shape_radio(self, callback) -> None:
        lbl = QLabel("Forme:")
        round_rb = QRadioButton("Rond")
        square_rb = QRadioButton("Carré")
        round_rb.setChecked(True)
        round_rb.toggled.connect(lambda checked: callback(checked))
        for w in (lbl, round_rb, square_rb):
            self._layout.addWidget(w)
            self._widgets.append(w)

    def _add_fill_mode_combo(self, tool_name: str) -> None:
        lbl = QLabel("Remplissage:")
        combo = QComboBox()
        combo.addItem("Contour seulement", FillMode.OUTLINE)
        combo.addItem("Rempli seulement", FillMode.FILLED)
        combo.addItem("Contour + remplissage", FillMode.BOTH)

        def _set(idx):
            mode = combo.currentData()
            if tool_name == "rectangle":
                self._canvas.get_rect_tool().fill_mode = mode
            else:
                self._canvas.get_ellipse().fill_mode = mode

        combo.currentIndexChanged.connect(_set)
        for w in (lbl, combo):
            self._layout.addWidget(w)
            self._widgets.append(w)

    def _set_thickness(self, tool_name: str, v: int) -> None:
        if tool_name == "line":
            self._canvas.get_line().thickness = v
        elif tool_name == "rectangle":
            self._canvas.get_rect_tool().thickness = v
        elif tool_name == "ellipse":
            self._canvas.get_ellipse().thickness = v
        elif tool_name == "polygon":
            self._canvas.get_polygon().thickness = v
        elif tool_name == "curve":
            self._canvas.get_line().thickness = v  # reuse line thickness


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Dessinator — Paint moderne")
        self.setMinimumSize(900, 650)

        self._current_file: Path | None = None
        self._modified = False

        # Core components
        self._engine = DrawingEngine(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self._palette_mgr = PaletteManager()

        # Canvas
        self._canvas = CanvasWidget(self._engine)
        self._canvas.cursor_moved.connect(self._on_cursor)
        self._canvas.tool_changed.connect(self._on_tool_changed)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        self._canvas.color_picked.connect(self._on_color_picked)
        self._engine.image_changed.connect(self._mark_modified)

        # Toolbar
        self._toolbar = ToolBar()
        self._toolbar.tool_selected.connect(self._on_tool_selected)

        # Palette
        self._palette = PaletteWidget(self._palette_mgr)
        self._palette.fg_changed.connect(self._on_fg_changed)
        self._palette.bg_changed.connect(self._on_bg_changed)

        # Status bar
        self._status = StatusBar()
        self.setStatusBar(self._status)
        self._status.update_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        # Tool options
        self._tool_options = ToolOptionsPanel(self._canvas)
        self._canvas.tool_changed.connect(self._tool_options.update_for_tool)

        # Scroll area for canvas
        self._scroll = QScrollArea()
        self._scroll.setWidget(self._canvas)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setWidgetResizable(False)

        # Central layout
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._tool_options)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._toolbar)
        content.addWidget(self._scroll, 1)
        main_layout.addLayout(content, 1)
        main_layout.addWidget(self._palette)

        self.setCentralWidget(central)

        self._build_menus()
        self._update_canvas_colors()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------
    def _build_menus(self) -> None:
        mb = self.menuBar()

        # ── Fichier ──
        file_menu = mb.addMenu("&Fichier")

        act_new = QAction("&Nouveau", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._file_new)
        file_menu.addAction(act_new)

        act_open = QAction("&Ouvrir…", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._file_open)
        file_menu.addAction(act_open)

        file_menu.addSeparator()

        act_save = QAction("&Enregistrer", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._file_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("Enregistrer &sous…", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._file_save_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_quit = QAction("&Quitter", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # ── Édition ──
        edit_menu = mb.addMenu("&Édition")

        act_undo = QAction("&Annuler", self)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.triggered.connect(self._engine.undo)
        edit_menu.addAction(act_undo)

        act_redo = QAction("&Rétablir", self)
        act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        act_redo.triggered.connect(self._engine.redo)
        edit_menu.addAction(act_redo)

        edit_menu.addSeparator()

        act_copy = QAction("&Copier", self)
        act_copy.setShortcut(QKeySequence("Ctrl+C"))
        act_copy.triggered.connect(self._edit_copy)
        edit_menu.addAction(act_copy)

        act_cut = QAction("Co&uper", self)
        act_cut.setShortcut(QKeySequence("Ctrl+X"))
        act_cut.triggered.connect(self._edit_cut)
        edit_menu.addAction(act_cut)

        act_paste = QAction("Co&ller", self)
        act_paste.setShortcut(QKeySequence("Ctrl+V"))
        act_paste.triggered.connect(self._edit_paste)
        edit_menu.addAction(act_paste)

        act_delete = QAction("&Supprimer", self)
        act_delete.setShortcut(QKeySequence("Delete"))
        act_delete.triggered.connect(self._edit_delete)
        edit_menu.addAction(act_delete)

        edit_menu.addSeparator()

        act_sel_all = QAction("Tout sé&lectionner", self)
        act_sel_all.setShortcut(QKeySequence("Ctrl+A"))
        act_sel_all.triggered.connect(self._edit_select_all)
        edit_menu.addAction(act_sel_all)

        # ── Image ──
        img_menu = mb.addMenu("&Image")

        act_invert = QAction("&Inverser les couleurs", self)
        act_invert.triggered.connect(self._engine.invert_colors)
        img_menu.addAction(act_invert)

        act_flip_h = QAction("Retourner &horizontalement", self)
        act_flip_h.triggered.connect(self._engine.flip_horizontal)
        img_menu.addAction(act_flip_h)

        act_flip_v = QAction("Retourner &verticalement", self)
        act_flip_v.triggered.connect(self._engine.flip_vertical)
        img_menu.addAction(act_flip_v)

        img_menu.addSeparator()

        act_resize = QAction("Re&dimensionner…", self)
        act_resize.triggered.connect(self._image_resize)
        img_menu.addAction(act_resize)

        # ── Affichage ──
        view_menu = mb.addMenu("&Affichage")

        act_zoom_in = QAction("Zoom &+", self)
        act_zoom_in.setShortcut(QKeySequence("Ctrl++"))
        act_zoom_in.triggered.connect(self._canvas.zoom_in)
        view_menu.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom &-", self)
        act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        act_zoom_out.triggered.connect(self._canvas.zoom_out)
        view_menu.addAction(act_zoom_out)

        act_zoom_100 = QAction("Zoom &100%", self)
        act_zoom_100.setShortcut(QKeySequence("Ctrl+0"))
        act_zoom_100.triggered.connect(lambda: self._canvas.set_zoom(1.0))
        view_menu.addAction(act_zoom_100)

        view_menu.addSeparator()

        act_grid = QAction("&Grille pixel", self)
        act_grid.setCheckable(True)
        act_grid.setShortcut(QKeySequence("Ctrl+G"))
        act_grid.toggled.connect(self._canvas.set_show_grid)
        view_menu.addAction(act_grid)

        # ── Palette ──
        pal_menu = mb.addMenu("&Palette")

        act_fg = QAction("Couleur &avant-plan…", self)
        act_fg.triggered.connect(self._pick_fg)
        pal_menu.addAction(act_fg)

        act_bg = QAction("Couleur &arrière-plan…", self)
        act_bg.triggered.connect(self._pick_bg)
        pal_menu.addAction(act_bg)

        pal_menu.addSeparator()

        act_save_pal = QAction("&Sauvegarder palette…", self)
        act_save_pal.triggered.connect(self._save_palette)
        pal_menu.addAction(act_save_pal)

        act_load_pal = QAction("&Charger palette…", self)
        act_load_pal.triggered.connect(self._load_palette)
        pal_menu.addAction(act_load_pal)

    # ------------------------------------------------------------------
    # Tool / colour slots
    # ------------------------------------------------------------------
    def _on_tool_selected(self, name: str) -> None:
        self._canvas.set_tool(name)

    def _on_tool_changed(self, name: str) -> None:
        self._status.update_tool(name)

    def _on_cursor(self, x: int, y: int) -> None:
        self._status.update_cursor(x, y)

    def _on_zoom_changed(self, zoom: float) -> None:
        self._status.update_zoom(zoom)

    def _on_color_picked(self, color: QColor, is_fg: bool) -> None:
        if is_fg:
            self._palette_mgr.foreground = color
            self._palette.set_fg(color)
        else:
            self._palette_mgr.background = color
            self._palette.set_bg(color)
        self._update_canvas_colors()

    def _on_fg_changed(self, color: QColor) -> None:
        self._update_canvas_colors()

    def _on_bg_changed(self, color: QColor) -> None:
        self._update_canvas_colors()

    def _update_canvas_colors(self) -> None:
        self._canvas.set_colors(
            self._palette_mgr.foreground,
            self._palette_mgr.background,
        )

    def _pick_fg(self) -> None:
        dlg = ColorPickerDialog(self._palette_mgr.foreground, self)
        if dlg.exec():
            c = dlg.selected_color()
            self._palette_mgr.foreground = c
            self._palette.set_fg(c)
            self._update_canvas_colors()

    def _pick_bg(self) -> None:
        dlg = ColorPickerDialog(self._palette_mgr.background, self)
        if dlg.exec():
            c = dlg.selected_color()
            self._palette_mgr.background = c
            self._palette.set_bg(c)
            self._update_canvas_colors()

    def _mark_modified(self) -> None:
        if not self._modified:
            self._modified = True
            self._update_title()

    def _update_title(self) -> None:
        name = self._current_file.name if self._current_file else "Sans titre"
        mod = " *" if self._modified else ""
        self.setWindowTitle(f"Dessinator — {name}{mod}")

    # ------------------------------------------------------------------
    # File actions
    # ------------------------------------------------------------------
    def _file_new(self) -> None:
        if not self._confirm_discard():
            return
        dlg = NewCanvasDialog(self)
        if dlg.exec():
            w, h = dlg.size_px()
            self._engine.new(w, h)
            self._status.update_size(w, h)
            self._current_file = None
            self._modified = False
            self._update_title()

    def _file_open(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une image", "",
            "Images (*.png *.jpg *.jpeg);;PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if not path:
            return
        try:
            img = load_image(path)
            self._engine.replace_image(img)
            self._current_file = Path(path)
            self._modified = False
            self._update_title()
            self._status.update_size(img.width(), img.height())
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'ouverture", str(e))

    def _file_save(self) -> None:
        if self._current_file is None:
            self._file_save_as()
            return
        self._do_save(self._current_file)

    def _file_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer sous", "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if not path:
            return
        self._do_save(Path(path))

    def _do_save(self, path: Path) -> None:
        try:
            save_image(self._engine.image, path)
            self._current_file = path
            self._modified = False
            self._update_title()
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'enregistrement", str(e))

    def _confirm_discard(self) -> bool:
        if not self._modified:
            return True
        answer = QMessageBox.question(
            self,
            "Modifications non sauvegardées",
            "Le document a été modifié. Voulez-vous enregistrer les changements ?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            self._file_save()
            return not self._modified   # False if save was cancelled
        return answer == QMessageBox.StandardButton.Discard

    # ------------------------------------------------------------------
    # Edit actions
    # ------------------------------------------------------------------
    def _edit_copy(self) -> None:
        sel = self._canvas.selection
        if sel.has_selection:
            sel.copy(self._engine.image)

    def _edit_cut(self) -> None:
        sel = self._canvas.selection
        if sel.has_selection:
            self._engine.save_state()
            sel.cut(self._engine.image, self._palette_mgr.background)
            self._engine.image_changed.emit()

    def _edit_paste(self) -> None:
        sel = self._canvas.selection
        # Vérifier d'abord le presse-papier système (screenshots, etc.)
        from PyQt6.QtWidgets import QApplication
        qt_clipboard = QApplication.clipboard().image()
        if not qt_clipboard.isNull():
            self._engine.save_state()
            from PyQt6.QtGui import QPainter
            p = QPainter(self._engine.image)
            p.drawImage(0, 0, qt_clipboard)
            p.end()
            self._engine.image_changed.emit()
        elif sel.get_clipboard() is not None:
            self._engine.save_state()
            sel.paste(self._engine.image)
            self._engine.image_changed.emit()

    def _edit_delete(self) -> None:
        sel = self._canvas.selection
        if sel.has_selection:
            self._engine.save_state()
            sel.delete(self._engine.image, self._palette_mgr.background)
            self._engine.image_changed.emit()

    def _edit_select_all(self) -> None:
        from PyQt6.QtCore import QRect
        img = self._engine.image
        self._canvas.selection._rect = QRect(0, 0, img.width(), img.height())
        self._canvas.selection.selection_changed.emit()

    # ------------------------------------------------------------------
    # Image actions
    # ------------------------------------------------------------------
    def _image_resize(self) -> None:
        img = self._engine.image
        w, ok_w = QInputDialog.getInt(
            self, "Redimensionner", "Nouvelle largeur (px):",
            img.width(), 1, 8192
        )
        if not ok_w:
            return
        h, ok_h = QInputDialog.getInt(
            self, "Redimensionner", "Nouvelle hauteur (px):",
            img.height(), 1, 8192
        )
        if not ok_h:
            return
        self._engine.resize(w, h)
        self._status.update_size(w, h)

    # ------------------------------------------------------------------
    # Palette persistence
    # ------------------------------------------------------------------
    def _save_palette(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder palette", "palette.json", "JSON (*.json)"
        )
        if path:
            try:
                self._palette_mgr.save(Path(path))
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _load_palette(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Charger palette", "", "JSON (*.json)"
        )
        if path:
            try:
                self._palette_mgr.load(Path(path))
                # Refresh palette widget
                for i, swatch in enumerate(self._palette._swatches):
                    if i < len(self._palette_mgr.colors):
                        swatch.set_color(self._palette_mgr.colors[i])
                self._palette.set_fg(self._palette_mgr.foreground)
                self._palette.set_bg(self._palette_mgr.background)
                self._update_canvas_colors()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
