# Tech Bytes

The NFV Technology Department's weekly newsletter: one small tech skill per
issue, with short animated demos, for staff and students.

Content lives in plain text (YAML and Jinja templates). `build.py` turns it into
a static site, and GitHub Actions publishes that site to GitHub Pages on every
push to `main`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # only needed for the PNG cheat sheets

python build.py                # full build into site/
python build.py --skip-images  # faster: HTML only
open site/index.html
```

## Layout

```
newsletter.yaml          site name, tagline, contact
issues/
  001-quick-keys/
    issue.yaml           number, title, date, summary, cheat sheets used
    body.html.j2         the issue itself, including its CSS animations
cheatsheets/
  macos-shortcuts.yaml   shortcut data; rendered to .html and .png
templates/
  base.html.j2           page shell: masthead, footer
  macros.html.j2         keycaps, combos, brand headline
  cheatsheet.html.j2     cheat sheet layout (US Letter, 300 dpi PNG)
  index.html.j2          archive page
styles/
  brand.css              NFV colors and Open Sans
  components.css         keycaps and combos
  newsletter.css         page layout
brand/
  fonts/                 Open Sans (SIL Open Font License, see OFL.txt)
  logos/                 official NFV logo files
keys.py                  turns "cmd shift 4" into keycaps
build.py                 the build
```

## Writing shortcuts

Shortcuts are space-separated key names, written in Apple's modifier order
(`ctrl`, `opt`, `shift`, `cmd`):

| You write              | It shows            |
|------------------------|---------------------|
| `cmd C`                | ⌘ C                 |
| `shift cmd 4`          | ⇧ ⌘ 4               |
| `opt left/right`       | ⌥ ← / →             |
| `["ctrl cmd space", "fn E"]` | two combos joined by "or" |

Named keys: `ctrl opt shift cmd fn delete esc tab return space left right up down`.
Any single character is shown as-is. An unknown name such as `cmmd` stops the
build with an error, so typos can't slip through.

Modifier symbols are drawn as SVG icons rather than font characters, because
Open Sans doesn't include them. That keeps the PNG identical on every machine.

## Adding an issue

1. Copy `issues/001-quick-keys/` to `issues/002-your-topic/`.
2. Edit `issue.yaml` (bump `number`, set `published`).
3. Rewrite `body.html.j2`. Keep the `{% extends "base.html.j2" %}` line and the
   pause-button script if the issue has animations.
4. Run `python build.py`, check `site/`, then commit on a branch and open a PR.
   The workflow builds every PR, so a broken template fails the check before
   it reaches `main`.

## Publishing

`.github/workflows/publish.yml` builds the site and deploys it to GitHub Pages.
One-time setup:

1. Move `setup/publish.yml` to `.github/workflows/publish.yml` (if it isn't
   there already) and delete the `setup/` folder.
2. In the repo, choose **Settings → Pages → Source → GitHub Actions**.

Pages on a private repository needs a paid GitHub plan (or GitHub Education);
the published site is public either way.

## Brand and accessibility

- Colors, type, and logos follow the NFV brand guide (*How we look*, v1.0). Use
  only the files in `brand/logos/`.
- Light Blue (`#6AB2E2`) is never used for text on white; it fails contrast.
- Animations pause with the on-page button and are replaced by a still,
  finished state when a visitor's device asks for reduced motion.
- Every demo has a numbered, text-only version of its steps for screen readers.
