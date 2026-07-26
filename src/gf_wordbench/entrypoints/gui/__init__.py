"""Qt GUI entrypoint and presentation-adapter package.

GUI implementations remain in their owning modules. Importing this package
does not import PySide6, create a QApplication, load application state, access
the filesystem, start workers, or execute validation. The installed GUI
entrypoint is :mod:`gf_wordbench.entrypoints.gui.main`.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
