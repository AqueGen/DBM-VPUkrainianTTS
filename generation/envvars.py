#!/usr/bin/env python3
"""Read an environment variable, falling back to the Windows user environment.

`setx` writes to the registry, so a process started before it keeps the old value until
it is restarted. That turns every credential change into a restart of whatever is
driving the pipeline. This looks the variable up in the live user environment instead.

The value is used, never printed: callers get the string, and `describe` reports only
its shape so a wrong paste can be diagnosed without exposing the secret.
"""
import os
import subprocess
import sys


def _from_user_scope(name):
    if sys.platform != "win32":
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             '[Environment]::GetEnvironmentVariable("%s","User")' % name],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    value = out.stdout.strip()
    return value or None


def get(name, required=True):
    """Current value, preferring the live user environment over this process's copy.

    That order is the whole point: the process copy is a snapshot taken at start-up, so
    after a `setx` it is the stale one. A variable set for one shell only still works -
    the user scope simply has nothing to say about it.
    """
    value = _from_user_scope(name) or os.environ.get(name)
    if not value and required:
        raise SystemExit("%s is not set" % name)
    return value


def describe(name):
    """Shape of the value, for diagnosing a bad paste without revealing it."""
    value = get(name, required=False)
    if not value:
        return "%s: not set" % name
    stale = os.environ.get(name) and os.environ.get(name) != value
    return "%s: %d chars%s" % (name, len(value),
                               " (process copy is stale)" if stale else "")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(describe(arg))
