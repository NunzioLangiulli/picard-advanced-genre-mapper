"""Pure genre normalization and album voting rules."""
from collections import Counter
import re


def key(value):
    return re.sub(r'[\s-]+', '', value).casefold()


def parse_rules(text):
    rules = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f'Line {number}: expected alias = preferred spelling.')
        alias, target = (part.strip() for part in line.split('=', 1))
        if not alias or not target or any(c in target for c in ';,|'):
            raise ValueError(f'Line {number}: invalid alias or preferred spelling.')
        normalized = key(alias)
        if normalized in rules and rules[normalized] != target:
            raise ValueError(f'Line {number}: conflicting spelling for {alias}.')
        rules[normalized] = target
    return rules


def normalize(values, rules, separators=';,|', unknown='keep'):
    result, seen = [], set()
    for value in values:
        parts = re.split('[' + re.escape(separators) + ']', value) if separators else [value]
        for part in parts:
            part = part.strip()
            if not part:
                continue
            genre = rules.get(key(part), part if unknown == 'keep' else '')
            if genre and genre.casefold() not in seen:
                result.append(genre)
                seen.add(genre.casefold())
    return result


def choose(lists, tie='first', ignore_empty=True):
    votes, representatives = Counter(), {}
    for genres in lists:
        if not genres and ignore_empty:
            continue
        identity = tuple(sorted(g.casefold() for g in genres))
        votes[identity] += 1
        representatives.setdefault(identity, genres)
    if not votes:
        return None
    winners = [identity for identity in votes if votes[identity] == max(votes.values())]
    if len(winners) > 1 and tie == 'skip':
        return None
    winner = min(winners) if tie == 'alphabetical' else winners[0]
    return representatives[winner]
