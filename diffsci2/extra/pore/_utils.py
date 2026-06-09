"""Vendored from poregen.utils (ported into diffsci2 to drop the poregen dependency)."""

class AttrDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
