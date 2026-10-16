"""Original icon artwork (24x24 SVG viewBox), rendered with cairosvg.

All glyphs here were drawn for this project; none are copied from Amazfit/Zepp.
"""
import io
import cairosvg
import numpy as np
from PIL import Image

# ----------------------------------------------------------------------------- metric icons
METRIC_SVG = {
    "steps": lambda c: f'''<g fill="{c}">
        <ellipse cx="8" cy="9" rx="3.2" ry="5"/><ellipse cx="8" cy="17.2" rx="2.6" ry="2"/>
        <ellipse cx="16" cy="6" rx="3.2" ry="5"/><ellipse cx="16" cy="14.2" rx="2.6" ry="2"/></g>''',
    "heart": lambda c: f'<path fill="{c}" d="M12 21s-7.5-4.6-9.4-9.3C1.2 8.1 3.4 4.5 7 4.5c2 0 3.6 1.1 5 2.9 1.4-1.8 3-2.9 5-2.9 3.6 0 5.8 3.6 4.4 7.2C19.5 16.4 12 21 12 21z"/>',
    "distance": lambda c: f'''<path fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" d="M5 19c3-1 4-4 7-5s5 0 7-3" stroke-dasharray="0.1 4"/>
        <path fill="{c}" d="M18 2.5a3.6 3.6 0 0 0-3.6 3.6c0 2.7 3.6 6.2 3.6 6.2s3.6-3.5 3.6-6.2A3.6 3.6 0 0 0 18 2.5zm0 5a1.4 1.4 0 1 1 0-2.8 1.4 1.4 0 0 1 0 2.8z"/>
        <circle cx="5" cy="19" r="2.4" fill="{c}"/>''',
    "calories": lambda c: f'<path fill="{c}" d="M12.5 2c.6 3.2-1.2 4.9-2.7 6.6C8.3 10.3 7 12 7 14.6 7 18.6 9.6 22 13 22s6-2.9 6-6.9c0-3-1.5-5.2-2.6-6.4-.1 1.6-.8 2.9-2 3.6.4-3.6-.6-7.4-1.9-10.3zM13 19.5c-1.5 0-2.6-1.2-2.6-2.8 0-1.8 1.4-2.7 2.3-4 .4 1.5 2.9 2.2 2.9 4.2 0 1.5-1.1 2.6-2.6 2.6z"/>',
    "floors": lambda c: f'<path fill="none" stroke="{c}" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round" d="M3 20h5v-4.5h4.5V11H17V6.5h4"/><path fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" d="M5 11.5 12 4.5m0 0H8m4 0v4"/>',
    "pai": lambda c: f'<path fill="none" stroke="{c}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" d="M2 13h4.5l2.5-6 4 11 3-8 1.5 3H22"/>',
    "stand": lambda c: f'<circle cx="12" cy="4.2" r="2.4" fill="{c}"/><path fill="none" stroke="{c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M12 8v7.5M12 15.5l-3 6M12 15.5l3 6M7 10.5l5-2 5 2"/>',
    "fatburn": lambda c: f'<path fill="{c}" d="M12 2.2c1 3-1.4 4.6-2.8 6.4C7.9 10.3 7 12 7 14.3 7 18.6 9.4 22 12.6 22c3.3 0 5.4-3.1 5.4-6.6 0-2.3-.9-4.3-2.3-5.8.2 1.5-.4 2.8-1.5 3.4.5-4-1-8.4-2.2-10.8z"/><circle cx="12.6" cy="16.6" r="2.1" fill="#000000aa"/>',
    "spo2": lambda c: f'<path fill="{c}" d="M12 2.5s-7 7.6-7 12.3A7 7 0 0 0 12 21.8a7 7 0 0 0 7-7c0-4.7-7-12.3-7-12.3z"/><circle cx="12" cy="15" r="3.1" fill="none" stroke="#000000b0" stroke-width="1.8"/>',
    "stress": lambda c: f'<circle cx="12" cy="12" r="9.3" fill="none" stroke="{c}" stroke-width="2"/><path fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" d="M7 14.5c1.2-1.4 2.4-1.4 3.6 0s2.4 1.4 3.6 0 2.4-1.4 3.6 0"/><circle cx="9" cy="9.5" r="1.3" fill="{c}"/><circle cx="15" cy="9.5" r="1.3" fill="{c}"/>',
    "uvi": lambda c: f'''<g stroke="{c}" stroke-width="2" stroke-linecap="round">
        <path d="M12 1.8v2.6M12 19.6v2.6M1.8 12h2.6M19.6 12h2.6M4.8 4.8l1.8 1.8M17.4 17.4l1.8 1.8M4.8 19.2l1.8-1.8M17.4 6.6l1.8-1.8"/></g>
        <circle cx="12" cy="12" r="5" fill="{c}"/>''',
    "humidity": lambda c: f'<path fill="{c}" d="M12 2.5s-7 7.6-7 12.3A7 7 0 0 0 12 21.8a7 7 0 0 0 7-7c0-4.7-7-12.3-7-12.3z"/><path fill="#00000055" d="M9.2 15.4a.9.9 0 0 0-1.7.4 4.6 4.6 0 0 0 3.6 3.6.9.9 0 1 0 .4-1.7 2.9 2.9 0 0 1-2.3-2.3z"/>',
    "aqi": lambda c: f'<path fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" d="M2.5 8.5h11a3 3 0 1 0-3-3M2.5 12.5h16a3 3 0 1 1-3 3M2.5 16.5h7"/>',
    "sun": lambda c: f'''<g fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round">
        <path d="M2.5 18h19M6 21h12M12 2.5v5M9.5 5.5 12 8l2.5-2.5"/>
        <path d="M5.5 11.2l1.4 1.4M18.5 11.2l-1.4 1.4"/></g>
        <path fill="{c}" d="M7 18a5 5 0 0 1 10 0z"/>''',
    "sunrise": lambda c: f'''<g fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round">
        <path d="M2.5 18h19M6 21h12M12 8V3M9.5 5.5 12 3l2.5 2.5"/>
        <path d="M5.5 11.2l1.4 1.4M18.5 11.2l-1.4 1.4"/></g>
        <path fill="{c}" d="M7 18a5 5 0 0 1 10 0z"/>''',
}

BATTERY_SVG = lambda c: f'<rect x="2" y="7" width="18" height="10" rx="2.5" fill="none" stroke="{c}" stroke-width="1.8"/><rect x="20.6" y="10" width="2" height="4" rx="1" fill="{c}"/><rect x="4.4" y="9.4" width="11" height="5.2" rx="1.2" fill="{c}"/>'

GLANCE_SVG = {
    "disconnect": '<g fill="none" stroke="#5AA9FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7l10 10-5 4V3l5 4-10 10"/></g><path d="M3 3l18 18" stroke="#FF5A6A" stroke-width="2.4" stroke-linecap="round"/>',
    "dnd": '<path fill="#B98CFF" d="M14.5 3a8.5 8.5 0 1 0 6.5 13.9A7 7 0 0 1 14.5 3z"/>',
    "alarm": '<g fill="none" stroke="#FFC23D" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="13" r="7.5"/><path d="M12 9v4l2.5 2M3.5 5.5l3-2.5M20.5 5.5l-3-2.5"/></g>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2" fill="#AEB8C4"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" fill="none" stroke="#AEB8C4" stroke-width="2"/>',
}

# Shown underneath each status icon while that status is NOT active. The active
# icon (above) is drawn on an opaque black disc so it fully covers this one.
GLANCE_OFF_SVG = {
    "disconnect": '<g fill="none" stroke="#5AA9FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7l10 10-5 4V3l5 4-10 10"/></g>',
    "dnd": '<path fill="none" stroke="#5E6672" stroke-width="1.8" d="M14.5 3a8.5 8.5 0 1 0 6.5 13.9A7 7 0 0 1 14.5 3z"/>',
    "alarm": '<g fill="none" stroke="#5E6672" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="13" r="7.5"/><path d="M12 9v4l2.5 2"/></g>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2" fill="none" stroke="#5E6672" stroke-width="1.8"/><path d="M8 10.5V8a4 4 0 0 1 7.6-1.8" fill="none" stroke="#5E6672" stroke-width="1.8" stroke-linecap="round"/>',
}

# ----------------------------------------------------------------------------- weather
SUN_RAYS = '<g stroke="#FFC23D" stroke-width="2" stroke-linecap="round"><path d="M12 1.8v2.6M12 19.6v2.6M1.8 12h2.6M19.6 12h2.6M4.8 4.8l1.8 1.8M17.4 17.4l1.8 1.8M4.8 19.2l1.8-1.8M17.4 6.6l1.8-1.8"/></g><circle cx="12" cy="12" r="5.2" fill="#FFC23D"/>'
SMALL_SUN = '<g stroke="#FFC23D" stroke-width="1.8" stroke-linecap="round"><path d="M9 1.5v2.2M2.6 4.2l1.6 1.6M1 10.5h2.2M15.4 4.2l-1.6 1.6"/></g><circle cx="9" cy="10" r="4.4" fill="#FFC23D"/>'
MOON = '<path fill="#E8E2C8" d="M14.5 3a8.5 8.5 0 1 0 6.5 13.9A7 7 0 0 1 14.5 3z"/>'
SMALL_MOON = '<path fill="#E8E2C8" d="M10 2.5a6.5 6.5 0 1 0 5 10.6A5.4 5.4 0 0 1 10 2.5z"/>'


def _cloud(fill, dy=0):
    return f'<g transform="translate(0,{dy})"><path fill="{fill}" d="M7.5 21.5h11a4.2 4.2 0 0 0 .6-8.4 6 6 0 0 0-11.5 1.3 3.6 3.6 0 0 0-.1 7.1z"/></g>'


def _drops(n, color="#4FC3F7", slant=True):
    xs = {1: [13], 2: [10, 15], 3: [9, 13, 17]}[n]
    d = " ".join(f"M{x} 22.5l-1 2" if slant else f"M{x} 22.3v2.2" for x in xs)
    return f'<g stroke="{color}" stroke-width="2" stroke-linecap="round"><path d="{d}"/></g>'


def _flakes(n):
    xs = {1: [13], 2: [10, 16], 3: [8.5, 13, 17.5]}[n]
    return "".join(f'<circle cx="{x}" cy="23.3" r="1.25" fill="#E6F2FF"/>' for x in xs)


def weather_svg(kind):
    up = -3
    if kind == "sunny":
        return SUN_RAYS
    if kind == "clear_night":
        return MOON
    if kind == "partly_day":
        return SMALL_SUN + _cloud("#E6ECF2")
    if kind == "partly_night":
        return SMALL_MOON + _cloud("#C9D3DD")
    if kind == "overcast":
        return '<g transform="translate(-3,-4) scale(0.8)">' + _cloud("#8796A6") + "</g>" + _cloud("#C9D3DD")
    if kind == "rain_light":
        return _cloud("#AFC0D0", up) + _drops(1)
    if kind == "rain":
        return _cloud("#9FB3C8", up) + _drops(2)
    if kind == "rain_heavy":
        return _cloud("#7F93A8", up) + _drops(3)
    if kind == "shower":
        return SMALL_SUN + _cloud("#B9C8D6", up) + _drops(2)
    if kind == "thunder":
        return _cloud("#7F93A8", up) + '<path fill="#FFC23D" d="M13.5 17.5h-3l-1.5 4h2.2l-1.2 4.2 4.5-5.7h-2.4z"/>'
    if kind == "snow_light":
        return _cloud("#D6E2EE", up) + _flakes(1)
    if kind == "snow":
        return _cloud("#C9D6E4", up) + _flakes(2)
    if kind == "snow_heavy":
        return _cloud("#AFC0D0", up) + _flakes(3)
    if kind == "sleet":
        return _cloud("#AFC0D0", up) + '<g stroke="#4FC3F7" stroke-width="2" stroke-linecap="round"><path d="M10 22.5l-1 2"/></g><circle cx="15.5" cy="23.3" r="1.25" fill="#E6F2FF"/>'
    if kind == "hail":
        return _cloud("#9FB3C8", up) + '<g fill="#E6F2FF"><circle cx="9.5" cy="23.2" r="1.5"/><circle cx="14" cy="23.2" r="1.5"/><circle cx="18" cy="23.2" r="1.5"/></g>'
    if kind == "fog":
        return _cloud("#C9D3DD", -4) + '<g stroke="#AEB8C4" stroke-width="2" stroke-linecap="round"><path d="M3 20h14M7 23h14"/></g>'
    if kind == "dust":
        return SMALL_SUN.replace("#FFC23D", "#D9A85C") + '<g stroke="#D9A85C" stroke-width="2" stroke-linecap="round"><path d="M3 15h13a2.5 2.5 0 1 0-2.5-2.5M3 19h17a2.5 2.5 0 1 1-2.5 2.5M3 23h9"/></g>'
    # unknown
    return _cloud("#5C6670") + '<text x="13" y="19.5" font-family="sans-serif" font-size="8" font-weight="700" fill="#000" text-anchor="middle">?</text>'


# ----------------------------------------------------------------------------- rendering
def svg_to_image(inner, px, vb=24):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb} {vb}" '
           f'width="{px}" height="{px}">{inner}</svg>')
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA")


def retint(img, theme, metric_rgb=None):
    """Recolour an RGBA icon for the mono or night theme (colour theme untouched).

    Brightness is kept so multi-colour glyphs stay legible; hue is replaced.
    """
    if theme == "color":
        return img
    a = np.asarray(img).astype(float)
    rgb, alpha = a[..., :3] / 255, a[..., 3]
    v = np.clip(0.6 * rgb.max(axis=2) + 0.4 * (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) * 1.6, 0, 1)
    base = np.array(metric_rgb, float) / 255
    out = np.clip(v[..., None] * base[None, None, :] * 1.15, 0, 1) * 255
    return Image.fromarray(np.dstack([out, alpha]).astype(np.uint8), "RGBA")
