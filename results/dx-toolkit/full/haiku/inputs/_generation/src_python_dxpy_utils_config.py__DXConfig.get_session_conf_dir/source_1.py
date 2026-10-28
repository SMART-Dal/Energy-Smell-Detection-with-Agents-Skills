import os
import random
import shutil

import psutil

from dxpy.utils.config import DXConfig

# Build the config manager once (its constructor itself calls get_session_conf_dir).
_instance = DXConfig()


def _ancestor_pids():
    pids = []
    try:
        p = psutil.Process(os.getpid()).parent()
    except Exception:
        p = None
    while p is not None and p.pid != 0:
        pids.append(p.pid)
        try:
            p = p.parent()
        except Exception:
            break
    return pids


_ANC = _ancestor_pids()
if not _ANC:
    _ANC = [os.getpid()]
_PARENT_PID = _ANC[0]
_GRANDPARENT_PID = _ANC[1] if len(_ANC) > 1 else _ANC[0]

# Deterministic pool of definitely-nonexistent pids.
_rng = random.Random(0)
_DEAD = []
_p = 10 ** 7
while len(_DEAD) < 2500:
    if not psutil.pid_exists(_p):
        _DEAD.append(_p)
    _p += 1

# Dedicated config dirs under WORKDIR.
_C1 = WORKDIR / "c1"
_C2 = WORKDIR / "c2"
_C3 = WORKDIR / "c3"
_C4 = WORKDIR / "c4"
_C5 = WORKDIR / "c5"
_C6 = WORKDIR / "c6"
_C7 = WORKDIR / "c7"
_C8 = WORKDIR / "c8"
_CK1 = WORKDIR / "ck1"
_CK2 = WORKDIR / "ck2"
_CK3 = WORKDIR / "ck3"

for _d in (_C1, _C2, _C3, _C4, _C5, _C6, _C7, _C8, _CK1, _CK2, _CK3):
    _d.mkdir(parents=True, exist_ok=True)


def _prep(conf_dir, entries):
    """(Re)create <conf_dir>/sessions. entries is None to leave it absent,
    otherwise a list of (name, nfiles, depth)."""
    sessions = os.path.join(str(conf_dir), "sessions")
    shutil.rmtree(sessions, ignore_errors=True)
    if entries is None:
        return
    os.makedirs(sessions)
    for name, nfiles, depth in entries:
        d = os.path.join(sessions, name)
        os.makedirs(d)
        for i in range(nfiles):
            sub = os.path.join(d, "sub%d" % (i % depth))
            os.makedirs(sub, exist_ok=True)
            with open(os.path.join(sub, "f%d" % i), "w") as fh:
                fh.write("x")


# ---- measured cases -------------------------------------------------------

def _t1():
    _instance._user_conf_dir = str(_C1)
    _prep(_C1, [(str(p), 2, 1) for p in _DEAD[:500]])
    return (_instance, True)


def _t2():
    _instance._user_conf_dir = str(_C2)
    entries = [("abc%d" % i, 1, 1) for i in range(400)]
    entries += [(str(p), 1, 1) for p in _DEAD[500:900]]
    _prep(_C2, entries)
    return (_instance, True)


def _t3():
    _instance._user_conf_dir = str(_C3)
    _prep(_C3, None)
    return (_instance, True)


def _t4():
    _instance._user_conf_dir = str(_C4)
    entries = [(str(_PARENT_PID), 1, 1)]
    entries += [(str(p), 1, 1) for p in _DEAD[900:1200]]
    _prep(_C4, entries)
    return (_instance,)


def _t5():
    _instance._user_conf_dir = str(_C5)
    _prep(_C5, [(str(_GRANDPARENT_PID), 1, 1)])
    return (_instance,)


def _t6():
    _instance._user_conf_dir = str(_C6)
    _prep(_C6, None)
    return (_instance,)


def _t7():
    _instance._user_conf_dir = str(_C7)
    entries = [(str(os.getpid()), 1, 1), ("1", 1, 1), (str(_PARENT_PID), 1, 1)]
    entries += [(str(p), 1, 1) for p in _DEAD[1200:1500]]
    _prep(_C7, entries)
    return (_instance, True)


def _t8():
    _instance._user_conf_dir = str(_C8)
    _prep(_C8, [(str(p), 4, 3) for p in _DEAD[1500:1800]])
    return (_instance, True)


def cases():
    return [
        ("cleanup-500-dead", _t1),
        ("cleanup-mixed-names", _t2),
        ("cleanup-missing-dir", _t3),
        ("no-cleanup-parent-hit", _t4),
        ("no-cleanup-grandparent-hit", _t5),
        ("no-cleanup-no-dir", _t6),
        ("cleanup-alive-plus-dead", _t7),
        ("cleanup-deep-trees", _t8),
    ]


# ---- edge checks ----------------------------------------------------------

def _ck_no_sessions():
    _instance._user_conf_dir = str(_CK1)
    _prep(_CK1, None)
    return (_instance,)


def _ck_empty_sessions():
    _instance._user_conf_dir = str(_CK2)
    _prep(_CK2, [])
    return (_instance, True)


def _ck_odd_file():
    _instance._user_conf_dir = str(_CK3)
    sessions = os.path.join(str(_CK3), "sessions")
    shutil.rmtree(sessions, ignore_errors=True)
    os.makedirs(sessions)
    with open(os.path.join(sessions, "notapid"), "w") as fh:
        fh.write("x")
    return (_instance,)


def checks():
    return [
        ("no-sessions-dir", _ck_no_sessions),
        ("empty-sessions-dir", _ck_empty_sessions),
        ("non-integer-entry", _ck_odd_file),
    ]
