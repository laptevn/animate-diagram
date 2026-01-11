# Animate Diagram

CLI tool to animate data-flow arrows in SVG diagrams and export a GIF. This project was created by Codex.

Notes:
- Works with Excalidraw diagrams today.
- Other SVG sources are not fully tested but may work.

## How It Works
The tool detects arrow groups in the SVG (as Excalidraw exports them), infers the arrow direction, and applies a dashed stroke animation only to the arrow bodies. Each frame is rendered to PNG and then assembled into an animated GIF.

Before (source SVG):
![Source diagram](docs/source.svg)

After (animated GIF):
![Animated diagram](docs/output.gif)

## Build and Run
Requires Python 3.9+.

Install dependencies:
```bash
pip install -e .
```

Run the CLI:
```bash
python -m animate_diagram path/to/diagram.svg output.gif
```

Or via the console script:
```bash
animate-diagram path/to/diagram.svg output.gif
```

Useful flags:
```bash
animate-diagram input.svg output.gif --frames 12 --dash-length 6 --gap-length 6 --step 2 --duration 80
```

## License
MIT. See `LICENSE`.
