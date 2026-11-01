"""Browser rendering: cheat sheet PNGs and animated GIFs of the issue demos.

Email apps don't run CSS animations, so each demo marked with ``data-gif`` is
played frame by frame in a headless browser and saved as a GIF for the email
version of the issue:

    <figure class="demo" data-gif="copy-paste" data-gif-seconds="10" data-gif-start="0.8">

- ``data-gif``          output name, saved as ``<name>.gif``
- ``data-gif-seconds``  length of the animation loop
- ``data-gif-start``    where in the loop the GIF begins (0 to 1). Outlook on
                        Windows shows only the first frame, so start on a frame
                        that makes sense on its own, such as the finished result.

Playwright is imported inside each function so ``build.py --skip-images``
works on a machine without it.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

GIF_FRAMES_PER_SECOND = 12
GIF_COLORS = 128
# The issue page has 32px side gutters, so this viewport makes each demo panel
# 600 CSS pixels wide: the standard email width.
GIF_VIEWPORT_WIDTH = 664
# 1.5x keeps text crisp on high-density screens without huge files.
GIF_SCALE = 1.5

# Jump every CSS animation on the page to the same moment, then hold it there.
SEEK_ANIMATIONS = """ms => document.getAnimations().forEach(animation => {
  animation.pause();
  const loop = animation.effect.getComputedTiming().duration;
  animation.currentTime = ms % loop;
})"""

# The pause button means nothing inside a GIF.
HIDE_PAGE_CONTROLS = ".demo__toolbar { display: none !important; }"


def screenshot_cheatsheets(pages: list[tuple[Path, dict[str, Any]]]) -> None:
    """Render each (html_path, sheet) pair to a PNG next to the HTML file."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for html_path, sheet in pages:
            page = browser.new_page(
                viewport={"width": sheet["width"], "height": sheet["height"]},
                device_scale_factor=sheet.get("scale", 2),
            )
            page.goto(html_path.as_uri())
            page.evaluate("document.fonts.ready")
            png_path = html_path.with_suffix(".png")
            page.screenshot(path=png_path)
            page.close()
            print(f"  wrote {png_path.name}")
        browser.close()


def record_demo_gifs(page_path: Path, output_dir: Path) -> list[Path]:
    """Save every ``[data-gif]`` demo on the page as an animated GIF."""
    from playwright.sync_api import sync_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": GIF_VIEWPORT_WIDTH, "height": 1000},
            device_scale_factor=GIF_SCALE,
        )
        page.goto(page_path.as_uri())
        page.add_style_tag(content=HIDE_PAGE_CONTROLS)
        page.evaluate("document.fonts.ready")

        for demo in page.locator("[data-gif]").all():
            name = demo.get_attribute("data-gif")
            seconds = float(demo.get_attribute("data-gif-seconds") or 0)
            start = float(demo.get_attribute("data-gif-start") or 0)
            if not name or seconds <= 0:
                raise ValueError("Each [data-gif] demo needs a name and data-gif-seconds")

            panel = demo.locator(".demo__panel")
            frame_count = round(seconds * GIF_FRAMES_PER_SECOND)
            frames = []
            for index in range(frame_count):
                moment_ms = (start * seconds + index / GIF_FRAMES_PER_SECOND) * 1000
                page.evaluate(SEEK_ANIMATIONS, moment_ms)
                frames.append(Image.open(BytesIO(panel.screenshot())).convert("RGB"))

            gif_path = output_dir / f"{name}.gif"
            save_gif(frames, gif_path, frame_ms=1000 / GIF_FRAMES_PER_SECOND)
            print(f"  wrote {gif_path.name} ({gif_path.stat().st_size // 1024} KB)")
            written.append(gif_path)
        browser.close()
    return written


def save_gif(frames: list[Image.Image], path: Path, frame_ms: float) -> None:
    """Write frames as a looping GIF.

    Identical neighbouring frames are merged into one longer frame, and every
    frame shares one palette so colors don't flicker between frames.
    """
    unique: list[Image.Image] = []
    durations: list[float] = []
    for frame in frames:
        if unique and ImageChops.difference(frame, unique[-1]).getbbox() is None:
            durations[-1] += frame_ms
        else:
            unique.append(frame)
            durations.append(frame_ms)

    palette = _shared_palette(unique)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in unique]
    indexed[0].save(
        path,
        save_all=True,
        append_images=indexed[1:],
        duration=[round(ms) for ms in durations],
        loop=0,
        optimize=True,
        disposal=1,
    )


def _shared_palette(frames: list[Image.Image]) -> Image.Image:
    """One palette built from a sample of all frames."""
    sample = frames[:: max(1, len(frames) // 12)]
    width, height = sample[0].size
    sheet = Image.new("RGB", (width, height * len(sample)))
    for offset, frame in enumerate(sample):
        sheet.paste(frame, (0, offset * height))
    return sheet.quantize(colors=GIF_COLORS, method=Image.Quantize.MEDIANCUT)
