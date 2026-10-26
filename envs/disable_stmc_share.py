#!/usr/bin/env python3
"""Fail closed when disabling the STMC Gradio public share link.

Only one simple module-level SHARE = True/False assignment is supported.
Unexpected upstream configuration must be reviewed rather than launched
with an unverified share setting. No STMC imports or network activity.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


_SHARE_LINE = re.compile(
    r"(?P<before>[ \t]*SHARE[ \t]*=[ \t]*)(?P<value>True|False)"
    r"(?P<after>[ \t]*(?:#[^\r\n]*)?)\Z"
)


def disable_public_share(path: Path) -> bool:
    """Return True if edited, False if already disabled; raise on ambiguity."""
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("app_config.py must be a regular file, not a symlink")

    original = path.read_text(encoding="utf-8")
    tree = ast.parse(original, filename=str(path))
    # A second assignment, including inside a conditional or function,
    # makes the effective value ambiguous; do not start the Gradio app.
    assignments = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "SHARE"
        and isinstance(node.ctx, ast.Store)
    ]
    candidates = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "SHARE"
        and isinstance(node.value, ast.Constant)
        and type(node.value.value) is bool
    ]
    if len(assignments) != 1 or len(candidates) != 1:
        raise ValueError("expected exactly one simple module-level SHARE = True/False assignment")

    statement = candidates[0]
    lines = original.splitlines(keepends=True)
    index = statement.lineno - 1
    line = lines[index]
    without_newline = line.rstrip("\r\n")
    match = _SHARE_LINE.fullmatch(without_newline)
    if match is None:
        raise ValueError("SHARE assignment has unsupported layout or additional code")
    if (match.group("value") == "True") != statement.value.value:
        raise ValueError("SHARE parsed value differs from source line")
    if statement.value.value is False:
        return False

    lines[index] = (
        match.group("before") + "False" + match.group("after")
        + line[len(without_newline):]
    )
    updated = "".join(lines)
    # The file is small and should parse after the patch before it replaces
    # the existing configuration.
    ast.parse(updated, filename=str(path))
    fd, temporary = tempfile.mkstemp(
        prefix=".app_config.share-", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as writer:
            writer.write(updated)
            writer.flush()
            os.fsync(writer.fileno())
        os.chmod(temporary, stat.S_IMODE(info.st_mode))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: disable_stmc_share.py /path/to/app_config.py", file=sys.stderr)
        return 2
    try:
        changed = disable_public_share(Path(argv[0]))
    except (OSError, ValueError, SyntaxError, UnicodeError) as exc:
        print(f"Refusing to launch STMC: cannot verify SHARE=False: {exc}", file=sys.stderr)
        return 1
    print("STMC SHARE=False verified" + (" (updated)" if changed else " (already disabled)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
