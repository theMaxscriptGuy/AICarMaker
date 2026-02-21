from __future__ import annotations

import datetime as dt
from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from aicarmaker_app.services.gemini_client import GeminiClient
from aicarmaker_app.services.render_service import CameraAngle, RenderService
from aicarmaker_app.ui.widgets import CameraAnglesWidget, DropListWidget, LabeledLineEdit


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-image"


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AICarMaker")
        self.resize(1100, 800)

        self.project_name = LabeledLineEdit("Project name", placeholder="e.g., Ferrari Concept")

        self.api_key = LabeledLineEdit("Gemini API key", placeholder="Paste API key…", echo_password=True)

        self.model_name = LabeledLineEdit("Gemini model name", placeholder=DEFAULT_GEMINI_MODEL)
        self.model_name.set_value(DEFAULT_GEMINI_MODEL)

        self.blueprints = DropListWidget(
            "Car blueprints (drag & drop)",
            accept_ext={"png", "jpg", "jpeg", "webp", "pdf"},
            hint="Drop blueprint images/PDFs here (png/jpg/webp/pdf).",
        )

        self.car_prompt = QTextEdit()
        self.car_prompt.setPlaceholderText(
            "Describe the car (style, era, materials, wheels, paint, interior hints, etc.)…"
        )

        self.angles = CameraAnglesWidget()
        self.angles.set_default_angles()

        self.generate_btn = QPushButton("Generate renders")
        self.generate_btn.clicked.connect(self.on_generate)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        top = QHBoxLayout()
        top.addWidget(self.project_name)
        top.addWidget(self.model_name)

        keys = QHBoxLayout()
        keys.addWidget(self.api_key)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addLayout(keys)
        layout.addWidget(self.blueprints)
        layout.addWidget(self.car_prompt)
        layout.addWidget(self.angles)
        layout.addWidget(self.generate_btn)
        layout.addWidget(self.log)
        self.setLayout(layout)

    def _append_log(self, msg: str) -> None:
        self.log.append(msg)

    def on_generate(self) -> None:
        api_key = self.api_key.value()
        if not api_key:
            QMessageBox.warning(self, "Missing API key", "Please paste your Gemini API key.")
            return

        blueprint_files = self.blueprints.items()
        if not blueprint_files:
            QMessageBox.warning(self, "Missing blueprints", "Please drag & drop at least one blueprint file.")
            return

        car_prompt = self.car_prompt.toPlainText().strip()
        if not car_prompt:
            QMessageBox.warning(self, "Missing prompt", "Please describe the car in the prompt box.")
            return

        angles = [CameraAngle(name=a.name, description=a.description) for a in self.angles.angles()]
        if not angles:
            QMessageBox.warning(self, "Missing camera angles", "Add at least one camera angle.")
            return

        model = self.model_name.value() or DEFAULT_GEMINI_MODEL

        out_dir = Path(__file__).resolve().parents[2] / "output"
        client = GeminiClient(api_key=api_key)
        service = RenderService(gemini=client, output_dir=out_dir)

        self.generate_btn.setEnabled(False)
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._append_log(f"[{ts}] Generating {len(angles)} render(s) using model '{model}'…")

        try:
            out = service.generate_renders(
                project_name=self.project_name.value(),
                model_name=model,
                car_prompt=car_prompt,
                blueprint_files=blueprint_files,
                camera_angles=angles,
            )
        except Exception as e:
            self.generate_btn.setEnabled(True)
            QMessageBox.critical(self, "Error", str(e))
            self._append_log(f"ERROR: {e}")
            return

        self.generate_btn.setEnabled(True)
        self._append_log(f"Done. Output -> {out}")
        QMessageBox.information(self, "Done", f"Render generation finished.\nOutput: {out}")
