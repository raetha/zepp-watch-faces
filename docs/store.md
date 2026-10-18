# Submitting a face to the Zepp store

What's already in place, what's left, and the store-facing text for each face. The store review takes about 1–5 working days ([How to submit a watchface](https://docs.zepp.com/docs/distribute/watchface/)).

## Already in place

- **Package:** CI attaches a `.zab` to every release (`faces/<face>/dist/*.zab` locally). That's the file the store takes.
- **Previews:** `faces/<face>/docs/store/preview_en.png`, `preview_sc.png` and `preview_tc.png`, 324×324 (the size for 480×480 watches), showing 10:09 as Zepp requires. They're rewritten with the screenshots (`npm run screenshots -- <face>`). The face's own text is English in every language, so the three are the same picture.
- **Languages:** the app name and every editor title are in English, Simplified and Traditional Chinese. On the watch, other languages fall back to English.
- **Design rules** ([watch face specification](https://docs.zepp.com/docs/watchface/specification/), [watch face design](https://docs.zepp.com/docs/designs/customization/watchface/)):
  - Text is at least 22px and lines at least 1px. Text, icons and ticks stay well inside the 2px edge margin; only the band and divider lines run to the rim, by design.
  - The always-on screen is black, lights about 5% of the screen (the limit is 10%), uses 2px digit outlines, and keeps the time where it is on the normal screen.
  - Empty values show "--" (and "0" for counts).
  - Weather icons cover all 29 conditions, numbered as the system's.
- **Originality:** all artwork is drawn for this project (`lib/py/zfkit/icons.py`); the only third-party asset is Roboto Condensed (SIL Open Font License, bundled with its licence).

## Left to do (needs the Zepp developer account)

1. **Register each face in the [Zepp Console](https://console.zepp.com/)** and get its app ID. The store checks that the package's `appId` matches the listing. Put the assigned ID in `faces/<face>/app.json` (`app.appId`). DEV test builds take that ID + 1,000,000 automatically.
   - A new app ID makes a new app on the watch: anyone who installed a face by QR code with the old ID gets the store version as a separate face.
2. **Choose the countries or regions**, the category, and the supported devices (the console detects them from the package).
3. **Bump the version and release** (`docs/development.md` → "Releasing"), then upload the release's `.zab` with the text below and the previews.
4. **Decide on other screen sizes.** The `.zab` holds a package for every round Zepp OS watch, scaled from the 480×480 design. Only the Balance 3 (and the Balance 2 emulator) have been checked. To list only 480×480 watches, `app.json` → `targets.common.platforms` can name their device IDs instead of `{"st": "r"}`.

## Store text

Each face has its listing (name, short and full description in English, Simplified and Traditional Chinese, category and work statement) in `faces/<face>/docs/store/listing.md`.
