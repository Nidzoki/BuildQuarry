"""Main BuildQuarry window."""

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QListWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
from pydantic import ValidationError

from buildquarry.application.markdown import plan_to_markdown
from buildquarry.domain.models import ProjectInput
from buildquarry.domain.planner import create_plan
from buildquarry.domain.scope_rules import enforce_scope
from buildquarry.infrastructure.database import PlanDatabase
from buildquarry.infrastructure.gemini import GeminiError, create_gemini_plan
from buildquarry.infrastructure.secrets import delete_api_key, get_api_key, save_api_key


class GeminiWorker(QObject):
    finished = Signal(object, object)
    failed = Signal(str)

    def __init__(self, project: ProjectInput, api_key: str, model: str) -> None:
        super().__init__()
        self.project = project
        self.api_key = api_key
        self.model = model

    def run(self) -> None:
        try:
            plan = create_gemini_plan(self.project, self.api_key, self.model)
            self.finished.emit(plan, self.project)
        except GeminiError as error:
            self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_markdown = ""
        self.current_plan = None
        self.current_plan_id: int | None = None
        self.database = PlanDatabase()
        self.gemini_consent = False
        self.gemini_thread: QThread | None = None
        self.gemini_worker: GeminiWorker | None = None
        self.gemini_cancelled = False
        self.setWindowTitle("BuildQuarry")
        self.resize(1100, 700)
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #15171c; color: #e8ebf2; }
            QLabel#brand {
                color: #f4f6fb; font-size: 16px; font-weight: 800; letter-spacing: 2px;
            }
            QLabel#brandAccent { color: #8b96ff; }
            QLabel#navItem {
                color: #8f96a8; padding: 7px 10px; border-radius: 6px;
            }
            QLabel#navActive {
                color: #f4f6fb; background: #252a3d; padding: 7px 10px; border-radius: 6px;
            }
            QLabel#statusPill {
                color: #aeb5ff; background: #292d4b; border: 1px solid #454b78;
                border-radius: 10px; padding: 5px 10px;
            }
            QGroupBox {
                background: #1d2027; border: 1px solid #303541; border-radius: 10px;
                margin-top: 14px; padding: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 14px; padding: 0 6px;
                color: #8b96ff; font-weight: 700;
            }
            QWidget#resultCard, QGroupBox#historyCard {
                background: #1b1e26; border: 1px solid #303541; border-radius: 12px;
            }
            QWidget#resultCard QPlainTextEdit {
                background: #101217; border: 1px solid #353b4a; border-radius: 9px;
                padding: 14px; selection-background-color: #454b78;
            }
            QLineEdit, QPlainTextEdit, QComboBox {
                background: #111318; border: 1px solid #373c49; border-radius: 6px;
                padding: 7px;
            }
            QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
                border: 2px solid #8b96ff; padding: 6px;
            }
            QPushButton {
                background: #6875f5; color: #ffffff; border: 0; border-radius: 6px;
                padding: 8px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #7d88ff; }
            QPushButton:disabled { background: #41465c; color: #9aa0b1; }
            QListWidget {
                background: #111318; border: 1px solid #303541; border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item { padding: 7px; border-radius: 4px; }
            QListWidget::item:selected { background: #30355c; color: #ffffff; }
            QComboBox QAbstractItemView {
                background: #1d2027; color: #e8ebf2; selection-background-color: #30355c;
            }
            QScrollBar:vertical { background: #15171c; width: 12px; margin: 2px; }
            QScrollBar::handle:vertical { background: #3b4050; border-radius: 5px; min-height: 24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollArea#briefScroll {
                background: #1d2027; border: 1px solid #303541; border-radius: 10px;
            }
            QScrollArea#briefScroll QWidget#briefContent {
                background: #1d2027;
            }
            QScrollArea#briefScroll QGroupBox#briefContent {
                border: 0;
                margin-top: 0;
            }
            QScrollArea#briefScroll QScrollBar:vertical {
                background: #111318;
                width: 16px;
                margin: 4px 3px 4px 0;
                border: 1px solid #3d4352;
                border-radius: 7px;
            }
            QScrollArea#briefScroll QScrollBar::handle:vertical {
                background: #6875f5;
                min-height: 42px;
                border-radius: 5px;
            }
            QScrollArea#briefScroll QScrollBar::handle:vertical:hover {
                background: #9aa2ff;
            }
            QScrollArea#briefScroll QScrollBar::add-line:vertical,
            QScrollArea#briefScroll QScrollBar::sub-line:vertical {
                height: 0;
            }
            QWidget#briefActions {
                background: #15171c;
                border-top: 1px solid #303541;
            }
            QSplitter::handle { background: #303541; }
            """
        )
        self._set_programming_font()
        self._build_ui()

    def _set_programming_font(self) -> None:
        available_fonts = set(QFontDatabase.families())
        for family in ("JetBrains Mono", "Cascadia Code", "Cascadia Mono", "Consolas"):
            if family in available_fonts:
                self.setFont(QFont(family, 10))
                return

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 22, 28, 24)
        layout.setSpacing(14)

        topbar = QHBoxLayout()
        brand = QLabel("BUILDQUARRY")
        brand.setObjectName("brand")
        topbar.addWidget(brand)
        topbar.addSpacing(28)
        for text, active in (("Workspace", True), ("Saved plans", False), ("Settings", False)):
            nav = QLabel(text)
            nav.setObjectName("navActive" if active else "navItem")
            topbar.addWidget(nav)
        topbar.addStretch()
        status = QLabel("LOCAL-FIRST")
        status.setObjectName("statusPill")
        topbar.addWidget(status)
        layout.addLayout(topbar)

        heading = QLabel("Turn oversized ideas into focused MVP plans")
        heading.setStyleSheet("font-size: 22px; font-weight: 700; color: #f4f6fb;")
        subtitle = QLabel("Manual planning stays local. Gemini adds optional interpretation.")
        subtitle.setStyleSheet("color: #9aa0b1;")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_input_panel())
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([420, 680])
        layout.addWidget(splitter)
        layout.addWidget(self._build_history_panel())
        self.setCentralWidget(root)

    def _build_history_panel(self) -> QWidget:
        group = QGroupBox("Saved plans")
        group.setObjectName("historyCard")
        layout = QVBoxLayout(group)
        self.history = QListWidget()
        self.history.itemDoubleClicked.connect(self._open_saved_plan)
        layout.addWidget(self.history)
        buttons = QHBoxLayout()
        save = QPushButton("Save")
        save.clicked.connect(self._save_plan)
        delete = QPushButton("Delete")
        delete.clicked.connect(self._delete_saved_plan)
        import_button = QPushButton("Import Markdown")
        import_button.clicked.connect(self._import_markdown)
        buttons.addWidget(save)
        buttons.addWidget(delete)
        buttons.addWidget(import_button)
        layout.addLayout(buttons)
        self._refresh_history()
        return group

    def _build_input_panel(self) -> QWidget:
        group = QGroupBox("Project brief")
        group.setObjectName("briefContent")
        group.setMinimumWidth(360)
        form = QFormLayout(group)
        form.setContentsMargins(16, 24, 16, 16)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.idea = QPlainTextEdit()
        self.idea.setPlaceholderText("Describe the oversized project idea...")
        self.idea.setMinimumHeight(120)
        self.idea.setMaximumHeight(160)
        self.idea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.target_user = QLineEdit()
        self.target_user.setPlaceholderText("Who is this for?")
        self.time_budget = QComboBox()
        self.time_budget.addItem("Weekend", "weekend")
        self.time_budget.addItem("One week", "one_week")
        self.time_budget.addItem("Two weeks", "two_weeks")
        self.time_budget.addItem("One month", "one_month")
        self.skill_level = QComboBox()
        self.skill_level.addItems(["Beginner", "Intermediate", "Advanced"])
        self.tech_stack = QLineEdit()
        self.constraints = QPlainTextEdit()
        self.constraints.setPlaceholderText("Optional constraints")
        self.constraints.setMinimumHeight(60)
        self.constraints.setMaximumHeight(90)
        self.constraints.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form.addRow("Project idea", self.idea)
        form.addRow("Target user", self.target_user)
        form.addRow("Time budget", self.time_budget)
        form.addRow("Skill level", self.skill_level)
        form.addRow("Tech stack", self.tech_stack)
        form.addRow("Constraints", self.constraints)
        self.mode = QComboBox()
        self.mode.addItems(["Manual", "Gemini"])
        form.addRow("Planning mode", self.mode)
        self.model = QComboBox()
        self.model.addItems(["gemini-3.6-flash", "gemini-3.6-pro"])
        form.addRow("Gemini model", self.model)

        self.generate_button = QPushButton("Create plan")
        self.generate_button.clicked.connect(self._create_plan)
        self.change_key_button = QPushButton("Change Gemini key")
        self.change_key_button.clicked.connect(self._change_api_key)
        self.cancel_button = QPushButton("Cancel request")
        self.cancel_button.clicked.connect(self._cancel_gemini_request)
        self.cancel_button.setVisible(False)

        scroll = QScrollArea()
        scroll.setObjectName("briefScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setContentsMargins(0, 0, 0, 0)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidget(group)

        actions = QWidget()
        actions.setObjectName("briefActions")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 10, 0, 0)
        actions_layout.addWidget(self.generate_button, 1)
        actions_layout.addWidget(self.change_key_button)
        actions_layout.addWidget(self.cancel_button)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll, 1)
        container_layout.addWidget(actions)
        return container

    def _build_result_panel(self) -> QWidget:
        container = QWidget()
        container.setObjectName("resultCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("PLAN WORKSPACE")
        title.setStyleSheet("color: #8b96ff; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(title)
        description = QLabel("Review, edit, and export your focused build plan.")
        description.setStyleSheet("color: #8f96a8;")
        layout.addWidget(description)
        self.result_tabs = QTabWidget()
        self.result = QPlainTextEdit()
        self.result.setPlaceholderText(
            "Your plan will appear here.\n\n"
            "Create a plan from the brief, then edit the Markdown before saving or exporting."
        )
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Structured plan preview will appear here.")
        self.result_tabs.addTab(self.preview, "Overview")
        self.result_tabs.addTab(self.result, "Markdown")
        layout.addWidget(self.result_tabs)
        buttons = QHBoxLayout()
        save_button = QPushButton("Save plan")
        save_button.clicked.connect(self._save_plan)
        copy_button = QPushButton("Copy Markdown")
        copy_button.clicked.connect(self._copy_markdown)
        export_button = QPushButton("Export Markdown")
        export_button.clicked.connect(self._export_markdown)
        buttons.addWidget(save_button)
        buttons.addWidget(copy_button)
        buttons.addWidget(export_button)
        layout.addLayout(buttons)
        return container

    def _set_plan(self, plan) -> None:
        self.current_plan = plan
        self.current_markdown = plan_to_markdown(plan)
        self.current_plan_id = None
        self.result.setPlainText(self.current_markdown)
        self.preview.setPlainText(self._plan_preview(plan))
        self.result_tabs.setCurrentWidget(self.preview)

    @staticmethod
    def _plan_preview(plan) -> str:
        sections = [
            f"{plan.title}\n{'=' * len(plan.title)}",
            f"\nFOCUSED MVP\n{plan.mvp}",
            f"\nPRIMARY USER\n{plan.primary_user}",
            "\nIN SCOPE\n" + "\n".join(f"  • {item}" for item in plan.in_scope),
            "\nOUT OF SCOPE\n" + "\n".join(f"  • {item}" for item in plan.out_of_scope),
            "\nMILESTONES\n"
            + "\n".join(
                f"  {index}. {milestone.title}\n"
                + "\n".join(f"     - {task}" for task in milestone.tasks)
                for index, milestone in enumerate(plan.milestones, 1)
            ),
            "\nACCEPTANCE CRITERIA\n"
            + "\n".join(f"  • {item}" for item in plan.acceptance_criteria),
        ]
        technical_sections = (
            ("ARCHITECTURE", plan.architecture),
            ("DATA MODEL", plan.data_model),
            ("API DESIGN", plan.api_design),
            ("TECHNICAL RISKS", plan.technical_risks),
            ("IMPLEMENTATION NOTES", plan.implementation_notes),
        )
        for title, items in technical_sections:
            if items:
                sections.append(f"\n{title}\n" + "\n".join(f"  • {item}" for item in items))
        return "\n".join(sections)

    def _create_plan(self) -> None:
        try:
            project = ProjectInput(
                idea=self.idea.toPlainText().strip(),
                target_user=self.target_user.text().strip(),
                time_budget=self.time_budget.currentData(),
                skill_level=self.skill_level.currentText(),
                tech_stack=self.tech_stack.text().strip(),
                constraints=self.constraints.toPlainText().strip(),
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Incomplete brief", error.errors()[0]["msg"])
            return
        if self.mode.currentText() == "Gemini":
            api_key = get_api_key()
            if self._looks_like_error(api_key):
                delete_api_key()
                api_key = ""
            if not api_key:
                api_key, accepted = self._api_key_dialog()
                if not accepted:
                    return
                save_api_key(api_key)
            if not self.gemini_consent:
                consent = QMessageBox.question(
                    self,
                    "Gemini privacy notice",
                    "Gemini mode sends your project information to Google Gemini. "
                    "Do not include secrets, credentials, private code, or sensitive personal data. "
                    "Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if consent != QMessageBox.StandardButton.Yes:
                    return
                self.gemini_consent = True
            self._start_gemini_request(project, api_key)
            return
        else:
            plan = enforce_scope(create_plan(project), project)
        self._set_plan(plan)

    def _start_gemini_request(self, project: ProjectInput, api_key: str) -> None:
        self.gemini_cancelled = False
        self._set_planning_enabled(False)
        self.cancel_button.setVisible(True)
        self.result.setPlainText("Generating plan with Gemini...")
        self.gemini_thread = QThread(self)
        self.gemini_worker = GeminiWorker(project, api_key, self.model.currentText())
        self.gemini_worker.moveToThread(self.gemini_thread)
        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_worker.finished.connect(self._finish_gemini_request)
        self.gemini_worker.failed.connect(self._fail_gemini_request)
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_worker.failed.connect(self.gemini_thread.quit)
        self.gemini_thread.finished.connect(self._clear_gemini_request)
        self.gemini_thread.start()

    def _finish_gemini_request(self, plan, project: ProjectInput) -> None:
        if self.gemini_cancelled:
            return
        final_plan = enforce_scope(plan, project)
        self._set_plan(final_plan)
        self._set_planning_enabled(True)
        self.cancel_button.setVisible(False)

    def _fail_gemini_request(self, message: str) -> None:
        if self.gemini_cancelled:
            return
        if "rejected this API key" in message:
            delete_api_key()
        QMessageBox.warning(self, "Gemini unavailable", message)
        self._set_planning_enabled(True)
        self.cancel_button.setVisible(False)

    def _cancel_gemini_request(self) -> None:
        if self.gemini_thread is None or not self.gemini_thread.isRunning():
            return
        self.gemini_cancelled = True
        self.cancel_button.setVisible(False)
        self._set_planning_enabled(True)
        self.result.setPlainText("Gemini request cancelled. No plan was generated.")

    def _change_api_key(self) -> None:
        delete_api_key()
        api_key, accepted = self._api_key_dialog()
        if accepted:
            save_api_key(api_key)


    def _clear_gemini_request(self) -> None:
        if self.gemini_worker is not None:
            self.gemini_worker.deleteLater()
        if self.gemini_thread is not None:
            self.gemini_thread.deleteLater()
        self.gemini_worker = None
        self.gemini_thread = None

    def _set_planning_enabled(self, enabled: bool) -> None:
        self.mode.setEnabled(enabled)
        self.model.setEnabled(enabled)
        self.generate_button.setEnabled(enabled)

    def _api_key_dialog(self) -> tuple[str, bool]:
        dialog = QDialog(self)
        dialog.setWindowTitle("Gemini API key")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enter your Gemini API key. It is used only from this app."))
        field = QLineEdit()
        field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setPlaceholderText("Gemini API key")
        layout.addWidget(field)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        api_key = field.text().strip()
        if accepted and (not api_key or self._looks_like_error(api_key) or any(char.isspace() for char in api_key)):
            QMessageBox.warning(
                self,
                "Invalid Gemini key",
                "Enter API key only. Do not paste the error message or include spaces/newlines.",
            )
            return "", False
        return api_key, accepted

    @staticmethod
    def _looks_like_error(value: str) -> bool:
        return value.startswith("Gemini request failed") or value.startswith("Gemini rejected")

    def _refresh_history(self) -> None:
        self.history.clear()
        for saved_plan in self.database.list_plans():
            self.history.addItem(saved_plan.title)
            self.history.item(self.history.count() - 1).setData(Qt.ItemDataRole.UserRole, saved_plan.plan_id)

    def _save_plan(self) -> None:
        content = self.result.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Nothing to save", "Create or import a plan first.")
            return
        title = content.splitlines()[0].removeprefix("# ").strip() or "Untitled plan"
        self.current_plan_id = self.database.save(title, content, self.current_plan_id)
        self.current_markdown = content
        self._refresh_history()

    def _open_saved_plan(self, item) -> None:
        plan_id = item.data(Qt.ItemDataRole.UserRole)
        saved_plan = self.database.get(int(plan_id))
        if saved_plan is None:
            return
        self.current_plan_id = saved_plan.plan_id
        self.current_markdown = saved_plan.markdown
        self.result.setPlainText(saved_plan.markdown)
        self.result_tabs.setCurrentWidget(self.result)

    def _delete_saved_plan(self) -> None:
        item = self.history.currentItem()
        if item is None:
            return
        self.database.delete(int(item.data(Qt.ItemDataRole.UserRole)))
        self.current_plan_id = None
        self._refresh_history()

    def _import_markdown(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Markdown", "", "Markdown (*.md);;All files (*)")
        if not path:
            return
        with open(path, encoding="utf-8") as file:
            content = file.read().strip()
        if not content:
            QMessageBox.warning(self, "Empty file", "Selected Markdown file is empty.")
            return
        self.current_plan_id = None
        self.current_markdown = content
        self.result.setPlainText(content)
        self.result_tabs.setCurrentWidget(self.result)

    def _copy_markdown(self) -> None:
        if not self.result.toPlainText().strip():
            return
        self.current_markdown = self.result.toPlainText()
        QApplication.clipboard().setText(self.current_markdown)

    def _export_markdown(self) -> None:
        content = self.result.toPlainText().strip()
        if not content:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", "buildquarry-plan.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content + "\n")

    def closeEvent(self, event) -> None:
        if self.gemini_thread is not None and self.gemini_thread.isRunning():
            self.gemini_thread.quit()
            self.gemini_thread.wait(1000)
        self.database.close()
        super().closeEvent(event)
