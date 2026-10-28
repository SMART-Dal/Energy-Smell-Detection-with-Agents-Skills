import random

_HEX = '0123456789abcdef'


def _gen_ids(n, seed):
    rng = random.Random(seed)
    seen = set()
    ids = []
    while len(ids) < n:
        s = 'localjob-' + ''.join(rng.choice(_HEX) for _ in range(24))
        if s not in seen:
            seen.add(s)
            ids.append(s)
    return ids


# A large pool of realistic localjob ids, and the "finished local jobs" output
# hash that the repository builds before calling wait_for_depends_on.
_POOL = _gen_ids(60000, 0)
_ALL_OUTPUTS = {jid: {'job': jid, 'output': {'value': i}} for i, jid in enumerate(_POOL)}


def _sample(n, seed):
    rng = random.Random(seed)
    return rng.sample(_POOL, n)


def _shuffled(ids, seed):
    rng = random.Random(seed)
    out = list(ids)
    rng.shuffle(out)
    return out


# Dictionaries whose size matches the number of ids we wait on (dense lookups).
_SMALL_DICT_IDS = _POOL[:3000]
_SMALL_OUTPUTS = {jid: _ALL_OUTPUTS[jid] for jid in _SMALL_DICT_IDS}
_MED_DICT_IDS = _POOL[:20000]
_MED_OUTPUTS = {jid: _ALL_OUTPUTS[jid] for jid in _MED_DICT_IDS}

# depends_on lists are built once; the function only iterates over them, so the
# same objects can be handed to every call.
_C_EMPTY = []
_C_SINGLE = _POOL[:1]
_C_SMALL = _sample(100, 1)
_C_MED = _sample(3000, 2)
_C_LARGE = _sample(12000, 3)
_C_HUGE = _sample(20000, 4)
_C_DENSE_SMALL = _shuffled(_SMALL_DICT_IDS, 5)
_C_DENSE_MED = _shuffled(_MED_DICT_IDS, 6)


def checks():
    return [
        ("empty", lambda: ([], {})),
        ("missing-localjob", lambda: (["localjob-000000000000000000000000"], {})),
        ("none-depends-on", lambda: (None, {})),
    ]


def cases():
    return [
        ("empty", lambda: (_C_EMPTY, _ALL_OUTPUTS)),
        ("single", lambda: (_C_SINGLE, _ALL_OUTPUTS)),
        ("small", lambda: (_C_SMALL, _ALL_OUTPUTS)),
        ("medium", lambda: (_C_MED, _ALL_OUTPUTS)),
        ("large", lambda: (_C_LARGE, _ALL_OUTPUTS)),
        ("huge", lambda: (_C_HUGE, _ALL_OUTPUTS)),
        ("dense-small-dict", lambda: (_C_DENSE_SMALL, _SMALL_OUTPUTS)),
        ("dense-medium-dict", lambda: (_C_DENSE_MED, _MED_OUTPUTS)),
    ]
