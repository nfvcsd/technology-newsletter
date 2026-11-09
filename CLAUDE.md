# CLAUDE.md

Notes for Claude on how this repo works. Read this before changing anything.
`README.md` is the human-facing guide; this file covers the reasoning, the
conventions, and the traps.

## What this is

**Tech Bytes** is the weekly tech newsletter from the North Fayette Valley CSD
(NFVCSD, Iowa) Technology Department. Each issue teaches one small,
bite-sized skill, mostly macOS and classroom ed-tech, with short animated
demos. Readers are staff (teachers, paras, admin) and sometimes students, so
write for a busy adult and keep anything student-facing friendly.

The owner is Alex Snyder, Technology Director. He wants Python, a
GitOps-friendly workflow (everything in git, CI builds and deploys), and code
that is clean and easy to read. Match the existing style: small, typed,
documented functions; no clever one-liners; comments explain *why*.

- Repo: `nfvcsd/technology-newsletter` (public)
- Live site: https://nfvcsd.github.io/technology-newsletter/ (GitHub Pages)
- Deploy: `.github/workflows/publish.yml` runs `python build.py` and deploys
  `site/` on every push to `main`. PRs build only, as a check.
- The claude.ai project "technology-newsletter" has `claude/issue-log.md`, a
  running list of issues and topics. Read it before planning a new issue so
  topics don't repeat, and add a row when an issue ships.

## How the build works

```
python build.py                  # full build into site/ (needs Playwright + Chromium)
python build.py --skip-images    # HTML only; no browser needed
python build.py --base-url URL   # override base_url, e.g. file://$PWD/site/ to preview emails locally
```

`build.py` wipes and recreates `site/` (gitignored), then:

1. Copies `brand/fonts`, `brand/logos`, and `styles/*.css` into `site/assets/`.
2. Renders each `cheatsheets/*.yaml` with `templates/cheatsheet.html.j2` into
   `site/cheatsheets/<name>.html`.
3. For each `issues/NNN-slug/`: renders `body.html.j2` into `site/<slug>.html`.
   If `email.html.j2` exists, it also renders `site/email/<slug>.html` and an
   `.eml` draft (`X-Unsent: 1` makes Outlook open it as a new message).
4. Renders `site/index.html` (the archive).
5. Unless `--skip-images`: `render.py` screenshots each cheat sheet to PNG, and
   records every `[data-gif]` demo on each issue page to
   `site/media/<slug>/<name>.gif`.

Modules:

- `keys.py` turns `"shift cmd 4"` into `Key` objects. Each key has an SVG
  `icon` for the web, plus `symbol`/`plain` (⌘ ⌥ ⌃ ⇧) for email. An unknown
  multi-character token raises `ValueError`, so typos fail the build.
- `render.py` does all the headless-browser work. Playwright and Pillow are
  imported lazily so `--skip-images` works without them.
- Jinja runs with `StrictUndefined`. Any missing variable is an error.

## Adding a weekly issue

1. Check `claude/issue-log.md` in the project for past topics.
2. Copy `issues/001-quick-keys/` to `issues/NNN-short-slug/`. Edit
   `issue.yaml`: `number`, `title`, `published` (the Monday it goes out),
   `summary` (used as the email preview text), and `cheatsheets`.
3. Write `body.html.j2` (web) and then `email.html.j2` (email), with the same
   words in both. The email is not generated from the web page; keep them in
   sync by hand.
4. Build, check (see "Checking your work"), and hand the files to Alex. He
   commits and pushes. Don't commit or push unless he asks, and use a branch
   when you do.
5. Add the issue to `claude/issue-log.md`.

### Issue shape (keep it bite-sized)

Issue 1 is the reference. The pattern:

- Hero: kicker ("Issue N · This week's skill"), two-part brand headline, 1–2
  sentence lede, a rule.
- One or two short concept sections, each with one animated demo.
- A card grid or short list of the key items.
- Callouts: "New on your Mac" (version-gated features), "Try it this week"
  (one concrete challenge), "Classroom corner" (student memory hooks plus
  Spanish vocabulary for multilingual learners).
- Optional bottom band: a cheat sheet PNG with Copy image and Download buttons.

## Content rules

- **District rules:** never include student personal information. Student
  materials need supports for multilingual learners and students with
  disabilities, described in asset-based language. Family-facing text goes at
  about a 6th-grade reading level. Treat the teacher as the audience and
  expect them to adapt.
- **Accuracy:** check every shortcut or feature claim against Apple's
  documentation (https://support.apple.com/en-us/102650 for shortcuts), or the
  vendor's for other tools. Look up the current macOS versions before writing
  version notes. As of Nov 2026 the supported releases are Sequoia 15, Tahoe
  26, and macOS 27. Tag newer features with `since:` (cheat sheets) or a
  "macOS X and later" kicker (issues).
- **Voice:** plain, warm, short sentences, second person. No hype. Avoid
  "not X, but Y" constructions and em-dash asides.
- **Modifier order:** write combos in Apple's order: `ctrl opt shift cmd`.

## Brand (NFV "How we look" v1.0)

- Open Sans only, self-hosted in `brand/fonts` (OFL). ExtraBold or Bold for
  headlines; Regular for body. Left-aligned, never justified.
- Colors live in `styles/brand.css` as `--nfv-*` tokens. Text is Black
  `#231F20` on white; accents are Navy `#002F6D` and Light Blue `#6AB2E2`.
  **Never set text in Light Blue on white**: its contrast is 2.3:1. Light Blue
  is for fills, rules, and text on dark backgrounds.
- Signature headline: `ui.headline("Lead phrase.", "continuation")` gives an
  uppercase line with a navy ExtraBold lead.
- Logos: use only the files in `brand/logos/`, and never redraw, recolor, or
  add effects. Use the horizontal color logo on white and the reversed logo on
  Midnight. Use the SVGs on the web and the PNGs in email. Keep clear space of
  about 25% of the logo's height.
- Graphics: simple geometric shapes and thin rules only. No clip art, emoji
  section markers, or starbursts.

## Animations (web)

Each demo is pure CSS: no JS animation libraries. Each issue keeps its own
demo CSS in its `body.html.j2`, so building a new issue never changes an old
one. Copy what you need from an earlier issue rather than sharing it.

- One loop per demo: set `--dur` on the figure. Every element in that demo
  animates on that same duration with keyframe percentages, so all the parts
  stay in sync. Plan the timeline as percentages first (e.g. select 10–22%,
  copy 30–42%, paste 62–74%), then write the keyframes.
- The numbered `.steps` list under each demo highlights in time with the
  animation, and it is also the text version for screen readers. Mark the
  visual stage `aria-hidden="true"`.
- Required on every demo: the `pause_button()` toolbar (WCAG 2.2.2), and a
  `prefers-reduced-motion` block that turns animations off and shows the
  finished state.
- Attach pointers and highlights to the text span they act on, so layout
  changes can't knock them out of place. Give those spans `white-space: nowrap`
  so they don't break across lines; that broke the highlight once.
- Give every keyframe in an animation the same set of properties. If a
  property such as `color` appears in only some keyframes, the browser fades it
  across the gap between them, and the element looks dim for most of the loop.
  That happened to the Record button in Issue 2.
- For the email GIF, add `data-gif="name" data-gif-seconds="<loop length>"
  data-gif-start="<0–1>"` to the `<figure>`. Start on a frame that makes sense
  alone, usually the finished state, because Outlook for Windows shows only
  the first frame.

## Email version

Email apps don't run CSS animations, `<style>` blocks (Gmail drops them on
paste), CSS variables, SVG, or JS. So:

- Use only the `em.` macros in `templates/email_macros.html.j2`: inline
  styles, a 600px table, hex colors, keycaps as styled text spans, and each
  demo as a GIF via `gifs["name"]`. `em.shortcut` takes `join="then"` for
  sequences like ⇧⌘4 then Space.
- Build every image and link URL with `absolute(path)`, which resolves against
  `base_url`. The email loads its images from the live site, so the issue must
  be pushed and deployed before anyone sends it.
- Keep the email HTML under about 100 KB (Gmail clips longer messages; issue 1
  is about 35 KB) and each GIF under about 500 KB (issues 1–2 run 145–345 KB).
- Single column only. A paste into Gmail strips media queries, so layouts
  can't change for phones.

**Sending is Alex's job, always by hand.** He opens
`<base_url>email/<slug>.html` in Chrome, presses ⌘A then ⌘C, and pastes into a
new Gmail message. Claude never sends email, never creates drafts, and never
builds automated sending, even when a mail connector is available. The `.eml`
file is there only as a manual fallback for Outlook or Apple Mail.

## Cheat sheets

`cheatsheets/*.yaml` sets the page size (Letter at 150 dpi CSS, rendered 2x),
the sections with a `column` number from 1 to 3, and the shortcuts:

```yaml
- { keys: shift cmd 4, action: Select an area }
- { keys: [shift cmd 4, space], join: then, action: One window }
- { keys: opt left/right, action: Jump word by word }      # slash = alternatives
- { keys: cmd space, action: Spotlight, since: Tahoe 26 }
```

Quote any `action` that contains a comma, such as `"Copy area, don't save"`.
YAML flow mappings split on commas and silently drop the rest of the text.
Keep actions short (about 25 characters) so they fit on one line, and balance
the three columns by eye.

## Checking your work

Always look at the output before handing it over:

- Screenshot each page at 1280px and 390px with Playwright (`full_page=True`).
- To check a demo at a given moment, seek every animation and pause it:
  `document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms % a.effect.getComputedTiming().duration })`.
  Use `document.getAnimations()`, not the element's own
  `element.getAnimations()`, because the element version misses `::before`
  animations.
- Preview the email locally with `--base-url "file://$PWD/site/"` at 720px and
  375px widths. Rebuild without the flag before shipping.
- Open the cheat sheet PNG and check its alignment and that nothing overflows.
- Run `ruff check *.py`.

## Environment notes

- **Cloud workspace:** Google Fonts, npm, and PyPI may all be blocked, which
  is why fonts are vendored. Public GitHub repos can be cloned through the git
  proxy (that's how Open Sans was fetched from `googlefonts/opensans`).
  Playwright and Chromium come preinstalled.
- **Alex's Mac (linked folder):** the files are in
  `~/Documents/GitHub/technology-newsletter`. Its shell is a Linux VM with
  Python 3.10 and no network or Playwright, so build in the cloud workspace and
  copy files across. `--skip-images` builds do work there, but in a temp copy
  only.
- **No deletes in the linked folder:** deleting is off by default, so
  `build.py`'s wipe of `site/` fails there. Don't run git commands that delete
  or rewrite files either.
- **`.github/` is protected:** the file tools can't write to `.github/`. Put
  workflow changes in `setup/` and ask Alex to move them.
- Before copying files over, run `git status` in the linked folder so his own
  edits don't get overwritten. He has edited `newsletter.yaml` and
  `.gitignore` himself.
