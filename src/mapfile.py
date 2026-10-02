"""Parser and statistics for GNU ddrescue map (log) files. No GTK dependency."""

import bisect
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class MapFileError(Exception):
    pass


class Status(Enum):
    NON_TRIED = ("?", "Non-tried", "Not yet attempted", (0x90, 0x90, 0x90))
    NON_TRIMMED = ("*", "Non-trimmed", "Failed block edges not yet trimmed", (0xFF, 0xE0, 0x00))
    NON_SCRAPED = ("/", "Non-scraped", "Trimmed, not yet scraped", (0x20, 0x20, 0xFF))
    BAD = ("-", "Bad sector", "Read failed; unrecoverable so far", (0xFF, 0x00, 0x00))
    FINISHED = ("+", "Finished", "Successfully rescued", (0x20, 0xE0, 0x20))

    def __init__(self, char, label, description, rgb):
        self.char, self.label, self.description, self.rgb = char, label, description, rgb

    @classmethod
    def from_char(cls, ch: str) -> "Status":
        for s in cls:
            if s.char == ch:
                return s
        raise MapFileError(f"Unknown block status {ch!r}")


# Order in which a mixed cell is reported: the "worst" status wins.
SEVERITY = [Status.BAD, Status.NON_SCRAPED, Status.NON_TRIMMED, Status.NON_TRIED, Status.FINISHED]

PASS_NAMES = {
    "?": "Non-tried", "*": "Copying", "/": "Trimming", "-": "Scraping",
    "F": "Filling", "G": "Generating", "+": "Finished",
}
PASS_NAMES.update({"1": "Copying", "2": "Trimming", "3": "Sweeping", "4": "Scraping"})


@dataclass
class Block:
    pos: int
    size: int
    status: Status

    @property
    def end(self) -> int:
        return self.pos + self.size


@dataclass
class MapFile:
    path: str | None = None
    blocks: list[Block] = field(default_factory=list)
    current_pos: int = 0
    current_status: str = "?"
    current_pass: int | None = None
    comments: list[str] = field(default_factory=list)
    _starts: list[int] = field(default_factory=list, repr=False)

    @property
    def start(self) -> int:
        return self.blocks[0].pos if self.blocks else 0

    @property
    def end(self) -> int:
        return self.blocks[-1].end if self.blocks else 0

    @property
    def total(self) -> int:
        return self.end - self.start

    @property
    def command_line(self) -> str | None:
        for c in self.comments:
            if c.lower().startswith("command line:"):
                return c.split(":", 1)[1].strip()
        return None

    @property
    def version(self) -> str | None:
        for c in self.comments:
            if "GNU ddrescue version" in c:
                return c.rsplit("version", 1)[1].strip()
        return None

    @property
    def phase(self) -> str:
        return PASS_NAMES.get(self.current_status, self.current_status)

    def totals(self) -> dict[Status, int]:
        out = {s: 0 for s in Status}
        for b in self.blocks:
            out[b.status] += b.size
        return out

    def count(self) -> dict[Status, int]:
        out = {s: 0 for s in Status}
        for b in self.blocks:
            out[b.status] += 1
        return out

    def block_at(self, offset: int) -> Block | None:
        if not self._starts:
            return None
        i = bisect.bisect_right(self._starts, offset) - 1
        if i >= 0 and self.blocks[i].pos <= offset < self.blocks[i].end:
            return self.blocks[i]
        return None

    def range_totals(self, lo: int, hi: int) -> dict[Status, int]:
        """Bytes of each status within [lo, hi)."""
        out = {s: 0 for s in Status}
        if not self._starts or hi <= lo:
            return out
        i = max(bisect.bisect_right(self._starts, lo) - 1, 0)
        while i < len(self.blocks) and self.blocks[i].pos < hi:
            b = self.blocks[i]
            overlap = min(hi, b.end) - max(lo, b.pos)
            if overlap > 0:
                out[b.status] += overlap
            i += 1
        return out

    def grid(self, cells: int) -> list[dict[Status, int]]:
        """Split the map into `cells` equal spans and return per-status bytes for each."""
        if cells <= 0 or self.total <= 0:
            return []
        span = self.total / cells
        return [
            self.range_totals(self.start + int(i * span), self.start + int((i + 1) * span))
            for i in range(cells)
        ]


def parse_mapfile(text: str, path: str | None = None) -> MapFile:
    mf = MapFile(path=path)
    status_seen = False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            mf.comments.append(line.lstrip("#").strip())
            continue
        parts = line.split()
        try:
            if not status_seen:
                mf.current_pos = int(parts[0], 0)
                mf.current_status = parts[1]
                if len(parts) > 2:
                    mf.current_pass = int(parts[2])
                status_seen = True
                continue
            pos, size = int(parts[0], 0), int(parts[1], 0)
            status = Status.from_char(parts[2])
        except (IndexError, ValueError, MapFileError) as e:
            raise MapFileError(f"Line {n}: cannot parse {raw!r} ({e})") from e
        if size <= 0:
            continue
        # Merge adjacent same-status blocks to keep the list small.
        if mf.blocks and mf.blocks[-1].status is status and mf.blocks[-1].end == pos:
            mf.blocks[-1].size += size
        else:
            mf.blocks.append(Block(pos, size, status))
    if not mf.blocks:
        raise MapFileError("No data blocks found; not a ddrescue map file?")
    mf.blocks.sort(key=lambda b: b.pos)
    mf._starts = [b.pos for b in mf.blocks]
    return mf


def load_mapfile(path: str | Path) -> MapFile:
    p = Path(path)
    try:
        text = p.read_text(errors="replace")
    except OSError as e:
        raise MapFileError(str(e)) from e
    return parse_mapfile(text, str(p))


def format_size(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(n) < 1024 or unit == "PiB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024
