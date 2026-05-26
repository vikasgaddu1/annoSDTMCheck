"""
Main GUI module for SDTM Annotation Checker.
"""

import sys
import logging
import os
import tempfile
from pathlib import Path
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
    QFileDialog,
    QMenuBar,
    QMenu,
    QTextEdit,
    QGroupBox,
    QLabel,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl, QObject
from PyQt6.QtGui import QAction, QDesktopServices, QIcon
from datetime import datetime

from .config_tab import ConfigurationTab
from .ui_state_cache import UIStateCache
from .html_viewer import open_documentation
from ..config_manager import ConfigurationManager
from ..validation_engine import ValidationEngine
from ..annotation_extractor import AnnotationExtractor
from ..sdtm_reader import SDTMDatasetManager
from ..report_generator import ReportGenerator
from ..dynamic_annotation_parser import DynamicAnnotationParser as AnnotationParser
from ..core.annotation_standardizer import AnnotationStandardizer, StandardizationConfig
from ..core.xfdf_color_updater import create_standardized_xfdf, import_standardized_xfdf
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class LogEmitter(QObject):
    """Helper class to emit log signals."""
    log_signal = pyqtSignal(str)


class QTextEditLogger(logging.Handler):
    """Custom logging handler that writes to a QTextEdit widget."""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.emitter = LogEmitter()
        # Connect signal to text widget append method
        self.emitter.log_signal.connect(self.text_edit.append)
        
    def emit(self, record):
        """Emit a log record to the text widget."""
        try:
            msg = self.format(record)
            # Emit signal which is thread-safe
            self.emitter.log_signal.emit(msg)
        except Exception:
            self.handleError(record)


class CheckerThread(QThread):
    """Thread for running SDTM checks in the background."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, str)  # success, message, report_path

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
                # Combine with the configured output directory and normalize
                report_path = os.path.normpath(os.path.join(self.config.paths["output_directory"], output_filename))
            else:
                report_path = os.path.normpath(os.path.join(
                    self.config.paths["output_directory"],
                    f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                ))
            reporter.export_to_excel(
                validation_results, sdtm_data, report_path)
            self.progress.emit(100)

            # Emit success signal with report path
            self.finished.emit(
                True, f"Check completed successfully. Report saved to: {report_path}", report_path)
        except Exception as e:
            logger.error(f"Error during SDTM check: {e}")
            self.finished.emit(False, str(e), "")


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
        
        # Set application icon
        self.set_window_icon()
        
        # Create menu bar
        self.create_menu_bar()

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

        # Create button container layout
        button_container_layout = QHBoxLayout()
        button_container_layout.setSpacing(15)
        button_container_layout.setContentsMargins(10, 10, 10, 10)

        # Action buttons group
        action_group = QGroupBox("Actions")
        action_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.setContentsMargins(15, 15, 15, 15)

        # Run button
        self.run_button = QPushButton("Run Check")
        self.run_button.setMinimumHeight(35)
        self.run_button.setMinimumWidth(120)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_button.clicked.connect(self.run_check)
        self.run_button.setToolTip(
            "Validate CRF annotations against SDTM datasets\n\n"
            "This will:\n"
            "• Extract annotations from PDF\n"
            "• Parse SDTM domain/variable patterns\n"
            "• Validate against SAS7BDAT files\n"
            "• Generate Excel report with results"
        )
        action_layout.addWidget(self.run_button)

        # Standardize Annotations button
        self.standardize_button = QPushButton("Standardize Annotations")
        self.standardize_button.setMinimumHeight(35)
        self.standardize_button.setMinimumWidth(180)
        self.standardize_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a6bc2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.standardize_button.clicked.connect(self.standardize_annotations)
        self.standardize_button.setToolTip(
            "Standardize PDF annotations and create bookmarks\n\n"
            "This will:\n"
            "• Standardize colors (blue, red, green)\n"
            "• Apply cyan backgrounds\n"
            "• Set custom author name\n"
            "• Create dual bookmark structure\n"
            "• Add black borders to rectangles\n"
            "• Auto-resize textboxes (if enabled in settings)"
        )
        action_layout.addWidget(self.standardize_button)
        action_layout.addStretch()
        action_group.setLayout(action_layout)
        button_container_layout.addWidget(action_group)

        # Configuration buttons group
        config_group = QGroupBox("Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QHBoxLayout()
        config_layout.setSpacing(10)
        config_layout.setContentsMargins(15, 15, 15, 15)

        # Save As button
        save_as_button = QPushButton("Save Configuration As...")
        save_as_button.setMinimumHeight(35)
        save_as_button.setMinimumWidth(180)
        save_as_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        save_as_button.clicked.connect(self.save_configuration_as)
        save_as_button.setToolTip(
            "Save current configuration to a new file\n\n"
            "Use this to:\n"
            "• Create project-specific configurations\n"
            "• Maintain multiple config files\n"
            "• Share settings with team members"
        )
        config_layout.addWidget(save_as_button)

        # Load Configuration button
        load_button = QPushButton("Load Configuration...")
        load_button.setMinimumHeight(35)
        load_button.setMinimumWidth(180)
        load_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        load_button.clicked.connect(self.load_configuration_from)
        load_button.setToolTip(
            "Load configuration from a saved file\n\n"
            "Switch between different configurations for:\n"
            "• Different projects\n"
            "• Different studies\n"
            "• Team-specific settings"
        )
        config_layout.addWidget(load_button)

        # Reset button
        reset_button = QPushButton("Reset to Default")
        reset_button.setMinimumHeight(35)
        reset_button.setMinimumWidth(140)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7700;
            }
        """)
        reset_button.clicked.connect(self.reset_configuration)
        reset_button.setToolTip(
            "Reset all settings to default values\n\n"
            "This will restore:\n"
            "• Default file paths\n"
            "• Default validation settings\n"
            "• Default annotation patterns"
        )
        config_layout.addWidget(reset_button)
        config_layout.addStretch()
        config_group.setLayout(config_layout)
        button_container_layout.addWidget(config_group)

        layout.addLayout(button_container_layout)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Create log viewer section
        log_group = QGroupBox("Log Output")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        log_layout = QVBoxLayout()
        log_layout.setSpacing(10)
        log_layout.setContentsMargins(15, 15, 15, 15)
        
        # Log controls
        log_controls = QHBoxLayout()
        log_controls.setSpacing(10)
        
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.setMinimumHeight(32)
        clear_log_button.setMinimumWidth(100)
        clear_log_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        clear_log_button.clicked.connect(self.clear_log)
        clear_log_button.setToolTip("Clear all log messages")
        log_controls.addWidget(clear_log_button)
        
        copy_log_button = QPushButton("Copy Log to Clipboard")
        copy_log_button.setMinimumHeight(32)
        copy_log_button.setMinimumWidth(180)
        copy_log_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        copy_log_button.clicked.connect(self.copy_log)
        copy_log_button.setToolTip("Copy all log messages to clipboard")
        log_controls.addWidget(copy_log_button)
        
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        # Log text widget - auto-resize with window
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)  # Minimum height for usability
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.log_text, 1)  # Stretch factor of 1 for auto-resize
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)  # Stretch factor of 1 to allow log area to expand
        
        # Set up logging handler to write to the log widget
        self.log_handler = QTextEditLogger(self.log_text)
        self.log_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        # Add handler to root logger to capture all logs
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

    def set_window_icon(self):
        """Set the window icon."""
        import os
        import sys
        
        # Try multiple possible icon locations
        icon_paths = []
        
        # For PyInstaller bundle (check this first)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            icon_paths.append(os.path.join(sys._MEIPASS, "assets", "icon.ico"))
        
        # For development (running from source)
        # Get the root directory by going up from gui/main.py: src/sdtm_checker/gui/main.py -> root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
        icon_paths.append(os.path.join(root_dir, "assets", "icon.ico"))
        
        # Check relative to current working directory (for module execution)
        cwd = os.getcwd()
        icon_paths.append(os.path.join(cwd, "assets", "icon.ico"))
        
        # Check relative to package root (where setup.py is)
        # Try to find setup.py by going up from various locations
        base_dirs = [cwd, script_dir]
        if hasattr(sys, 'executable') and sys.executable:
            exe_base = os.path.dirname(sys.executable)
            if exe_base:
                base_dirs.append(exe_base)
        
        for base_dir in base_dirs:
            if base_dir and os.path.exists(base_dir):
                current = Path(base_dir)
                # Look for setup.py or assets folder going up the directory tree
                for _ in range(5):  # Check up to 5 levels up
                    assets_path = current / "assets" / "icon.ico"
                    if assets_path.exists():
                        icon_paths.append(str(assets_path))
                        break
                    setup_path = current / "setup.py"
                    if setup_path.exists():
                        icon_paths.append(str(current / "assets" / "icon.ico"))
                        break
                    parent = current.parent
                    if parent == current:  # Reached root
                        break
                    current = parent
        
        # Alternative: relative to executable location (for bundled app)
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            icon_paths.append(os.path.join(exe_dir, "assets", "icon.ico"))
        
        # Try each path
        for icon_path in icon_paths:
            if icon_path and os.path.exists(icon_path):
                try:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        # Also set as application icon
                        app = QApplication.instance()
                        if app:
                            app.setWindowIcon(icon)
                        logger.info(f"Loaded icon from: {icon_path}")
                        return
                except Exception as e:
                    logger.warning(f"Could not load icon from {icon_path}: {e}")
        
        logger.warning("Could not find application icon")
    
    def create_menu_bar(self):
        """Create the menu bar with Help menu."""
        menubar = self.menuBar()
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # User Guide action
        user_guide_action = QAction("📖 User Guide", self)
        user_guide_action.setShortcut("F1")
        user_guide_action.triggered.connect(self.open_user_guide)
        user_guide_action.setToolTip("Open the comprehensive user guide (F1)")
        help_menu.addAction(user_guide_action)
        
        # Quick Start action
        quick_start_action = QAction("🚀 Quick Start Guide", self)
        quick_start_action.triggered.connect(self.open_quick_start)
        quick_start_action.setToolTip("Open the quick start guide for validation settings")
        help_menu.addAction(quick_start_action)
        
        help_menu.addSeparator()
        
        # What's This action
        whats_this_action = QAction("❓ What's This?", self)
        whats_this_action.setShortcut("Shift+F1")
        whats_this_action.triggered.connect(self.enter_whats_this_mode)
        whats_this_action.setToolTip("Click on any element to see detailed help (Shift+F1)")
        help_menu.addAction(whats_this_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        about_action.setToolTip("About SDTM Annotation Checker")
        help_menu.addAction(about_action)
    
    def open_user_guide(self):
        """Open the user guide in the browser as HTML."""
        success, message = open_documentation("USER_GUIDE.md", "SDTM Annotation Checker - User Guide")
        
        if not success:
            QMessageBox.warning(
                self,
                "User Guide",
                message
            )
    
    def open_quick_start(self):
        """Open the quick start guide in the browser as HTML."""
        success, message = open_documentation("QUICK_START_GUIDE.md", "SDTM Annotation Checker - Quick Start")
        
        if not success:
            QMessageBox.warning(
                self,
                "Quick Start",
                message
            )
    
    def enter_whats_this_mode(self):
        """Enter What's This? mode."""
        QApplication.instance().setOverrideCursor(Qt.CursorShape.WhatsThisCursor)
        QMessageBox.information(
            self,
            "What's This? Mode",
            "Click on any element to see detailed help about it.\n\n"
            "Press Esc to exit this mode."
        )
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SDTM Annotation Checker",
            "<h3>SDTM Annotation Checker</h3>"
            "<p><b>Version 1.2.0</b></p>"
            "<p>A comprehensive GUI application for validating and standardizing SDTM annotations in PDF CRFs.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Annotation validation against SDTM datasets</li>"
            "<li>PDF standardization with color correction</li>"
            "<li>Dual hierarchical bookmark structure</li>"
            "<li>Configurable settings for different projects</li>"
            "</ul>"
            "<p><b>Built with:</b> Python, PyQt6, PyMuPDF</p>"
            "<p>For help, press F1 to open the User Guide.</p>"
        )
    
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

    def check_finished(self, success: bool, message: str, report_path: str = ""):
        """Handle check completion."""
        self.run_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_bar.showMessage(message)
            self.show_success_dialog(message, report_path)
        else:
            self.status_bar.showMessage("Check failed")
            QMessageBox.critical(self, "Error", message)

    def show_success_dialog(self, message: str, report_path: str):
        """Show success dialog with option to open report."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(message)
        
        # Add custom buttons
        open_button = msg_box.addButton("Open Report", QMessageBox.ButtonRole.AcceptRole)
        ok_button = msg_box.addButton(QMessageBox.StandardButton.Ok)
        
        # Set OK as default button
        msg_box.setDefaultButton(ok_button)
        
        # Show dialog and handle response
        msg_box.exec()
        
        # Check which button was clicked and handle accordingly
        if msg_box.clickedButton() == open_button:
            # Use QTimer to open report after dialog is fully closed
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.open_report(report_path))

    def open_report(self, report_path: str):
        """Open the report file with the default system application."""
        if not report_path:
            QMessageBox.warning(
                self, 
                "Warning", 
                "No report path provided."
            )
            return
        
        # Normalize the path to handle mixed separators
        normalized_path = os.path.normpath(report_path)
        
        # Check if file exists
        if not os.path.exists(normalized_path):
            QMessageBox.warning(
                self, 
                "Warning", 
                f"Report file not found at:\n{normalized_path}\n\nPlease check if the file was created successfully."
            )
            return
        
        try:
            # Use os.startfile on Windows to open with default application
            if sys.platform.startswith('win'):
                os.startfile(normalized_path)
            elif sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{normalized_path}"')
            else:  # Linux and other Unix-like systems
                os.system(f'xdg-open "{normalized_path}"')
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open report at:\n{normalized_path}\n\nError: {str(e)}"
            )

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

    def standardize_annotations(self):
        """Standardize PDF annotations with consistent formatting."""
        try:
            # Get the PDF file path from the configuration
            config = self.config_tab.save_configuration()
            if not config:
                QMessageBox.warning(self, "Warning", "Please configure settings first.")
                return
                
            input_pdf = config.paths.get("annotated_crf_file")
            if not input_pdf or not os.path.exists(input_pdf):
                QMessageBox.warning(
                    self, 
                    "Warning", 
                    "Please select a valid annotated CRF file in the configuration."
                )
                return
            
            # Ask user for output file location
            # Default to C:\Users\{username}\Documents for local drive (required for XFDF import)
            import getpass
            username = getpass.getuser()
            default_dir = Path(f"C:/Users/{username}/Documents/SDTM_Standardized")
            default_dir.mkdir(parents=True, exist_ok=True)
            
            input_filename = Path(input_pdf).stem
            default_output = str(default_dir / f"{input_filename}_standardized.pdf")
            
            output_pdf, _ = QFileDialog.getSaveFileName(
                self,
                "Save Standardized PDF As (MUST be on C: drive for XFDF import)",
                default_output,
                "PDF Files (*.pdf)"
            )
            
            if not output_pdf:
                return  # User cancelled
            
            # Validate that output is on local drive (not network)
            output_path = Path(output_pdf)
            if str(output_path.drive).startswith('\\\\') or not output_path.drive.startswith('C:'):
                reply = QMessageBox.warning(
                    self,
                    "Network Drive Detected",
                    f"Output path: {output_pdf}\n\n"
                    f"⚠ XFDF import works best on local drives (C:).\n"
                    f"Network drives (\\\\server) may cause import issues.\n\n"
                    f"Recommended: Save to C:\\Users\\{username}\\Documents\\SDTM_Standardized\\\n\n"
                    f"Do you want to continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Confirm standardization settings
            author_name = config.validation.get("generic_author_name", "Geron")
            form_label = config.validation.get("form_bookmark_label", "Form_bookmarks")
            sdtm_label = config.validation.get("sdtm_bookmark_label", "SDTM")
            auto_resize = config.validation.get("auto_resize_textboxes", True)
            auto_align = config.validation.get("align_annotations", True)
            skip_pages_str = config.validation.get("resize_skip_pages", "").strip()
            align_skip_pages_str = config.validation.get("align_skip_pages", "").strip()
            
            msg = "The following standardization will be applied:\n\n"
            msg += f"• Author: {author_name}\n"
            msg += "• Background: Cyan for all annotations\n"
            msg += "• Colors: Standardized (blue, red, green)\n"
            msg += "• Headers: 12pt (domain headers)\n"
            msg += "• Regular text: 10pt\n"
            msg += "• Rectangle borders: Black\n"
            msg += f"• Bookmarks: Dual structure ({form_label} + {sdtm_label})\n"
            if auto_resize:
                if skip_pages_str:
                    msg += f"• Auto-Resize: Enabled (skipping pages: {skip_pages_str})\n"
                else:
                    msg += f"• Auto-Resize: Enabled (textboxes will be expanded to fit content)\n"
            if auto_align:
                if align_skip_pages_str:
                    msg += f"• Auto-Align: Enabled (skipping pages: {align_skip_pages_str})\n"
                else:
                    msg += f"• Auto-Align: Enabled (annotations will be aligned)\n"
            msg += "\nDo you want to proceed?"
            
            reply = QMessageBox.question(
                self,
                "Confirm Standardization",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Disable buttons and show progress
            self.standardize_button.setEnabled(False)
            self.status_bar.showMessage("Standardizing annotations...")
            
            # Create standardizer config (using settings from validation)
            author_name = config.validation.get("generic_author_name", "Geron")
            form_label = config.validation.get("form_bookmark_label", "Form_bookmarks")
            sdtm_label = config.validation.get("sdtm_bookmark_label", "SDTM")
            auto_resize = config.validation.get("auto_resize_textboxes", True)
            auto_align = config.validation.get("align_annotations", True)
            horizontal_tol = config.validation.get("horizontal_tolerance", 1.0)
            vertical_tol = config.validation.get("vertical_tolerance", 10.0)
            
            # Extract color config from validation settings
            color_config = {
                "standard_red_color": config.validation.get("standard_red_color", [255, 0, 0]),
                "standard_blue_color": config.validation.get("standard_blue_color", [0, 0, 255]),
                "standard_green_color": config.validation.get("standard_green_color", [0, 124, 0])
            }
            
            # Extract background and border colors from validation settings
            # Convert from [0-255] scale to (0-1) scale for StandardizationConfig
            bg_color_255 = config.validation.get("background_color", [0, 255, 255])
            background_color = tuple(c / 255.0 for c in bg_color_255)
            
            border_color_255 = config.validation.get("textbox_border_color", [0, 0, 0])
            textbox_border_color = tuple(c / 255.0 for c in border_color_255)
            
            # NEW XFDF WORKFLOW: Extract, standardize, create XFDF, import back
            temp_xfdf_path = None
            try:
                # Open PDF document
                doc = fitz.open(input_pdf)
                
                # Parse and validate skip pages for resize
                skip_pages_str = config.validation.get("resize_skip_pages", "").strip()
                skip_pages_0_indexed = None
                invalid_pages = []
                pdf_page_count = len(doc)
                
                if skip_pages_str and auto_resize:
                    # Parse comma-separated page numbers
                    page_numbers_str = [p.strip() for p in skip_pages_str.split(",") if p.strip()]
                    valid_pages = []
                    
                    for page_str in page_numbers_str:
                        try:
                            page_num_1_indexed = int(page_str)
                            # Validate range (1 to PDF page count)
                            if 1 <= page_num_1_indexed <= pdf_page_count:
                                # Convert to 0-indexed
                                valid_pages.append(page_num_1_indexed - 1)
                            else:
                                invalid_pages.append(page_str)
                        except ValueError:
                            invalid_pages.append(page_str)
                    
                    if valid_pages:
                        skip_pages_0_indexed = valid_pages
                    
                    # Show warning if invalid pages were found
                    if invalid_pages:
                        QMessageBox.warning(
                            self,
                            "Invalid Page Numbers (Auto-Resize)",
                            f"The following page numbers are invalid and will be ignored:\n"
                            f"{', '.join(invalid_pages)}\n\n"
                            f"Valid range: 1 to {pdf_page_count}"
                        )
                
                # Parse and validate skip pages for align
                align_skip_pages_str = config.validation.get("align_skip_pages", "").strip()
                align_skip_pages_0_indexed = None
                align_invalid_pages = []
                
                if align_skip_pages_str and auto_align:
                    # Parse comma-separated page numbers
                    page_numbers_str = [p.strip() for p in align_skip_pages_str.split(",") if p.strip()]
                    valid_pages = []
                    
                    for page_str in page_numbers_str:
                        try:
                            page_num_1_indexed = int(page_str)
                            # Validate range (1 to PDF page count)
                            if 1 <= page_num_1_indexed <= pdf_page_count:
                                # Convert to 0-indexed
                                valid_pages.append(page_num_1_indexed - 1)
                            else:
                                align_invalid_pages.append(page_str)
                        except ValueError:
                            align_invalid_pages.append(page_str)
                    
                    if valid_pages:
                        align_skip_pages_0_indexed = valid_pages
                    
                    # Show warning if invalid pages were found
                    if align_invalid_pages:
                        QMessageBox.warning(
                            self,
                            "Invalid Page Numbers (Auto-Align)",
                            f"The following page numbers are invalid and will be ignored:\n"
                            f"{', '.join(align_invalid_pages)}\n\n"
                            f"Valid range: 1 to {pdf_page_count}"
                        )
                
                # Get normalize_quotes setting
                normalize_quotes = config.validation.get("normalize_quotes", True)
                
                # Create standardizer config (after parsing skip pages)
                standardizer_config = StandardizationConfig(
                    default_author=author_name,
                    color_config=color_config,
                    background_color=background_color,
                    rectangle_border_color=textbox_border_color,
                    form_bookmark_label=form_label,
                    sdtm_bookmark_label=sdtm_label,
                    auto_resize_textboxes=auto_resize,
                    align_annotations=auto_align,
                    horizontal_tolerance=horizontal_tol,
                    vertical_tolerance=vertical_tol,
                    resize_skip_pages=skip_pages_0_indexed,
                    align_skip_pages=align_skip_pages_0_indexed,
                    normalize_quotes=normalize_quotes
                )
                
                # Create temporary XFDF file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.xfdf', delete=False, encoding='utf-8') as tmp_xfdf:
                    temp_xfdf_path = tmp_xfdf.name
                
                try:
                    # Step 1: Create standardized XFDF
                    self.status_bar.showMessage("Creating standardized XFDF...")
                    xfdf_stats = create_standardized_xfdf(doc, standardizer_config, temp_xfdf_path, output_pdf)
                    
                    if xfdf_stats['exported'] == 0:
                        doc.close()
                        QMessageBox.warning(self, "Warning", "No FreeText annotations found in PDF.")
                        self.standardize_button.setEnabled(True)
                        self.status_bar.showMessage("Ready")
                        if temp_xfdf_path:
                            try:
                                Path(temp_xfdf_path).unlink(missing_ok=True)
                            except:
                                pass
                        return
                    
                    # Save XFDF file next to output PDF for manual import if needed
                    xfdf_output_path = Path(output_pdf).with_suffix('.xfdf')
                    try:
                        import shutil
                        shutil.copy2(temp_xfdf_path, xfdf_output_path)
                        logger.info(f"Saved XFDF file to: {xfdf_output_path}")
                    except Exception as copy_error:
                        logger.warning(f"Could not save XFDF file: {copy_error}")
                        xfdf_output_path = None
                    
                    # Close the original document
                    doc.close()
                    
                    # For manual XFDF import workflow:
                    # Step 2: Create a clean PDF without annotations for manual import
                    doc = fitz.open(input_pdf)
                    
                    # Clear all existing annotations to prepare for manual import
                    self.status_bar.showMessage("Creating clean PDF for XFDF import...")
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        annots = list(page.annots() or [])
                        for annot in annots:
                            try:
                                page.delete_annot(annot)
                            except:
                                pass
                    
                    # Save clean PDF
                    doc.save(output_pdf)
                    
                    # Create dummy import stats for consistency
                    import_stats = {'imported': xfdf_stats['exported'], 'errors': []}
                    
                    stats = {
                        'annotations_modified': import_stats['imported'],
                        'headers_found': 0,  # Would need separate processing
                        'text_capitalized': 0,
                        'rectangles_styled': 0,
                        'bookmarks_created': 0,  # Would need separate processing
                        'errors': import_stats.get('errors', []),
                        'xfdf_exported': xfdf_stats['exported'],
                        'xfdf_imported': import_stats['imported'],
                        'xfdf_path': str(xfdf_output_path) if xfdf_output_path else None
                    }
                    
                    # Clean up temp file
                    if temp_xfdf_path:
                        try:
                            Path(temp_xfdf_path).unlink(missing_ok=True)
                        except:
                            pass
                    
                    doc.close()
                    
                except Exception as import_error:
                    # Import failed - save XFDF file for manual import
                    logger.warning(f"XFDF import failed: {import_error}")
                    
                    # Save XFDF file next to output PDF
                    xfdf_output_path = Path(output_pdf).with_suffix('.xfdf')
                    try:
                        import shutil
                        shutil.copy2(temp_xfdf_path, xfdf_output_path)
                        logger.info(f"Saved XFDF file to: {xfdf_output_path}")
                    except Exception as copy_error:
                        logger.error(f"Could not save XFDF file: {copy_error}")
                        xfdf_output_path = temp_xfdf_path  # Use temp file location
                    
                    # Save PDF without annotations (or with original annotations)
                    doc.save(output_pdf)
                    doc.close()
                    
                    # Clean up temp file if we copied it
                    if xfdf_output_path != temp_xfdf_path and temp_xfdf_path:
                        try:
                            Path(temp_xfdf_path).unlink(missing_ok=True)
                        except:
                            pass
                    
                    # Show message with XFDF location
                    msg = f"Standardization XFDF file created.\n\n"
                    msg += f"XFDF import failed: {str(import_error)}\n\n"
                    msg += f"XFDF file saved to:\n{xfdf_output_path}\n\n"
                    msg += "Please import this XFDF file manually into your PDF using Adobe Acrobat:\n"
                    msg += "1. Open the PDF\n"
                    msg += "2. Go to Comments > Import Comments\n"
                    msg += f"3. Select: {xfdf_output_path}"
                    
                    QMessageBox.information(self, "XFDF Created", msg)
                    
                    self.standardize_button.setEnabled(True)
                    self.status_bar.showMessage("XFDF file created")
                    return
                
            except Exception as e:
                # General error - try to clean up
                if temp_xfdf_path:
                    try:
                        Path(temp_xfdf_path).unlink(missing_ok=True)
                    except:
                        pass
                raise
            
            # Re-enable button
            self.standardize_button.setEnabled(True)
            
            # Show results
            if stats.get('errors'):
                error_msg = "Standardization completed with errors:\n\n"
                for error in stats['errors'][:5]:  # Show first 5 errors
                    error_msg += f"• {error}\n"
                if len(stats['errors']) > 5:
                    error_msg += f"\n...and {len(stats['errors']) - 5} more errors"
                QMessageBox.warning(self, "Standardization Completed", error_msg)
            else:
                result_msg = f"XFDF Export Complete!\n\n"
                result_msg += f"✓ Exported {stats.get('xfdf_exported', 0)} annotations with standardized colors\n\n"
                
                result_msg += f"Files Created:\n"
                result_msg += f"• Clean PDF (no annotations): {output_pdf}\n"
                if stats.get('xfdf_path'):
                    result_msg += f"• XFDF file: {stats['xfdf_path']}\n\n"
                
                result_msg += f"Standardized Colors Applied:\n"
                result_msg += f"• Blue text: Standard annotations\n"
                result_msg += f"• Red text: Warnings/errors\n"
                result_msg += f"• Cyan background: All annotations\n"
                result_msg += f"• Black borders: All annotations\n\n"
                
                result_msg += f"To Apply Annotations (EASY METHOD):\n"
                result_msg += f"1. Double-click the XFDF file: {stats['xfdf_path']}\n"
                result_msg += f"   → This will automatically open the PDF with annotations!\n"
                result_msg += f"2. Use 'Save As' in Adobe Acrobat to save the PDF with annotations\n\n"
                
                result_msg += f"Alternative Method:\n"
                result_msg += f"1. Open: {output_pdf}\n"
                result_msg += f"2. Tools → Comment → More → Import Data\n"
                result_msg += f"3. Select the XFDF file and click Import\n\n"
                
                result_msg += f"✓ Annotations will appear with standardized colors, sizes, and alignment!"
                
                # Show success dialog with option to open
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("Standardization Complete")
                msg_box.setText(result_msg)
                
                # Add custom buttons
                open_xfdf_button = msg_box.addButton("Open XFDF (Double-click)", QMessageBox.ButtonRole.AcceptRole)
                open_pdf_button = msg_box.addButton("Open PDF", QMessageBox.ButtonRole.ActionRole)
                ok_button = msg_box.addButton(QMessageBox.StandardButton.Ok)
                msg_box.setDefaultButton(ok_button)
                
                msg_box.exec()
                
                # Check which button was clicked
                if msg_box.clickedButton() == open_xfdf_button:
                    # Open XFDF file (will auto-open PDF with annotations)
                    if stats.get('xfdf_path'):
                        QDesktopServices.openUrl(QUrl.fromLocalFile(stats['xfdf_path']))
                elif msg_box.clickedButton() == open_pdf_button:
                    # Open the standardized PDF
                    normalized_path = os.path.normpath(output_pdf)
                    try:
                        logger.info(f"Attempting to open PDF at: {normalized_path}")
                        
                        # Verify file exists before opening
                        if not os.path.exists(normalized_path):
                            QMessageBox.warning(self, "Warning", f"Output file not found:\n{normalized_path}")
                        else:
                            if sys.platform.startswith('win'):
                                os.startfile(normalized_path)
                            elif sys.platform.startswith('darwin'):
                                os.system(f'open "{normalized_path}"')
                            else:
                                os.system(f'xdg-open "{normalized_path}"')
                            
                            logger.info(f"Successfully opened PDF: {normalized_path}")
                    except Exception as e:
                        logger.error(f"Failed to open PDF: {e}")
                        QMessageBox.warning(self, "Warning", f"Could not open PDF:\n{str(e)}\n\nFile location:\n{normalized_path}")
            
            self.status_bar.showMessage("Standardization complete")
            
        except Exception as e:
            self.standardize_button.setEnabled(True)
            self.status_bar.showMessage("Standardization failed")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to standardize annotations:\n{str(e)}"
            )
            logger.exception("Standardization error")

    def clear_log(self):
        """Clear the log output."""
        self.log_text.clear()
        logger.info("Log cleared")
    
    def copy_log(self):
        """Copy log contents to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        self.status_bar.showMessage("Log copied to clipboard", 3000)
        logger.info("Log copied to clipboard")

    def closeEvent(self, event):
        """Handle window close event."""
        # Remove the log handler to avoid issues on close
        if hasattr(self, 'log_handler'):
            logging.getLogger().removeHandler(self.log_handler)
        self.save_window_state()
        super().closeEvent(event)


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
