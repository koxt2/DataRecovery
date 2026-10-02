"""GTK4 / Libadwaita widgets for displaying a ddrescue map file."""

import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, GObject, Gtk  # noqa: E402

from .mapfile import (  # noqa: E402
    SEVERITY,
    MapFile,
    MapFileError,
    Status,
    format_size,
    load_mapfile,
)

EMPTY_RGB = (0x34, 0x34, 0x34)
GAP = 1


def _rgb(c):
    return c[0] / 255, c[1] / 255, c[2] / 255


class MapGrid(Gtk.DrawingArea):
    """Draws the whole disk as a grid of cells, each coloured by its health."""

    __gtype_name__ = "DataRecoveryMapGrid"
    __gsignals__ = {"cell-hover": (GObject.SignalFlags.RUN_FIRST, None, (int,))}

    def __init__(self):
        super().__init__()
        self.map: MapFile | None = None
        self.cell_size = 12
        self.blend = False
        self.cols = self.rows = 0
        self._cells: list[dict[Status, int]] = []
        self.hover = -1
        self.set_draw_func(self._draw)
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        motion.connect("leave", lambda *_: self._set_hover(-1))
        self.add_controller(motion)

    def set_map(self, mf: MapFile | None):
        self.map = mf
        self._cells = []
        self.queue_draw()

    def set_cell_size(self, px: int):
        self.cell_size = max(2, int(px))
        self._cells = []
        self.queue_draw()

    def set_blend(self, blend: bool):
        self.blend = blend
        self.queue_draw()

    def cell_range(self, idx: int) -> tuple[int, int]:
        n = self.cols * self.rows
        span = self.map.total / n
        return (self.map.start + int(idx * span), self.map.start + int((idx + 1) * span))

    def cell_totals(self, idx: int) -> dict[Status, int]:
        return self._cells[idx] if 0 <= idx < len(self._cells) else {}

    def _layout(self, w, h):
        cols, rows = max(1, w // self.cell_size), max(1, h // self.cell_size)
        if self.map and cols * rows > self.map.total:
            cols = rows = 1
        if (cols, rows) != (self.cols, self.rows) or not self._cells:
            self.cols, self.rows = cols, rows
            self._cells = self.map.grid(cols * rows) if self.map else []

    def _colour(self, totals):
        present = [s for s in SEVERITY if totals.get(s)]
        if not present:
            return _rgb(EMPTY_RGB)
        if not self.blend:
            return _rgb(present[0].rgb)
        tot = sum(totals[s] for s in present)
        return tuple(sum(totals[s] * s.rgb[i] for s in present) / tot / 255 for i in range(3))

    def _draw(self, _area, cr, w, h):
        if not self.map:
            return
        self._layout(w, h)
        cs = self.cell_size
        ox, oy = (w - self.cols * cs) // 2, (h - self.rows * cs) // 2
        for i, totals in enumerate(self._cells):
            x, y = ox + (i % self.cols) * cs, oy + (i // self.cols) * cs
            cr.set_source_rgb(*self._colour(totals))
            cr.rectangle(x, y, cs - GAP, cs - GAP)
            cr.fill()
        if self.hover >= 0:
            x, y = ox + (self.hover % self.cols) * cs, oy + (self.hover // self.cols) * cs
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(2)
            cr.rectangle(x, y, cs - GAP, cs - GAP)
            cr.stroke()

    def _index_at(self, x, y):
        cs = self.cell_size
        ox = (self.get_width() - self.cols * cs) // 2
        oy = (self.get_height() - self.rows * cs) // 2
        c, r = int((x - ox) // cs), int((y - oy) // cs)
        if 0 <= c < self.cols and 0 <= r < self.rows:
            return r * self.cols + c
        return -1

    def _on_motion(self, _ctl, x, y):
        self._set_hover(self._index_at(x, y) if self.map else -1)

    def _set_hover(self, idx):
        if idx != self.hover:
            self.hover = idx
            self.queue_draw()
            self.emit("cell-hover", idx)


class StatusSwatch(Gtk.DrawingArea):
    """Small colour key, instantiated by the UI template."""

    __gtype_name__ = "DataRecoveryStatusSwatch"

    def __init__(self):
        super().__init__()
        self.rgb = EMPTY_RGB
        self.set_content_width(18)
        self.set_content_height(18)
        self.set_valign(Gtk.Align.CENTER)
        self.set_draw_func(self._draw)

    def set_rgb(self, rgb):
        self.rgb = rgb
        self.queue_draw()

    def _draw(self, _area, cr, width, height):
        cr.set_source_rgb(*_rgb(self.rgb))
        cr.rectangle(0, 0, width, height)
        cr.fill()


@Gtk.Template(resource_path="/datarecovery/gtk/map_health_view.ui")
class MapHealthView(Gtk.Box):
    """Embeddable widget: grid + legend + statistics for one map file.

    Call `load(path)` to show a map. With `auto_refresh` it re-reads the file
    when it changes, so it can follow a running ddrescue.
    """

    __gtype_name__ = "MapHealthView"

    stack = Gtk.Template.Child()
    grid = Gtk.Template.Child()
    cell_size_scale = Gtk.Template.Child()
    blend_switch = Gtk.Template.Child()
    hover_row = Gtk.Template.Child()
    bad_value = Gtk.Template.Child()
    non_scraped_value = Gtk.Template.Child()
    non_trimmed_value = Gtk.Template.Child()
    non_tried_value = Gtk.Template.Child()
    finished_value = Gtk.Template.Child()
    bad_swatch = Gtk.Template.Child()
    non_scraped_swatch = Gtk.Template.Child()
    non_trimmed_swatch = Gtk.Template.Child()
    non_tried_swatch = Gtk.Template.Child()
    finished_swatch = Gtk.Template.Child()
    size_row = Gtk.Template.Child()
    rescued_row = Gtk.Template.Child()
    errors_row = Gtk.Template.Child()
    phase_row = Gtk.Template.Child()
    pos_row = Gtk.Template.Child()
    blocks_row = Gtk.Template.Child()
    cmd_row = Gtk.Template.Child()
    file_row = Gtk.Template.Child()

    def __init__(self, path: str | None = None, auto_refresh: bool = True):
        super().__init__()
        self.map: MapFile | None = None
        self.path: str | None = None
        self._mtime = 0.0
        self._timer = 0
        self._legend_rows = {
            Status.BAD: self.bad_value,
            Status.NON_SCRAPED: self.non_scraped_value,
            Status.NON_TRIMMED: self.non_trimmed_value,
            Status.NON_TRIED: self.non_tried_value,
            Status.FINISHED: self.finished_value,
        }
        self._swatches = {
            Status.BAD: self.bad_swatch,
            Status.NON_SCRAPED: self.non_scraped_swatch,
            Status.NON_TRIMMED: self.non_trimmed_swatch,
            Status.NON_TRIED: self.non_tried_swatch,
            Status.FINISHED: self.finished_swatch,
        }
        self._info = {
            "size": self.size_row,
            "rescued": self.rescued_row,
            "errors": self.errors_row,
            "phase": self.phase_row,
            "pos": self.pos_row,
            "blocks": self.blocks_row,
            "cmd": self.cmd_row,
            "file": self.file_row,
        }
        for status, swatch in self._swatches.items():
            swatch.set_rgb(status.rgb)
        self.grid.connect("cell-hover", self._on_hover)
        self.cell_size_scale.connect(
            "value-changed", lambda scale: self.grid.set_cell_size(scale.get_value())
        )
        self.blend_switch.connect(
            "notify::active",
            lambda switch, _pspec: self.grid.set_blend(switch.get_active()),
        )

        self.auto_refresh = auto_refresh
        if auto_refresh:
            self._timer = GLib.timeout_add_seconds(2, self._poll)
        self.connect("destroy", lambda *_: self._timer and GLib.source_remove(self._timer))
        if path:
            self.load(path)

    def load(self, path: str):
        """Load and display `path`. Raises MapFileError on failure."""
        mf = load_mapfile(path)
        self.path = path
        self._mtime = os.path.getmtime(path)
        self.map = mf
        self.grid.set_map(mf)
        self._update_stats()
        self.stack.set_visible_child_name("content")

    def _poll(self):
        if self.path:
            try:
                m = os.path.getmtime(self.path)
                if m != self._mtime:
                    self.load(self.path)
            except (OSError, MapFileError):
                pass
        return True

    def _update_stats(self):
        mf = self.map
        tot = mf.totals()
        size = mf.total or 1
        for status, label in self._legend_rows.items():
            label.set_label(f"{format_size(tot[status])}\n{tot[status] / size * 100:.2f}%")
        bad = tot[Status.BAD]
        self._info["size"].set_subtitle(f"{format_size(mf.total)} ({mf.total:,} bytes)")
        self._info["rescued"].set_subtitle(
            f"{format_size(tot[Status.FINISHED])} ({tot[Status.FINISHED] / size * 100:.2f}%)"
        )
        self._info["errors"].set_subtitle(
            f"{format_size(bad)} in {mf.count()[Status.BAD]:,} areas" if bad else "None found"
        )
        phase = mf.phase + (f" (pass {mf.current_pass})" if mf.current_pass else "")
        self._info["phase"].set_subtitle(phase)
        self._info["pos"].set_subtitle(f"0x{mf.current_pos:X} ({format_size(mf.current_pos)})")
        self._info["blocks"].set_subtitle(f"{len(mf.blocks):,}")
        self._info["cmd"].set_subtitle(GLib.markup_escape_text(mf.command_line or "Unknown"))
        self._info["file"].set_subtitle(GLib.markup_escape_text(mf.path or ""))

    def _on_hover(self, _grid, idx):
        if idx < 0 or not self.map:
            self.hover_row.set_title("Hover over the grid")
            self.hover_row.set_subtitle(" ")
            return
        lo, hi = self.grid.cell_range(idx)
        totals = self.grid.cell_totals(idx)
        span = max(hi - lo, 1)
        self.hover_row.set_title(f"0x{lo:X} – 0x{hi:X}  ({format_size(hi - lo)})")
        lines = [
            f"{status.label}: {format_size(totals[status])} "
            f"({totals[status] / span * 100:.1f}%)"
            for status in SEVERITY
            if totals.get(status)
        ]
        self.hover_row.set_subtitle(GLib.markup_escape_text("\n".join(lines)))


@Gtk.Template(resource_path="/datarecovery/gtk/map_health_window.ui")
class MapHealthWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MapHealthWindow"

    view = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    open_button = Gtk.Template.Child()
    reload_button = Gtk.Template.Child()

    def __init__(
        self,
        application=None,
        path: str | None = None,
        allow_open: bool = True,
        **kwargs,
    ):
        super().__init__(application=application, **kwargs)
        self.toasts = self.toast_overlay
        self.open_button.set_visible(allow_open)
        self.open_button.connect("clicked", self._on_open)
        self.reload_button.connect(
            "clicked", lambda *_: self.open_path(self.view.path) if self.view.path else None
        )
        if path:
            self.open_path(path)

    def open_path(self, path: str) -> bool:
        try:
            self.view.load(path)
        except MapFileError as e:
            self.toasts.add_toast(Adw.Toast(title=f"Cannot read map file: {e}"))
            return False
        self.set_title(f"Drive Health — {os.path.basename(path)}")
        return True

    def _on_open(self, *_):
        dlg = Gtk.FileDialog(title="Open ddrescue map file")
        dlg.open(self, None, self._on_chosen)

    def _on_chosen(self, dlg, res):
        try:
            f = dlg.open_finish(res)
        except GLib.Error:
            return
        self.open_path(f.get_path())


class MapHealth:
    """Callable that shows a health window for a ddrescue mapfile.

        health = MapHealth(parent=main_window)
        health("/path/to/rescue.map")

    The window uses the host's Adw.Application; no second main loop is needed.
    """

    def __init__(
        self,
        application: Adw.Application | None = None,
        parent: Gtk.Window | None = None,
        modal: bool = False,
    ):
        self.application = application
        self.parent = parent
        self.modal = modal

    def __call__(self, path: str) -> MapHealthWindow:
        application = self.application or (
            self.parent.get_application() if self.parent else None
        )
        win = MapHealthWindow(application=application, path=path, allow_open=False)
        if self.parent:
            win.set_transient_for(self.parent)
            win.set_modal(self.modal)
        win.present()
        return win
