# What can Lomography's film pages give us as a reference?

Research note for [issue #96](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/96), a child of the map in [issue #93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). Every page was read on 2026-11-13, logged out, in a normal browser. The evidence is Lomography's own pages: its `robots.txt`, its Terms & Conditions, its film index and a small sample of film and photo pages. Where a statement is my own reasoning and not something a page says, it is marked **(my reasoning)**.

A note on quoting. I work under a limit on how much of a site's own text I may reproduce, so the terms are paraphrased closely here, with the name of the section each point comes from, and only one short phrase is quoted word for word. Each section is a single click away at [T]. Read the original before relying on any wording.

## Short answer

- **The catalogue is a list of film names that members typed, not one page per film stock.** The index says it holds over 49,000 different film names [F]. One film stock is spread over dozens of names: a filter for "portra" lists about a hundred, among them plain, per-format, expired and pushed variants, misspellings, and names that hold several films at once [Q1]. Each name has its own page and its own photo count.
- **All seven first-set film stocks have a main name page with tens of thousands of photos**, from about 22,000 (Fuji Pro 400H) to about 163,000 (Ilford HP5 Plus 400). Of all 72 film stocks, 41 have a matching name that I saw, 5 have only a near match, 1 was looked for and not listed (CineStill 400T), and 25 were not checked.
- **A photo page says nothing about scanning or editing.** In 9 photo pages across the 7 film stocks there was no field for lab, scanner, development or adjustments on any of them. The fields that exist are photographer, upload date, camera, film, lens, tags, city, country, decade, year, time of day and album. Camera was filled in 9 of 9, lens 2 of 9.
- **The photos belong to the people who uploaded them, and visitors get no licence to them.** The terms give Lomography a broad non-exclusive licence, tell visitors to assume everything is under copyright, and say the service is for personal, non-commercial use [T].
- **Automated access is forbidden by the terms unless Lomography agrees**, even though `robots.txt` leaves `/films` and `/photos` open to crawlers [R][T]. The clause names bots, software and any other way of pulling data out of the site; its wording is quoted in Part four. It makes no exception for programs that keep nothing. An API exists, on a path that `robots.txt` closes to crawlers, and by a third party's account it needs a key that Lomography hands out on request [A1][A2].
- **So: looking by eye is fine; measuring with a program is not, without consent.** That holds whether or not the photos are stored. The terms do not mention numbers derived from photos at all.
- **As a reference it is uncontrolled.** The film label is unverified free text, the scan and edit are unknown, a large share of some film stocks' photos come from plastic-lens toy cameras, and the default view of each film page is a set hand-picked by Lomography. It shows what people post under a film's name. It cannot show what the film does under known conditions.

## Part one: how the catalogue is organised

### What a film page is

- The index at `/films` shows 100 film names as links and says the archive holds photos taken with over 49,000 different films [F]. 
- The names are free text typed by members. This is my reading of what the filter returns, not a statement by the site: a filter for "portra" lists names such as a plain "Kodak Portra 400", a second identical-looking "Kodak Portra 400", "(35mm)" and "(120)" variants, "expired" variants, one marked as shot at 800, a misspelt one, and several that name two to four films in one entry [Q1].
- Each name has a page at `/films/<number>-<slug>`, which redirects to `/films/<number>-<slug>/photos`. The page gives one photo count for that name, a grid of 50 photos per page with a pager, and four orders: Trending, Recent, Popular, Selected [P1].
- With no order chosen, the page shows Selected. The page itself says this is a curated set hand-picked by Lomography and a smaller subset of all photos [P1].
- Each film page also lists "popular combinations" of that film name with a camera, a decade, a year, a country or a time of day, each with a rounded figure such as "(4k)" [P1]. I read these figures as photo counts for the combination **(my reasoning)**. The links lead into `/browse`, which `robots.txt` disallows [R], so I did not follow them.
- The index has a filter box. It loads `/films?query=<text>`, which is inside the path `robots.txt` allows, and returns matching names with no counts [Q1].

### The seven first-set film stocks

Counts are as shown on each page on 2026-11-13. Each count is for that one name only, not for the film stock across all its names.

| M-Film film stock | Lomography name | Page | Photos shown |
|---|---|---|---|
| Kodak Portra 400 | Kodak Portra 400 | https://www.lomography.com/films/871910984-kodak-portra-400 | 115,935 |
| Kodak Gold 200 | Kodak Gold 200 | https://www.lomography.com/films/871958647-kodak-gold-200 | 48,384 |
| Kodak Ektar 100 | Kodak Ektar 100 | https://www.lomography.com/films/871912245-kodak-ektar-100 | 109,711 |
| Fujichrome Velvia 50 | Fuji Velvia 50 | https://www.lomography.com/films/871953612-fuji-velvia-50 | 35,548 |
| CineStill 800T | Cinestill 800T | https://www.lomography.com/films/871964831-cinestill-800t | 47,683 |
| Ilford HP5 Plus | Ilford HP5 Plus 400 | https://www.lomography.com/films/871911956-ilford-hp5-plus-400 | 162,613 |
| Fujifilm Pro 400H | Fuji Pro 400H | https://www.lomography.com/films/871912904-fuji-pro-400h | 22,110 |

Notes on the rows:

- **Gold 200 has a second large name.** "Kodak Gold 200 (35mm)" has its own page, https://www.lomography.com/films/871920737-kodak-gold-200-35mm, and is the first entry under "Popular photos" on the index [F]. I did not open it, so its count is not known.
- **HP5 has a second name too.** "Ilford HP5" is at https://www.lomography.com/films/871910945-ilford-hp5 [F]. Not opened, count not known.
- **The seven pages are the largest names I saw, not the only ones.** The "cinestill" filter alone lists over a dozen names for 800T: per format, expired, pushed to 1600 and 3200, redscaled, one marked as recalled, and two that call themselves a simulation [Q3].

### The other 65 film stocks

How each was checked: **index** means the name is among the 100 on the index page [F]; **filter** means it appeared in one of the six filter queries I ran (portra, kodachrome, cinestill, rollei, 2383, neopan) [Q1–Q6]. Counts were not read for any of these.

| Result | Number | Film stocks |
|---|---|---|
| Matching name seen (index) | 21 | Fujicolor Superia 400, Portra 160, Portra 800, Portra 160VC, Superia 100, Superia 200, Agfa Vista 200, Provia 100F, Ektachrome E100VS, Elite Chrome 200, Agfa Precisa 100, Lomography X-Pro Slide 200, Tri-X 400, T-MAX 100, T-MAX 400, BW400CN, Delta 400, Delta 3200, FP4 Plus, XP2 Super, Agfa APX 100 |
| Matching name seen (filter) | 13 | Portra 160NC, Portra 400NC, Portra 400VC, Portra 400UC, Kodachrome 25, Kodachrome 64, Kodachrome 200, Fujifilm Acros 100, Neopan 1600, Rollei Retro 80S, Rollei Ortho 25, Rollei Infrared 400, Kodak Vision 2383 |
| Near match only | 5 | Lomography Redscale 100 (index has "Redscale XR 50–200"), Velvia 100 (index has "Velvia 100F" and a bare "Fuji Velvia"), Sensia 100 (index has a bare "Fuji Sensia" and "Sensia 200"), Kodak ExtraColor 100 (index has "Elitechrome EBX" and "Kodak EBX"), Rollei Retro 100 Tonal (filter has "Rollei Retro 100", none with "Tonal") |
| Looked for, not listed | 1 | CineStill 400T. The "cinestill" filter lists 400D, 50D, 800T and BwXX names, and none called 400T [Q3] |
| Not checked | 25 | Kodak Elite Color 200, Elite Color 400, Fujifilm Pro 160C, Pro 800Z, Reala 100, Superia 800, Superia 1600, X-TRA 800, Agfa Ultra 100, Provia 400F, Provia 400X, Astia 100F, Ektachrome E100GX, Elite Chrome 400, Kodak Elite 100 X-Pro, Superia 200 X-Pro, T-MAX P3200, Kodak HIE Infrared, Delta 100, Pan F Plus, HPS 800, Agfa APX 25, Kodak Vision 2393, Eterna 3510, Eterna 3513 |

Tally over all 72: 41 with a matching name seen (the 7 first-set film stocks, 21 more from the index, 13 from the filter), 5 near match only, 1 looked for and not listed, 25 not checked.

Notes:

- **"Not checked" is not "absent".** With over 49,000 names, most of the 25 probably exist **(my reasoning)**. I stopped at six queries to keep the number of page loads small.
- **The filter may cut its list off.** Four of the six queries returned about a hundred names each. I do not know whether that is a limit, so a name missing from a long list is weak evidence.
- **Cross-processed film stocks have no clean match.** The site has no field for the process. Members put it in the film name when they record it at all: the kodachrome query shows one name ending in "x pro" [Q2]. Kodak Elite 100 X-Pro and Superia 200 X-Pro would have to be found the same way.
- **Print films are barely there.** The "2383" query returned four names and no "Popular photos" list, where the other five queries each returned one [Q5]. Kodak 2383 is a cinema print film, not a camera film, so few photos are to be expected **(my reasoning)**.

## Part two: what a photo page says

I opened 9 photo pages: two each under the Portra 400 and Gold 200 names, one each under the other five. Seven came from the Recent order, two from Selected.

Fields seen, and how often each was filled:

| Field | Filled | Notes |
|---|---|---|
| Photographer | 9 of 9 | A member name |
| Uploaded | 9 of 9 | The upload date, not the date the photo was taken |
| Film | 9 of 9 | Always filled here, since the sample was drawn from film pages |
| Camera | 9 of 9 | |
| Lens | 2 of 9 | Both on the two Portra 400 pages |
| Tags | 4 of 9 | Free words about subject or technique |
| City | 7 of 9 | |
| Country/Region | 6 of 9 | |
| Decade and Year | 4 of 9 | |
| Time | 1 of 9 | A time of day, such as afternoon |
| Albums | 7 of 9 | |
| Title or caption | 5 of 9 | Free text |
| Lab, scanner, development, editing, exposure settings | 0 of 9 | No such field appears on any page |

The pages, with what bears on fitness as a reference:

| Film name | Photo page | Camera as given | What else the page says |
|---|---|---|---|
| Kodak Portra 400 | [P2] | Fujica ST 705, with a 35mm lens named | Caption dates the photo to 2015; uploaded 2019 |
| Kodak Portra 400 | [P3] | Contax ST, with a 35mm lens named | Nothing on process |
| Kodak Gold 200 | [P4] | Lomo LC-A+ | Caption is a travel story. Nothing on process |
| Kodak Gold 200 | [P5] | Nikon AD3 | Nothing on process |
| Kodak Ektar 100 | [P6] | Olympus Pen EE2 | Nothing on process |
| Fuji Velvia 50 | [P7] | Nikon FM2 | Caption says the film was out of date, with no date given |
| Cinestill 800T | [P8] | Minolta X-700 | Only a city |
| Ilford HP5 Plus 400 | [P9] | Nikon FE2 | Nothing on process |
| Fuji Pro 400H | [P10] | Holga CFN | Tagged as a double exposure |

What this shows:

- **Scanning and editing are never recorded as data.** When anything about the process is told, it is in free text the member chose to write: one caption in nine here.
- **Nine pages is a small sample.** It shows which fields exist. The fill rates are rough.
- **I could not see the upload form** without logging in, so I cannot say whether a member is offered fields that these nine left empty.

## Part three: what the terms say about the photos

All from the Terms & Conditions at [T], paraphrased, with the section named.

- **Who is bound.** Section "Scope": visiting the site is enough to be bound by the terms. No account is needed.
- **Personal use only.** Section "Scope": the services are for personal use and not for commercial purposes, which it defines broadly as including anything that earns revenue, involves business operations or provides services to third parties. Anyone wanting commercial use is told to contact Lomography.
- **Who owns the photos.** The terms never say outright that the member keeps ownership. Section "Intellectual Property Guidelines; Granting Licence" has the member warrant that they hold the rights, and grant Lomography and parties it authorises a licence that is royalty-free, perpetual, irrevocable, worldwide and non-exclusive, covering use, copying, modification, derivative works and public display, for editorial or commercial purposes in any medium. Since the licence is non-exclusive and the member must hold the rights, the member remains the owner **(my reasoning)**.
- **What others may do.** Nothing is granted to other members or visitors. Section "Warning: Intellectual Property Infringement and Indemnity" tells the reader to assume all material on the services is under copyright unless noted otherwise, and that unauthorised use may break copyright, data protection, trade mark and privacy law. On the nine photo pages I saw no licence line, such as a Creative Commons mark.
- **No promise that the information is right.** Section "Our Duties": Lomography gives no warranty that information on the services is accurate, complete or authentic. Section "Community Photo Upload Service": it does not review content before it appears. So the film name on a photo is whatever the member typed.
- **Camera-made pictures only.** Section "AI-generated Content restrictions": the service is meant for wholly camera-based photography, and AI-generated content is forbidden. The section does not mention digital photos edited to look like film. Two film names in the cinestill query and one in the kodachrome query call themselves a simulation [Q2][Q3].
- **Law.** Section "Disagreements; Governing Law and Jurisdiction": Austrian law, with Vienna as the venue.

I found no separate community guidelines page. The terms refer to policies or guidelines published on the websites, without a link, and to a Community Privacy Statement, which I did not read.

## Part four: rules for automated access

### robots.txt

Fetched from [R]. One group, for every user agent. It disallows these paths and nothing else:

`/api`, `/backend`, `/browse`, `/clickme`, `/colors`, `/homes/*/notes`, `/homes/random`, `/homes/search`, `/login`, `/my`, `/openme`, `/photos/random`, `/search`

It names a sitemap at `https://www.lomography.com/sitemap.xml`. It sets no crawl delay. `/films`, `/films?query=` and `/photos/<id>` are not disallowed.

### The terms

Section "Prohibition of Web Scraping and Crawling" at [T] is stricter than `robots.txt`. The reader agrees not to scrape or crawl the services. The section says this includes:

> "automated bots, software, or any other means to extract, collect, or scrape data"

from the websites without Lomography's explicit consent. It extends the ban to interfacing with the services through unauthorised applications or software, and reserves technical safeguards and legal remedies.

Three points about this section:

- **It is about how data is taken, not what is kept.** It has no exception for a program that reads a photo, computes a number and discards the photo.
- **Consent is the stated way through.** The ban applies without explicit consent, and the "Scope" section invites contact about other uses. The contact addresses on the page are `info@lomography.com` and `help@lomography.com`.
- **A plain non-browser request is refused.** Issue #96 records an HTTP 403 for a plain fetch. That fits the technical safeguards the section mentions **(my reasoning)**.

### The API

- A third-party Python package documents a Lomography API with base address `https://api.lomography.com/v1`, with calls for popular, recent and selected photos, for films, and for popular and recent photos by film number [A1].
- That package's guide says a key is needed, that it is requested from the Lomography team, and links to `https://www.lomography.com/api/` for details [A2].
- `/api` is disallowed in `robots.txt` [R], so I did not open that page. What the API returns for a photo, its terms and its limits are not verified here.
- Lomography's own GitHub organisation has no API documentation repository among the 29 public ones listed [A3].

### What this allows, plainly

| Use | Allowed? | Basis |
|---|---|---|
| A person looking at film pages and photos by eye | Yes | Public pages; personal use is what the terms describe [T] |
| A person writing down impressions of a film's look | Yes, as far as the terms go | Nothing in the terms addresses notes **(my reasoning)** |
| A program fetching pages or photos to compute statistics, keeping no photos | No, without Lomography's consent | The scraping section covers software that extracts or collects data, and has no exception for not storing [T] |
| A program fetching and storing photos | No | The same section, plus copyright in each photo [T] |
| Keeping derived numbers in the repository | The terms are silent | The limit is on how the numbers are obtained. Whether numbers derived from someone's photo carry any of the photographer's rights is a legal question this note cannot answer **(my reasoning)** |
| Committing photos to the repository | No | Already ruled out by the map; also unlicensed [T] |
| Using the API with a key | Unknown | Depends on API terms I have not read |

A grey case: a person opening photos one at a time and measuring them with a colour picker. No bot is involved, but the section also covers ways of extracting data other than bots and software, and that wording is wide. I would not treat it as clearly allowed **(my reasoning)**.

## Part five: fitness as a reference

What the evidence shows, and no more:

- **The film label is not checked.** It is free text [Q1], and the terms disclaim its accuracy [T].
- **A name's photos mix conditions, and many more sit under other names.** Names seen in the filters include expired film (some with dates back to the 1960s to 1980s), pushed film, redscaled film, cross-processed film, simulations and several films under one name [Q1][Q2][Q3][Q6]. The plain name is the largest, but nothing keeps such photos out of it: the Velvia 50 sample under the plain name says in its caption that the film was out of date [P7], and the Pro 400H sample is a double exposure [P10].
- **Scan and edit are unknown for every photo.** No field records them (Part two).
- **Toy cameras are a large share for some film stocks.** From the "popular combinations" lists, reading the figures as rounded photo counts **(my reasoning)**:

| Film name | Photos | Cameras in its popular combinations |
|---|---|---|
| Fuji Pro 400H | 22,110 | Only Diana F+ (4k) and three Holga models (1k, 1k, 2k). No other camera is listed |
| Fuji Velvia 50 | 35,548 | Lomo LC-A+ (5k), Lomo LC-A (4k), LC-A 120, LC-Wide, Holga 120 CFN, Canon AE-1 (1k each) |
| Kodak Ektar 100 | 109,711 | Holga 120 N (1k), Holga 120 GCFN (2k), Lomo LC-A+, LC-Wide, Horizon Perfekt, Olympus OM-10, Olympus Trip 35, Canon EOS 300 |
| Kodak Portra 400 | 115,935 | Canon AE-1 (4k), AE-1 Program (3k), Lomo LC-A+, LC-A, LC-Wide (2k each), Olympus XA, MJU II, OM-1, Pentax 17, Holga 120 N (1k each) |
| Kodak Gold 200 | 48,384 | Canon AE-1, Olympus XA2, Minolta X-700, Lomo LC-A+, LC-A, Olympus MJU II, Nikon FM2, Canon EOS 500N (1k each) |
| Cinestill 800T | 47,683 | Eight SLRs (1k to 2k each) and Lomo LC-A+ (2k) |
| Ilford HP5 Plus 400 | 162,613 | Mostly SLRs and a Leica (1k to 2k each), Lomo LC-A+ (2k), Lomography Fisheye No. 2 (1k) |

  Some entries in these lists are narrowed further by a country, a year or a decade; the table gives the camera only. For Pro 400H the listed toy-camera figures add up to roughly 8,000 of 22,110 photos, and those are only the combinations the page chooses to show. The lists come from [P1] and the six film pages in the first table.

- **The default view is curated.** Selected is hand-picked by Lomography [P1], and the terms describe the site as showcasing experimental analogue photography [T]. Recent or Popular is the less filtered view, but Popular is ranked by members' likes **(my reasoning)**.
- **Scenes are arbitrary.** Nothing on the pages suggests a shared subject, a grey card or a chart. I did not study the photos themselves, so this note says nothing about how the colours look.

Put together: the pages fit the map's wording of the target in one respect, since they are community scans of the film as people post them. They fail as something to measure against, for two separate reasons. The conditions behind each photo are unknown and mixed, and measuring by program is not permitted without consent. For looking by eye, the Recent order under the plain name of a film stock, read with the camera field in view, is the least filtered thing the site offers **(my reasoning)**.

## Not known / could not verify

- **Counts for the second names** of Gold 200 and HP5, and for every film stock outside the first seven. Not read.
- **Whether 25 film stocks have a name at all.** Not checked; listed in Part one.
- **Whether the filter cuts its list off** at about a hundred names.
- **What the "(4k)" figures mean exactly.** Read as photo counts; the page does not say.
- **The upload form**, and so whether fields exist that members leave empty. Needs a login.
- **Photo resolution and whether the image files carry EXIF data** such as scanner make. I did not open or save any image file.
- **The API**: its documentation page, terms, limits and what it returns. The page is on a path `robots.txt` disallows. Only a third party's description was read [A1][A2].
- **The sitemap** named in `robots.txt`. Not fetched.
- **The Community Privacy Statement, the FAQ and any community guidelines page.** Not read. No guidelines page was found.
- **The date of the terms.** The page text shows none. The terms say they may change, so the reading here is of 2026-11-13.
- **Whether M-Film's use counts as personal and non-commercial** under the terms. A question for the maintainer or Lomography, not for this note.
- **Whether my own reading was within the terms.** This research was done by an AI agent driving a normal browser, one page at a time, 26 page loads in all, on paths `robots.txt` allows, with nothing saved. I read the scraping section after the first few pages and kept the rest to the minimum the ticket needed. The section's wording is wide enough that this may fall under it. Anything larger should not be done this way without asking Lomography first.

## Method

Pages loaded on www.lomography.com, in order: `robots.txt`; the film index; the Portra 400 film page; one photo page; the terms; then for each of the other six film stocks its film page in Recent order and one photo page (two for Gold 200); one more Portra 400 photo page; the film index again; six filter queries. 26 loads. No login, no downloads, no `/api`, `/search` or `/browse`. The GitHub and Read the Docs pages for [A1]–[A3] were read separately.

## Sources

Lomography, read 2026-11-13:

- [R] https://www.lomography.com/robots.txt
- [T] https://www.lomography.com/about/terms/
- [F] https://www.lomography.com/films
- [P1] https://www.lomography.com/films/871910984-kodak-portra-400/photos (the other six film pages are in the table in Part one)
- [P2] https://www.lomography.com/films/871910984-kodak-portra-400/photos/23265019
- [P3] https://www.lomography.com/films/871910984-kodak-portra-400/photos/29324129
- [P4] https://www.lomography.com/films/871958647-kodak-gold-200/photos/30065474
- [P5] https://www.lomography.com/films/871958647-kodak-gold-200/photos/30063467
- [P6] https://www.lomography.com/films/871912245-kodak-ektar-100/photos/30064860
- [P7] https://www.lomography.com/films/871953612-fuji-velvia-50/photos/30055528
- [P8] https://www.lomography.com/films/871964831-cinestill-800t/photos/30065693
- [P9] https://www.lomography.com/films/871911956-ilford-hp5-plus-400/photos/30065816
- [P10] https://www.lomography.com/films/871912904-fuji-pro-400h/photos/30041133
- [Q1] https://www.lomography.com/films?query=portra
- [Q2] https://www.lomography.com/films?query=kodachrome
- [Q3] https://www.lomography.com/films?query=cinestill
- [Q4] https://www.lomography.com/films?query=rollei
- [Q5] https://www.lomography.com/films?query=2383
- [Q6] https://www.lomography.com/films?query=neopan

Third party, about the API:

- [A1] https://github.com/scornz/python-lomography at commit `2d55b2f` (`lomography/constants.py`, `lomography/base.py`). Not written by Lomography.
- [A2] https://python-lomography.readthedocs.io/en/latest/usage.html
- [A3] https://github.com/orgs/lomography/repositories (29 public repositories listed through the GitHub API; none documents a photo API)

M-Film's film stocks: `FILMS.md`, `ml-dev/films/films.py`, `ml-dev/films/filmluts.py` at `origin/main` `8118e9c`.
