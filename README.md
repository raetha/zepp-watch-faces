# Zepp watch faces

Watch faces for Amazfit watches running Zepp OS, designed for the **Balance 3** (480×480 round). Each face lives in [`faces/`](faces/) and shares one asset pipeline, runtime helpers and an offline test harness.

## Faces

| | Face | |
| :---: | --- | :---: |
| <img src="faces/sextant/screenshots/day.png" width="200"> | **[Sextant](faces/sextant/)**<br>Nautical and data-rich: a navy and brass time bar, five editable complications with compass-tick gauges, automatic red night mode, a mono theme and an outline always-on display. | <img src="faces/sextant/docs/install-qr.png" width="140"><br><sub>scan to install</sub> |

## Installing a face

1. In the **Zepp app**, turn on Developer Mode: **Profile → Settings → About**, then tap the Zepp logo 7 times.
2. Go to **Profile → your watch → Developer Mode** and tap the **scan** icon.
3. Scan the face's QR code (above, or on the [install page](https://raetha.github.io/zepp-watch-faces/)) and confirm.

Each face is versioned separately. Its QR code always installs its latest release, and each release (with that face's changelog) appears on the repo's [Releases](https://github.com/raetha/zepp-watch-faces/releases) page, so you can watch the repo for release notifications.

## Repository layout

```
faces/<name>/      one watch face: app.json, watchface/ code, design/ generator,
                   assets/ (generated), scenarios/, screenshots/, docs/
lib/js/            shared runtime helpers (formatting, sunrise/sunset, metrics)
lib/py/zfkit/      shared generator helpers (fonts, icon artwork)
tools/             asset runner, offline harness, previews, QR + Pages site, new-face template
fonts/             OFL source fonts
```

## Development

See [`docs/development.md`](docs/development.md).

```bash
pip install -r tools/requirements.txt && npm install
npm run assets                       # regenerate every face's images + layout
npm test                             # run every face's code against stubbed Zepp OS APIs
npm run previews                     # quick offline renders for prototyping (faces/*/previews)
npm run emu -- start                 # real Zepp OS firmware in QEMU (setup: docs/development.md)
npm run screenshots -- sextant       # retake a face's screenshots on the emulator
npm run new-face -- mynewface        # start a new face from Sextant as a template
```

## License

- **Shared code and tooling** (`lib/`, `tools/`, CI): [MIT](LICENSES/MIT.txt).
- **Each face** (`faces/<name>/`): [CC BY-NC-SA 4.0](LICENSES/CC-BY-NC-SA-4.0.txt). Share and remix it non-commercially with credit, but don't sell it or its derivatives.
- **Face names** aren't licensed for reuse.
- **Fonts**: SIL Open Font License.

Details are in [LICENSE](LICENSE).
