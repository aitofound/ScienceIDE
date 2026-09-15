#!/usr/bin/env python3
"""Generate the README's source-grounded, standalone SVG IDE mockup.

Run from any directory: python3 docs/assets/make_ide_overview.py
Render from the repository root:
  uv run --with cairosvg python -c "import cairosvg; cairosvg.svg2png(\
url='docs/assets/ide_overview.svg', write_to='docs/assets/ide_overview.png', \
output_width=1600)"

Content sources (all relative to the repository root):
* README.md, environments/README.md, hard85/README.md: release counts, grading.
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

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" font-family="{SANS}" role="img" aria-labelledby="title description">',
       '<title id="title">ScienceIDE — environments, task repair, verification and learning</title>',
       '<desc id="description">IDE showcase using published repository content. The CFC task displays its instruction and reference repair. Archived nop and oracle evaluations grade cfc-offline and cfc-online. SFT is a workflow concept whose pipeline is not in this preview. RL shows the published Qwen3.5-4B reward summaries from async GRPO on PSRL.</desc>']


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


# The shadow is plain SVG geometry; it also renders consistently in CairoSVG.
rect(0, 0, 1600, 900, '#edf2f8')
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
svg.append('</svg>')

out = ROOT / 'docs/assets/ide_overview.svg'
out.write_text('\n'.join(svg) + '\n')
print(f'{out.relative_to(ROOT)}: {out.stat().st_size:,} bytes · 1600 × 900')
