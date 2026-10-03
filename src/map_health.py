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
SECTOR = 512


def _rgb(c):
    return c[0] / 255, c[1] / 255, c[2] / 255


def _cell_rgb(totals, blend=False):
    present = [s for s in SEVERITY if totals.get(s)]
    if not present:
        return _rgb(EMPTY_RGB)
    if not blend:
        return _rgb(present[0].rgb)
    tot = sum(totals[s] for s in present)
    return tuple(sum(totals[s] * s.rgb[i] for s in present) / tot / 255 for i in range(3))


class MapGrid(Gtk.DrawingArea):
    """Draws the disk as a grid of cells, each coloured by its health.

    At zoom 1 the grid shows the whole disk. At zoom N each cell covers 1/N of the bytes, so
    only a window of rows is visible; scroll with the mouse wheel or the overview.
    """

    __gtype_name__ = "DataRecoveryMapGrid"
    __gsignals__ = {
        "cell-hover": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "view-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.map: MapFile | None = None
        self.cell_size = 16
        self.blend = False
        self.zoom = 1
        self.position = 0.0  # 0..1 through the scrollable range
        self.cols = self.rows = 0
        self.first_row = 0
        self._cells: list[dict[Status, int]] = []
        self._key = None
        self.hover = -1
        self.set_draw_func(self._draw)
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        motion.connect("leave", lambda *_: self._set_hover(-1))
        self.add_controller(motion)
        scroll = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.VERTICAL)
        scroll.connect("scroll", self._on_scroll)
        self.add_controller(scroll)

    def set_map(self, mf: MapFile | None):
        self.map = mf
        self._key = None
        self.queue_draw()
        self.emit("view-changed")

    def set_cell_size(self, px: int):
        self.cell_size = max(2, int(px))
        self._key = None
        self.queue_draw()

    def set_blend(self, blend: bool):
        self.blend = blend
        self.queue_draw()

    def set_zoom(self, zoom: int):
        zoom = max(1, int(zoom))
        if zoom == self.zoom:
            return
        centre = self.view_top() + self.view_height() / 2
        self.zoom = zoom
        self.centre_on(centre)

    def max_zoom(self) -> int:
        """Zoom at which one cell covers a single 512-byte sector."""
        if not self.map or not self.cols:
            return 1
        return max(1, int(self.map.total // (self.cols * self.rows * SECTOR)))

    def bytes_per_cell(self) -> float:
        if not self.map or not self.cols:
            return 0.0
        return self.map.total / (self.cols * self.rows * self.zoom)

    def view_top(self) -> float:
        """Top of the visible window as a fraction (0..1) of the whole map."""
        return self.position * (self.zoom - 1) / self.zoom

    def view_height(self) -> float:
        return 1 / self.zoom

    def centre_on(self, fraction: float):
        """Scroll so `fraction` (0..1) of the map is in the middle of the view."""
        if self.zoom == 1:
            self.position = 0.0
        else:
            top = fraction - self.view_height() / 2
            self.position = min(1.0, max(0.0, top * self.zoom / (self.zoom - 1)))
        self._key = None
        self.queue_draw()
        self.emit("view-changed")

    def _on_scroll(self, _ctl, _dx, dy):
        if self.zoom == 1 or not self.rows:
            return False
        self.position = min(1.0, max(0.0, self.position + dy * 3 / (self.rows * (self.zoom - 1))))
        self._key = None
        self.queue_draw()
        self.emit("view-changed")
        return True

    def cell_range(self, idx: int) -> tuple[int, int]:
        n = self.cols * self.rows * self.zoom
        span = self.map.total / n
        idx += self.first_row * self.cols
        return (self.map.start + int(idx * span), self.map.start + int((idx + 1) * span))

    def cell_totals(self, idx: int) -> dict[Status, int]:
        return self._cells[idx] if 0 <= idx < len(self._cells) else {}

    def _layout(self, w, h):
        cols, rows = max(1, w // self.cell_size), max(1, h // self.cell_size)
        if self.map and cols * rows * self.zoom > self.map.total:
            cols = rows = 1
        first_row = round(self.position * rows * (self.zoom - 1))
        key = (cols, rows, self.zoom, first_row)
        if key != self._key:
            self._key = key
            self.cols, self.rows, self.first_row = cols, rows, first_row
            self._cells = (
                self.map.grid(cols * rows * self.zoom, first_row * cols, cols * rows)
                if self.map
                else []
            )

    def _draw(self, _area, cr, w, h):
        if not self.map:
            return
        self._layout(w, h)
        cs = self.cell_size
        ox, oy = (w - self.cols * cs) // 2, (h - self.rows * cs) // 2
        for i, totals in enumerate(self._cells):
            x, y = ox + (i % self.cols) * cs, oy + (i // self.cols) * cs
            cr.set_source_rgb(*_cell_rgb(totals, self.blend))
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


class MapOverview(Gtk.DrawingArea):
    """Thumbnail of the whole map with a box showing what the grid is zoomed in on.
    Click or drag to move the view."""

    COLS, ROWS = 48, 30

    def __init__(self, grid: MapGrid):
        super().__init__()
        self.grid = grid
        self._cells = []
        self._cells_for = None
        self.set_content_width(192)
        self.set_content_height(120)
        self.set_draw_func(self._draw)
        grid.connect("view-changed", lambda *_: self.queue_draw())
        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        self.add_controller(drag)
        self._drag_start_y = 0.0

    def _draw(self, _area, cr, w, h):
        mf = self.grid.map
        if not mf:
            return
        if self._cells_for is not mf:
            self._cells = mf.grid(self.COLS * self.ROWS)
            self._cells_for = mf
        cw, ch = w / self.COLS, h / self.ROWS
        for i, totals in enumerate(self._cells):
            cr.set_source_rgb(*_cell_rgb(totals))
            cr.rectangle((i % self.COLS) * cw, (i // self.COLS) * ch, cw + 0.5, ch + 0.5)
            cr.fill()
        if self.grid.zoom > 1:
            cr.set_source_rgba(0, 0, 0, 0.5)
            top, height = self.grid.view_top() * h, self.grid.view_height() * h
            cr.rectangle(0, 0, w, top)
            cr.rectangle(0, top + height, w, h - top - height)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(2)
            cr.rectangle(1, top + 1, w - 2, max(height - 2, 1))
            cr.stroke()

    def _move_to(self, y):
        self.grid.centre_on(min(1.0, max(0.0, y / max(self.get_height(), 1))))

    def _on_drag_begin(self, _gesture, _x, y):
        self._drag_start_y = y
        self._move_to(y)

    def _on_drag_update(self, _gesture, _dx, dy):
        self._move_to(self._drag_start_y + dy)


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


@Gtk.Template(resource_path="/datarecovery/gtk/map_health_window.ui")
class MapHealthWindow(Adw.ApplicationWindow):
    """Window showing the grid, legend and statistics for one ddrescue map file."""

    __gtype_name__ = "MapHealthWindow"

    toast_overlay = Gtk.Template.Child()
    grid_holder = Gtk.Template.Child()
    overview_holder = Gtk.Template.Child()
    zoom_scale = Gtk.Template.Child()
    zoom_label = Gtk.Template.Child()
    cell_size_scale = Gtk.Template.Child()
    blend_switch = Gtk.Template.Child()
    hover_row = Gtk.Template.Child()
    bad_value = Gtk.Template.Child()
    non_scraped_value = Gtk.Template.Child()
    non_trimmed_value = Gtk.Template.Child()
    non_tried_value = Gtk.Template.Child()
    finished_value = Gtk.Template.Child()
    bad_swatch_holder = Gtk.Template.Child()
    non_scraped_swatch_holder = Gtk.Template.Child()
    non_trimmed_swatch_holder = Gtk.Template.Child()
    non_tried_swatch_holder = Gtk.Template.Child()
    finished_swatch_holder = Gtk.Template.Child()
    size_row = Gtk.Template.Child()
    rescued_row = Gtk.Template.Child()
    errors_row = Gtk.Template.Child()
    file_row = Gtk.Template.Child()

    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        self.map: MapFile | None = None
        self.path: str | None = None
        self._legend_rows = {
            Status.BAD: self.bad_value,
            Status.NON_SCRAPED: self.non_scraped_value,
            Status.NON_TRIMMED: self.non_trimmed_value,
            Status.NON_TRIED: self.non_tried_value,
            Status.FINISHED: self.finished_value,
        }
        self._swatches = {
            Status.BAD: self.bad_swatch_holder,
            Status.NON_SCRAPED: self.non_scraped_swatch_holder,
            Status.NON_TRIMMED: self.non_trimmed_swatch_holder,
            Status.NON_TRIED: self.non_tried_swatch_holder,
            Status.FINISHED: self.finished_swatch_holder,
        }
        self._info = {
            "size": self.size_row,
            "rescued": self.rescued_row,
            "errors": self.errors_row,
            "file": self.file_row,
        }
        self.grid = MapGrid()
        self.grid.set_hexpand(True)
        self.grid.set_vexpand(True)
        self.grid.set_size_request(240, 180)
        self.grid_holder.append(self.grid)
        self.overview_holder.append(MapOverview(self.grid))
        self.zoom_scale.connect("value-changed", self._on_zoom_changed)
        self.grid.connect("view-changed", lambda *_: self._update_zoom_label())
        for status, holder in self._swatches.items():
            swatch = StatusSwatch()
            swatch.set_rgb(status.rgb)
            holder.append(swatch)
        self.grid.connect("cell-hover", self._on_hover)
        self.cell_size_scale.connect(
            "value-changed", lambda scale: self.grid.set_cell_size(scale.get_value())
        )
        self.blend_switch.connect(
            "notify::active",
            lambda switch, _pspec: self.grid.set_blend(switch.get_active()),
        )
        try:
            self.load(path)
        except MapFileError as e:
            self.toast_overlay.add_toast(Adw.Toast(title=f"Cannot read map file: {e}"))

    def load(self, path: str):
        """Load and display `path`. Raises MapFileError on failure."""
        mf = load_mapfile(path)
        self.path = path
        self.map = mf
        self.grid.set_map(mf)
        self._update_stats()
        self.set_title(f"Drive Health — {os.path.basename(path)}")

    def _on_zoom_changed(self, scale):
        # The slider is logarithmic: 0 is the whole map, 100 is one sector per cell.
        self.grid.set_zoom(round(self.grid.max_zoom() ** (scale.get_value() / 100)))
        self._update_zoom_label()

    def _update_zoom_label(self):
        per_cell = self.grid.bytes_per_cell()
        self.zoom_label.set_label(f"1 cell = {format_size(per_cell)}" if per_cell else "")

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


class MapHealth:
    """Callable that shows a health window for a ddrescue mapfile.

        MapHealth(parent=main_window)("/path/to/rescue.map")
    """

    def __init__(self, parent: Gtk.Window | None = None, modal: bool = False):
        self.parent = parent
        self.modal = modal

    def __call__(self, path: str) -> MapHealthWindow:
        app = self.parent.get_application() if self.parent else None
        win = MapHealthWindow(path=path, application=app)
        if self.parent:
            win.set_transient_for(self.parent)
            win.set_modal(self.modal)
        win.present()
        return win
