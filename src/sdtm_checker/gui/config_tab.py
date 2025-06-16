"""
Configuration tab component for SDTM Annotation Checker GUI.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QCheckBox,
    QDoubleSpinBox,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..config_manager import ConfigurationManager
from ..pattern_manager import PatternManager


class PatternTesterDialog(QDialog):
    """Dialog for testing annotation patterns."""

    def __init__(self, parent=None, pattern_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.pattern_data = pattern_data or {}
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Test Pattern")
        layout = QVBoxLayout(self)

        # Show pattern info
        info_layout = QFormLayout()
        info_layout.addRow("Pattern Name:", QLabel(
            self.pattern_data.get("name", "")))
        info_layout.addRow("Regex:", QLabel(
            self.pattern_data.get("regex", "")))
        layout.addLayout(info_layout)

        # Test input
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText(
            "Enter text to test against pattern")
        layout.addWidget(self.test_input)

        # Test button
        test_button = QPushButton("Test")
        test_button.clicked.connect(self.test_pattern)
        layout.addWidget(test_button)

        # Result display
        self.result_label = QLabel("Enter text and click Test to see results")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def test_pattern(self):
        """Test the pattern against input text."""
        import re
        try:
            pattern = self.pattern_data.get("regex", "")
            text = self.test_input.text()

            match = re.match(pattern, text)
            if match:
                groups = self.pattern_data.get("groups", {})
                result_text = "Pattern matched!\n\nCapture groups:\n"
                for name, index in groups.items():
                    try:
                        value = match.group(index)
                        result_text += f"{name}: {value}\n"
                    except:
                        result_text += f"{name}: (no match)\n"
                self.result_label.setText(result_text)
            else:
                self.result_label.setText("Pattern did not match")

        except Exception as e:
            self.result_label.setText(f"Error testing pattern: {str(e)}")


class PatternEditorDialog(QDialog):
    """Dialog for editing annotation patterns."""

    def __init__(self, parent=None, pattern_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.pattern_data = pattern_data or {}
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Edit Pattern")
        layout = QVBoxLayout(self)

        # Pattern form
        form_layout = QFormLayout()

        # Name field
        self.name_edit = QLineEdit(self.pattern_data.get("name", ""))
        form_layout.addRow("Name:", self.name_edit)

        # Description field
        self.desc_edit = QLineEdit(self.pattern_data.get("description", ""))
        form_layout.addRow("Description:", self.desc_edit)

        # Regex field
        self.regex_edit = QLineEdit(self.pattern_data.get("regex", ""))
        form_layout.addRow("Regex Pattern:", self.regex_edit)

        # Groups field
        self.groups_edit = QLineEdit(str(self.pattern_data.get("groups", {})))
        form_layout.addRow("Groups (dict):", self.groups_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_pattern_data(self) -> Dict[str, Any]:
        """Get the pattern data from the form."""
        try:
            groups = eval(self.groups_edit.text())
            if not isinstance(groups, dict):
                raise ValueError("Groups must be a dictionary")
        except Exception as e:
            QMessageBox.warning(self, "Invalid Groups", str(e))
            return None

        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "regex": self.regex_edit.text().strip(),
            "groups": groups
        }


class ConfigurationTab(QWidget):
    """Configuration tab component."""

    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigurationManager()
        self.pattern_manager = PatternManager()
        self.setup_ui()
        self.load_configuration()

    def setup_ui(self):
        """Set up the tab UI."""
        layout = QVBoxLayout(self)

        # Create tab widget
        tab_widget = QTabWidget()

        # File Paths tab
        paths_tab = QWidget()
        paths_layout = QFormLayout(paths_tab)

        # Annotated CRF file
        crf_layout = QHBoxLayout()
        self.crf_edit = QLineEdit()
        crf_browse = QPushButton("Browse...")
        crf_browse.clicked.connect(lambda: self.browse_file(
            self.crf_edit, "PDF Files (*.pdf)"))
        crf_layout.addWidget(self.crf_edit)
        crf_layout.addWidget(crf_browse)
        paths_layout.addRow("Annotated CRF File:", crf_layout)

        # SDTM directory
        sdtm_layout = QHBoxLayout()
        self.sdtm_edit = QLineEdit()
        sdtm_browse = QPushButton("Browse...")
        sdtm_browse.clicked.connect(
            lambda: self.browse_directory(self.sdtm_edit))
        sdtm_layout.addWidget(self.sdtm_edit)
        sdtm_layout.addWidget(sdtm_browse)
        paths_layout.addRow("SDTM Directory:", sdtm_layout)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(
            lambda: self.browse_directory(self.output_edit))
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_browse)
        paths_layout.addRow("Output Directory:", output_layout)

        # Default output file
        self.output_file_edit = QLineEdit()
        paths_layout.addRow("Default Output File:", self.output_file_edit)

        tab_widget.addTab(paths_tab, "File Paths")

        # Pattern Management tab
        pattern_tab = QWidget()
        pattern_layout = QVBoxLayout(pattern_tab)

        # Pattern list
        self.pattern_list = QListWidget()
        pattern_layout.addWidget(self.pattern_list)

        # Pattern buttons
        pattern_buttons = QHBoxLayout()
        add_pattern = QPushButton("Add Pattern")
        edit_pattern = QPushButton("Edit Pattern")
        delete_pattern = QPushButton("Delete Pattern")
        test_pattern = QPushButton("Test Pattern")

        add_pattern.clicked.connect(self.add_pattern)
        edit_pattern.clicked.connect(self.edit_pattern)
        delete_pattern.clicked.connect(self.delete_pattern)
        test_pattern.clicked.connect(self.test_pattern)

        pattern_buttons.addWidget(add_pattern)
        pattern_buttons.addWidget(edit_pattern)
        pattern_buttons.addWidget(delete_pattern)
        pattern_buttons.addWidget(test_pattern)
        pattern_layout.addLayout(pattern_buttons)

        # Pattern help text
        help_text = QLabel(
            "To add a pattern, click 'Add Pattern' and fill in the form.\n"
            "For the groups field, use a dictionary format like: {\"domain\": 1, \"variable\": 2}\n"
            "The numbers refer to the capture groups in your regex pattern."
        )
        help_text.setWordWrap(True)
        pattern_layout.addWidget(help_text)

        tab_widget.addTab(pattern_tab, "Pattern Management")

        # Validation Settings tab
        validation_tab = QWidget()
        validation_layout = QFormLayout(validation_tab)

        # Fuzzy matching
        self.fuzzy_matching = QCheckBox()
        validation_layout.addRow("Fuzzy Matching:", self.fuzzy_matching)

        # Fuzzy threshold
        self.fuzzy_threshold = QDoubleSpinBox()
        self.fuzzy_threshold.setRange(0, 1)
        self.fuzzy_threshold.setSingleStep(0.05)
        validation_layout.addRow("Fuzzy Threshold:", self.fuzzy_threshold)

        # Ignore domains
        self.ignore_domains = QLineEdit()
        validation_layout.addRow("Ignore Domains:", self.ignore_domains)

        # Ignore variables
        self.ignore_variables = QLineEdit()
        validation_layout.addRow("Ignore Variables:", self.ignore_variables)

        tab_widget.addTab(validation_tab, "Validation Settings")

        layout.addWidget(tab_widget)

    def browse_file(self, line_edit: QLineEdit, file_filter: str):
        """Open a file browser dialog and set the selected file path."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            line_edit.text() or os.getcwd(),
            file_filter
        )
        if file_path:
            line_edit.setText(file_path)
            self.config_changed.emit()

    def browse_directory(self, line_edit: QLineEdit):
        """Open a directory browser dialog and set the selected directory path."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            line_edit.text() or os.getcwd()
        )
        if dir_path:
            line_edit.setText(dir_path)
            self.config_changed.emit()

    def load_configuration(self):
        """Load configuration into UI."""
        try:
            config = self.config_manager.get_config()
            if not config:
                return

            # Update file path fields from config
            self.crf_edit.setText(config.paths.get("annotated_crf_file", ""))
            self.sdtm_edit.setText(config.paths.get("sdtm_directory", ""))
            self.output_edit.setText(config.paths.get("output_directory", ""))
            self.output_file_edit.setText(
                config.paths.get("default_output_file", ""))

            # Load validation settings
            self.fuzzy_matching.setChecked(
                config.annotation_patterns["settings"]["fuzzy_matching"])
            self.fuzzy_threshold.setValue(
                config.annotation_patterns["settings"]["fuzzy_threshold"])
            self.ignore_domains.setText(
                ",".join(config.validation.get("ignore_domains", [])))
            self.ignore_variables.setText(
                ",".join(config.validation.get("ignore_variables", [])))

            # Load patterns
            self.pattern_list.clear()
            for pattern in config.annotation_patterns["patterns"]:
                item = QListWidgetItem(
                    f"{pattern.get('name', 'Unnamed')}: {pattern.get('description', '')}")
                item.setData(Qt.ItemDataRole.UserRole, pattern)
                self.pattern_list.addItem(item)

            self.config_changed.emit()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load configuration: {str(e)}")

    def save_configuration(self):
        """Save configuration from UI."""
        try:
            # Collect file paths
            paths = {
                "annotated_crf_file": self.crf_edit.text(),
                "sdtm_directory": self.sdtm_edit.text(),
                "output_directory": self.output_edit.text(),
                "default_output_file": self.output_file_edit.text()
            }

            # Collect pattern settings
            annotation_patterns = {
                "patterns": [
                    self.pattern_list.item(i).data(Qt.ItemDataRole.UserRole)
                    for i in range(self.pattern_list.count())
                ],
                "settings": {
                    "fuzzy_matching": self.fuzzy_matching.isChecked(),
                    "fuzzy_threshold": self.fuzzy_threshold.value()
                }
            }

            # Collect validation settings
            validation = {
                "ignore_domains": [d.strip() for d in self.ignore_domains.text().split(",") if d.strip()],
                "ignore_variables": [v.strip() for v in self.ignore_variables.text().split(",") if v.strip()]
            }

            # Update configuration
            self.config_manager.update_config({
                "paths": paths,
                "annotation_patterns": annotation_patterns,
                "validation": validation
            })

            # Validate configuration
            is_valid, errors = self.config_manager.validate_configuration()
            if not is_valid:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Configuration has validation errors:\n" +
                    "\n".join(errors)
                )
                return None

            self.config_changed.emit()
            return self.config_manager.get_config()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: {str(e)}")
            return None

    def save_configuration_as(self):
        """Save configuration to a new file."""
        try:
            # First, collect current UI values into config manager
            config = self.save_configuration()
            if not config:
                return False
                
            # Get save path from user
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Configuration",
                str(Path.home()),
                "YAML Files (*.yaml)"
            )

            if not file_path:
                return False

            # Ensure .yaml extension
            if not file_path.lower().endswith('.yaml'):
                file_path += '.yaml'

            # Save configuration
            self.config_manager.save_configuration(file_path)
            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: {str(e)}")
            return False

    def load_configuration_from(self):
        """Load configuration from a file."""
        try:
            # Get load path from user
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Load Configuration",
                str(Path.home()),
                "YAML Files (*.yaml)"
            )

            if not file_path:
                return False

            # Load configuration using public method
            self.config_manager.load_configuration(file_path)
            self.load_configuration()
            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load configuration: {str(e)}")
            return False

    def reset_configuration(self):
        """Reset configuration to default values."""
        self.config_manager.reset_to_default()
        self.load_configuration()
        self.config_changed.emit()

    def add_pattern(self):
        """Add a new pattern."""
        dialog = PatternEditorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            if pattern_data:
                # Validate pattern
                errors = self.pattern_manager.validate_pattern(pattern_data)
                if errors:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "\n".join(errors)
                    )
                    return

                # Add pattern to list
                item = QListWidgetItem(
                    f"{pattern_data['name']}: {pattern_data.get('description', '')}")
                item.setData(Qt.ItemDataRole.UserRole, pattern_data)
                self.pattern_list.addItem(item)
                self.config_changed.emit()

    def edit_pattern(self):
        """Edit selected pattern."""
        selected = self.pattern_list.currentItem()
        if not selected:
            QMessageBox.warning(
                self, "Warning", "Please select a pattern to edit")
            return

        pattern_data = selected.data(Qt.ItemDataRole.UserRole)
        dialog = PatternEditorDialog(self, pattern_data)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_pattern_data = dialog.get_pattern_data()
            if new_pattern_data:
                # Validate pattern
                errors = self.pattern_manager.validate_pattern(
                    new_pattern_data)
                if errors:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "\n".join(errors)
                    )
                    return

                # Update pattern in list
                selected.setText(
                    f"{new_pattern_data['name']}: {new_pattern_data.get('description', '')}")
                selected.setData(Qt.ItemDataRole.UserRole, new_pattern_data)
                self.config_changed.emit()

    def delete_pattern(self):
        """Delete selected pattern."""
        selected = self.pattern_list.currentItem()
        if not selected:
            QMessageBox.warning(
                self, "Warning", "Please select a pattern to delete")
            return

        reply = QMessageBox.question(
            self,
            "Delete Pattern",
            "Are you sure you want to delete this pattern?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.pattern_list.takeItem(self.pattern_list.row(selected))
            self.config_changed.emit()

    def test_pattern(self):
        """Test selected pattern."""
        selected = self.pattern_list.currentItem()
        if not selected:
            QMessageBox.warning(
                self, "Warning", "Please select a pattern to test")
            return

        pattern_data = selected.data(Qt.ItemDataRole.UserRole)
        dialog = PatternTesterDialog(self, pattern_data)
        dialog.exec()
