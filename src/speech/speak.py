#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "piper-tts>=1.2.0",
#   "pygame>=2.6.1",
# ]
# ///
"""Generate and play speech with a local Piper voice.

Run this file directly or with ``uv run src/speech/speak.py``.  Piper's
``.onnx`` model and matching ``.onnx.json`` metadata must be in ``voices/``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

DEFAULT_TEXT = "This is a test"
DEFAULT_VOICE_DIR = Path(__file__).resolve().parents[2] / "voices"


def available_voices(voice_dir: Path) -> list[Path]:
    """Return models that have the sidecar metadata required by Piper."""
    return sorted(
        model
        for model in voice_dir.glob("*.onnx")
        if model.with_name(f"{model.name}.json").is_file()
    )


def find_voice(voice: str, voice_dir: Path) -> Path:
    """Resolve a voice name or model path and validate its Piper sidecar."""
    candidate = Path(voice).expanduser()
    if not candidate.is_absolute():
        candidate = voice_dir / candidate
    if candidate.suffix != ".onnx":
        candidate = candidate.with_suffix(".onnx")

    if not candidate.is_file():
        voices = available_voices(voice_dir)
        names = ", ".join(model.stem for model in voices) or "none"
        raise FileNotFoundError(
            f"Voice model not found: {candidate}\n"
            f"Available voices in {voice_dir}: {names}"
        )

    metadata = candidate.with_name(f"{candidate.name}.json")
    if not metadata.is_file():
        raise FileNotFoundError(f"Voice metadata not found: {metadata}")
    return candidate


def text_to_speech(
    text: str,
    output_file: Path,
    voice: str,
    voice_dir: Path,
    length_scale: float = 1.0,
    play: bool = True,
) -> None:
    model = find_voice(voice, voice_dir)
    command = [
        sys.executable,
        "-m",
        "piper",
        "-m",
        str(model),
        "-f",
        str(output_file),
        "--length-scale",
        str(length_scale),
        "--",
        text,
    ]
    subprocess.run(command, check=True)
    print(f"Speech saved to {output_file}")

    if not play:
        return



    pygame.mixer.init()
    try:
        pygame.mixer.music.load(str(output_file))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    finally:
        pygame.mixer.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="*", help="Text to speak")
    parser.add_argument(
        "-v",
        "--voice",
        default="glados",
        help="Voice name or .onnx path (default: glados)",
    )
    parser.add_argument(
        "--voice-dir",
        type=Path,
        default=DEFAULT_VOICE_DIR,
        help=f"Directory containing Piper voices (default: {DEFAULT_VOICE_DIR})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output.wav"),
        help="Output WAV path (default: output.wav)",
    )
    parser.add_argument(
        "--length-scale",
        type=float,
        default=1.0,
        help=(
            "Speech timing multiplier: greater than 1 is slower, less than 1 "
            "is faster (default: 1.0)"
        ),
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Generate the WAV file without playing it",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.length_scale <= 0:
        raise SystemExit("--length-scale must be greater than 0")
    text = " ".join(args.text) if args.text else DEFAULT_TEXT
    text_to_speech(
        text,
        args.output,
        args.voice,
        args.voice_dir.expanduser(),
        length_scale=args.length_scale,
        play=not args.no_play,
    )


if __name__ == "__main__":
    main()
