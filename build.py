"""Build the Tech Bytes newsletter into a static site.

    python build.py               # full build into site/
    python build.py --skip-images # HTML only (fast, no browser needed)

Layout of the output:

    site/
      index.html                  archive of every issue
      <issue-slug>.html           one page per issue
      cheatsheets/<name>.html     printable web version of each cheat sheet
      cheatsheets/<name>.png      the same sheet as an image staff can copy
      assets/                     brand CSS, fonts, and logos
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from keys import ICON_PATHS, parse_combo, spoken

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "site"
ISSUES_DIR = ROOT / "issues"
CHEATSHEETS_DIR = ROOT / "cheatsheets"


@dataclass(frozen=True)
class Issue:
    """One newsletter issue, read from issues/<slug>/issue.yaml."""

    slug: str
    number: int
    title: str
    published: date
    summary: str
    cheatsheets: list[str] = field(default_factory=list)

    @property
    def template(self) -> str:
        return f"{self.slug}/body.html.j2"

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_issues() -> list[Issue]:
    """All issues, newest first."""
    issues = []
    for meta_path in sorted(ISSUES_DIR.glob("*/issue.yaml")):
        meta = read_yaml(meta_path)
        issues.append(
            Issue(
                slug=meta_path.parent.name,
                number=meta["number"],
                title=meta["title"],
                published=meta["published"],
                summary=meta["summary"],
                cheatsheets=meta.get("cheatsheets", []),
            )
        )
    return sorted(issues, key=lambda issue: issue.number, reverse=True)


def load_cheatsheets() -> dict[str, dict[str, Any]]:
    return {path.stem: read_yaml(path) for path in sorted(CHEATSHEETS_DIR.glob("*.yaml"))}


def make_environment(site: dict[str, Any]) -> Environment:
    env = Environment(
        loader=FileSystemLoader([ROOT / "templates", ISSUES_DIR]),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=StrictUndefined,  # a typo in a template fails the build
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(
        site=site,
        parse_combo=parse_combo,
        spoken=spoken,
        icon_paths=ICON_PATHS,
    )
    return env


def copy_assets() -> None:
    """Copy brand fonts, logos, and stylesheets into site/assets."""
    assets = OUTPUT_DIR / "assets"
    shutil.copytree(ROOT / "brand" / "fonts", assets / "fonts")
    shutil.copytree(ROOT / "brand" / "logos", assets / "logos")
    for stylesheet in (ROOT / "styles").glob("*.css"):
        shutil.copy2(stylesheet, assets / stylesheet.name)


def write_page(env: Environment, template: str, destination: Path, **context: Any) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = env.get_template(template).render(**context)
    destination.write_text(html, encoding="utf-8")
    print(f"  wrote {destination.relative_to(ROOT)}")


def screenshot_pages(pages: list[tuple[Path, dict[str, Any]]]) -> None:
    """Render each (html_path, sheet) pair to a PNG next to it.

    Imported lazily so `--skip-images` works without Playwright installed.
    """
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
            page.screenshot(path=png_path, full_page=False)
            page.close()
            print(f"  wrote {png_path.relative_to(ROOT)}")
        browser.close()


def build(skip_images: bool) -> None:
    site = read_yaml(ROOT / "newsletter.yaml")
    env = make_environment(site)
    issues = load_issues()
    cheatsheets = load_cheatsheets()

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()
    copy_assets()

    print("Cheat sheets")
    rendered_sheets = []
    for name, sheet in cheatsheets.items():
        html_path = OUTPUT_DIR / "cheatsheets" / f"{name}.html"
        write_page(env, "cheatsheet.html.j2", html_path, sheet=sheet)
        rendered_sheets.append((html_path, sheet))

    print("Issues")
    for issue in issues:
        missing = set(issue.cheatsheets) - cheatsheets.keys()
        if missing:
            raise SystemExit(f"Issue {issue.slug} uses unknown cheat sheet(s): {sorted(missing)}")
        write_page(
            env,
            issue.template,
            OUTPUT_DIR / issue.filename,
            issue=issue,
            cheatsheets={name: cheatsheets[name] for name in issue.cheatsheets},
        )
    write_page(env, "index.html.j2", OUTPUT_DIR / "index.html", issues=issues)

    if skip_images:
        print("Skipping PNG rendering (--skip-images)")
    else:
        print("Images")
        screenshot_pages(rendered_sheets)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-images", action="store_true", help="skip rendering cheat sheet PNGs")
    args = parser.parse_args()
    build(skip_images=args.skip_images)


if __name__ == "__main__":
    main()
