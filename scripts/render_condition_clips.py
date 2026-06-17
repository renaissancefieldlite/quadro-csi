#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1280
HEIGHT = 720
FPS = 12

CLIPS = [
    {
        "id": "01_pass_scoped_refund",
        "slug": "approve_scoped_refund",
        "condition": "Consent, refund evidence, and approval policy are present.",
        "concept": "Quadro approves only the scoped next step and still leaves human signoff in place.",
    },
    {
        "id": "02_block_revoked_consent",
        "slug": "say_no_revoked_consent",
        "condition": "Customer authorization was withdrawn before export.",
        "concept": "Quadro stops the workflow even though evidence exists, because consent is no longer valid.",
    },
    {
        "id": "03_block_missing_approval_policy",
        "slug": "need_more_info_missing_approval",
        "condition": "Consent and financial evidence exist, but required approval policy evidence is missing.",
        "concept": "Quadro blocks signoff until the missing authority evidence is attached.",
    },
    {
        "id": "04_revisit_consent_narrowed",
        "slug": "approve_after_consent_reroute",
        "condition": "Consent changes mid-workflow and narrows the usable source scope.",
        "concept": "Quadro reroutes evidence and policy review, then approves only the newly scoped packet.",
    },
    {
        "id": "08_government_procurement_policy_block",
        "slug": "say_no_policy_prohibition",
        "condition": "The vendor screen triggers a hard procurement policy prohibition.",
        "concept": "Quadro says no on policy grounds, even with review authorization present.",
    },
]


def main() -> None:
    output_dir = ROOT / "docs" / "public" / "media"
    output_dir.mkdir(parents=True, exist_ok=True)
    results = load_results()
    rendered = []
    for clip in CLIPS:
        result = results[clip["id"]]
        manifest = json.loads(
            (ROOT / "data" / "evaluation_sets" / clip["id"] / "manifest.json").read_text()
        )
        rendered.append(render_clip(output_dir, clip, manifest, result))
    print(json.dumps({"condition_clips": rendered}, indent=2))


def load_results() -> dict[str, dict]:
    raw = subprocess.check_output(
        [str(ROOT / ".venv" / "bin" / "python"), str(ROOT / "scripts" / "run_document_sets.py")],
        cwd=ROOT,
        text=True,
    )
    payload = json.loads(raw)
    return {item["id"]: item for item in payload["document_sets"]}


def render_clip(output_dir: Path, clip: dict, manifest: dict, result: dict) -> dict:
    output = output_dir / f"quadro_condition_{clip['slug']}.mp4"
    poster = output_dir / f"quadro_condition_{clip['slug']}.jpg"
    with tempfile.TemporaryDirectory() as tmp:
        frame_dir = Path(tmp)
        frames = build_frames(clip, manifest, result)
        for index, image in enumerate(frames):
            image.save(frame_dir / f"frame_{index:04d}.png")
        frames[0].save(poster, quality=88)
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                str(FPS),
                "-i",
                str(frame_dir / "frame_%04d.png"),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            cwd=ROOT,
        )
    return {
        "id": clip["id"],
        "video": str(output.relative_to(ROOT)),
        "poster": str(poster.relative_to(ROOT)),
        "outcome": result["outcome"],
        "gate": result["gate"],
    }


def build_frames(clip: dict, manifest: dict, result: dict) -> list[Image.Image]:
    seconds = 8
    total = seconds * FPS
    frames = []
    stages = ["Input", "Evidence", "Policy", "Decision"]
    for idx in range(total):
        phase = min(len(stages) - 1, int(idx / total * len(stages)))
        frames.append(render_frame(clip, manifest, result, stages, phase, idx / total))
    return frames


def render_frame(
    clip: dict,
    manifest: dict,
    result: dict,
    stages: list[str],
    active_stage: int,
    progress: float,
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f7fbfd")
    draw = ImageDraw.Draw(image)
    font_eyebrow = font(22, bold=True)
    font_title = font(48, bold=True)
    font_subtitle = font(25)
    font_body = font(25)
    font_body_bold = font(25, bold=True)
    font_small = font(18)
    font_chip = font(18, bold=True)

    draw.rectangle((0, 0, WIDTH, 76), fill="#061018")
    draw.text((44, 24), "QUADRO CSI / ACCEPTANCE CONDITION", fill="#d8a82e", font=font_eyebrow)

    title = manifest["title"].replace("Block:", "Block -").replace("Pass:", "Pass -")
    title_lines = wrapped(title, 40)[:2]
    title_y = 102
    for line in title_lines:
        draw.text((44, title_y), line, fill="#101820", font=font_title)
        title_y += 55
    rule_y = 170 if len(title_lines) == 1 else 222
    draw.line((44, rule_y, WIDTH - 44, rule_y), fill="#54bdd8", width=4)

    y = rule_y + 35
    draw_label_value(draw, "Dataset", clip["id"], 44, y, font_body_bold, font_body)
    y += 43
    for line in wrapped(clip["condition"], 68):
        draw_label_value(draw, "Trigger" if y == 248 else "", line, 44, y, font_body_bold, font_body)
        y += 35
    y += 6
    for line in wrapped(clip["concept"], 78):
        draw.text((44, y), line, fill="#283746", font=font_body)
        y += 33

    metric_y = 432
    cards = [
        ("Outcome", humanize_outcome(result["outcome"])),
        ("Gate", humanize(result["gate"])),
        ("Risk", humanize(result["risk_level"])),
        ("Evidence", f"{result['evidence_items']} items"),
    ]
    card_w = 280
    for i, (label, value) in enumerate(cards):
        x = 44 + i * (card_w + 18)
        draw.rounded_rectangle((x, metric_y, x + card_w, metric_y + 112), 10, fill="#ffffff", outline="#cfe3ee", width=2)
        draw.text((x + 18, metric_y + 16), label.upper(), fill="#6a7986", font=font_small)
        fill = outcome_color(result["outcome"]) if label == "Outcome" else "#101820"
        for j, line in enumerate(wrapped(value, 18)[:2]):
            draw.text((x + 18, metric_y + 46 + j * 28), line, fill=fill, font=font_body_bold)

    chain_y = 585
    x = 44
    for i, stage in enumerate(stages):
        fill = "#0b7fa2" if i <= active_stage else "#e7f5fb"
        text_fill = "#ffffff" if i <= active_stage else "#0b536b"
        draw.rounded_rectangle((x, chain_y, x + 164, chain_y + 48), 8, fill=fill, outline="#66bdd8", width=2)
        draw.text((x + 18, chain_y + 13), stage, fill=text_fill, font=font_chip)
        if i < len(stages) - 1:
            draw.line((x + 172, chain_y + 24, x + 218, chain_y + 24), fill="#66bdd8", width=3)
        x += 226

    bar_w = WIDTH - 88
    draw.rounded_rectangle((44, HEIGHT - 42, 44 + bar_w, HEIGHT - 30), 6, fill="#d6eaf2")
    draw.rounded_rectangle((44, HEIGHT - 42, 44 + int(bar_w * progress), HEIGHT - 30), 6, fill="#0b7fa2")
    draw.text((WIDTH - 360, HEIGHT - 68), "Renaissance Field Lite / Quadro CSI", fill="#60717f", font=font_small)
    return image


def draw_label_value(draw, label: str, value: str, x: int, y: int, label_font, value_font) -> None:
    if label:
        draw.text((x, y), f"{label}:", fill="#0b536b", font=label_font)
        x += 112
    draw.text((x, y), value, fill="#182636", font=value_font)


def wrapped(text: str, width: int) -> list[str]:
    import textwrap

    return textwrap.wrap(str(text), width=width) or [str(text)]


def humanize(value: object) -> str:
    return str(value).replace("_", " ").strip().capitalize()


def humanize_outcome(value: object) -> str:
    text = str(value)
    if text == "SAY_NO":
        return "SAY NO"
    if text == "NEED_MORE_INFO":
        return "NEED MORE INFO"
    return text


def outcome_color(value: object) -> str:
    return {
        "APPROVE": "#1f8a5b",
        "SAY_NO": "#b93737",
        "NEED_MORE_INFO": "#a06913",
    }.get(str(value), "#101820")


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
