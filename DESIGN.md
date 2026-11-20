---
name: M-Film (mfilm.app)
description: A camera maker's product page, dark and quiet, with amber only where something can be done.
colors:
  ground: "#0b0b0a"
  surface: "#141413"
  surface-raised: "#1c1b19"
  hairline: "#2b2a27"
  hairline-strong: "#3a3835"
  ink-faint: "#8a847b"
  ink-muted: "#b0a99f"
  ink: "#ece8e1"
  amber: "#eca834"
  amber-hi: "#f4bd5c"
  amber-ink: "#17110a"
  signal-red: "#e0442f"
  error-ink: "#ff9c8a"
typography:
  display:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "clamp(40px, 5.4vw, 76px)"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "clamp(30px, 3.6vw, 48px)"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  lede:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 500
    lineHeight: 1.6
  body:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 500
    lineHeight: 1.6
  body-small:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.5
  label:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    letterSpacing: "0.08em"
  figure:
    fontFamily: "Barlow, Noto Sans Thai, Leelawadee UI, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 600
    letterSpacing: "-0.01em"
    fontFeature: "tnum"
  wordmark:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    letterSpacing: "0.1em"
rounded:
  none: "0px"
  control: "6px"
  dialog: "10px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  band-head: "48px"
  band: "120px"
  band-narrow: "88px"
  gutter-min: "16px"
  container: "1240px"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.amber-ink}"
    rounded: "{rounded.control}"
    padding: "0 22px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.amber-hi}"
    textColor: "{colors.amber-ink}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 22px"
    height: "48px"
  button-small:
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "36px"
  select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 40px 0 14px"
    height: "40px"
  shelf-tab:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    padding: "0 0 12px"
  shelf-tab-active:
    textColor: "{colors.ink}"
  lang-toggle:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.control}"
    height: "32px"
  dialog:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.dialog}"
    padding: "32px 28px 26px"
    width: "460px"
  error-box:
    textColor: "{colors.error-ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
---

# Design System: M-Film (mfilm.app)

## Overview

**Creative North Star: "The Camera Maker's Product Page"**

mfilm.app is built the way Leica and Fujifilm present a camera: a near-black ground, one working camera as the product shot, and real developed frames as the photography. Everything around them stays quiet so the camera and the photographs carry the page. Type is large and calm, rules are hairlines, and colour appears only where the visitor can act.

The page is a single dark column with wide bands. The playable camera sits centred at the top, then each band opens with a two-column head (headline left, a short paragraph right) over hairline-ruled content: three numbered columns, a film viewer with its shelf, a spec table, a three-column price row, the download steps and the questions. Nothing is boxed in cards; grouping comes from rules and spacing.

English and Thai are equals. Barlow carries Latin and Noto Sans Thai (Thai subset, self-hosted) carries Thai in the same stack, and every tracked or uppercase treatment drops for Thai.

**Key Characteristics:**
- Near-black warm ground with every grey drawn from one ramp.
- Amber is the only colour, kept for actions, the active state and progress.
- Barlow at 500 and 600, large and quiet; tabular figures wherever numbers are compared.
- Hairline rules instead of cards; square photographs; 6px corners on controls only.
- Three motion gestures (develop, shutter curtain, frame counter) and 150 to 300 ms colour and opacity changes for everything else.

## Colors

One warm neutral ramp from near-black to warm paper white, one amber, and one red that belongs to errors and to the camera's own live signal.

### Primary
- **Darkroom Amber** (`amber`): the Download buttons, the active film's name, the active shelf tab underline, done and current try-it steps, the install progress line and meter, focus rings, selection and caret. Shared with the README and the camera; a brand commitment.
- **Amber, Lit** (`amber-hi`): hover on amber buttons and on the active progress segment only.
- **Amber Ink** (`amber-ink`): text set on amber.

### Neutral
- **Darkroom Black** (`ground`): the page, the sticky header, the sticky install progress bar.
- **Lifted Black** (`surface`): the one lifted surface: the download dialog, selects, the install status box, the photo frame before it loads.
- **Raised Black** (`surface-raised`): menu-path chips in the install guide, film thumbnails while loading, dialog close hover.
- **Hairline** (`hairline`): row rules, the header's bottom rule, the line under the camera.
- **Strong Hairline** (`hairline-strong`): the rule that opens a group (top of a table, a column row, a list), control borders.
- **Faint Ink** (`ink-faint`): labels, counters, footers, secondary metadata.
- **Muted Ink** (`ink-muted`): body paragraphs and descriptions.
- **Paper Ink** (`ink`): headings, names, values, and the camera-status dots.

### Signal
- **Signal Red** (`signal-red`): errors, and the camera's own live-view and record signal (the status dot while live view runs, the live-view key's border), which the drawn camera also carries.
- **Error Ink** (`error-ink`): the text of an error message, readable on the dark ground.

### Named Rules
**The One Colour Rule.** Amber is the only hue on the page. It marks what can be pressed, what is active and how far along something is, never a decoration, a status or a heading.

**The Form-Not-Hue Rule.** Camera status in the table is told by the dot's form, filled (Working), half (Issues) or open ring (Testing), plus the word, in ink on the neutral ramp. Status never gets a colour of its own.

**The One Red Rule.** Red means an error, or the camera's live signal. It is never an accent.

## Typography

**Display Font:** Barlow (with Noto Sans Thai, Leelawadee UI, system-ui)
**Body Font:** Barlow, same stack
**Label/Mono Font:** Barlow for labels; the system monospace stack (ui-monospace, SF Mono, Menlo) only for card file trees in the install guide.
**Wordmark:** Barlow Condensed 700, tracked, for the M·FILM wordmark only.

**Character:** One grotesque at two weights, set large with slight negative tracking in headings and plain at body size. It reads as a maker's spec sheet, not a gadget ad.

### Hierarchy
- **Display** (600, clamp 40 to 76px, line-height 1): the home headline, one line on desktop and two on narrow screens. The install page sets its h1 at clamp(38px, 5vw, 60px); the 404 at clamp(44px, 8vw, 84px).
- **Headline** (600, clamp 30 to 48px, line-height 1.05): band headings.
- **Title** (600, 22 to 26px, line-height 1.25): step titles, film name in the viewer caption (24px), column heads in "how it works" (24px).
- **Lede** (500, 18 to 19px): the paragraph under a page headline.
- **Body** (500, 17px, line-height 1.6, max 64ch): paragraphs in Muted Ink.
- **Body small** (500, 14 to 15px): table notes, step descriptions, captions, footer.
- **Label** (600, 13px, 0.08 to 0.1em, uppercase): form field labels, the camera-picker label and the camera table's column heads. Faint Ink.
- **Figure** (600, 30px, tabular): prices; the price input sets at 42px and the firmware badge at 34px, both tabular.

### Named Rules
**The Tabular Figures Rule.** Every number that sits beside another (ISO, firmware versions, prices, step counts, shelf counts) uses tabular figures.

**The Thai Equals Rule.** Under `:lang(th)`, headings drop to letter-spacing 0 and line-height 1.25, and labels drop uppercase and tracking and step up to 14px. Thai has no capitals; nothing is tracked for it.

## Layout

A centred column. Bands sit in a 1240px container with a gutter of max(16px, 4vw), 120px apart (88px under 860px); the footer sits 140px below the last band. A band head is a two-column grid (headline, paragraph) aligned to the bottom with 48px under it, collapsing to one column under 860px.

The hero is centred: headline, lede, two actions, then the camera at 760px wide, whole within a 1440x900 viewport, with its status and dial keys on one hairline beneath, then the four try-it steps in one row (two under 820px).

The film viewer is the frame (3:2) beside a 340px shelf, stacking under 900px. Content grids use equal fractional columns with 32 to 64px gaps; the install guide is an 860px reading column. The header is 64px and sticky; the install progress bar sticks directly under it.

**The Rule-Not-Box Rule.** Groups open with a Strong Hairline across the top and separate rows with a Hairline. Containers do not get backgrounds or borders on all four sides.

## Elevation & Depth

Flat. Depth comes from the ramp (ground, then one lifted surface) and hairlines. The single shadow belongs to the modal download dialog, which floats over a dimmed backdrop (rgba(0,0,0,.72)); the lightbox is a near-opaque black field (rgba(5,5,5,.96)) with no shadow.

### Shadow Vocabulary
- **Dialog lift** (`box-shadow: 0 30px 60px rgba(0, 0, 0, .5)`): the download dialog only.

**The One Lift Rule.** Only a modal floats. Everything on the page lies flat on the ground.

## Shapes

Controls (buttons, selects, the language toggle, presets, chips, status and error boxes) take a 6px corner. The download dialog takes 10px. Photographs, the film viewer, thumbnails and screenshots are square-cornered. Circles are reserved for meaning: camera-status dots, the install step's frame-counter badge (40px ring) and the live-status dot. Line icons are 20px, stroke 1.6, round caps and joins, drawn in currentColor.

**The Square Print Rule.** A photograph is never rounded, framed or shadowed.

## Components

### Buttons
Solid and plain, like a camera's labelled key.
- **Shape:** 6px corners, 48px tall, 22px side padding; 600 weight at 16px.
- **Primary:** Darkroom Amber with Amber Ink text and a matching 1px border. One primary per group: Download, the detected OS's Darkrooms build, Next.
- **Hover / Focus:** background to Amber, Lit in 150ms; focus is a 2px amber outline, 3px offset.
- **Ghost:** transparent, Paper Ink text, Strong Hairline border; the border goes to Paper Ink on hover.
- **Small:** 36px tall, 14px padding, 15px text; header Download and the install Back and Next.
- **Disabled:** 40% opacity.

### Inputs / Fields
- **Select:** Lifted Black field, Strong Hairline border, 6px corners, 40px tall, a drawn chevron; border to Muted Ink on hover.
- **Price input:** a 42px tabular figure in a Darkroom Black field with an amber currency mark; the field border goes amber on focus-within. Presets are 38px ghost keys that turn amber (border and text) when chosen.
- **Error:** Error Ink text in a dark red-tinted box with 6px corners; empty errors are not rendered.

### Navigation
A 64px sticky header on Darkroom Black over a Hairline: the wordmark left; links in Muted Ink (to Paper Ink on hover), the TH/EN toggle as a 32px ghost key, and a small amber Download on the right. Under 760px only the toggle and Download remain.

### Shelf tabs
Text tabs on a Hairline with a tabular count in Faint Ink; the active tab is Paper Ink with a 2px amber underline. No pills.

### Film viewer (signature)
One large 3:2 frame and a scrolling shelf of film rows (64px thumbnail, name, ISO and process). Picking a film re-develops the frame: the first time it is seen it comes up from bare paper over 1.1s (brightness, contrast and saturation stepped toward 1, linear timing with the ease built into the values); each later pick runs a light 0.42s version so two films can still be compared. Thumbnails sit at 75% opacity and come to full on hover or when chosen; the chosen film's name turns amber. The frame opens a lightbox.

### Camera status (spec table)
A 9px dot with a 1.5px Paper Ink ring beside the status word in 600: filled for Working, left-half filled for Issues, an open Muted Ink ring for Testing.

### Install step form
One step at a time under a sticky bar holding the count ("2 of 6", tabular), a segmented 2px progress line (amber up to the current step) and Back and Next. Each step's number sits in a 40px amber ring and turns up like a frame counter (0.5s). Moving between steps runs a focal-plane shutter curtain: a clip that opens downward going forward and upward going back, 420ms on cubic-bezier(0.16, 1, 0.3, 1). The write-to-card meter is the same 2px amber line.

### Try-it steps
Four columns under a Strong Hairline, each with a tabular number; the current and finished steps turn their rule and number amber in 300ms.

## Do's and Don'ts

### Do:
- **Do** keep amber (#eca834) to actions, the active state and progress; let everything else come from the warm neutral ramp.
- **Do** tell camera status by dot form plus the word, in ink.
- **Do** open groups with a Strong Hairline and separate rows with a Hairline instead of drawing boxes.
- **Do** set every compared number in tabular figures.
- **Do** keep feedback transitions at 150 to 300ms (colour, border, opacity) and save larger motion for the develop, the shutter curtain and the frame counter.
- **Do** honour reduced motion: the develop and the curtain drop, and a step change becomes a 160ms fade.
- **Do** write every string in English and Thai, and drop tracking and uppercase for Thai.

### Don't:
- **Don't** introduce a second accent hue, or give camera status its own colour.
- **Don't** use red for anything but errors and the camera's live signal.
- **Don't** round, frame or shadow a photograph.
- **Don't** put content in shadowed or fully bordered cards; only the modal dialog lifts.
- **Don't** use gradient glows, badge rows, emoji icons or pill tabs on the page. The drawn camera's own shading is the camera's, not the page's.
- **Don't** set page type in weights other than 500 and 600; Barlow Condensed is the wordmark only.
- **Don't** change the film OS screens to suit the page.
