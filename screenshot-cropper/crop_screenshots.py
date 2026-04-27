"""crop_screenshots.py - Crop UI chrome from screenshots in place.

Default margins are tuned for a 1720x968 headless Playwright / code-server
viewport. Only the VS Code tab bar (top) and status bar (bottom) are removed:

  top    = 32
  bottom = 18
  left   = 0
  right  = 0

The script defaults to the ``assets/`` directory and can be overridden with CLI
flags or environment variables.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency during bootstrap
    load_dotenv = None


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR / ".env"
DEFAULT_INPUT_DIR = SCRIPT_DIR / "assets"

DEFAULT_TOP = 32
DEFAULT_BOTTOM = 18
DEFAULT_LEFT = 0
DEFAULT_RIGHT = 0


def _maybe_load_env() -> None:
    if load_dotenv is not None and ENV_FILE.exists():
        load_dotenv(ENV_FILE)


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid integer: {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"Value must be >= 0, got: {parsed}")
    return parsed


def _env_or_default(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return _non_negative_int(raw)
    except argparse.ArgumentTypeError as exc:
        raise SystemExit(f"[ERROR] Environment variable {name}: {exc}") from exc


def _positive_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.exists() else path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crop UI chrome from screenshots in-place."
    )
    parser.add_argument(
        "--input-dir",
        type=_positive_path,
        default=_positive_path(os.environ.get("SCREENSHOTS_DIR", str(DEFAULT_INPUT_DIR))),
        help="Directory containing PNG screenshots to crop.",
    )
    parser.add_argument(
        "--top",
        type=_non_negative_int,
        default=_env_or_default("CROP_TOP", DEFAULT_TOP),
    )
    parser.add_argument(
        "--bottom",
        type=_non_negative_int,
        default=_env_or_default("CROP_BOTTOM", DEFAULT_BOTTOM),
    )
    parser.add_argument(
        "--left",
        type=_non_negative_int,
        default=_env_or_default("CROP_LEFT", DEFAULT_LEFT),
    )
    parser.add_argument(
        "--right",
        type=_non_negative_int,
        default=_env_or_default("CROP_RIGHT", DEFAULT_RIGHT),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing any files.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Save originals as *.orig.png before overwriting.",
    )
    return parser.parse_args()


def _iter_pngs(input_dir: Path) -> list[Path]:
    pngs = sorted(input_dir.rglob("*.png"))
    return [path for path in pngs if not path.name.endswith(".orig.png")]


def main() -> int:
    _maybe_load_env()
    args = parse_args()

    if not args.input_dir.exists():
        print(f"[INFO] {args.input_dir} does not exist - no screenshots to crop.")
        return 0

    pngs = _iter_pngs(args.input_dir)
    if not pngs:
        print(f"[INFO] No PNG files found in {args.input_dir}.")
        return 0

    try:
        from PIL import Image
    except ImportError:
        print("[ERROR] Pillow is not installed. Run: pip install -r requirements.txt", file=sys.stderr)
        return 1

    processed = 0
    skipped = 0
    total_pixels_before = 0
    total_pixels_after = 0

    for png in pngs:
        with Image.open(png) as img:
            width, height = img.size

            right_coord = width - args.right if args.right > 0 else width
            bottom_coord = height - args.bottom if args.bottom > 0 else height

            if args.left >= right_coord or args.top >= bottom_coord:
                print(
                    f"[SKIP] {png.relative_to(args.input_dir)} - margins exceed image size ({width}x{height}), skipping."
                )
                skipped += 1
                continue

            box = (args.left, args.top, right_coord, bottom_coord)
            new_width = right_coord - args.left
            new_height = bottom_coord - args.top

            total_pixels_before += width * height
            total_pixels_after += new_width * new_height

            rel_name = png.relative_to(args.input_dir)
            if args.dry_run:
                print(f"[DRY-RUN] {rel_name}: {width}x{height} -> {new_width}x{new_height} (crop box {box})")
                processed += 1
                continue

            if args.backup:
                backup_path = png.with_suffix(".orig.png")
                import shutil

                shutil.copy2(png, backup_path)
                print(f"[BACKUP] {rel_name} -> {backup_path.name}")

            cropped = img.crop(box)
            cropped.save(png)
            print(f"[CROP] {rel_name}: {width}x{height} -> {new_width}x{new_height}")
            processed += 1

    print()
    print("-- Crop Summary ----------------------------------")
    print(f"  Files processed : {processed}")
    print(f"  Files skipped   : {skipped}")
    if total_pixels_before > 0:
        reduction_pct = 100 * (1 - total_pixels_after / total_pixels_before)
        print(f"  Pixel reduction : ~{reduction_pct:.1f}%")
    if args.dry_run:
        print("  (dry-run - no files were written)")
    print("--------------------------------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())