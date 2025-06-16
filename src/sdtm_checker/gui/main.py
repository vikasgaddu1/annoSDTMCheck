"""
Main GUI module for SDTM Annotation Checker.
"""

import sys
import logging
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QProgressBar,
    QStatusBar,
)
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime

from .config_tab import ConfigurationTab
from .ui_state_cache import UIStateCache
from ..config_manager import ConfigurationManager
from ..validation_engine import ValidationEngine
from ..annotation_extractor import AnnotationExtractor
from ..sdtm_reader import SDTMDatasetManager
from ..report_generator import ReportGenerator
from ..dynamic_annotation_parser import DynamicAnnotationParser as AnnotationParser

logger = logging.getLogger(__name__)


class CheckerThread(QThread):
    """Thread for running SDTM checks in the background."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config

    def run(self):
        try:
            # Initialize components
            extractor = AnnotationExtractor()  # Don't pass config here
            sdtm_manager = SDTMDatasetManager(
                self.config.paths["sdtm_directory"])

            # Read SDTM data first
            self.progress.emit(10)
            sdtm_data = {}
            for domain in sdtm_manager.get_all_domains():
                dataset = sdtm_manager.get_dataset(domain)
                if dataset:
                    sdtm_data[domain] = dataset

            # Initialize validation engine with datasets
            validator = ValidationEngine(
                datasets=sdtm_data,
                fuzzy_match_threshold=self.config.annotation_patterns["settings"]["fuzzy_threshold"],
                ignore_domains=self.config.validation.get("ignore_domains", []),
                ignore_variables=self.config.validation.get("ignore_variables", [])
            )
            reporter = ReportGenerator(validation_engine=validator)

            # Extract annotations
            self.progress.emit(30)
            annotations = extractor.extract_from_pdf(
                self.config.paths["annotated_crf_file"])

            # Parse annotation tuples into AnnotationData objects
            # Get DM variables for parser
            dm_variables = sdtm_manager.get_dm_variables() if hasattr(sdtm_manager, 'get_dm_variables') else []
            
            # Create parser with configuration
            parser = AnnotationParser(
                dm_variables=dm_variables,
                config=self.config.__dict__ if self.config else None
            )
            parsed_annotations = []
            for text, page, position in annotations:
                parsed_annotations.extend(
                    parser.parse_annotation(text, page, position))

            # Validate annotations against SDTM
            self.progress.emit(50)
            validation_results = validator.validate_annotations(
                parsed_annotations)

            # Generate report
            self.progress.emit(90)
            if self.config.paths.get("default_output_file"):
                # Get just the filename from the default_output_file path
                output_filename = os.path.basename(self.config.paths["default_output_file"])
                # Combine with the configured output directory
                report_path = os.path.join(self.config.paths["output_directory"], output_filename)
            else:
                report_path = os.path.join(
                    self.config.paths["output_directory"],
                    f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                )
            reporter.export_to_excel(
                validation_results, sdtm_data, report_path)
            self.progress.emit(100)

            # Emit success signal
            self.finished.emit(
                True, f"Check completed successfully. Report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Error during SDTM check: {e}")
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main window for SDTM Annotation Checker."""

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigurationManager()
        self.ui_cache = UIStateCache()
        self.checker_thread = None
        self.setup_ui()
        self.load_window_state()

    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("SDTM Annotation Checker")
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create tab widget
        tab_widget = QTabWidget()

        # Add configuration tab
        self.config_tab = ConfigurationTab()
        tab_widget.addTab(self.config_tab, "Configuration")

        layout.addWidget(tab_widget)

        # Create button layout
        button_layout = QHBoxLayout()

        # Run button
        self.run_button = QPushButton("Run Check")
        self.run_button.clicked.connect(self.run_check)
        button_layout.addWidget(self.run_button)

        # Save As button
        save_as_button = QPushButton("Save Configuration As...")
        save_as_button.clicked.connect(self.save_configuration_as)
        button_layout.addWidget(save_as_button)

        # Load Configuration button
        load_button = QPushButton("Load Configuration...")
        load_button.clicked.connect(self.load_configuration_from)
        button_layout.addWidget(load_button)

        # Reset button
        reset_button = QPushButton("Reset to Default")
        reset_button.clicked.connect(self.reset_configuration)
        button_layout.addWidget(reset_button)

        layout.addLayout(button_layout)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

    def update_status_bar(self):
        """Update the status bar with current configuration information."""
        config_path = self.config_manager.get_current_config_path()
        if config_path:
            self.status_bar.showMessage(
                f"Current Configuration: {config_path}")
        else:
            self.status_bar.showMessage("Using Default Configuration")

    def load_window_state(self):
        """Load saved window state."""
        geometry = self.ui_cache.get_state("window_geometry")
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except Exception as e:
                logger.warning(f"Failed to restore window geometry: {e}")

        state = self.ui_cache.get_state("window_state")
        if state:
            try:
                self.restoreState(bytes.fromhex(state))
            except Exception as e:
                logger.warning(f"Failed to restore window state: {e}")

    def save_window_state(self):
        """Save window state."""
        try:
            self.ui_cache.set_state(
                "window_geometry", self.saveGeometry().toHex().data().decode())
            self.ui_cache.set_state(
                "window_state", self.saveState().toHex().data().decode())
        except Exception as e:
            logger.warning(f"Failed to save window state: {e}")

    def run_check(self):
        """Run the SDTM check."""
        try:
            config = self.config_tab.save_configuration()
            if not config:
                return

            self.run_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_bar.showMessage("Running check...")

            self.checker_thread = CheckerThread(config)
            self.checker_thread.progress.connect(self.progress_bar.setValue)
            self.checker_thread.finished.connect(self.check_finished)
            self.checker_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start check: {e}")
            self.run_button.setEnabled(True)
            self.progress_bar.setVisible(False)

    def check_finished(self, success: bool, message: str):
        """Handle check completion."""
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_bar.showMessage(message)
            QMessageBox.information(self, "Success", message)
        else:
            self.status_bar.showMessage("Check failed")
            QMessageBox.critical(self, "Error", message)

    def save_configuration_as(self):
        """Save configuration to a new file."""
        if self.config_tab.save_configuration_as():
            self.update_status_bar()

    def load_configuration_from(self):
        """Load configuration from a file."""
        if self.config_tab.load_configuration_from():
            self.update_status_bar()

    def reset_configuration(self):
        """Reset the configuration to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset the configuration to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config_tab.reset_configuration()
            self.update_status_bar()

    def closeEvent(self, event):
        """Handle window close event."""
        self.save_window_state()
        super().closeEvent(event)


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
