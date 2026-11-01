# Tech Bytes

The NFV Technology Department's weekly newsletter: one small tech skill per
issue, with short animated demos, for staff and students.

Content lives in plain text (YAML and Jinja templates). `build.py` turns it into
a static site plus an email version of every issue, and GitHub Actions publishes
the site to GitHub Pages on every push to `main`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # only needed for the PNGs and GIFs

python build.py                # full build into site/
python build.py --skip-images  # faster: HTML only
open site/index.html
```

## Layout

```
newsletter.yaml          site name, tagline, contact, public base_url
issues/
  001-quick-keys/
    issue.yaml           number, title, date, summary, cheat sheets used
    body.html.j2         the issue itself, including its CSS animations
    email.html.j2        the email version of the issue
cheatsheets/
  macos-shortcuts.yaml   shortcut data; rendered to .html and .png
templates/
  base.html.j2           page shell: masthead, footer
  macros.html.j2         keycaps, combos, brand headline
  cheatsheet.html.j2     cheat sheet layout (US Letter, 300 dpi PNG)
  index.html.j2          archive page
  email_base.html.j2     email shell: masthead, footer, 600px table
  email_macros.html.j2   email building blocks, all inline styles
styles/
  brand.css              NFV colors and Open Sans
  components.css         keycaps and combos
  newsletter.css         page layout
brand/
  fonts/                 Open Sans (SIL Open Font License, see OFL.txt)
  logos/                 official NFV logo files
keys.py                  turns "cmd shift 4" into keycaps
render.py                headless browser: cheat sheet PNGs and demo GIFs
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
   pause-button script if the issue has animations. Give each animated demo
   `data-gif`, `data-gif-seconds`, and `data-gif-start` attributes so the build
   records it as a GIF (details at the top of `render.py`).
4. Rewrite `email.html.j2` with the same content, using the `em.` macros.
   Refer to each demo GIF as `gifs["name"]`.
5. Run `python build.py`, check `site/`, then commit on a branch and open a PR.
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

## Sending an issue by email

Email apps don't run CSS animations, scripts, or SVG, so each issue also has an
email version. It uses the same words, shows each demo as an animated GIF, and
loads its images from the live site at `base_url`. Push the issue and let
the site publish before you send, or the images won't load.

The build writes two copies to `site/email/`:

- **Gmail:** open `<base_url>email/<issue-slug>.html` in Chrome, press ⌘A then
  ⌘C, and paste into a new Gmail message with ⌘V. Add the subject, address it
  to your staff group, and send.
- **Outlook or Apple Mail:** open `<issue-slug>.eml`. Outlook opens it as a new
  draft. In Apple Mail, choose **Message → Send Again** to make it editable.

Send yourself a test first. Things to know:

- Outlook for Windows shows only the first frame of a GIF, so each GIF starts
  on its finished state (`data-gif-start`).
- Gmail cuts off messages over about 100 KB of HTML. Issue 1 is about 35 KB.
- Every email has a link at the top to open the full animated issue online.

## Brand and accessibility

- Colors, type, and logos follow the NFV brand guide (*How we look*, v1.0). Use
  only the files in `brand/logos/`.
- Light Blue (`#6AB2E2`) is never used for text on white; it fails contrast.
- Animations pause with the on-page button and are replaced by a still,
  finished state when a visitor's device asks for reduced motion.
- Every demo has a numbered, text-only version of its steps for screen readers.
