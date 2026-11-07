# Launch checklist — Howdy World Web & Apps

Checked 2026-11-07. Branch `cursor/howdy-front-porch-4869`. Design basis: approved v3.1 mockup (no later mockup). Production before this branch is commit `77602e4292c0e2647ac4916c5a5ad3444185ad9a` on `main`.

**No open P0.** The contact gap is closed by an ordinary link to the configured quote form. Mail delivery was not end-to-end tested. That is a disclosed limitation, not a failed delivery and not an E2E pass.

## Contact

| Item | Result | Evidence |
| --- | --- | --- |
| Contact path on howdy-world.com | **PASS** | Homepage and support link to `https://zachmoffett.com/#quote`. Visible copy: “Continue to Zach’s project request form; choose Not sure for a web app.” No `<form>` on this site, no cross-origin post, no success message, no personal Gmail. |
| Quote service configured and deployed | **PASS** (configured and deployed; not delivery-tested) | Authoritative read-only inspection: `zachmofo/zach` PR 2 merged 2026-11-06 8:31 AM CT at SHA `e4f5e425db219f7c24cf58ab9ba3d25b6a4d8ae9`. Cloudflare Pages production deployment `326858a1-e6bc-41f3-b431-68b332863e6c` at 8:32 AM CT for that SHA. Domain `zachmoffett.com` attached, Functions enabled. Current index has real `form id=quote` posting to `/api/quote` with Turnstile. `TURNSTILE_SECRET` is present, `QUOTE_MAILER` is bound to `zach-quote-mailer`, and the Turnstile domain is authorized. The mailer has a `QUOTE_MAIL` `send_email` binding, `DELIVER_TO` secret, `QUOTE_FROM`, and two verified Email Routing destinations. The handler errors if required mail fails. Secret values were not read. |
| End-to-end form delivery | **Not tested** | No submission was sent. This is not an E2E pass and it is not evidence that the configured path is broken. |

Publishing is a normal merge of this pull request to `main`. GitHub Pages then serves that tree at https://howdy-world.com/.

## Deployment mechanism

| Item | Result | Evidence |
| --- | --- | --- |
| How production is published | **PASS** (identified, not used) | `gh api repos/zachmofo/howdy-world.com/pages` returned `status: built`, `cname: howdy-world.com`, `source.branch: main`, `source.path: /`. https://howdy-world.com/ responds `server: GitHub.com`. https://zachmofo.github.io/howdy-world.com/ returns 301 to https://howdy-world.com/. The repo `CNAME` file is `howdy-world.com`. There is no GitHub Actions deploy on `main`. |
| This change’s CI | **N/A** for publish | `.github/workflows/prelaunch.yml` runs `python3 tests/prelaunch_check.py` on pull requests only. It does not deploy. |
| Cloudflare Pages upload | **N/A** | Not used. The earlier direct-upload attempt failed authorization (`8000013`). That route was not repeated and was not bypassed. |
| DNS, redirects, accounts, spend | **N/A** | None changed. |
| Branch protection | **N/A** (unreadable) | `GET /repos/zachmofo/howdy-world.com/branches/main/protection` returned 403 (needs administration). Protection was not bypassed. |

## Rollback, before any later launch

Production is GitHub Pages serving the root of `main`. The known-good commit is `77602e4292c0e2647ac4916c5a5ad3444185ad9a` (“Rewrite lessons as readable teaching text; drop jumpy inline code”).

If a later merge to `main` needs to come down:

1. On `main`, revert that merge or squash commit. Do not reset public history unless that is already the repo’s practice.
2. Push `main`. GitHub Pages rebuilds from `main` and serves the reverted tree at https://howdy-world.com/.
3. Leave the `CNAME` file and DNS alone. Do not point the domain anywhere else.

Lessons, `styles.css`, `app/`, `images/`, and `CNAME` are unchanged on this branch, so a revert also restores the current homepage and support page together.

## Prelaunch checks

Static command: `python3 tests/prelaunch_check.py` → exit 0, 0 failures. Browser command: headless Chrome via Puppeteer against `python3 -m http.server` on 127.0.0.1:8765, plus axe-core 4.14.0. Results below.

| Check | Result | Evidence |
| --- | --- | --- |
| Homepage indexable, canonical https://howdy-world.com/ | **PASS** | `robots` meta is `index,follow`. Canonical link matches. No `noindex` in `index.html` or `support.html`. |
| Support canonical | **PASS** | `https://howdy-world.com/support.html` |
| 404 | **PASS** | `/404.html` has one `h1` and `noindex`. GitHub Pages uses this file for unknown paths. The local Python server does not, so live 404 routing was not exercised. |
| robots.txt | **PASS** | Allows `/`. Sitemap line is `https://howdy-world.com/sitemap.xml`. It does not disallow the site. |
| Sitemap | **PASS** | Lists `/`, support, `learn.html`, lessons `00`–`05`, demo steps `step1`–`step5`, and `/app/ranch-office-hub.html`. |
| Staging noindex / review banner not copied | **PASS** | No `_headers`. No “Review-only”, “Design preview”, “Preview complete”, “Simulation only”, or “Request sent”. |
| No fake contact success | **PASS** | No `<form>` on the homepage or support page. No `/api/quote` post, Turnstile widget, or `mailto:` on this site. The project action is a normal link to `https://zachmoffett.com/#quote`. It does not say a message was sent. |
| Three-sample gallery, fictional labels | **PASS** | Three `.sample-entry` blocks in Stripewell, Bramblewick, Keelstone order. Each says “Fictional concept · not client work”. Nearby copy says they are not client projects. |
| Desktop 3-column / mobile stacked gallery | **PASS** | Rendered at 1440 (three columns) and at 360, 390, and 430 (stacked). Screenshots below. |
| Phone composites clear of captions | **PASS** | Bounding boxes at 360, 390, 430, and 1440: each phone does not intersect its caption or “View sample” link. Fiction label does not intersect the desktop image. |
| No horizontal overflow | **PASS** | `scrollWidth` within 1px of the viewport at 360, 390, 430, and 1440. |
| Menu, Escape, focus | **PASS** | At 390, Menu sets `aria-expanded=true` and shows the nav. Escape closes it and returns focus to the button. First Tab lands on “Skip to content” with a 3px solid outline. |
| Sticky project bar | **PASS** | Bar stays hidden on the hero and while `#work` is on screen, so it does not cover the phone composites. After the gallery, at 390, the bar is `display: flex` and does not intersect gallery captions. |
| Reduced motion | **PASS** | `prefers-reduced-motion: reduce` → gallery transition `0s`. Otherwise `0.3s`. |
| Contrast | **PASS** | axe-core reported no contrast violations. Sample computed ratios: muted `#5b584f` on paper `#f3f0ea` 6.25:1; footer `#c6c2b8` on ink `#1c1916` 9.84:1; process text `#e0e7df` on green `#245c4a` 6.16:1; paper on the green button 6.83:1; ink on wheat `#e7c66a` 10.57:1. |
| axe-core | **PASS** | 0 violations on the homepage at 1440 and at 390. |
| Semantic headings | **PASS** | Homepage has one `h1`. Gallery `h2` precedes services. axe-core reported no heading violations. |
| Lesson URLs and lesson footer | **PASS** | `git diff main -- learn styles.css app images CNAME` is empty. Rendered `/learn/00-intro.html` footer still says “Howdy World Coding” and does not say “Start a project”. `/styles.css` returns 200. |
| Archive / toys kept | **PASS** | `app/lumapps.html`, `app/ranch-office-hub.html`, and `images/cyberskull.jpg` still exist. Ranch Office Hub is linked at `/app/ranch-office-hub.html` and is not described as a shipped client app. |
| Support purpose and destinations | **PASS** | Rendered support page includes the non-tax-deductible charity sentence, the separate-from-services sentence, Venmo `@Zachmoffett`, Cash App `$ZachMoffett`, PayPal `@zachmoffett`, and Bitcoin `3BrYKKNQQe9MrnRTyje4fgp4QvmzuiqjYV` with the Bitcoin-network-only warning. No new payment processor. |
| GitHub and YouTube | **PASS** | `https://github.com/zachmofo` and `https://youtube.com/@howdy-world-coding` remain. |
| No shipped-app, testimonial, or client-count claims | **PASS** | Apps copy says “Potential project ideas—not claims of shipped apps.” No testimonial language. |
| Fonts and sample-image disclosure | **PASS** | Fraunces and Figtree are self-hosted. `assets/fonts/OFL.txt` is the SIL Open Font License 1.1 with the Fraunces and Figtree copyright lines. Footer says the samples are fictional and the photos are illustrative. WebP files are unchanged copies from the approved mockup. |
| Local link/asset targets | **PASS** | Static checker resolved homepage, support, and 404 local `href`/`src` targets. |
| External sample HTTP status | **N/A** | Not re-requested after the Cloudflare challenge stop. The three URLs are the ones in the approved mockup. |
| Lighthouse | **N/A** | Lighthouse is not installed here. axe-core and the viewport checks above were used instead. |
| Performance basics | **PASS** | Self-hosted fonts with `font-display: swap`, width/height on gallery images, desktop shots eager, phone shots `loading="lazy"`, one small `site.js`. No third-party script on the new pages. |
| Production publish | **PASS** to attempt | No remaining P0. Publish only by merging this pull request into `main` after the static check is green. Do not use another host or change DNS. |

## Visual fixes made after render

1. Fiction labels sit in normal flow above each desktop shot. The mockup pinned that label with a fixed 42px pad, so a wrap could cover the screenshot. At 360, 390, 430, and 1440 the label box does not intersect the image.
2. The mobile “Start a project” bar was covering a gallery phone (Bramblewick, 390, scrolled). The bar now stays hidden while the gallery is on screen and appears once that section has moved off. The later 390 shot shows the bar on the services section, not on a phone composite.
3. The brand link and the three sample links had `aria-label` values that did not include their visible text. axe-core reported that as a serious `label-content-name-mismatch` on 4 nodes. Those overrides were removed. The rerun reports 0 violations at 1440 and 390.

## Screenshots

Saved for review, not committed:

- `/opt/cursor/artifacts/howdy-desktop-1440-full.png`
- `/opt/cursor/artifacts/howdy-desktop-1440-hero.png`
- `/opt/cursor/artifacts/howdy-mobile-390-full.png`
- `/opt/cursor/artifacts/howdy-mobile-390-hero.png`
- `/opt/cursor/artifacts/howdy-w360-full.png`
- `/opt/cursor/artifacts/howdy-w430-full.png`
- `/opt/cursor/artifacts/howdy-w1440-gallery.png`
- `/opt/cursor/artifacts/howdy-w390-gallery.png`
- `/opt/cursor/artifacts/howdy-w390-menu.png`
- `/opt/cursor/artifacts/howdy-w390-sticky.png`
- `/opt/cursor/artifacts/howdy-support-1440-full.png`
- `/opt/cursor/artifacts/howdy-support-390-full.png`
