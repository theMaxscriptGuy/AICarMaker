from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from aicarmaker_app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    # Theme via qt-material
    # Available themes include: dark_cyan.xml, light_cyan.xml, etc.
    try:
        from qt_material import apply_stylesheet  # type: ignore

        apply_stylesheet(app, theme="dark_cyan.xml")
    except Exception:
        # Fallback: basic style
        app.setStyleSheet(
            """
            QWidget { font-size: 13px; }
            """
        )

    w = MainWindow()
    w.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
