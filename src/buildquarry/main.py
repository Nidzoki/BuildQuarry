"""Application entry point."""

import sys

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from buildquarry.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("BuildQuarry")
    available_fonts = set(QFontDatabase.families())
    for family in ("JetBrains Mono", "Cascadia Code", "Cascadia Mono", "Consolas"):
        if family in available_fonts:
            app.setFont(QFont(family, 10))
            break
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
