#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1920
HEIGHT = 1080
FPS = 10


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a zero-token Quadro combined partner proof video."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output .mov path. Defaults to audit/quadro_combined_partner_proof_video_<utc>.mov",
    )
    args = parser.parse_args()

    capture = json.loads((ROOT / "audit" / "submission_demo_latest.json").read_text())
    proof = (ROOT / "docs" / "public" / "SUBMISSION_DEMO_PROOF.md").read_text()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (
        Path(args.output)
        if args.output
        else ROOT / "audit" / f"quadro_combined_partner_proof_video_{stamp}.mov"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    slides = build_slides(capture, proof)
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (WIDTH, HEIGHT),
    )
    if not writer.isOpened():
        raise SystemExit(f"Could not open video writer for {output}")
    for slide in slides:
        frame = render_slide(slide)
        frame_array = np.array(frame)
        for _ in range(slide.get("seconds", 10) * FPS):
            writer.write(cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR))
    writer.release()
    print(output)


def build_slides(capture: dict, proof: str) -> list[dict]:
    summary = capture["summary"]
    aiml = capture.get("aimlapi_usage") or {}
    featherless = capture.get("featherless_usage") or {}
    proof_lines = compact_proof_lines(proof)
    errors = capture.get("partner_errors", {})
    return [
        {
            "eyebrow": "QUADRO CSI / BAND OF AGENTS",
            "title": "Combined Partner Capture Passed",
            "body": [
                f"Captured at UTC: {capture['captured_at_utc']}",
                "Providers requested: " + ", ".join(capture["providers_requested"]),
                f"Document set: {humanize(capture['document_set'])}",
                f"Outcome: {humanize(summary['outcome'])}",
                f"Gate: {humanize(summary['gate'])}",
                f"Recommendation: {humanize(summary['recommendation'])}",
                f"Risk: {humanize(summary['risk_level'])}",
            ],
            "chips": ["Band live", "Featherless live", "AI/ML API live", "No toy data"],
            "seconds": 12,
        },
        {
            "eyebrow": "AGENT HANDOFF / DECISION STATE",
            "title": "Revoked Consent Stops The Workflow",
            "body": [
                f"Band publish: {summary['band_ok']} / {summary['band_event_count']} events",
                f"Evidence items: {summary['evidence_items']}",
                "Input cohesion: "
                + f"{humanize(summary['input_cohesion_status'])} -> {humanize(summary['input_cohesion_next_gate'])}",
                f"Featherless verifier present: {summary['featherless_readout_present']}",
                f"AI/ML API verifier present: {summary['aimlapi_readout_present']}",
                "Partner errors: none" if not errors else f"Partner errors: {errors}",
            ],
            "chips": ["Customer Intake", "Evidence Spine", "Policy Risk", "Decision Packet"],
            "seconds": 12,
        },
        {
            "eyebrow": "PARTNER MODEL USAGE",
            "title": "Bounded Token Spend",
            "body": [
                "AI/ML API",
                f"  Model: {aiml.get('model')}",
                f"  {usage_line(aiml.get('usage'))}",
                "",
                "Featherless",
                f"  Model: {featherless.get('model')}",
                f"  {usage_line(featherless.get('usage'))}",
            ],
            "chips": ["AI/ML cap: 96 output tokens", "Saved artifact", "Replayable proof"],
            "seconds": 12,
        },
        {
            "eyebrow": "PUBLIC PROOF EXCERPT",
            "title": "Submission Demo Proof",
            "body": proof_lines[:18],
            "chips": ["docs/public/SUBMISSION_DEMO_PROOF.md"],
            "seconds": 14,
        },
        {
            "eyebrow": "ARTIFACT PACKAGE",
            "title": "Files Ready For Submission Package",
            "body": [
                f"audit/submission_demo_{capture['captured_at_utc']}.json",
                "audit/submission_demo_latest.json",
                "docs/public/SUBMISSION_DEMO_PROOF.md",
                "",
                "Verification commands:",
                ".venv/bin/python -m unittest discover -s tests",
                ".venv/bin/python scripts/run_document_sets.py",
                ".venv/bin/python scripts/check_public_boundary.py",
            ],
            "chips": ["Band + Featherless + AI/ML", "SAY_NO", "stopped_consent_revoked"],
            "seconds": 12,
        },
    ]


def compact_proof_lines(text: str) -> list[str]:
    lines = []
    keep = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("| Document set") or line.startswith("## Featherless"):
            keep = True
        if line.startswith("## Partner Errors"):
            keep = False
        if keep and line and not line.startswith("```"):
            lines.append(line)
    return lines


def humanize(value: object) -> str:
    text = str(value).replace("_", " ").strip()
    if text.upper() == "SAY NO":
        return "SAY NO"
    return text[:1].upper() + text[1:]


def usage_line(usage: object) -> str:
    if not isinstance(usage, dict):
        return "Usage: not returned"
    total = usage.get("total_tokens", "not returned")
    prompt = usage.get("prompt_tokens", "not returned")
    completion = usage.get("completion_tokens", "not returned")
    return f"Usage: {total} total tokens ({prompt} prompt, {completion} completion)"


def render_slide(slide: dict) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f7fbfd")
    draw = ImageDraw.Draw(image)
    font_title = font(84, bold=True)
    font_eyebrow = font(28, bold=True)
    font_body = font(34)
    font_chip = font(24, bold=True)
    font_footer = font(22)

    draw.rectangle((0, 0, WIDTH, 110), fill="#061018")
    draw.text((72, 34), slide["eyebrow"], fill="#d8a82e", font=font_eyebrow)
    draw.text((72, 150), slide["title"], fill="#111820", font=font_title)
    draw.line((72, 255, WIDTH - 72, 255), fill="#53b4d0", width=4)

    x = 92
    y = 295
    for line in wrapped_lines(slide["body"], width=84):
        draw.text((x, y), line, fill="#142332", font=font_body)
        y += 46
        if y > 880:
            break

    chip_x = 72
    chip_y = HEIGHT - 130
    for chip in slide.get("chips", []):
        tw = draw.textlength(chip, font=font_chip)
        draw.rounded_rectangle(
            (chip_x, chip_y, chip_x + tw + 34, chip_y + 46),
            radius=8,
            fill="#e7f5fb",
            outline="#66bdd8",
            width=2,
        )
        draw.text((chip_x + 17, chip_y + 10), chip, fill="#0b536b", font=font_chip)
        chip_x += int(tw) + 52
        if chip_x > WIDTH - 320:
            break

    draw.text(
        (WIDTH - 610, HEIGHT - 55),
        "Renaissance Field Lite / Quadro CSI proof playback",
        fill="#566273",
        font=font_footer,
    )
    return image


def wrapped_lines(lines: Iterable[str], width: int) -> list[str]:
    out: list[str] = []
    for line in lines:
        if not line:
            out.append("")
            continue
        wrapped = textwrap.wrap(line, width=width, replace_whitespace=False)
        out.extend(wrapped or [line])
    return out


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
