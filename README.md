# Vinyl collection

A local, mobile-first vinyl collection built from `vinyl_collection.md`: 58 releases and 316 locally bundled photographs. The landing page focuses on the animated record stack, with a charcoal, copper and ivory palette.

## Run locally

Requires Node.js 22.12+ (Node 24 recommended).

```sh
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. No API keys, database, accounts, or external services are needed to browse the site. Keep the terminal running while using it.

## Production and offline/PWA mode

```sh
npm run build
npm run preview
```

Open **http://127.0.0.1:4173**. On the first online visit, the service worker saves the complete app, fonts, catalogue, covers and release galleries (approximately 36 MB). After caching finishes, it can be reloaded and browsed offline. Install through the browser's installation menu; a footer install control also appears when the browser exposes the installation prompt. Browser support for installation varies. Service workers require localhost or HTTPS; opening `index.html` directly from the filesystem does not work.

The development server intentionally does not register a service worker. Use the production preview for offline testing.

## Controls

- Scroll over the record, swipe horizontally, use arrow keys, or use the previous/next buttons.
- Click the sleeve or the turntable action to open a release.
- The grid button opens all matching records; the shuffle button picks a different record.
- The search icon (or `/`) reveals search, genre, format, and sorting controls.
- Change between Ukrainian and English using the header controls. The choice is remembered.
- Release galleries support thumbnails, previous/next buttons, swiping, and a full-size viewer. Use left/right arrows in the full-size viewer and Escape to close it.
- Turntable rotation can be paused. The footer motion setting and the operating system's reduced-motion preference are respected.
- Release URLs such as `/#record-773190` can be bookmarked. Browser back/forward works.

The turntable is a visual animation, not an audio player. No music files were supplied.

## Validation

```sh
npm test
npm run build
```

The Node tests check all 58 source headings, catalogue integrity, local assets, English summaries, tracklist parsing, filters, sorting, navigation, safe rendering, and PWA metadata.

Browser regression checks use Playwright CLI. Start both local servers in separate terminals before running:

```sh
npm run test:browser
```

They cover both languages, all 58 release dialogs, search/filter/reset/empty states, wheel and keyboard navigation, five viewport widths (320–1440 px), deep links, history, photo galleries, the full-size viewer, touch swipes, reduced motion, and production offline reload. Screenshots are saved under `output/playwright/`. A Chrome installation is required by the browser checks; use `npx playwright-cli install-browser` if the CLI reports a missing browser.

## Content and updating

- `vinyl_collection.md`: the original supplied catalogue, preserved.
- `public/collection.json`: parsed catalogue and tracklists.
- `public/tracklist-supplements.json`: four missing single tracklists obtained from their exact Discogs releases.
- `src/english.js`: English editorial summaries adapted from the supplied Ukrainian notes. Longer original notes remain available in Ukrainian mode; proper titles and release metadata retain their original wording.
- `public/covers/`: all 58 local cover images.
- `public/gallery.json` and `public/gallery/`: 316 photographs of the exact pressings, with source URLs. These include sleeves, gatefolds, inserts, labels and other release photographs; they are not invented historical images.

To regenerate metadata after editing the source:

```sh
npm run catalogue
```

Optional maintenance scripts `scripts/upgrade_covers.py` and `scripts/prepare_galleries.py` fetch images from Discogs. They require network access and respect a delay between API requests. They are not needed to build or run the delivered site.

Release information and images come from the supplied catalogue and Discogs contributors. Artwork rights remain with their respective owners. Manrope is bundled locally under the SIL Open Font License (`public/fonts/OFL.txt`).

### Artist archives

The galleries also include **68 distinct archival images across 51 releases**: artist and band portraits, live performances, publicity photos and period documents. The dedicated “Artist archive” strip opens the same full-size viewer, with photograph dates, authors, licenses and links to the original Commons file pages. All images are bundled locally and included in the offline cache.

Dates describe the photograph, not the album. Some images show a different point in the artist's career; they are not presented as recording-session photographs. Releases without a reviewed archival source retain their complete pressing galleries.

The reviewed sources are preserved in `scripts/archive-sources.json`. Run `python3 scripts/prepare_archive.py` to restore any missing local archive assets from that manifest.

### Physical interactions and record-room mode

- Drag a sleeve horizontally to reveal its neighbours. Longer, faster flicks carry farther through the crate; wheel and arrow navigation still work.
- Album artwork supplies the ambient light color, which blends between releases.
- Opening and closing a release animates the sleeve and disc between the crate and turntable.
- Drag the tonearm left to lower it or right to park it. With keyboard focus, use the arrow keys, Home (park), and End (lower).
- Hold the vinyl with a pointer or hold Space/Enter while it is focused to slow its rotation; release to restore its speed.
- “Flip record” turns to the next documented side and shows its tracks. “All tracks” restores the complete tracklist.
- Archive photographs appear as contact prints and lift into the full-size viewer.
- The ⛶ button enters record-room mode. Controls fade when idle and return on movement, touch, or keyboard use; the exit remains visible. Fullscreen is used where the browser permits it, with an immersive layout as the fallback.

All new motion respects the footer motion setting and the operating system's reduced-motion preference. The scene uses native browser animations and CSS transforms, with no WebGL dependency. The added browser regression suite covers the motion-enabled transitions and interactive controls as well as reduced motion.
