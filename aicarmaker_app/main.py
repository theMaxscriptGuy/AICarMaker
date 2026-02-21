from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from aicarmaker_app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    # Light-ish defaults
    app.setStyleSheet(
        """
        QWidget { font-size: 13px; }
        QLineEdit, QTextEdit { background: white; }
        """
    )

    w = MainWindow()
    w.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
