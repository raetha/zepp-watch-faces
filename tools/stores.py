"""Where each face is published, for the install page, READMEs and release notes.

The Zepp store has no web pages: people find a face by name in the Zepp app.
amazfitwatchfaces.com has one page per face.
"""
AMAZFITWATCHFACES = {
    "sextant": "https://amazfitwatchfaces.com/balance/view/9036",
    "twisted-sextant": "https://amazfitwatchfaces.com/balance/view/9037",
}


def store_lines_md(face, app_name):
    """Markdown bullets: the recommended ways to install `face`."""
    lines = [f'- **Zepp store:** in the Zepp app, open your watch\'s watch face store and search for "{app_name}".']
    if face in AMAZFITWATCHFACES:
        lines.append(f"- **amazfitwatchfaces.com:** [{app_name}]({AMAZFITWATCHFACES[face]})")
    return "\n".join(lines)
