"""Filesystem helper utilities for skills tools."""

import errno
from pathlib import Path
import stat
import tempfile


def write_atomically(target: Path, content: str) -> None:
    """Write text content to target atomically using a temporary file."""
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            delete=False,
        ) as output:
            temporary = Path(output.name)
            output.write(content)
        if mode is not None:
            temporary.chmod(mode)
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def remove_empty_directory(directory: Path) -> bool:
    """Remove directory if it is an empty real directory.

    Returns True if the directory was removed, False if it does not exist,
    is a symlink, or is not empty. Raises OSError on unexpected errors.
    """
    if not directory.exists() or directory.is_symlink() or not directory.is_dir():
        return False
    try:
        directory.rmdir()
        return True
    except OSError as error:
        if error.errno in (errno.ENOTEMPTY, errno.EEXIST):
            return False
        raise
