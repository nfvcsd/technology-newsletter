"""Build the Tech Bytes newsletter into a static site plus email versions.

    python build.py                 # full build into site/
    python build.py --skip-images   # HTML only (fast, no browser needed)
    python build.py --base-url URL  # point email images somewhere else (testing)

Layout of the output:

    site/
      index.html                  archive of every issue
      <issue-slug>.html           one page per issue
      media/<issue-slug>/*.gif    each animated demo recorded as a GIF
      email/<issue-slug>.html     email version: open, copy, paste into Gmail
      email/<issue-slug>.eml      the same email as a draft for Outlook or Apple Mail
      cheatsheets/<name>.html     printable web version of each cheat sheet
      cheatsheets/<name>.png      the same sheet as an image staff can copy
      assets/                     brand CSS, fonts, and logos
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from keys import ICON_PATHS, parse_combo, spoken

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "site"
ISSUES_DIR = ROOT / "issues"
CHEATSHEETS_DIR = ROOT / "cheatsheets"

# Matches data-gif="name" on demos in a rendered issue page.
GIF_ATTRIBUTE = re.compile(r'data-gif="([a-z0-9-]+)"')


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
    def email_template(self) -> str:
        return f"{self.slug}/email.html.j2"

    @property
    def has_email(self) -> bool:
        return (ISSUES_DIR / self.email_template).exists()

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"

    @property
    def media_dir(self) -> str:
        return f"media/{self.slug}"


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


def make_environment(site: dict[str, Any], base_url: str) -> Environment:
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
        # Emails are read outside the site, so their links and images need full URLs.
        absolute=lambda path: urljoin(base_url, path),
    )
    return env


def copy_assets() -> None:
    """Copy brand fonts, logos, and stylesheets into site/assets."""
    assets = OUTPUT_DIR / "assets"
    shutil.copytree(ROOT / "brand" / "fonts", assets / "fonts")
    shutil.copytree(ROOT / "brand" / "logos", assets / "logos")
    for stylesheet in (ROOT / "styles").glob("*.css"):
        shutil.copy2(stylesheet, assets / stylesheet.name)


def write_page(env: Environment, template: str, destination: Path, **context: Any) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = env.get_template(template).render(**context)
    destination.write_text(html, encoding="utf-8")
    print(f"  wrote {destination.relative_to(ROOT)}")
    return html


def write_draft_email(html: str, issue: Issue, site: dict[str, Any], issue_url: str, destination: Path) -> None:
    """Save an .eml draft. `X-Unsent: 1` makes Outlook open it as a new message ready to send."""
    message = EmailMessage()
    message["Subject"] = f"{site['name']} #{issue.number}: {issue.title}"
    message["X-Unsent"] = "1"
    message.set_content(f"{issue.summary}\n\nRead this issue online: {issue_url}\n")
    message.add_alternative(html, subtype="html")
    destination.write_bytes(bytes(message))
    print(f"  wrote {destination.relative_to(ROOT)}")


def build(skip_images: bool, base_url: str) -> None:
    site = read_yaml(ROOT / "newsletter.yaml")
    base_url = base_url or site.get("base_url", "")
    if not base_url.endswith("/"):
        raise SystemExit("Set base_url in newsletter.yaml (ending in /) so email images can load.")
    env = make_environment(site, base_url)
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
    issue_pages = []
    for issue in issues:
        missing = set(issue.cheatsheets) - cheatsheets.keys()
        if missing:
            raise SystemExit(f"Issue {issue.slug} uses unknown cheat sheet(s): {sorted(missing)}")
        context = {
            "issue": issue,
            "cheatsheets": {name: cheatsheets[name] for name in issue.cheatsheets},
        }
        page_path = OUTPUT_DIR / issue.filename
        page_html = write_page(env, issue.template, page_path, **context)
        issue_pages.append((issue, page_path))

        if issue.has_email:
            gifs = {name: f"{issue.media_dir}/{name}.gif" for name in GIF_ATTRIBUTE.findall(page_html)}
            email_path = OUTPUT_DIR / "email" / issue.filename
            email_html = write_page(env, issue.email_template, email_path, gifs=gifs, **context)
            write_draft_email(
                email_html, issue, site, urljoin(base_url, issue.filename), email_path.with_suffix(".eml")
            )
    write_page(env, "index.html.j2", OUTPUT_DIR / "index.html", issues=issues)

    if skip_images:
        print("Skipping PNG and GIF rendering (--skip-images)")
        return

    from render import record_demo_gifs, screenshot_cheatsheets

    print("Images")
    screenshot_cheatsheets(rendered_sheets)
    for issue, page_path in issue_pages:
        record_demo_gifs(page_path, OUTPUT_DIR / issue.media_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-images", action="store_true", help="skip rendering PNGs and GIFs")
    parser.add_argument("--base-url", default="", help="override base_url from newsletter.yaml")
    args = parser.parse_args()
    build(skip_images=args.skip_images, base_url=args.base_url)


if __name__ == "__main__":
    main()
