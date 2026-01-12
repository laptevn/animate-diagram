import argparse
import io
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import cairosvg
from PIL import Image

SVG_NS = "http://www.w3.org/2000/svg"
NS = {"svg": SVG_NS}
ET.register_namespace("", SVG_NS)

TOKEN_RE = re.compile(r"[A-Za-z]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")
NUMBER_RE = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")


@dataclass
class PathInfo:
    start: Tuple[float, float]
    end: Tuple[float, float]
    length: float


@dataclass
class ArrowLine:
    element: ET.Element
    direction_sign: int


def tokenize_path(path_data: str) -> List[str]:
    return TOKEN_RE.findall(path_data)


def split_subpaths(path_data: str) -> List[str]:
    tokens = tokenize_path(path_data)
    if not tokens:
        return []

    subpaths: List[str] = []
    current: List[str] = []
    for token in tokens:
        if token in {"M", "m"} and current:
            subpaths.append(" ".join(current))
            current = []
        current.append(token)
    if current:
        subpaths.append(" ".join(current))
    return subpaths


def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _apply_command(
    command: str, params: List[float], current: Tuple[float, float]
) -> Tuple[float, float]:
    x, y = current
    is_relative = command.islower()
    cmd = command.upper()
    if cmd in {"M", "L", "T"}:
        nx, ny = params[0], params[1]
        if is_relative:
            return x + nx, y + ny
        return nx, ny
    if cmd == "H":
        nx = params[0]
        return (x + nx, y) if is_relative else (nx, y)
    if cmd == "V":
        ny = params[0]
        return (x, y + ny) if is_relative else (x, ny)
    if cmd == "C":
        nx, ny = params[4], params[5]
        if is_relative:
            return x + nx, y + ny
        return nx, ny
    if cmd in {"S", "Q"}:
        nx, ny = params[2], params[3]
        if is_relative:
            return x + nx, y + ny
        return nx, ny
    if cmd == "A":
        nx, ny = params[5], params[6]
        if is_relative:
            return x + nx, y + ny
        return nx, ny
    return current


def parse_path(path_data: str) -> Optional[PathInfo]:
    tokens = tokenize_path(path_data)
    if not tokens:
        return None

    param_counts = {
        "M": 2,
        "L": 2,
        "H": 1,
        "V": 1,
        "C": 6,
        "S": 4,
        "Q": 4,
        "T": 2,
        "A": 7,
    }

    current = (0.0, 0.0)
    start: Optional[Tuple[float, float]] = None
    length = 0.0
    cmd: Optional[str] = None
    pending_move = False
    i = 0

    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            cmd = token
            i += 1
            if cmd in {"Z", "z"}:
                if start is not None:
                    length += _distance(current, start)
                    current = start
                continue
            if cmd in {"M", "m"}:
                pending_move = True
            continue

        if cmd is None:
            break

        effective_cmd = cmd
        if cmd in {"M", "m"} and not pending_move:
            effective_cmd = "L" if cmd == "M" else "l"
        if cmd in {"M", "m"} and pending_move:
            pending_move = False

        param_count = param_counts.get(effective_cmd.upper())
        if param_count is None or i + param_count > len(tokens):
            break
        params = [float(value) for value in tokens[i : i + param_count]]
        i += param_count

        next_point = _apply_command(effective_cmd, params, current)
        if effective_cmd.upper() == "M":
            if start is None:
                start = next_point
            current = next_point
            continue

        length += _distance(current, next_point)
        current = next_point

    if start is None:
        return None
    return PathInfo(start=start, end=current, length=length)


def parse_style(style: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for part in style.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        key, value = part.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def serialize_style(styles: Dict[str, str]) -> str:
    return "; ".join(f"{key}: {value}" for key, value in sorted(styles.items()))


def find_arrow_lines(root: ET.Element) -> List[ArrowLine]:
    arrow_lines: List[ArrowLine] = []
    for group in root.findall(".//svg:g[@mask]", NS):
        path_elements = [
            path
            for path in group.findall(".//svg:path", NS)
            if path.get("d")
        ]
        if len(path_elements) < 2:
            continue

        path_infos: List[Tuple[ET.Element, PathInfo, str]] = []
        for path in path_elements:
            path_data = path.get("d", "")
            subpaths = split_subpaths(path_data)
            best_info: Optional[PathInfo] = None
            best_subpath = ""
            for subpath in subpaths:
                info = parse_path(subpath)
                if info and (best_info is None or info.length > best_info.length):
                    best_info = info
                    best_subpath = subpath
            if best_info:
                path_infos.append((path, best_info, best_subpath))

        if len(path_infos) < 2:
            continue

        line_path, line_info, line_subpath = max(
            path_infos, key=lambda item: item[1].length
        )
        arrowhead_infos = [
            info for element, info, _ in path_infos if element is not line_path
        ]
        if not arrowhead_infos:
            continue

        tip_x = sum(info.end[0] for info in arrowhead_infos) / len(arrowhead_infos)
        tip_y = sum(info.end[1] for info in arrowhead_infos) / len(arrowhead_infos)
        tip = (tip_x, tip_y)

        dist_start = _distance(line_info.start, tip)
        dist_end = _distance(line_info.end, tip)
        head_is_end = dist_end <= dist_start
        direction_sign = -1 if head_is_end else 1
        if line_subpath:
            line_path.set("d", line_subpath)
        arrow_lines.append(ArrowLine(element=line_path, direction_sign=direction_sign))

    return arrow_lines


def relocate_masks_to_defs(root: ET.Element) -> None:
    defs = root.find("svg:defs", NS)
    if defs is None:
        defs = ET.Element(f"{{{SVG_NS}}}defs")
        root.insert(0, defs)

    parent_map = {child: parent for parent in root.iter() for child in parent}
    for mask in list(root.findall(".//svg:mask", NS)):
        parent = parent_map.get(mask)
        if parent is None or parent is defs:
            continue
        parent.remove(mask)
        defs.append(mask)


def parse_svg_dimensions(root: ET.Element) -> Tuple[int, int]:
    def parse_number(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        match = NUMBER_RE.search(value)
        if not match:
            return None
        return float(match.group(0))

    width = parse_number(root.get("width"))
    height = parse_number(root.get("height"))

    if (width is None or height is None) and root.get("viewBox"):
        parts = [float(p) for p in root.get("viewBox", "").split() if p]
        if len(parts) == 4:
            width = width if width is not None else parts[2]
            height = height if height is not None else parts[3]

    if width is None or height is None:
        raise RuntimeError("SVG width/height could not be determined.")

    return int(round(width)), int(round(height))


class ChromiumRenderer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self) -> "ChromiumRenderer":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is required for Chromium rendering. "
                "Install it with: pip install playwright && playwright install chromium"
            ) from exc

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch()
        self._page = self._browser.new_page(
            viewport={"width": self.width, "height": self.height}
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def render(self, svg_markup: str) -> bytes:
        if not self._page:
            raise RuntimeError("Chromium renderer is not initialized.")

        html = (
            "<!doctype html><html><head><meta charset=\"utf-8\">"
            "<style>html,body{margin:0;padding:0;background:#fff;}"
            "svg{display:block;}</style></head><body>"
            f"{svg_markup}</body></html>"
        )
        self._page.set_content(html, wait_until="load")
        self._page.wait_for_function("document.fonts.status === 'loaded'")
        return self._page.screenshot(type="png")


def apply_dash_style(
    element: ET.Element,
    dash_length: float,
    gap_length: float,
    dash_offset: float,
) -> None:
    style = parse_style(element.get("style", ""))
    style["stroke-dasharray"] = f"{dash_length} {gap_length}"
    style["stroke-dashoffset"] = f"{dash_offset}"
    element.set("style", serialize_style(style))


def render_frames(
    root: ET.Element,
    arrow_lines: Iterable[ArrowLine],
    frames: int,
    dash_length: float,
    gap_length: float,
    step: float,
    duration_ms: int,
    output_path: str,
    renderer: str,
) -> None:
    images: List[Image.Image] = []
    arrow_lines = list(arrow_lines)
    if renderer == "chromium":
        width, height = parse_svg_dimensions(root)
        with ChromiumRenderer(width, height) as chromium_renderer:
            for frame_index in range(frames):
                offset = frame_index * step
                for arrow in arrow_lines:
                    apply_dash_style(
                        arrow.element,
                        dash_length,
                        gap_length,
                        arrow.direction_sign * offset,
                    )

                svg_markup = ET.tostring(root, encoding="unicode")
                png_bytes = chromium_renderer.render(svg_markup)
                image = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                images.append(image)
    else:
        for frame_index in range(frames):
            offset = frame_index * step
            for arrow in arrow_lines:
                apply_dash_style(
                    arrow.element,
                    dash_length,
                    gap_length,
                    arrow.direction_sign * offset,
                )

            svg_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
            image = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            images.append(image)

    if not images:
        raise RuntimeError("No frames rendered.")

    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animate arrows in an SVG diagram and export a GIF."
    )
    parser.add_argument("input_svg", help="Path to the input SVG file.")
    parser.add_argument("output_gif", help="Path to the output GIF file.")
    parser.add_argument("--frames", type=int, default=12, help="Number of frames.")
    parser.add_argument(
        "--dash-length", type=float, default=6.0, help="Length of dash segments."
    )
    parser.add_argument(
        "--gap-length", type=float, default=6.0, help="Length of gaps between dashes."
    )
    parser.add_argument(
        "--step", type=float, default=2.0, help="Dash offset step per frame."
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=80,
        help="Frame duration in milliseconds.",
    )
    parser.add_argument(
        "--renderer",
        choices=("chromium", "cairosvg"),
        default="chromium",
        help="Renderer to use for SVG frames.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        tree = ET.parse(args.input_svg)
    except ET.ParseError as exc:
        print(f"Failed to parse SVG: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    root = tree.getroot()
    relocate_masks_to_defs(root)
    arrow_lines = find_arrow_lines(root)
    if not arrow_lines:
        print("No arrow lines detected in the SVG.", file=sys.stderr)
        raise SystemExit(1)

    try:
        render_frames(
            root=root,
            arrow_lines=arrow_lines,
            frames=args.frames,
            dash_length=args.dash_length,
            gap_length=args.gap_length,
            step=args.step,
            duration_ms=args.duration,
            output_path=args.output_gif,
            renderer=args.renderer,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
