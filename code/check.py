import re

from .master import Master
from .models import Vacancy

WORDNUM = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
YEARS = re.compile(r'(?:(\w+)\s+)?\b(\d+|' + '|'.join(WORDNUM) + r')(\+)?\s+years?\b', re.I)
NUM = re.compile(r'\d+(?:[.,]\d+)?%?')
TERM = re.compile(r"[A-Za-z][\w+#./'-]*")
SENTENCE = re.compile(r'(?<=[.!?:])\s+|\n+')


def vocab(*texts: str) -> set[str]:
    return {t.strip(".,;:()'").lower() for text in texts for t in TERM.findall(text or '')}


def years_problems(text: str) -> list[str]:
    out = []
    for m in YEARS.finditer(text):
        n = int(m.group(2)) if m.group(2).isdigit() else WORDNUM[m.group(2).lower()]
        hedge = (m.group(1) or '').lower() in ('almost', 'nearly')
        if n > 3 or (n == 3 and (m.group(3) or not hedge)):
            out.append(f'experience claim "{m.group(0).strip()}" exceeds almost three years')
    return out


def new_numbers(text: str, source: str) -> list[str]:
    allowed = set(NUM.findall(source))
    return [n for n in NUM.findall(YEARS.sub(' ', text)) if n not in allowed]


def new_terms(text: str, allowed: set[str]) -> list[str]:
    out = []
    for sentence in SENTENCE.split(text or ''):
        for i, tok in enumerate(TERM.findall(sentence)):
            t = tok.strip(".,;:()'")
            special = (i > 0 and t[:1].isupper()) or any(c.isupper() for c in t[1:]) \
                or any(c in t for c in '+#/') or any(c.isdigit() for c in t)
            if t and special and t.lower() not in allowed:
                out.append(t)
    return sorted(set(out))


def validate(plan: dict, m: Master, v: Vacancy, cfg: dict) -> list[str]:
    p = []
    if plan.get('vacancy_id') != v.id:
        p.append('vacancy_id does not match the vacancy')
    if plan.get('decision') not in ('prepare', 'skip'):
        p.append('decision must be prepare or skip')
    if not isinstance(plan.get('fit'), int) or not 0 <= plan['fit'] <= 100:
        p.append('fit must be an integer 0..100')
    if plan.get('eligible') not in ('yes', 'no', 'unclear'):
        p.append('eligible must be yes, no or unclear')
    gaps = plan.get('gaps', [])
    if any(g.get('kind') not in ('learnable', 'long_term') for g in gaps):
        p.append('every gap needs kind learnable or long_term')
    if plan.get('decision') != 'prepare':
        return p
    if plan.get('eligible') == 'no':
        p.append('prepared although not eligible')

    master_vocab = vocab(m.text)
    if plan.get('headline') not in cfg['headlines']:
        p.append(f'headline "{plan.get("headline")}" is not in settings.headlines')

    profile = plan.get('profile', '')
    p += [f'profile: {x}' for x in years_problems(profile)]
    p += [f'profile: number {n} not in the master CV' for n in new_numbers(profile, m.text)]
    p += [f'profile: term "{t}" not in the master CV' for t in new_terms(profile, master_vocab)]

    groups = plan.get('groups', {})
    for name in plan.get('group_order') or groups:
        if name not in m.groups:
            p.append(f'unknown group "{name}"')
    seen = set()
    for name, items in groups.items():
        for item in items:
            f = m.fact(item.get('id', ''))
            if not f:
                p.append(f'{name}: unknown fact id {item.get("id")}')
                continue
            if f.group != name:
                p.append(f'{f.id}: belongs to "{f.group}", not "{name}"')
            if not f.confirmed:
                p.append(f'{f.id}: fact is unconfirmed and cannot be used')
            if f.id in seen:
                p.append(f'{f.id}: used twice')
            seen.add(f.id)
            text = item.get('text') or f.text
            p += [f'{f.id}: number {n} not in its fact' for n in new_numbers(text, f.text)]
            p += [f'{f.id}: term "{t}" not in the master CV' for t in new_terms(text, master_vocab)]
            p += [f'{f.id}: {x}' for x in years_problems(text)]
    if len(seen) < 6:
        p.append(f'only {len(seen)} experience bullets, need at least 6')

    for label, items in plan.get('skills', {}).items():
        known = m.skills.get(label)
        if known is None:
            p.append(f'unknown skills line "{label}"')
            continue
        p += [f'skill "{s}" is not in the master line "{label}"' for s in items if s not in known]

    learning = plan.get('learning', [])
    learnable = {g['skill'].lower() for g in gaps if g.get('kind') == 'learnable'} | {s.lower() for s in m.learning}
    if len(learning) > cfg['learning_max']:
        p.append(f'learning line has {len(learning)} items, max {cfg["learning_max"]}')
    p += [f'learning item "{s}" is not a learnable gap' for s in learning if s.lower() not in learnable]
    have = {s.lower() for s in m.all_skills()}
    p += [f'learning item "{s}" is already a listed skill' for s in learning if s.lower() in have]

    letter = plan.get('letter', '')
    words = len(letter.split())
    if not 40 <= words <= cfg['letter_max_words']:
        p.append(f'letter has {words} words, allowed 40..{cfg["letter_max_words"]}')
    if v.company.lower() not in letter.lower():
        p.append('letter does not name the company')
    letter_vocab = master_vocab | vocab(v.description, v.title, v.company, ' '.join(learning))
    p += [f'letter: {x}' for x in years_problems(letter)]
    p += [f'letter: number {n} not in the master CV' for n in new_numbers(letter, m.text)]
    p += [f'letter: term "{t}" not in the CV or the vacancy' for t in new_terms(letter, letter_vocab)]

    review = plan.get('review') or {}
    if review.get('verdict') != 'ok':
        p.append('semantic fact-check review is missing or not ok')
    return p
