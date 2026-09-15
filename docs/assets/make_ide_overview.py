#!/usr/bin/env python3
"""Generate the README's source-grounded, standalone SVG IDE mockup.

Run from the repository root: python3 docs/assets/make_ide_overview.py
Render from the repository root:
  uv run --with cairosvg python -c "import cairosvg; cairosvg.svg2png(\
url='docs/assets/ide_overview.svg', write_to='docs/assets/ide_overview.png', \
output_width=1600)"

Content sources (all relative to the repository root):
* README.md, environments/README.md, hard85/README.md: release counts, grading.
* README.md published-environment table: all outer tile names and upstream codes.
* docs/assets/pipeline.svg: palette and '64 environments, 26 codes'.
* hard85/mitgcm-biogeo/<TASK>/: instruction, defect, fix and archived evals.
* environments/mitgcm-biogeo/{cases,scoring,validation,harbor}/: verifier.
* RL/README.md: Qwen3.5-4B, PSRL, published endpoint/peak rewards.
* RL/scienceide_rl/{agent_loop,reward,runner}.py: episodes, data and reward.

The SFT workflow is an owner-approved concept, explicitly marked as absent
from this preview. No SFT file or training result is claimed. Reward summaries
show documented endpoints and peaks; no intermediate curve is invented.
Line numbers belong to the displayed source. PASS/FAIL means archived case
equivalence, not a new evaluation. The repair diff is the inverse of defect.json.
Outer domain glyphs are decorative vector sketches, not measured simulations.
Seven original domain emblems use white paths on solid, rounded badges. They
are illustrations authored here, not official upstream logos or brand assets.
The original IDE is preserved at native size inside a translated group.
"""

import json
import re
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = 'mitgcm-biogeo-repair-sem-data-cfc11-schmidt-cubic'
TASK_DIR = ROOT / 'hard85' / 'mitgcm-biogeo' / TASK
ENV_DIR = ROOT / 'environments' / 'mitgcm-biogeo'
BLUE, ORANGE = '#3b6ea5', '#c97b2a'
INK, SECONDARY = '#1c2b3a', '#3a4a5a'
PANEL, BORDER = '#f4f7fb', '#dbe3ec'
MUTED, GREEN, RED = '#687b8f', '#28714e', '#ac4550'
SANS = 'Helvetica, Arial, sans-serif'
MONO = '"Liberation Mono", Consolas, "DejaVu Sans Mono", monospace'
WIDTH, HEIGHT, IDE_Y = 1600, 1352, 224
DOMAINS = {
    'astro': ('#8b63ad', '#e6d8f0'),
    'ocean': ('#2f8faa', '#d0eaf5'),
    'plasma': ('#bd5d82', '#f6dbe7'),
    'materials': ('#398b70', '#d3eddf'),
    'detector': (ORANGE, '#ffe8c4'),
    'quantum': ('#6967b4', '#dfdef7'),
}


def read(path):
    return (ROOT / path).read_text()


# Read real source text rather than duplicating code and instruction excerpts.
instruction = (TASK_DIR / 'instruction.md').read_text().splitlines()
defect = json.loads((TASK_DIR / 'defect.json').read_text())['edits'][0]
fix = json.loads((TASK_DIR / 'fix.json').read_text())['edits'][0]
assert fix['old'] == defect['new'] and fix['new'] == defect['old']
records = [json.loads(line) for line in (TASK_DIR / 'eval/evals.jsonl').read_text().splitlines()]
oracle = next(row for row in records if row['agent']['name'] == 'oracle')
nop = next(row for row in records if row['agent']['name'] == 'nop')
reward_lines = read('RL/scienceide_rl/reward.py').splitlines()
reward_excerpt = [line for line in reward_lines if line.strip().startswith((
    'reward_key = extra_info.get(', 'harbor_rewards = extra_info.get('))]
assert len(reward_excerpt) == 2
assert 'get_training_data(session_id)' in read('RL/scienceide_rl/agent_loop.py')
assert '64 environments, 26 codes' in read('docs/assets/pipeline.svg')
assert '30 of the 85' in read('README.md')
assert 'Fifteen environments' in read('environments/README.md')
assert '## Published (30)' in read('hard85/README.md')
rl_readme = read('RL/README.md')
assert 'Qwen3.5-4B' in rl_readme
laps = re.search(r'Reward climbs from (0\.\d+) to (0\.\d+), peaking at (0\.\d+)', rl_readme).groups()
biogeo = re.search(r'Reward climbs from ~(0\.\d+) to ~(0\.\d+), peaking at (0\.\d+)', rl_readme).groups()
formula = 'reward_repair = max(0, (reward - floor)/(1 - floor))'
assert 'reward_repair = max(0, (reward − floor) / (1 − floor))' in read('README.md')

published_section = read('README.md').split('## Published environments\n', 1)[1].split('Held out for now', 1)[0]
published = dict(re.findall(r'^\| `([^`]+)` \| ([^(|]+) \(', published_section, re.MULTILINE))
published = {name: code.strip() for name, code in published.items()}
TOP_TILES = [
    ('athena-chemistry', 'astro', 'field'),
    ('athena-gr', 'astro', 'gravity'),
    ('athena-sgfft', 'astro', 'density'),
    ('athena-sr', 'astro', 'shock'),
    ('gkeyll-vlasov', 'plasma', 'phase'),
    ('dscribe-descriptors', 'materials', 'lattice'),
    ('nest-noble-element-microphysics', 'detector', 'track'),
]
BOTTOM_TILES = [
    ('mitgcm-atmos', 'ocean', 'atmosphere'),
    ('mitgcm-biogeo', 'ocean', 'biogeo'),
    ('mitgcm-iceshelf', 'ocean', 'shelf'),
    ('mitgcm-mixing', 'ocean', 'mixing'),
    ('mitgcm-ocean', 'ocean', 'gyre'),
    ('mitgcm-seaice', 'ocean', 'ice'),
    ('edkit-adaptive-krylov-time-evolution', 'quantum', 'evolution'),
    ('stim-stab', 'quantum', 'circuit'),
]
assert len(published) == len(TOP_TILES + BOTTOM_TILES) == 15
assert {name for name, _, _ in TOP_TILES + BOTTOM_TILES} == published.keys()
assert all((ROOT/'environments'/name).is_dir() for name in published)

# Upstream name, palette, original emblem, domain description, group width.
TOP_GROUPS = [
    ('Athena++', 'astro', 'mhd', ['Astrophysical MHD'], 772),
    ('Gkeyll', 'plasma', 'plasma', ['Plasma kinetics'], 240),
    ('DScribe', 'materials', 'crystal', ['Materials descriptors'], 240),
    ('NEST', 'detector', 'detector', ['Noble-element detector', 'microphysics'], 240),
]
BOTTOM_GROUPS = [
    ('MITgcm', 'ocean', 'earth', ['Ocean / atmosphere / sea ice / biogeochemistry'], 1056),
    ('EDKit', 'quantum', 'many-body', ['Quantum many-body'], 228),
    ('Stim', 'quantum', 'stabilizer', ['Quantum stabilizer', 'circuits'], 228),
]
assert sum(group[-1] for group in TOP_GROUPS) + 20*(len(TOP_GROUPS)-1) == 1552
assert sum(group[-1] for group in BOTTOM_GROUPS) + 20*(len(BOTTOM_GROUPS)-1) == 1552

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{SANS}" role="img" aria-labelledby="title description">',
       '<title id="title">ScienceIDE — environments, task repair, verification and learning</title>',
       '<desc id="description">Seven original scientific domain emblems group fifteen published environments above and below an IDE. The badges show MHD, Earth systems, plasma, crystals, detector microphysics, quantum many-body dynamics, and stabilizer circuits; they are not upstream project logos. Each environment is named with its upstream code and a decorative sketch. The CFC task displays its instruction and reference repair. Archived nop and oracle evaluations grade cfc-offline and cfc-online. SFT is a workflow concept whose pipeline is not in this preview. RL shows the published Qwen3.5-4B reward summaries from async GRPO on PSRL.</desc>']


def rect(x, y, w, h, fill, stroke=None, radius=0, **attrs):
    extra = ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"'
               + (f' stroke="{stroke}"' if stroke else '') + extra + '/>')


def line(x1, y1, x2, y2, color=BORDER, width=1, **attrs):
    extra = ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{extra}/>')


def path(d, color, width=1.5, fill='none'):
    svg.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def text(x, y, value, size=15, color=INK, weight=400, mono=False, anchor='start', bounds=None):
    """Bounds are audit metadata; they never hide overflow with a clip path."""
    assert size >= 13
    family = MONO if mono else SANS
    extra = f' data-bounds="{bounds}"' if bounds else ''
    if mono:
        extra += ' xml:space="preserve"'
    svg.append(f'<text x="{x}" y="{y}" font-family="{escape(family, quote=True)}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}"{extra}>{escape(str(value))}</text>')


def dot(x, y, radius, color, stroke=None):
    svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"' + (f' stroke="{stroke}" stroke-width="2"' if stroke else '') + '/>')


def code_text(x, y, value, size=15, bounds=None):
    text(x, y, value, size, INK, mono=True, bounds=bounds)
    # Only color string literals; preserve every character of the real code.
    chunks = re.split(r'("[^"]*")', value)
    colored = ''.join(f'<tspan fill="{BLUE}">{escape(s)}</tspan>'
                      if s.startswith('"') else escape(s) for s in chunks)
    svg[-1] = svg[-1].replace(escape(value) + '</text>', colored + '</text>')


def folder(x, y):
    path(f'M{x},{y-8} h6 l3,3 h8 v12 h-17 z', ORANGE, 1.3, '#fff3e6')


def file_icon(x, y, color=MUTED):
    path(f'M{x},{y-9} h8 l4,4 v13 h-12 z M{x+8},{y-9} v4 h4', color, 1.2)


def chevron(x, y, opened=True):
    path(f'M{x},{y-2} l3,3 l3,-3' if opened else f'M{x+2},{y-4} l3,3 l-3,3', MUTED, 1.2)


def pill(x, y, w, value, fill=PANEL, color=SECONDARY, size=13):
    rect(x, y, w, 26, fill, radius=5)
    text(x+w/2, y+18, value, size, color, 600, anchor='middle', bounds=f'{x+4},{y},{x+w-4},{y+26}')


def tree(y, label, depth=0, is_folder=False, opened=True, selected=False):
    x = 47 + depth * 20
    if selected:
        rect(36, y-17, 336, 26, '#e4eef9', radius=4)
        rect(36, y-17, 3, 26, BLUE, radius=1)
    if is_folder:
        chevron(x, y-4, opened)
        folder(x+13, y-4)
    else:
        file_icon(x+14, y-4, BLUE if selected else MUTED)
    text(x+39, y, label, 15, BLUE if selected else SECONDARY,
         600 if selected else 400, mono=True, bounds='40,118,372,840')


def arrow(x1, x2, y):
    line(x1, y, x2, y, MUTED, 1.3)
    path(f'M{x2-4},{y-3} l4,3 l-4,3', MUTED, 1.3)


def soft_wrap(value, width=66):
    """Keep the source's lines intact, but avoid a tiny last visual fragment."""
    chunks = textwrap.wrap(value, width=width)
    if len(chunks) > 1 and len(chunks[-1]) < 16:
        while len(chunks[-1]) < 22:
            chunks[-2], word = chunks[-2].rsplit(' ', 1)
            chunks[-1] = word + ' ' + chunks[-1]
    assert ' '.join(chunks) == value
    return chunks


def domain_glyph(x, y, kind, color, tint):
    """Small hand-drawn SVG sketches; local coordinates stay inside 76 × 56."""
    svg.append(f'<g transform="translate({x} {y})" aria-hidden="true">')
    if kind == 'field':
        for yy in (12, 25, 38):
            path(f'M3,{yy} C19,{yy-16} 35,{yy+17} 72,{yy-2}', color, 1.8)
        for xx, yy in [(17, 16), (38, 32), (60, 10)]:
            dot(xx, yy, 3, color)
        path('M49,43 l7,-5 l-1,8 M56,38 l-4,11', color, 1.5)
    elif kind == 'gravity':
        for yy in (7, 20, 35, 48):
            path(f'M3,{yy} C28,{yy} 22,27 38,27 S50,{yy} 73,{yy}', color, 1.6)
        dot(38, 27, 8, color)
        svg.append(f'<ellipse cx="38" cy="27" rx="16" ry="12" fill="none" stroke="{color}" stroke-width="1.4"/>')
    elif kind == 'density':
        for yy, height in [(12, 9), (27, 17), (44, 10)]:
            path(f'M3,{yy} C15,{yy-height} 19,{yy+height} 30,{yy} S47,{yy-height} 56,{yy} S67,{yy+height} 73,{yy}', color, 1.8)
        for xx, yy in [(10, 27), (24, 27), (38, 27), (45, 26), (50, 28), (65, 27)]:
            dot(xx, yy, 2, color)
    elif kind == 'shock':
        path('M43,4 C37,15 46,21 40,30 S44,41 39,51', color, 2.4)
        for yy in (11, 25, 41):
            path(f'M3,{yy} h27 m-4,-3 l4,3 l-4,3', color, 1.6)
            path(f'M49,{yy} C54,{yy-7} 59,{yy+7} 73,{yy-2}', color, 1.6)
    elif kind == 'atmosphere':
        path('M3,44 Q38,8 73,44', color, 1.8)
        path('M8,49 Q38,20 69,49', color, 1.1)
        path('M8,14 H45 C61,14 57,2 49,6 M2,23 H59 C76,23 72,10 64,14', color, 2)
        path('M47,38 C56,34 66,36 72,42', color, 1.5)
    elif kind == 'biogeo':
        for yy in (28, 40, 51):
            path(f'M3,{yy} Q12,{yy-9} 21,{yy} T39,{yy} T57,{yy} T73,{yy}', color, 1.7)
        for xx, yy, rr in [(15, 10, 3), (31, 18, 2), (47, 8, 4), (63, 17, 2.5)]:
            dot(xx, yy, rr, tint, color)
    elif kind == 'phase':
        path('M6,3 V50 H74', color, 1.2)
        for rx, ry in [(28, 17), (20, 11), (11, 5)]:
            svg.append(f'<ellipse cx="40" cy="26" rx="{rx}" ry="{ry}" transform="rotate(-23 40 26)" fill="none" stroke="{color}" stroke-width="1.6"/>')
        dot(40, 26, 2.8, color)
    elif kind == 'lattice':
        rows = [[(10, 10), (33, 6), (61, 13)], [(16, 29), (40, 26), (68, 31)], [(8, 47), (33, 49), (60, 48)]]
        for row in rows:
            path('M' + ' L'.join(f'{xx},{yy}' for xx, yy in row), color, 1.3)
        for i in range(3):
            path('M' + ' L'.join(f'{row[i][0]},{row[i][1]}' for row in rows), color, 1.3)
        for row in rows:
            for xx, yy in row:
                dot(xx, yy, 3.7, '#ffffff', color)
    elif kind == 'shelf':
        path('M3,9 H65 L53,17 L47,42 L34,26 L24,19 H3 Z', color, 1.6, tint)
        path('M3,25 H20 M55,25 H73 M3,43 Q13,37 23,43 M55,43 Q64,37 73,43', color, 1.8)
        path('M10,14 H37 M41,13 H54', color, 1.1)
    elif kind == 'mixing':
        path('M3,10 C22,1 46,16 65,8 M6,48 C27,38 47,54 73,44', color, 1.6)
        path('M18,15 C-1,27 24,46 37,31 C48,17 24,12 24,25 C24,34 34,33 34,27', color, 1.8)
        path('M56,16 C38,8 37,39 56,40 C74,42 75,20 61,23 C50,26 60,35 64,30', color, 1.8)
    elif kind == 'gyre':
        path('M20,8 C63,-3 85,37 51,48 C18,60 -3,32 15,16 C34,1 66,15 56,34 C45,50 20,40 25,25 C29,16 49,18 44,30', color, 1.9)
        path('M40,26 l4,4 l4,-4 M17,7 l3,1 l-1,5', color, 1.7)
    elif kind == 'ice':
        for d in ['M6,13 l14,-8 l11,10 l-9,13 l-15,-2 z', 'M41,5 l18,3 l9,13 l-20,5 l-11,-10 z', 'M29,34 l14,-3 l14,11 l-10,11 l-19,-5 z']:
            path(d, color, 1.6, tint)
        path('M3,41 l8,-3 l9,3 M59,36 l7,-3 l7,3', color, 1.4)
    elif kind == 'track':
        path('M5,48 L33,27 L48,12 M33,27 L66,35 M33,27 L43,48', color, 1.9)
        for xx, yy in [(33, 27), (50, 10), (68, 36), (44, 49)]:
            dot(xx, yy, 2.8, color)
        for xx, yy in [(16, 11), (62, 12), (13, 30), (59, 50)]:
            path(f'M{xx-4},{yy} h8 M{xx},{yy-4} v8', color, 1.5)
        dot(33, 27, 8, 'none', color)
    elif kind == 'evolution':
        path('M5,3 V50 H73', color, 1.2)
        path('M8,37 C17,-6 27,3 34,23 S48,50 55,26 S66,6 73,15', color, 1.9)
        for xx, yy in [(10, 30), (25, 9), (40, 35), (57, 20), (71, 13)]:
            line(xx, 48, xx, yy, color, 1, stroke_dasharray='2 3', opacity=.45)
            dot(xx, yy, 2.4, '#ffffff', color)
    elif kind == 'circuit':
        for yy in (10, 27, 45):
            line(3, yy, 74, yy, color, 1.5)
        line(23, 10, 23, 27, color, 1.6)
        line(51, 27, 51, 45, color, 1.6)
        for xx, yy in [(23, 10), (51, 27)]:
            dot(xx, yy, 3, color)
        for xx, yy in [(23, 27), (51, 45)]:
            dot(xx, yy, 5, tint, color)
            path(f'M{xx-4},{yy} h8 M{xx},{yy-4} v8', color, 1.2)
        rect(60, 3, 10, 14, tint, color, 2)
    else:
        raise ValueError(kind)
    svg.append('</g>')


def environment_name_lines(name, width):
    chunks = textwrap.wrap(name, width=width, break_long_words=False, break_on_hyphens=True)
    assert ''.join(chunks) == name and len(chunks) <= 2
    return chunks


def domain_emblem(x, y, kind, color):
    """Original 44px badges, with consistent white 2px rounded path glyphs."""
    svg.append(f'<g data-emblem="{kind}" transform="translate({x} {y})">')
    rect(0, 0, 44, 44, color, radius=11)
    white = '#ffffff'
    if kind == 'mhd':
        path('M8,13 C16,5 28,5 36,13 M8,31 C16,39 28,39 36,31', white, 2)
        path('M22,11 L25,19 L33,22 L25,25 L22,33 L19,25 L11,22 L19,19 Z', white, 0, white)
    elif kind == 'earth':
        path('M9,22 A13,13 0 0 1 35,22 M22,9 C17,12 15,17 15,21 M22,9 C27,12 29,17 29,21', white, 2)
        path('M8,26 Q13,21 18,26 T28,26 T38,26 M8,33 Q13,28 18,33 T28,33 T38,33', white, 2)
    elif kind == 'plasma':
        path('M10,31 C2,24 16,8 29,9 C45,10 34,31 20,34 C16,35 12,34 10,31 Z', white, 2)
        path('M16,26 C11,21 22,14 28,16 C35,19 25,29 19,28 Z', white, 2)
        path('M21,22 h2', white, 3)
    elif kind == 'crystal':
        path('M22,8 L35,15 V29 L22,36 L9,29 V15 Z M9,15 L22,22 L35,15 M22,22 V36', white, 2)
        path('M22,8 V22', white, 2)
    elif kind == 'detector':
        path('M12,11 C12,6 32,6 32,11 V33 C32,39 12,39 12,33 Z M12,11 C12,16 32,16 32,11', white, 2)
        path('M16,31 L22,24 L27,18 M22,24 L29,29 M22,24 L19,18', white, 2)
        path('M22,22 v4 M20,24 h4', white, 2)
    elif kind == 'many-body':
        path('M13,13 H31 M13,13 L22,25 L31,13', white, 2)
        for xx, yy in [(13, 13), (31, 13), (22, 25)]:
            path(f'M{xx-2.8},{yy} a2.8,2.8 0 1 0 5.6,0 a2.8,2.8 0 1 0 -5.6,0', white, 1.5, color)
        path('M8,35 C13,24 17,40 23,34 S31,28 36,33', white, 2)
    elif kind == 'stabilizer':
        path('M8,13 H36 M8,31 H36 M19,13 V31', white, 2)
        path('M16,13 a3,3 0 1 0 6,0 a3,3 0 1 0 -6,0', white, 0, white)
        path('M14,31 a5,5 0 1 0 10,0 a5,5 0 1 0 -10,0', white, 2, color)
        path('M15,31 h8 M19,27 v8 M28,9 h7 v8 h-7 Z', white, 2)
    else:
        raise ValueError(kind)
    svg.append('</g>')


def environment_band(tiles, groups, header_y, bus_y, band_id, top):
    """Seven explicit upstream/domain groups, each with a badge and child tiles."""
    svg.append(f'<g id="{band_id}">')
    group_x = 24
    ports = []
    rendered = []
    y = header_y + 68
    for upstream, domain, emblem, description, group_width in groups:
        color, tint = DOMAINS[domain]
        children = [tile for tile in tiles if published[tile[0]] == upstream]
        assert children
        svg.append(f'<g data-domain-group="{escape(upstream, quote=True)}">')
        rect(group_x, header_y-8, group_width, 204, '#ffffff', '#d5e0ed', 13)
        rect(group_x+1, header_y-7, group_width-2, 66, tint, radius=12, opacity=.6)
        domain_emblem(group_x+12, header_y+2, emblem, color)
        header_bounds = f'{group_x+64},{header_y-2},{group_x+group_width-10},{header_y+54}'
        text(group_x+68, header_y+17, upstream, 17, INK, 600, bounds=header_bounds)
        for j, label in enumerate(description):
            text(group_x+68, header_y+35+j*14, label, 13, SECONDARY, bounds=header_bounds)
        branch_y = header_y+58
        line(group_x+34, header_y+46, group_x+34, branch_y, color, 1.2)
        line(group_x+8, branch_y, group_x+group_width-8, branch_y, color, 1.2, opacity=.45)
        dot(group_x+34, branch_y, 2, color)
        tile_width = (group_width-16-(len(children)-1)*12)/len(children)
        for i, (name, _, glyph) in enumerate(children):
            x = group_x+8+i*(tile_width+12)
            rendered.append(name)
            line(x+tile_width/2, branch_y, x+tile_width/2, y, color, 1.2, opacity=.45)
            svg.append(f'<g data-environment="{name}" data-upstream="{escape(published[name], quote=True)}" data-domain="{domain}">')
            rect(x, y+3, tile_width, 120, color, radius=10, opacity=.08)
            rect(x, y, tile_width, 120, f'url(#tile-{domain})', '#d9e2ed', 10)
            rect(x+13, y+12, 38, 4, color, radius=2)
            text(x+14, y+39, published[name], 15, color, 600,
                 bounds=f'{x+12},{y+20},{x+tile_width-90},{y+45}')
            domain_glyph(x+tile_width-88, y+10, glyph, color, tint)
            lines = environment_name_lines(name, 18 if tile_width < 200 else 22)
            name_size = 14 if tile_width < 175 or max(map(len, lines)) > 19 else 15
            baselines = [y+99] if len(lines) == 1 else [y+87, y+106]
            for baseline, chunk in zip(baselines, lines):
                text(x+14, baseline, chunk, name_size, INK, 600, mono=True,
                     bounds=f'{x+12},{y+70},{x+tile_width-12},{y+114}')
            svg.append('</g>')
        ports.append((group_x+group_width/2, color))
        svg.append('</g>')
        group_x += group_width+20
    assert set(rendered) == {tile[0] for tile in tiles}
    frame_edge = header_y+196 if top else header_y-8
    line(20, bus_y, ports[-1][0], bus_y, '#9fb8d1', 1.5)
    for port_x, color in ports:
        line(port_x, frame_edge, port_x, bus_y, color, 1.4, opacity=.72)
        dot(port_x, bus_y, 2.4, color)
    target_y = IDE_Y+(184 if top else 857)
    path(f'M20,{bus_y} Q12,{bus_y} 12,{bus_y+(8 if top else -8)} V{target_y-8 if top else target_y+8} Q12,{target_y} 20,{target_y} H24', BLUE, 1.3)
    path(f'M20,{target_y-3} l4,3 l-4,3', BLUE, 1.3)
    svg.append('</g>')


# Published environment bands frame the unchanged, full-size IDE.
svg.append('<defs>')
for domain, (color, tint) in DOMAINS.items():
    svg.append(f'<linearGradient id="tile-{domain}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{tint}"/><stop offset="1" stop-color="#ffffff"/></linearGradient>')
svg.append('</defs>')
rect(0, 0, WIDTH, HEIGHT, '#edf2f8')

environment_band(TOP_TILES, TOP_GROUPS, 20, 230, 'environments-above', True)
environment_band(BOTTOM_TILES, BOTTOM_GROUPS, 1140, 1120, 'environments-below', False)

# The shadow is plain SVG geometry; it also renders consistently in CairoSVG.
svg.append(f'<g id="ide-window" transform="translate(0 {IDE_Y})">')
for offset, opacity in [(11, .025), (8, .035), (5, .045)]:
    rect(24, 24+offset, 1552, 852, '#263f5e', radius=15, opacity=opacity)
rect(24, 24, 1552, 852, '#ffffff', BORDER, 13)
rect(25, 25, 1550, 48, '#f8fafd', radius=12)
rect(25, 60, 1550, 14, '#f8fafd')
for x, color in [(48, '#e47b78'), (70, '#e6ba64'), (92, '#75b69c')]:
    dot(x, 49, 6, color)
text(800, 57, 'ScienceIDE', 22, INK, 600, anchor='middle')
text(1548, 55, 'preview', 14, MUTED, anchor='end')
line(24, 74, 1576, 74)

# Explorer and tabs are parts of the same IDE window.
rect(25, 75, 359, 765, PANEL)
text(48, 101, 'Explorer', 16, SECONDARY, 600)
text(360, 101, '···', 18, MUTED, anchor='end')
rect(384, 75, 1191, 41, '#f0f4f9')
rect(384, 75, 204, 41, '#ffffff')
rect(384, 75, 204, 3, BLUE)
file_icon(404, 95, BLUE)
text(426, 101, 'instruction.md', 14, BLUE, mono=True)
text(568, 101, '×', 16, MUTED)
line(588, 75, 588, 116)
file_icon(608, 95)
text(630, 101, 'defect.json', 14, SECONDARY, mono=True)
line(772, 75, 772, 116)
file_icon(792, 95, ORANGE)
text(814, 101, 'RL/scienceide_rl/reward.py', 14, SECONDARY, mono=True)
line(384, 116, 1576, 116)
line(384, 74, 384, 840)

for x, y1, y2 in [(70, 220, 320), (70, 389, 563), (110, 434, 563), (70, 634, 786)]:
    line(x, y1, x, y2, '#d6e1ec')
tree(147, 'ScienceIDE', is_folder=True)
tree(184, 'environments/', 0, True)
tree(210, 'mitgcm-biogeo/', 1, True)
for y, name in zip([237, 263, 289, 315], ['cases/', 'harbor/', 'scoring/', 'validation/']):
    assert (ENV_DIR/name).is_dir()
    tree(y, name, 2, True, False)
tree(353, 'hard85/', 0, True)
tree(379, 'mitgcm-biogeo/', 1, True)
tree(405, 'mitgcm-biogeo-repair-', 2, True)
text(126, 423, 'sem-data-cfc11-schmidt-cubic/', 14, SECONDARY, mono=True, bounds='40,118,372,840')
for y, name in zip([454, 480, 506, 532, 558], ['task.toml', 'instruction.md', 'defect.json', 'fix.json', 'eval/evals.jsonl']):
    assert (TASK_DIR/name).is_file()
    tree(y, name, 3, selected=name == 'instruction.md')
tree(598, 'RL/', 0, True)
tree(624, 'scienceide_rl/', 1, True)
for y, name in zip([651, 677, 703, 729, 755, 781], ['agent_loop.py', 'reward.py', 'runner.py', 'prepare/', 'eval/', 'plot/']):
    assert (ROOT/'RL/scienceide_rl'/name).exists()
    tree(y, name, 2, name.endswith('/'), False)

# Editor: real markdown with its original source line numbers and soft wrapping.
text(410, 143, 'hard85/mitgcm-biogeo/', 13, MUTED, mono=True, bounds='400,117,1074,180')
text(410, 165, TASK + '/instruction.md', 13, SECONDARY, mono=True, bounds='400,117,1074,180')
line(384, 182, 1090, 182)
pill(946, 191, 118, 'repair', '#fff3e6', ORANGE)
y = 238
for number in range(2, 6):
    for i, chunk in enumerate(soft_wrap(instruction[number-1])):
        if i == 0:
            text(423, y, number, 13, MUTED, mono=True, anchor='end')
        text(443, y, chunk, 15.5, INK, mono=True, bounds='439,220,1072,382')
        y += 23
text(410, 405, 'Reference repair', 16, INK, 600)
text(1064, 405, 'fix.json · inverse of defect.json', 13, MUTED, anchor='end')
rect(409, 422, 655, 130, '#fbfcfe', BORDER, 7)
file_icon(426, 440, BLUE)
text(448, 446, defect['file'], 14, SECONDARY, mono=True, bounds='419,422,1054,462')
line(410, 460, 1063, 460)
rect(410, 461, 653, 39, '#fbeef0')
rect(410, 500, 653, 39, '#edf7f0')
text(429, 486, '−', 17, RED, mono=True)
text(456, 486, fix['old'].strip(), 17, RED, mono=True, bounds='448,461,1052,500')
text(429, 525, '+', 17, GREEN, mono=True)
text(456, 525, fix['new'].strip(), 17, GREEN, mono=True, bounds='448,500,1052,539')
text(410, 577, 'Pinned upstream source · MITgcm checkpoint69q', 14, MUTED)

# Verifier: archived baseline / reference-fix results, never a simulated live run.
line(1090, 116, 1090, 594)
text(1116, 150, 'Verifier', 19, INK, 600)
pill(1390, 129, 160, 'archived evaluation', '#eaf1f9', BLUE)
text(1116, 184, 'Physics cases · pointwise equivalence', 15, SECONDARY)
text(1116, 216, 'eval/evals.jsonl', 13, MUTED, mono=True)
rect(1115, 237, 436, 139, '#ffffff', BORDER, 7)
rect(1116, 238, 434, 33, PANEL, radius=6)
text(1132, 260, 'cases/', 13, MUTED, mono=True)
text(1390, 260, 'nop', 13, MUTED, mono=True, anchor='middle')
text(1489, 260, 'oracle', 13, BLUE, mono=True, anchor='middle')
for y, case in [(302, 'cfc-offline'), (350, 'cfc-online')]:
    assert (ENV_DIR/'cases'/case/'row.json').exists()
    key = 'check_' + case.replace('-', '_')
    assert nop['rewards'][key] == 0 and oracle['rewards'][key] == 1
    text(1132, y, case, 17, SECONDARY, mono=True)
    pill(1360, y-20, 60, 'FAIL', '#fbeef0', RED)
    pill(1457, y-20, 64, 'PASS', '#edf7f0', GREEN)
line(1116, 325, 1550, 325)
text(1116, 404, 'nop: untouched · oracle: reference fix', 14, MUTED)
text(1116, 442, 'reward', 15, BLUE, 600, mono=True)
text(1200, 442, 'mean physics-case score', 15, SECONDARY)
rect(1115, 462, 436, 72, PANEL, radius=6)
text(1130, 487, 'reward_repair =', 15, INK, mono=True)
text(1130, 513, 'max(0, (reward - floor)/(1 - floor))', 14, INK, mono=True, bounds='1126,462,1540,534')
text(1116, 572, 'scoring/grade.py → validation/', 14, MUTED, mono=True)

# Lower learning dock. The SFT panel makes its conceptual status explicit.
line(384, 594, 1576, 594)
line(950, 594, 950, 840)
rect(385, 595, 564, 42, '#f8fafd')
rect(951, 595, 624, 42, '#f8fafd')
text(410, 623, 'SFT', 19, BLUE, 600)
pill(469, 605, 147, 'workflow concept', '#fff3e6', ORANGE)
text(410, 666, 'Verified episodes → supervised segments', 19, INK, 600)
text(410, 690, '(pipeline not in this preview)', 14, ORANGE)
for x, label in zip([410, 540, 670, 800], ['read', 'edit', 'execute', 'inspect']):
    rect(x, 713, 103, 36, '#ffffff', BORDER, 6)
    text(x+51.5, 737, label, 15, SECONDARY, 500, mono=True, anchor='middle')
    if x != 800:
        arrow(x+109, x+123, 731)
path('M851,754 v10 H461 v-10', '#a8b8c9', 1.2)
path('M458,758 l3,-4 l3,4', '#a8b8c9', 1.2)
text(410, 797, 'Harbor episodes → TITO trajectories', 15, SECONDARY)
text(410, 823, 'RL/scienceide_rl/agent_loop.py', 14, BLUE, mono=True)

# Real RL code plus source-labelled numerical summaries (no invented curve).
text(976, 623, 'RL', 19, BLUE, 600)
text(1020, 623, 'async GRPO on PSRL', 15, SECONDARY)
pill(1424, 605, 126, 'Qwen3.5-4B', '#eaf1f9', BLUE)
for y, code in zip([662, 685], reward_excerpt):
    number = reward_lines.index(code)+1
    text(996, y, number, 13, MUTED, mono=True, anchor='end')
    code_text(1008, y, code.strip(), 15, bounds='1003,642,1550,700')
text(976, 714, 'Published reward · RL/README.md', 13, MUTED)
for x, label, values, approx in [(976, 'LAPS', laps, False), (1268, 'mitgcm-biogeo', biogeo, True)]:
    rect(x, 729, 274, 91, PANEL, radius=7)
    text(x+14, 750, label, 14, SECONDARY, 600)
    text(x+260, 750, 'start → final', 13, MUTED, anchor='end')
    summary = f'≈{values[0]} → ≈{values[1]}' if approx else f'{values[0]} → {values[1]}'
    text(x+14, 781, summary, 26, BLUE, 600)
    text(x+14, 806, f'peak {values[2]}', 14, ORANGE, 500)

# Counts match the release documents; pipeline.svg is the source of code count.
rect(25, 840, 1550, 35, '#eaf1f9', radius=10)
rect(25, 840, 1550, 18, '#eaf1f9')
line(24, 840, 1576, 840, '#cbd8e7')
dot(47, 857, 4, BLUE)
text(62, 863, '64 environments, 26 codes', 14, BLUE, 500)
line(258, 849, 258, 867, '#c1cfe0')
text(278, 863, '15 published environments', 14, SECONDARY)
text(1550, 863, '85 ScienceIDE-Hard tasks · 30 published', 14, SECONDARY, anchor='end')
svg.extend(['</g>', '</svg>'])

out = ROOT / 'docs/assets/ide_overview.svg'
out.write_text('\n'.join(svg) + '\n')
print(f'{out.relative_to(ROOT)}: {out.stat().st_size:,} bytes · {WIDTH} × {HEIGHT}')
