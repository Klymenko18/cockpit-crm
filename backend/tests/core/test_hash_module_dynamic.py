# -*- coding: utf-8 -*-
import importlib
import inspect


def _pick_hash_callable(mod):
    candidates = []
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj) and "hash" in name.lower():
            if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
                candidates.append(obj)
    return candidates[0] if candidates else None
