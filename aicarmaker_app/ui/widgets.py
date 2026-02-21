from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LabeledLineEdit(QWidget):
    def __init__(self, label: str, *, placeholder: str = "", echo_password: bool = False):
        super().__init__()
        self._label = QLabel(label)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        if echo_password:
            self._edit.setEchoMode(QLineEdit.EchoMode.Password)

        layout = QVBoxLayout()
        layout.addWidget(self._label)
        layout.addWidget(self._edit)
        self.setLayout(layout)

    def value(self) -> str:
        return self._edit.text().strip()

    def set_value(self, v: str) -> None:
        self._edit.setText(v)


class DropListWidget(QFrame):
    """Drag & drop files into a list."""

    changed = pyqtSignal()

    def __init__(self, title: str, *, accept_ext: set[str] | None = None, hint: str | None = None):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAcceptDrops(True)
        self.accept_ext = {e.lower() for e in (accept_ext or set())}

        self.title = QLabel(title)
        self.hint = QLabel(hint or "Drag & drop files here")
        self.hint.setStyleSheet("color: #666")

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)

        top = QHBoxLayout()
        top.addWidget(self.title)
        top.addStretch(1)
        top.addWidget(self.clear_btn)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.hint)
        layout.addWidget(self.list)
        self.setLayout(layout)

    def items(self) -> list[Path]:
        out: list[Path] = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            p = Path(it.data(Qt.ItemDataRole.UserRole))
            out.append(p)
        return out

    def clear(self) -> None:
        self.list.clear()
        self.changed.emit()

    def add_paths(self, paths: list[Path]) -> None:
        existing = {str(p) for p in self.items()}
        for p in paths:
            if not p.exists():
                continue
            if self.accept_ext and p.suffix.lower().lstrip(".") not in self.accept_ext:
                continue
            sp = str(p)
            if sp in existing:
                continue
            item = QListWidgetItem(p.name)
            item.setToolTip(sp)
            item.setData(Qt.ItemDataRole.UserRole, sp)
            self.list.addItem(item)
            existing.add(sp)
        self.changed.emit()

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        self.add_paths(paths)


@dataclass
class Angle:
    name: str
    description: str


class CameraAnglesWidget(QFrame):
    """Drag & drop a .txt file with camera angles, plus manual add/remove."""

    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAcceptDrops(True)

        self.title = QLabel("Camera angles")
        self.hint = QLabel(
            "Drag & drop a .txt here (one per line: name: description), or add manually."
        )
        self.hint.setStyleSheet("color: #666")

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Angle name (e.g., Front 3/4)")
        self.desc = QLineEdit()
        self.desc.setPlaceholderText("Angle description (e.g., 35mm, eye-level, front-left)")

        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_manual)
        self.remove_btn = QPushButton("Remove selected")
        self.remove_btn.clicked.connect(self._remove_selected)

        form = QHBoxLayout()
        form.addWidget(self.name)
        form.addWidget(self.desc)
        form.addWidget(self.add_btn)

        btns = QHBoxLayout()
        btns.addWidget(self.remove_btn)
        btns.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.list)
        self.setLayout(layout)

    def angles(self) -> list[Angle]:
        out: list[Angle] = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            payload = it.data(Qt.ItemDataRole.UserRole) or {}
            out.append(Angle(name=payload.get("name", "Angle"), description=payload.get("description", "")))
        return out

    def set_default_angles(self) -> None:
        defaults = [
            Angle("Front 3/4", "Front-left three-quarter view, eye-level, 35mm lens"),
            Angle("Side profile", "Perfect side profile, centered, studio lighting"),
            Angle("Rear 3/4", "Rear-right three-quarter view, eye-level, 35mm lens"),
        ]
        for a in defaults:
            self._add_angle(a)

    def _add_angle(self, a: Angle) -> None:
        item = QListWidgetItem(f"{a.name} — {a.description}")
        item.setData(Qt.ItemDataRole.UserRole, {"name": a.name, "description": a.description})
        self.list.addItem(item)
        self.changed.emit()

    def _add_manual(self) -> None:
        name = self.name.text().strip() or "Angle"
        desc = self.desc.text().strip()
        self._add_angle(Angle(name=name, description=desc))
        self.name.setText("")
        self.desc.setText("")

    def _remove_selected(self) -> None:
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))
        self.changed.emit()

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        from pathlib import Path

        urls = event.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        txts = [p for p in paths if p.suffix.lower() == ".txt" and p.exists()]
        if not txts:
            return
        p = txts[0]
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                name, desc = line.split(":", 1)
            elif "|" in line:
                name, desc = line.split("|", 1)
            else:
                name, desc = line, ""
            self._add_angle(Angle(name=name.strip(), description=desc.strip()))
