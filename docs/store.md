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

1. **App IDs:** both faces are registered in the [Zepp Console](https://console.zepp.com/): Sextant 1131924, Twisted Sextant 1131925, set in each `app.json`. DEV test builds take that ID + 1,000,000 automatically. The store checks that the package's `appId` matches the listing; the 1.0.0 releases carry these IDs, so their `.zab` files are ready to upload.
2. **Choose the countries or regions**, the category, and the supported devices (the console detects them from the package).
3. **Bump the version and release** (`docs/development.md` → "Branches and releases"), then upload the release's `.zab` with the text below and the previews.
4. **Paid listings:** Zepp only accepts paid watch faces from certified corporate developers in mainland China ([paid apps FAQ](https://docs.zepp.com/docs/guides/faq/paid-app/)), so the Console offers everyone else free listings only. A paid version wouldn't need a different app ID.
5. **Supported devices:** the `.zab` holds a package for every round Zepp OS screen (`{"st": "r"}` in `app.json`), scaled from the 480×480 design, and `minVersion` 4.2 limits installs to watches on API level 4.2 or later. Those are all 480×480 (Balance 3, Balance 2, Balance Ultra, Cheetah 2 Ultra, T-Rex Ultra 2, Active Max, T-Rex 3 Pro 48mm) or 466×466 (Active 2 round, Active 3 Premium, Cheetah 2 Pro, T-Rex 3 Pro 44mm), and 466 is a 97% scale. The Balance 2 and Active 2 emulator images both show the faces laid out correctly. Older watches with smaller round screens (360 to 454) can't install it. To list only 480×480 watches, `targets.common.platforms` can name their device IDs instead.

## Store text

Each face has its listing (name, short and full description in English, Simplified and Traditional Chinese, category and work statement) in `faces/<face>/docs/store/listing.md`.
