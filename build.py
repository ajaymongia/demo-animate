#!/usr/bin/env python3
"""Motion Kit builder.

One motion spec drives three outputs so they never drift apart:
  motion-kit.svg   standalone animated SVG (CSS keyframes, loops forever)
  motion-kit.json  Lottie (bodymovin 5.7 schema, single shape layer)
  motion-kit-preview.html  standalone preview of both
  index.html       Motion Kit page (preview + downloads)

Edit TREE / MARKERS below and re-run:  python3 build.py
"""
import json
import os
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src", "Frame.svg")
NS = "{http://www.w3.org/2000/svg}"
FPS, TOTAL = 60, 240  # 4.0 s seamless loop
DUR = TOTAL / FPS

# cubic-bezier presets; the ease on a keyframe applies to the segment that starts there
EASE = {
    "io": (0.45, 0, 0.55, 1),      # sine-ish in-out, used for floating
    "out": (0.22, 1, 0.36, 1),     # quick settle
    "in": (0.64, 0, 0.78, 0),      # wind-up
    "back": (0.34, 1.56, 0.64, 1), # overshoot pop
    "lin": (0, 0, 1, 1),           # holds / linear
}

# ---------------------------------------------------------------- source
src_text = open(SRC, encoding="utf-8").read()
root = ET.fromstring(src_text)
PATHS = [p for p in root.find(NS + "g") if p.tag == NS + "path"]
assert len(PATHS) == 72, len(PATHS)
DEFS_TEXT = re.search(r"<defs>.*</defs>", src_text, re.S).group(0)

GRADS = {}
for g in root.find(NS + "defs"):
    tag = g.tag.replace(NS, "")
    if tag in ("linearGradient", "radialGradient"):
        stops = [
            (float(s.get("offset", "0")), s.get("stop-color", "#000"), float(s.get("stop-opacity", "1")))
            for s in g.findall(NS + "stop")
        ]
        GRADS[g.get("id")] = {"type": tag, "attrs": dict(g.attrib), "stops": stops}


def P(line):
    """Original <path> by its line number in Frame.svg (first path is line 3)."""
    return dict(PATHS[line - 3].attrib)


def SPLIT(line, d):
    a = P(line)
    a["d"] = d
    return a


def NEW(**kw):
    return {k.replace("_", "-"): str(v) for k, v in kw.items()}


def circle_d(cx, cy, r):
    k = 0.5523 * r
    return (
        f"M{cx} {cy - r}C{cx + k} {cy - r} {cx + r} {cy - k} {cx + r} {cy}"
        f"C{cx + r} {cy + k} {cx + k} {cy + r} {cx} {cy + r}"
        f"C{cx - k} {cy + r} {cx - r} {cy + k} {cx - r} {cy}"
        f"C{cx - r} {cy - k} {cx - k} {cy - r} {cx} {cy - r}Z"
    )


def star_d(cx, cy, s):
    k = 0.16 * s
    return (
        f"M{cx} {cy - s}C{cx + k} {cy - k} {cx + k} {cy - k} {cx + s} {cy}"
        f"C{cx + k} {cy + k} {cx + k} {cy + k} {cx} {cy + s}"
        f"C{cx - k} {cy + k} {cx - k} {cy + k} {cx - s} {cy}"
        f"C{cx - k} {cy - k} {cx - k} {cy - k} {cx} {cy - s}Z"
    )


class G:
    def __init__(self, name, label, anchor, anims, children):
        self.name, self.label, self.anchor, self.anims, self.children = name, label, anchor, anims, children


# ---------------------------------------------------------------- motion spec
def float3(a, b, _=None):
    """Seamless float: value a at frame 0, b at mid-loop, back to a at the end."""
    return [(0, a, "io"), (TOTAL // 2, b, "io"), (TOTAL, a, None)]


def dot_pulse(start):
    k = [(0, [100, 100], "lin")]
    k += [(start, [100, 100], "back"), (start + 12, [132, 132], "io"), (start + 30, [100, 100], "lin")]
    k += [(TOTAL, [100, 100], None)]
    return k


def sparkle(start):
    return {
        "scale": [(0, [0, 0], "lin"), (start, [0, 0], "back"), (start + 16, [100, 100], "io"),
                  (start + 48, [0, 0], "lin"), (TOTAL, [0, 0], None)],
        "rot": [(0, 0, "lin"), (start, 0, "io"), (start + 48, 90, "lin"), (TOTAL, 90, None)],
    }


def ripple(start, end, to):
    return {
        "scale": [(0, [20, 20], "lin"), (start, [20, 20], "out"), (end, [to, to], "lin"), (TOTAL, [to, to], None)],
        "op": [(0, 0, "lin"), (start, 0, "out"), (start + 4, 100, "io"), (end, 0, "lin"), (TOTAL, 0, None)],
    }


BLINK = [(0, [100, 100], "lin"), (148, [100, 100], "in"), (154, [100, 8], "out"), (162, [100, 100], "lin"),
         (TOTAL, [100, 100], None)]
GLOW = {
    "scale": [(0, [100, 100], "lin"), (64, [100, 100], "out"), (78, [142, 142], "io"), (130, [100, 100], "io"),
              (190, [114, 114], "io"), (TOTAL, [100, 100], None)],
    "op": [(0, 78, "lin"), (64, 78, "out"), (78, 100, "io"), (130, 78, "io"), (190, 96, "io"), (TOTAL, 78, None)],
}
CLICK_X, CLICK_Y = -40, -70  # cursor travel; tip lands on the visor edge

TREE = [
    P(3),
    G("floor-shadow", "Floor shadow", (539, 863), {
        "scale": float3([100, 100], [90, 86], None),
        "op": float3(100, 72, None),
    }, [P(4)]),
    G("cursor-shadow", "Cursor shadow", (754, 892), {
        "pos": [(0, [0, 0], "io"), (50, [-32, -6], "lin"), (100, [-32, -6], "io"), (160, [0, 0], "io"),
                (200, [2, 1], "io"), (TOTAL, [0, 0], None)],
        "scale": [(0, [100, 100], "io"), (50, [86, 86], "lin"), (100, [86, 86], "io"), (160, [100, 100], "lin"),
                  (TOTAL, [100, 100], None)],
    }, [P(5)]),
    G("panel-back", "Back panel", (513, 366), {"pos": float3([0, 6], [0, -10], None)}, [P(6), P(7), P(8)]),
    G("panel-mid", "Middle panel", (512, 485), {"pos": float3([0, -4], [0, 8], None)}, [P(9), P(10)]),
    G("window", "App window", (512, 496), {"pos": float3([0, 0], [0, -12], None)}, [
        *[P(n) for n in range(11, 23)],
        G("dot-1", "Dot · minimise", (655, 295), {"scale": dot_pulse(170)},
          [P(23), SPLIT(26, "M648 295H662"), SPLIT(27, "M648 297H661")]),
        G("dot-2", "Dot · expand", (693, 295), {"scale": dot_pulse(180)}, [P(24)]),
        G("dot-3", "Dot · close", (731, 295), {"scale": dot_pulse(190)},
          [P(25), SPLIT(26, "M726 290L731 295M731 295L736 300M731 295L736 290M731 295L726 300"),
           SPLIT(27, "M725 291L734 300")]),
        G("bar-1", "Text bar 1", (281, 642), {"scale": float3([100, 100], [76, 100], None)},
          [SPLIT(28, "M292 637H535C550 637 550 657 535 657H292C277 657 277 637 292 637Z"), P(29), P(31)]),
        G("bar-2", "Text bar 2", (281, 672), {"scale": float3([55, 100], [100, 100], None)},
          [SPLIT(28, "M290 666H433C447 666 447 687 433 687H290C277 687 277 666 290 666Z"), P(30)]),
        *[P(n) for n in range(32, 38)],  # torso
        G("head", "Robot head", (508, 545), {
            "pos": [(0, [0, 0], "lin"), (64, [0, 0], "out"), (78, [0, -14], "in"), (92, [0, 0], "out"),
                    (100, [0, -4], "in"), (108, [0, 0], "lin"), (TOTAL, [0, 0], None)],
            "rot": [(0, 0, "io"), (40, -2, "io"), (64, 0, "out"), (84, 3, "io"), (120, -2, "io"), (170, 1.5, "io"),
                    (TOTAL, 0, None)],
        }, [
            *[P(n) for n in range(38, 53)],
            G("eyes", "Eyes · look", (524, 437), {
                "pos": [(0, [0, 0], "io"), (44, [7, 5], "lin"), (100, [7, 5], "io"), (150, [0, 0], "lin"),
                        (TOTAL, [0, 0], None)],
            }, [
                G("glow-l", "Left eye glow", (474, 437), GLOW, [P(53)]),
                G("glow-r", "Right eye glow", (575, 437), GLOW, [P(54)]),
                G("eye-l", "Left eye", (474, 437), {"scale": BLINK}, [P(55)]),
                G("eye-r", "Right eye", (575, 437), {"scale": BLINK}, [P(56)]),
            ]),
            G("smile", "Smile", (523, 474), {
                "scale": [(0, [100, 100], "lin"), (64, [100, 100], "back"), (82, [122, 150], "io"),
                          (140, [100, 100], "lin"), (TOTAL, [100, 100], None)],
            }, [P(57), P(58)]),
        ]),
        G("hand-l", "Left hand · wave", (414, 606), {
            "pos": [(0, [0, 0], "lin"), (72, [0, 0], "out"), (84, [0, -12], "io"), (134, [0, 0], "lin"),
                    (TOTAL, [0, 0], None)],
            "rot": [(0, 0, "lin"), (72, 0, "out"), (84, -16, "io"), (96, 8, "io"), (108, -12, "io"), (120, 4, "io"),
                    (134, 0, "lin"), (TOTAL, 0, None)],
        }, [P(59), P(60), P(61)]),
        G("hand-r", "Right hand", (606, 606), {"pos": float3([0, 0], [0, -5], None)}, [P(62), P(63), P(64)]),
        G("spark-1", "Sparkle 1", (322, 392), sparkle(76),
          [NEW(d=star_d(322, 392, 16), fill="#DFFDFF", stroke="#7BE9FF", stroke_width=1.5)]),
        G("spark-2", "Sparkle 2", (690, 372), sparkle(84),
          [NEW(d=star_d(690, 372, 12), fill="#DFFDFF", stroke="#7BE9FF", stroke_width=1.5)]),
        G("spark-3", "Sparkle 3", (706, 520), sparkle(92),
          [NEW(d=star_d(706, 520, 9), fill="#DFFDFF", stroke="#7BE9FF", stroke_width=1.5)]),
    ]),
    G("ripple-1", "Click ripple 1", (619, 503), ripple(60, 108, 230), [
        NEW(d=circle_d(619, 503, 24), fill="#7BFFFF", opacity="0.28"),
        NEW(d=circle_d(619, 503, 24), stroke="#1FC8FF", stroke_width=4),
    ]),
    G("ripple-2", "Click ripple 2", (619, 503), ripple(68, 120, 170), [
        NEW(d=circle_d(619, 503, 24), stroke="#E9FDFF", stroke_width=3),
    ]),
    G("cursor", "Cursor", (659, 577), {
        "pos": [(0, [0, 0], "io"), (50, [CLICK_X, CLICK_Y], "lin"), (100, [CLICK_X, CLICK_Y], "io"),
                (160, [0, 0], "io"), (200, [3, 5], "io"), (TOTAL, [0, 0], None)],
        "rot": [(0, 0, "io"), (25, -5, "io"), (50, 0, "lin"), (100, 0, "io"), (130, 4, "io"), (160, 0, "lin"),
                (TOTAL, 0, None)],
        "scale": [(0, [100, 100], "lin"), (56, [100, 100], "in"), (62, [84, 84], "out"), (74, [100, 100], "lin"),
                  (TOTAL, [100, 100], None)],
    }, [P(n) for n in range(65, 75)]),
]

# timeline beats (also exported as Lottie markers)
MARKERS = [
    {"tm": 0, "dr": 50, "cm": "glide-in", "label": "Glide in", "lane": 0},
    {"tm": 62, "dr": 0, "cm": "click", "label": "Click", "lane": 1},
    {"tm": 64, "dr": 70, "cm": "react", "label": "Robot reacts", "lane": 0},
    {"tm": 100, "dr": 60, "cm": "return", "label": "Cursor returns", "lane": 2},
    {"tm": 148, "dr": 14, "cm": "blink", "label": "Blink", "lane": 1},
    {"tm": 170, "dr": 48, "cm": "status-pulse", "label": "Status pulse", "lane": 0},
]


# ---------------------------------------------------------------- helpers
def walk(nodes, depth=0):
    for n in nodes:
        if isinstance(n, G):
            yield n, depth
            yield from walk(n.children, depth + 1)


def check_spec():
    names = set()
    for g, _ in walk(TREE):
        assert g.name not in names, g.name
        names.add(g.name)
        for prop, kfs in g.anims.items():
            assert prop in ("pos", "rot", "scale", "op"), prop
            frames = [k[0] for k in kfs]
            assert frames[0] == 0 and frames[-1] == TOTAL, (g.name, prop, frames)
            assert all(a < b for a, b in zip(frames, frames[1:])), (g.name, prop, frames)
            # loop seam must match, except on parts that are invisible at the seam (ripples, sparkles)
            hidden = g.name.startswith(("ripple", "spark"))
            assert kfs[0][1] == kfs[-1][1] or hidden, (g.name, prop, "loop seam")


def fmt(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def r3(x):
    v = round(float(x), 3)
    return int(v) if v == int(v) else v


# ---------------------------------------------------------------- SVG + CSS
def css_decl(prop, v):
    if prop == "pos":
        return f"translate:{fmt(v[0])}px {fmt(v[1])}px"
    if prop == "rot":
        return f"rotate:{fmt(v)}deg"
    if prop == "scale":
        return f"scale:{fmt(v[0] / 100)} {fmt(v[1] / 100)}"
    if prop == "op":
        return f"opacity:{fmt(v / 100)}"
    raise ValueError(prop)


def build_css(reduced_motion_rule):
    out = [".mk{transform-box:view-box}"]
    for g, _ in walk(TREE):
        names = []
        for prop, kfs in g.anims.items():
            an = f"mk-{g.name}-{prop}"
            names.append(f"{an} {fmt(DUR)}s infinite")
            frames = []
            for i, (f, v, e) in enumerate(kfs):
                body = css_decl(prop, v)
                if i < len(kfs) - 1:
                    body += ";animation-timing-function:cubic-bezier({},{},{},{})".format(*map(fmt, EASE[e]))
                frames.append(f"{fmt(f / TOTAL * 100)}%{{{body}}}")
            out.append(f"@keyframes {an}{{{''.join(frames)}}}")
        ax, ay = g.anchor
        out.append(f".mk-{g.name}{{transform-origin:{ax}px {ay}px;animation:{','.join(names)}}}")
    if reduced_motion_rule:
        out.append("@media (prefers-reduced-motion:reduce){.mk{animation-play-state:paused!important}}")
    return "\n".join(out)


def svg_nodes(nodes, ind):
    out = []
    for n in nodes:
        if isinstance(n, G):
            out.append(f'{ind}<g class="mk mk-{n.name}">')
            out.extend(svg_nodes(n.children, ind + "  "))
            out.append(f"{ind}</g>")
        else:
            attrs = " ".join(f"{k}={quoteattr(v)}" for k, v in n.items())
            out.append(f"{ind}<path {attrs}/>")
    return out


def build_svg(inline):
    head = ('<svg viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Robot in an app window, poked by a cursor">') if inline else \
        '<svg width="1024" height="1024" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">'
    lines = [head, "<title>Motion Kit</title>" if not inline else "",
             f"<style>\n{build_css(reduced_motion_rule=not inline)}\n</style>",
             '<g clip-path="url(#clip0_2_16493)">', *svg_nodes(TREE, "  "), "</g>", DEFS_TEXT, "</svg>"]
    return "\n".join(l for l in lines if l) + "\n"


# ---------------------------------------------------------------- Lottie
def static(v):
    return {"a": 0, "k": v}


def lprop(kfs, conv, static_val):
    if not kfs:
        return static(static_val)
    out = []
    for i, (f, v, e) in enumerate(kfs):
        s = conv(v)
        k = {"t": f, "s": s}
        if i < len(kfs) - 1:
            n = len(s)
            x1, y1, x2, y2 = EASE[e]
            k["o"] = {"x": [x1] * n, "y": [y1] * n}
            k["i"] = {"x": [x2] * n, "y": [y2] * n}
            k["e"] = conv(kfs[i + 1][1])
        out.append(k)
    return {"a": 1, "k": out}


def tr(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    return {"ty": "tr", "p": p if isinstance(p, dict) else static(list(p)),
            "a": a if isinstance(a, dict) else static(list(a)),
            "s": s if isinstance(s, dict) else static(list(s)),
            "r": r if isinstance(r, dict) else static(r),
            "o": o if isinstance(o, dict) else static(o),
            "sk": static(0), "sa": static(0), "nm": "Transform"}


def group(nm, items, transform):
    return {"ty": "gr", "nm": nm, "np": len(items), "cix": 2, "bm": 0, "hd": False, "it": items + [transform]}


TOK = re.compile(r"[MLHVCZmlhvcz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")


def parse_path(d):
    toks = TOK.findall(d)
    subs, cur, cmd, pos, start, i = [], None, None, (0.0, 0.0), (0.0, 0.0), 0

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            assert t.isupper(), f"relative command {t} not supported"
            cmd = t
            i += 1
            if cmd == "Z":
                cur["c"] = True
                pos = start
                continue
        elif cmd == "M":
            cmd = "L"
        if cmd == "M":
            x, y = num(), num()
            cur = {"pts": [{"v": (x, y), "i": (x, y), "o": (x, y)}], "c": False}
            subs.append(cur)
            start = pos = (x, y)
        elif cmd in "LHV":
            if cmd == "L":
                x, y = num(), num()
            elif cmd == "H":
                x, y = num(), pos[1]
            else:
                x, y = pos[0], num()
            cur["pts"].append({"v": (x, y), "i": (x, y), "o": (x, y)})
            pos = (x, y)
        elif cmd == "C":
            c1 = (num(), num())
            c2 = (num(), num())
            p = (num(), num())
            cur["pts"][-1]["o"] = c1
            cur["pts"].append({"v": p, "i": c2, "o": p})
            pos = p
        else:
            raise ValueError(cmd)
    for s in subs:
        pts = s["pts"]
        if s["c"] and len(pts) > 1:
            a, b = pts[0]["v"], pts[-1]["v"]
            if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
                pts[0]["i"] = pts[-1]["i"]
                pts.pop()
    return subs


def shapes_for(d, ysquash=None):
    """ysquash=(cy, k): map y -> cy + (y-cy)/k so an elliptical radial gradient becomes circular."""
    out = []
    for n, s in enumerate(parse_path(d)):
        def fy(y):
            return y if not ysquash else ysquash[0] + (y - ysquash[0]) / ysquash[1]
        v = [[r3(p["v"][0]), r3(fy(p["v"][1]))] for p in s["pts"]]
        ii = [[r3(p["i"][0] - p["v"][0]), r3(fy(p["i"][1]) - fy(p["v"][1]))] for p in s["pts"]]
        oo = [[r3(p["o"][0] - p["v"][0]), r3(fy(p["o"][1]) - fy(p["v"][1]))] for p in s["pts"]]
        out.append({"ty": "sh", "ind": n, "nm": f"Path {n + 1}", "hd": False,
                    "ks": static({"i": ii, "o": oo, "v": v, "c": s["c"]})})
    return out


def rgb(c):
    c = {"white": "#FFFFFF", "black": "#000000"}.get(c.lower(), c)
    h = c.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return [r3(int(h[j:j + 2], 16) / 255) for j in (0, 2, 4)]


def gradient(gid):
    g = GRADS[gid]
    arr = []
    for off, col, _ in g["stops"]:
        arr += [r3(off)] + rgb(col)
    if any(op < 1 for *_, op in g["stops"]):
        for off, _, op in g["stops"]:
            arr += [r3(off), r3(op)]
    base = {"g": {"p": len(g["stops"]), "k": static(arr)}, "h": static(0), "a": static(0)}
    at = g["attrs"]
    if g["type"] == "linearGradient":
        base.update(t=1, s=static([r3(at["x1"]), r3(at["y1"])]), e=static([r3(at["x2"]), r3(at["y2"])]))
        return base, None
    m = re.match(r"translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)(?: ([-\d.]+))?\)", at["gradientTransform"])
    cx, cy, sx = float(m.group(1)), float(m.group(2)), float(m.group(3))
    sy = float(m.group(4)) if m.group(4) else sx
    base.update(t=2, s=static([r3(cx), r3(cy)]), e=static([r3(cx + sx), r3(cy)]))
    squash = None if abs(sx - sy) < 1e-6 else (cx, cy, sy / sx)
    return base, squash


def el_lottie(a, nm):
    items = []
    d = a["d"]
    stroke, fill = a.get("stroke"), a.get("fill")
    if stroke and stroke != "none":
        w = r3(a.get("stroke-width", "1"))
        lc = {"butt": 1, "round": 2, "square": 3}[a.get("stroke-linecap", "butt")]
        lj = {"miter": 1, "round": 2, "bevel": 3}[a.get("stroke-linejoin", "miter")]
        common = {"o": static(100), "w": static(w), "lc": lc, "lj": lj, "ml": 4, "bm": 0}
        if stroke.startswith("url("):
            gd, _ = gradient(stroke[5:-1])
            st = {"ty": "gs", "nm": "Gradient Stroke", **common, **gd}
        else:
            st = {"ty": "st", "nm": "Stroke", "c": static(rgb(stroke) + [1]), **common}
        items.append(group("Stroke", shapes_for(d) + [st], tr()))
    if fill and fill != "none":
        if fill.startswith("url("):
            gd, squash = gradient(fill[5:-1])
            fl = {"ty": "gf", "nm": "Gradient Fill", "o": static(100), "r": 1, "bm": 0, **gd}
            if squash:
                cx, cy, k = squash
                items.append(group("Fill", shapes_for(d, (cy, k)) + [fl],
                                   tr(p=(r3(cx), r3(cy)), a=(r3(cx), r3(cy)), s=(100, r3(100 * k)))))
            else:
                items.append(group("Fill", shapes_for(d) + [fl], tr()))
        else:
            fl = {"ty": "fl", "nm": "Fill", "c": static(rgb(fill) + [1]), "o": static(100), "r": 1, "bm": 0}
            items.append(group("Fill", shapes_for(d) + [fl], tr()))
    return group(nm, items, tr(o=r3(float(a.get("opacity", "1")) * 100)))


COUNTER = [0]


def lottie_nodes(nodes):
    out = []
    for n in reversed(nodes):  # Lottie draws the first item on top
        if isinstance(n, G):
            ax, ay = n.anchor
            t = tr(
                p=lprop(n.anims.get("pos"), lambda v: [r3(ax + v[0]), r3(ay + v[1])], [ax, ay]),
                a=(ax, ay),
                s=lprop(n.anims.get("scale"), lambda v: [r3(v[0]), r3(v[1])], [100, 100]),
                r=lprop(n.anims.get("rot"), lambda v: [r3(v)], 0),
                o=lprop(n.anims.get("op"), lambda v: [r3(v)], 100),
            )
            out.append(group(n.label, lottie_nodes(n.children), t))
        else:
            COUNTER[0] += 1
            out.append(el_lottie(n, f"shape {COUNTER[0]}"))
    return out


def build_lottie():
    layer = {
        "ddd": 0, "ind": 1, "ty": 4, "nm": "Robot window", "sr": 1, "ao": 0, "bm": 0,
        "ks": {"o": static(100), "r": static(0), "p": static([0, 0, 0]), "a": static([0, 0, 0]),
               "s": static([100, 100, 100])},
        "shapes": lottie_nodes(TREE), "ip": 0, "op": TOTAL, "st": 0,
    }
    return {
        "v": "5.7.4", "fr": FPS, "ip": 0, "op": TOTAL, "w": 1024, "h": 1024, "nm": "Motion Kit", "ddd": 0,
        "assets": [], "layers": [layer],
        "markers": [{"tm": m["tm"], "cm": m["cm"], "dr": m["dr"]} for m in MARKERS],
    }


# ---------------------------------------------------------------- standalone preview
PREVIEW_TPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Kit preview</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;background:#E8EDF4;color:#0D1A31;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:28px 16px}
  main{max-width:1180px;margin:0 auto;display:grid;gap:16px}
  h1{margin:0;font-size:28px}
  .stages{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media (max-width:760px){.stages{grid-template-columns:1fr}}
  figure{margin:0;background:#F7F9FC;border:1px solid #CDD6E2;border-radius:14px;padding:10px;display:grid;gap:8px}
  .stage{aspect-ratio:1/1;border-radius:9px;overflow:hidden;background:#E3E8EE}
  .stage>svg,#lottie{display:block;width:100%;height:100%}
  figcaption{font-weight:600;font-size:14px;padding:0 4px}
</style>
</head>
<body>
<main>
  <h1>Motion Kit</h1>
  <div class="stages">
    <figure><div class="stage">%%SVG%%</div><figcaption>Animated SVG</figcaption></figure>
    <figure><div class="stage"><div id="lottie"></div></div><figcaption>Lottie</figcaption></figure>
  </div>
</main>
<script type="application/json" id="data">%%LOTTIE%%</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>
<script>
  lottie.loadAnimation({container: document.getElementById('lottie'), renderer: 'svg', loop: true, autoplay: true,
    animationData: JSON.parse(document.getElementById('data').textContent)});
</script>
</body>
</html>
"""


def js_safe(s):
    return s.replace("</", "<\\/")


def main():
    check_spec()
    svg_file = build_svg(inline=False)
    lottie_text = json.dumps(build_lottie(), separators=(",", ":"))
    preview = PREVIEW_TPL.replace("%%SVG%%", build_svg(inline=False)).replace("%%LOTTIE%%", js_safe(lottie_text))
    outputs = {"motion-kit.svg": svg_file, "motion-kit.json": lottie_text, "motion-kit-preview.html": preview}
    for name, text in outputs.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(text)

    kb = lambda s: f"{len(s.encode()) / 1024:.0f} KB"
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    page = (tpl
            .replace("%%SVG_INLINE%%", build_svg(inline=True))
            .replace("%%LOTTIE%%", js_safe(lottie_text))
            .replace("%%SVG_TEXT%%", js_safe(json.dumps(svg_file)))
            .replace("%%PREVIEW_TEXT%%", js_safe(json.dumps(preview)))
            .replace("%%SVG_KB%%", kb(svg_file))
            .replace("%%JSON_KB%%", kb(lottie_text))
            .replace("%%PREVIEW_KB%%", kb(preview)))
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("  ".join(f"{n} {kb(t)}" for n, t in outputs.items()))


if __name__ == "__main__":
    main()
