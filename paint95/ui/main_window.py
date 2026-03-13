"""Main application window — menus, toolbar, canvas, palette, status bar."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QAction, QColor, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QStatusBar, QLabel, QDialog,
    QFileDialog, QMessageBox, QInputDialog,
    QSpinBox, QFormLayout, QDialogButtonBox, QSizePolicy,
)

from canvas.canvas_widget import CanvasWidget, ZOOM_LEVELS
from color.palette_manager import PaletteManager
from file_io.image_loader import ImageLoader
from file_io.image_saver import ImageSaver
from ui.toolbar import ToolBox
from ui.palette import PaletteWidget


# ── New-image dialog ─────────────────────────────────────────────────────────

class NewImageDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvelle image")
        layout = QFormLayout(self)

        self._w = QSpinBox()
        self._w.setRange(1, 4096)
        self._w.setValue(800)
        self._w.setSuffix(" px")

        self._h = QSpinBox()
        self._h.setRange(1, 4096)
        self._h.setValue(600)
        self._h.setSuffix(" px")

        layout.addRow("Largeur :", self._w)
        layout.addRow("Hauteur :", self._h)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def size(self) -> tuple[int, int]:
        return self._w.value(), self._h.value()


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    APP_NAME = "Dessinator"
    VERSION = "1.0"

    def __init__(self) -> None:
        super().__init__()
        self._palette_manager = PaletteManager()
        self._current_path: str | None = None
        self._modified = False

        self._build_ui()
        self._build_menus()
        self._build_status_bar()
        self._wire_signals()

        self.setWindowTitle(self.APP_NAME)
        self.resize(1100, 750)

    # ═══════════════════════════════════════════════════════════════════════
    # UI construction
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── middle area: toolbox + canvas ────────────────────────────────────
        middle = QHBoxLayout()
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(0)

        self._toolbox = ToolBox()
        middle.addWidget(self._toolbox)

        self._scroll = QScrollArea()
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setStyleSheet("background: #6b6b6b;")
        self._scroll.setWidgetResizable(False)

        self._canvas = CanvasWidget()
        self._scroll.setWidget(self._canvas)
        middle.addWidget(self._scroll, stretch=1)

        outer.addLayout(middle, stretch=1)

        # ── palette bar ──────────────────────────────────────────────────────
        self._palette_bar = PaletteWidget(self._palette_manager)
        self._palette_bar.setFixedHeight(52)
        self._palette_bar.setStyleSheet("background: #f0f0f0; border-top: 1px solid #ccc;")
        outer.addWidget(self._palette_bar)

        # ── connect pipette callbacks ────────────────────────────────────────
        self._toolbox.set_pipette_callbacks(
            self._palette_bar.set_fg,
            self._palette_bar.set_bg,
        )

        # Set initial tool
        self._toolbox.tool_selected.connect(self._on_tool_selected)
        # Trigger default tool
        from tools.pencil import PencilTool
        self._canvas.set_tool(self._toolbox.tool("pencil"))

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)

        self._lbl_pos = QLabel("x: 0  y: 0")
        self._lbl_pos.setFixedWidth(120)

        self._lbl_size = QLabel(
            f"800 × 600 px"
        )
        self._lbl_size.setFixedWidth(120)

        self._lbl_tool = QLabel("Crayon")
        self._lbl_zoom = QLabel("100 %")
        self._lbl_zoom.setFixedWidth(60)

        sb.addWidget(self._lbl_pos)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._lbl_size)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._lbl_tool)
        sb.addPermanentWidget(self._lbl_zoom)

    # ═══════════════════════════════════════════════════════════════════════
    # Menu bar
    # ═══════════════════════════════════════════════════════════════════════

    def _build_menus(self) -> None:
        mb = self.menuBar()

        # ── Fichier ──────────────────────────────────────────────────────────
        file_menu = mb.addMenu("&Fichier")

        act_new = QAction("&Nouveau", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._new_file)
        file_menu.addAction(act_new)

        act_open = QAction("&Ouvrir…", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._open_file)
        file_menu.addAction(act_open)

        file_menu.addSeparator()

        act_save = QAction("&Enregistrer", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_file)
        file_menu.addAction(act_save)

        act_saveas = QAction("Enregistrer &sous…", self)
        act_saveas.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_saveas.triggered.connect(self._save_file_as)
        file_menu.addAction(act_saveas)

        file_menu.addSeparator()

        act_quit = QAction("&Quitter", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # ── Édition ──────────────────────────────────────────────────────────
        edit_menu = mb.addMenu("&Édition")

        act_undo = QAction("&Annuler", self)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.triggered.connect(self._canvas.undo)
        edit_menu.addAction(act_undo)

        act_redo = QAction("Rétablir", self)
        act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        act_redo.triggered.connect(self._canvas.redo)
        edit_menu.addAction(act_redo)

        edit_menu.addSeparator()

        act_copy = QAction("&Copier", self)
        act_copy.setShortcut(QKeySequence("Ctrl+C"))
        act_copy.triggered.connect(self._canvas.copy_selection)
        edit_menu.addAction(act_copy)

        act_cut = QAction("C&ouper", self)
        act_cut.setShortcut(QKeySequence("Ctrl+X"))
        act_cut.triggered.connect(self._canvas.cut_selection)
        edit_menu.addAction(act_cut)

        act_paste = QAction("C&oller", self)
        act_paste.setShortcut(QKeySequence("Ctrl+V"))
        act_paste.triggered.connect(self._canvas.paste)
        edit_menu.addAction(act_paste)

        act_delete = QAction("S&upprimer", self)
        act_delete.setShortcut(QKeySequence("Delete"))
        act_delete.triggered.connect(self._canvas.delete_selection)
        edit_menu.addAction(act_delete)

        # ── Image ────────────────────────────────────────────────────────────
        image_menu = mb.addMenu("&Image")

        act_invert = QAction("&Inverser les couleurs", self)
        act_invert.triggered.connect(self._canvas.invert_colors)
        image_menu.addAction(act_invert)

        image_menu.addSeparator()

        act_fh = QAction("Retourner &horizontalement", self)
        act_fh.triggered.connect(self._canvas.flip_horizontal)
        image_menu.addAction(act_fh)

        act_fv = QAction("Retourner &verticalement", self)
        act_fv.triggered.connect(self._canvas.flip_vertical)
        image_menu.addAction(act_fv)

        image_menu.addSeparator()

        act_resize = QAction("Redimensionner…", self)
        act_resize.triggered.connect(self._resize_image)
        image_menu.addAction(act_resize)

        # ── Affichage ────────────────────────────────────────────────────────
        view_menu = mb.addMenu("A&ffichage")

        act_zin = QAction("Zoom &+", self)
        act_zin.setShortcut(QKeySequence("Ctrl++"))
        act_zin.triggered.connect(self._canvas.zoom_in)
        view_menu.addAction(act_zin)

        act_zout = QAction("Zoom &-", self)
        act_zout.setShortcut(QKeySequence("Ctrl+-"))
        act_zout.triggered.connect(self._canvas.zoom_out)
        view_menu.addAction(act_zout)

        zoom_menu = view_menu.addMenu("Niveau de zoom")
        for z in ZOOM_LEVELS:
            a = QAction(f"{z} %", self)
            a.triggered.connect(lambda checked, zz=z: self._canvas.set_zoom_level(zz))
            zoom_menu.addAction(a)

        view_menu.addSeparator()

        act_grid = QAction("Grille &pixels", self)
        act_grid.setCheckable(True)
        act_grid.setShortcut(QKeySequence("Ctrl+G"))
        act_grid.triggered.connect(self._canvas.toggle_grid)
        view_menu.addAction(act_grid)

        # ── Palette ──────────────────────────────────────────────────────────
        palette_menu = mb.addMenu("&Palette")

        act_save_pal = QAction("Sauvegarder la palette…", self)
        act_save_pal.triggered.connect(self._save_palette)
        palette_menu.addAction(act_save_pal)

        act_load_pal = QAction("Charger une palette…", self)
        act_load_pal.triggered.connect(self._load_palette)
        palette_menu.addAction(act_load_pal)

    # ═══════════════════════════════════════════════════════════════════════
    # Signal wiring
    # ═══════════════════════════════════════════════════════════════════════

    def _wire_signals(self) -> None:
        self._canvas.mouse_moved.connect(self._on_mouse_moved)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        self._palette_bar.fg_changed.connect(self._on_colors_changed)
        self._palette_bar.bg_changed.connect(self._on_colors_changed)
        # Initial colour sync
        self._on_colors_changed()

    # ═══════════════════════════════════════════════════════════════════════
    # Slots
    # ═══════════════════════════════════════════════════════════════════════

    def _on_tool_selected(self, tool) -> None:
        self._canvas.set_tool(tool)
        self._lbl_tool.setText(tool.name)

    def _on_mouse_moved(self, x: int, y: int) -> None:
        self._lbl_pos.setText(f"x: {x}  y: {y}")

    def _on_zoom_changed(self, zoom: int) -> None:
        self._lbl_zoom.setText(f"{zoom} %")

    def _on_colors_changed(self, _color=None) -> None:
        self._canvas.update_colors(
            self._palette_manager.foreground,
            self._palette_manager.background,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # File operations
    # ═══════════════════════════════════════════════════════════════════════

    def _new_file(self) -> None:
        if not self._confirm_discard():
            return
        dlg = NewImageDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            w, h = dlg.size()
            self._canvas.new_image(w, h, self._palette_manager.background)
            self._current_path = None
            self._modified = False
            self._update_title()
            self._update_size_label()

    def _open_file(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une image", "",
            "Images (*.png *.jpg *.jpeg);;PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if not path:
            return
        try:
            image = ImageLoader.load(path)
            self._canvas.load_image(image)
            self._current_path = path
            self._modified = False
            self._update_title()
            self._update_size_label()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir :\n{e}")

    def _save_file(self) -> None:
        if self._current_path:
            self._do_save(self._current_path)
        else:
            self._save_file_as()

    def _save_file_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer sous", "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if not path:
            return
        # Ensure extension
        p = Path(path)
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            path = str(p) + ".png"
        self._do_save(path)

    def _do_save(self, path: str) -> None:
        try:
            ImageSaver.save(self._canvas.image, path)
            self._current_path = path
            self._modified = False
            self._update_title()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{e}")

    # ── image operations ────────────────────────────────────────────────────

    def _resize_image(self) -> None:
        w = self._canvas.image.width()
        h = self._canvas.image.height()
        dlg = NewImageDialog(self)
        dlg.setWindowTitle("Redimensionner l'image")
        # Hack: pre-fill with current values
        dlg._w.setValue(w)
        dlg._h.setValue(h)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            nw, nh = dlg.size()
            from PyQt6.QtGui import QImage
            self._canvas.save_undo()
            scaled = self._canvas.image.scaled(
                nw, nh,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ).convertToFormat(QImage.Format.Format_ARGB32)
            self._canvas.load_image(scaled)
            self._update_size_label()

    # ── palette operations ──────────────────────────────────────────────────

    def _save_palette(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder la palette", "palette.json",
            "JSON (*.json)"
        )
        if path:
            try:
                self._palette_manager.save(path)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _load_palette(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Charger une palette", "",
            "JSON (*.json)"
        )
        if path:
            try:
                self._palette_manager.load(path)
                # Rebuild palette widget
                self._palette_bar._grid._colors = self._palette_manager.colors
                self._palette_bar._grid.update()
                self._palette_bar._squares.set_fg(self._palette_manager.foreground)
                self._palette_bar._squares.set_bg(self._palette_manager.background)
                self._on_colors_changed()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    # ═══════════════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _confirm_discard(self) -> bool:
        if not self._modified:
            return True
        reply = QMessageBox.question(
            self, "Modifications non enregistrées",
            "Voulez-vous ignorer les modifications ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _update_title(self) -> None:
        name = Path(self._current_path).name if self._current_path else "Sans titre"
        marker = " *" if self._modified else ""
        self.setWindowTitle(f"{name}{marker} — {self.APP_NAME}")

    def _update_size_label(self) -> None:
        w = self._canvas.image.width()
        h = self._canvas.image.height()
        self._lbl_size.setText(f"{w} × {h} px")

    # ── close event ─────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
