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
    QColorDialog,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

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
        self.crf_edit.setToolTip(
            "Path to the annotated CRF PDF file\n\n"
            "This PDF should contain:\n"
            "• Annotations with SDTM domain/variable mappings\n"
            "• Text annotations in supported formats\n"
            "• Examples: DM.SUBJID, VS-VSORRES, AESTDTC"
        )
        self.crf_edit.setWhatsThis(
            "<b>Annotated CRF File</b><br><br>"
            "Select the PDF file containing your Case Report Form with SDTM annotations. "
            "The annotations should follow standard formats like DOMAIN.VARIABLE or DOMAIN-VARIABLE. "
            "Click Browse to select a file from your file system."
        )
        crf_browse = QPushButton("Browse...")
        crf_browse.clicked.connect(lambda: self.browse_file(
            self.crf_edit, "PDF Files (*.pdf)"))
        crf_browse.setToolTip("Click to select a PDF file")
        crf_layout.addWidget(self.crf_edit)
        crf_layout.addWidget(crf_browse)
        paths_layout.addRow("Annotated CRF File:", crf_layout)

        # SDTM directory
        sdtm_layout = QHBoxLayout()
        self.sdtm_edit = QLineEdit()
        self.sdtm_edit.setToolTip(
            "Directory containing SDTM dataset files (.sas7bdat)\n\n"
            "Expected files:\n"
            "• dm.sas7bdat (Demographics)\n"
            "• ae.sas7bdat (Adverse Events)\n"
            "• vs.sas7bdat (Vital Signs)\n"
            "• Other SDTM domain datasets"
        )
        self.sdtm_edit.setWhatsThis(
            "<b>SDTM Directory</b><br><br>"
            "Select the directory containing your SDTM dataset files in SAS7BDAT format. "
            "The application will read all .sas7bdat files in this directory and validate "
            "your CRF annotations against the actual variables present in these datasets."
        )
        sdtm_browse = QPushButton("Browse...")
        sdtm_browse.clicked.connect(
            lambda: self.browse_directory(self.sdtm_edit))
        sdtm_browse.setToolTip("Click to select a directory")
        sdtm_layout.addWidget(self.sdtm_edit)
        sdtm_layout.addWidget(sdtm_browse)
        paths_layout.addRow("SDTM Directory:", sdtm_layout)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setToolTip(
            "Directory where reports will be saved\n\n"
            "The application will create:\n"
            "• Excel validation reports\n"
            "• Standardized PDF files (if using Standardize feature)"
        )
        self.output_edit.setWhatsThis(
            "<b>Output Directory</b><br><br>"
            "Choose where validation reports and standardized PDFs will be saved. "
            "The directory will be created if it doesn't exist."
        )
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(
            lambda: self.browse_directory(self.output_edit))
        output_browse.setToolTip("Click to select output directory")
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_browse)
        paths_layout.addRow("Output Directory:", output_layout)

        # Default output file
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setToolTip(
            "Default filename for validation reports\n\n"
            "Example: validation_report.xlsx\n"
            "The file will be saved in the Output Directory"
        )
        self.output_file_edit.setWhatsThis(
            "<b>Default Output File</b><br><br>"
            "Specify the default filename for validation reports. "
            "Include the .xlsx extension. This filename will be used "
            "unless you specify a different name when running the check."
        )
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
        pattern_buttons.setSpacing(10)
        pattern_buttons.setContentsMargins(0, 10, 0, 10)
        
        add_pattern = QPushButton("Add Pattern")
        add_pattern.setMinimumHeight(35)
        add_pattern.setMinimumWidth(120)
        add_pattern.setStyleSheet("""
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
        """)
        add_pattern.clicked.connect(self.add_pattern)
        add_pattern.setToolTip("Add a new annotation pattern")
        pattern_buttons.addWidget(add_pattern)
        
        edit_pattern = QPushButton("Edit Pattern")
        edit_pattern.setMinimumHeight(35)
        edit_pattern.setMinimumWidth(120)
        edit_pattern.setStyleSheet("""
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
        """)
        edit_pattern.clicked.connect(self.edit_pattern)
        edit_pattern.setToolTip("Edit the selected pattern")
        pattern_buttons.addWidget(edit_pattern)
        
        delete_pattern = QPushButton("Delete Pattern")
        delete_pattern.setMinimumHeight(35)
        delete_pattern.setMinimumWidth(130)
        delete_pattern.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        delete_pattern.clicked.connect(self.delete_pattern)
        delete_pattern.setToolTip("Delete the selected pattern")
        pattern_buttons.addWidget(delete_pattern)
        
        test_pattern = QPushButton("Test Pattern")
        test_pattern.setMinimumHeight(35)
        test_pattern.setMinimumWidth(120)
        test_pattern.setStyleSheet("""
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
        test_pattern.clicked.connect(self.test_pattern)
        test_pattern.setToolTip("Test the selected pattern with sample text")
        pattern_buttons.addWidget(test_pattern)
        
        pattern_buttons.addStretch()
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
        validation_layout = QVBoxLayout(validation_tab)

        # General Settings Group
        general_group = QGroupBox("General Settings")
        general_form = QFormLayout(general_group)

        # Fuzzy matching
        self.fuzzy_matching = QCheckBox()
        self.fuzzy_matching.setToolTip(
            "Enable fuzzy matching for annotation validation\n\n"
            "When enabled:\n"
            "• Allows slight variations in variable names\n"
            "• Useful for typos or case differences\n"
            "• Uses the Fuzzy Threshold setting"
        )
        self.fuzzy_matching.setWhatsThis(
            "<b>Fuzzy Matching</b><br><br>"
            "Enable this to allow approximate matches when validating annotations. "
            "Useful when annotations might have minor typos or case variations. "
            "The similarity threshold is controlled by the Fuzzy Threshold setting below."
        )
        general_form.addRow("Fuzzy Matching:", self.fuzzy_matching)

        # Fuzzy threshold
        self.fuzzy_threshold = QDoubleSpinBox()
        self.fuzzy_threshold.setRange(0, 1)
        self.fuzzy_threshold.setSingleStep(0.05)
        self.fuzzy_threshold.setValue(0.85)
        self.fuzzy_threshold.setMaximumWidth(120)
        self.fuzzy_threshold.setToolTip(
            "Similarity threshold for fuzzy matching (0.0 - 1.0)\n\n"
            "0.0 = No similarity required\n"
            "0.85 = 85% similarity (default)\n"
            "1.0 = Exact match required\n\n"
            "Higher values = stricter matching"
        )
        self.fuzzy_threshold.setWhatsThis(
            "<b>Fuzzy Threshold</b><br><br>"
            "Set how similar annotations must be to match SDTM variables. "
            "A value of 0.85 (85%) is the default - it catches typos while avoiding false matches. "
            "Lower values allow more variation but may produce false positives."
        )
        general_form.addRow("Fuzzy Threshold:", self.fuzzy_threshold)

        # Ignore domains
        self.ignore_domains = QLineEdit()
        self.ignore_domains.setMaximumWidth(300)
        self.ignore_domains.setToolTip(
            "Comma-separated list of domains to skip\n\n"
            "Example: DM,VS,AE\n"
            "These domains won't be validated\n"
            "Useful for domains not yet annotated"
        )
        self.ignore_domains.setWhatsThis(
            "<b>Ignore Domains</b><br><br>"
            "Enter domain codes (comma-separated) that should be skipped during validation. "
            "Example: <code>DM,CO,SUPPQUAL</code><br>"
            "Use this for domains that aren't annotated yet or don't need validation."
        )
        general_form.addRow("Ignore Domains:", self.ignore_domains)

        # Ignore variables
        self.ignore_variables = QLineEdit()
        self.ignore_variables.setMaximumWidth(300)
        self.ignore_variables.setToolTip(
            "Comma-separated list of variables to skip\n\n"
            "Example: STUDYID,USUBJID\n"
            "These variables won't be validated\n"
            "Useful for standard identifiers"
        )
        self.ignore_variables.setWhatsThis(
            "<b>Ignore Variables</b><br><br>"
            "Enter variable names (comma-separated) that should be skipped during validation. "
            "Example: <code>STUDYID,USUBJID,DOMAIN</code><br>"
            "Typically used for standard identifiers that don't need annotation validation."
        )
        general_form.addRow("Ignore Variables:", self.ignore_variables)

        # Generic Author Name
        self.generic_author_name = QLineEdit()
        self.generic_author_name.setPlaceholderText("Geron")
        self.generic_author_name.setMaximumWidth(300)
        self.generic_author_name.setToolTip(
            "Author name applied to all annotations during standardization\n\n"
            "Default: Geron\n"
            "Examples:\n"
            "• Your name\n"
            "• Team name\n"
            "• Organization name"
        )
        self.generic_author_name.setWhatsThis(
            "<b>Generic Author Name</b><br><br>"
            "Set the author name that will be applied to all annotations when using "
            "the Standardize Annotations feature. This can be your name, team name, "
            "or organization name. Leave empty to use the default 'Geron'."
        )
        general_form.addRow("Generic Author Name:", self.generic_author_name)

        # Form Bookmark Label
        self.form_bookmark_label = QLineEdit()
        self.form_bookmark_label.setPlaceholderText("Form_bookmarks")
        self.form_bookmark_label.setMaximumWidth(300)
        self.form_bookmark_label.setToolTip(
            "Label for form-based bookmark section\n\n"
            "Default: Form_bookmarks\n"
            "Examples:\n"
            "• Forms\n"
            "• CRF_Pages\n"
            "• Formularios (Spanish)"
        )
        self.form_bookmark_label.setWhatsThis(
            "<b>Form Bookmark Label</b><br><br>"
            "Customize the label for the form-based bookmark section in standardized PDFs. "
            "This appears as the top-level bookmark grouping forms by their names. "
            "Use any text - supports multilingual labels."
        )
        general_form.addRow("Form Bookmark Label:", self.form_bookmark_label)

        # SDTM Bookmark Label
        self.sdtm_bookmark_label = QLineEdit()
        self.sdtm_bookmark_label.setPlaceholderText("SDTM")
        self.sdtm_bookmark_label.setMaximumWidth(300)
        self.sdtm_bookmark_label.setToolTip(
            "Label for domain-based bookmark section\n\n"
            "Default: SDTM\n"
            "Examples:\n"
            "• Domains\n"
            "• Data_Domains\n"
            "• Dominios_SDTM (Spanish)"
        )
        self.sdtm_bookmark_label.setWhatsThis(
            "<b>SDTM Bookmark Label</b><br><br>"
            "Customize the label for the domain-based bookmark section in standardized PDFs. "
            "This appears as the top-level bookmark grouping forms by SDTM domains. "
            "Use any text - supports multilingual labels."
        )
        general_form.addRow("SDTM Bookmark Label:", self.sdtm_bookmark_label)

        # Normalize Quotes
        self.normalize_quotes = QCheckBox()
        self.normalize_quotes.setChecked(True)  # Enabled by default
        self.normalize_quotes.setToolTip(
            "Normalize quotes around annotation values\n\n"
            "When enabled:\n"
            "• Wraps values in double quotes (e.g., LBTESTCD = HGB → LBTESTCD = \"HGB\")\n"
            "• Converts single quotes to double quotes\n"
            "• Handles missing quotes\n"
            "• Normalizes spacing around '=' signs\n"
            "• Exceptions: RELREC annotations and header annotations (domain labels)\n\n"
            "This ensures consistent formatting before resizing/alignment calculations."
        )
        self.normalize_quotes.setWhatsThis(
            "<b>Normalize Quotes</b><br><br>"
            "Automatically normalize quotes around annotation values. Values after '=' will be wrapped "
            "in double quotes, single quotes will be converted to double quotes, and spacing around '=' "
            "will be normalized. This is performed before resizing/alignment to ensure accurate text length calculations. "
            "RELREC annotations (e.g., 'RELREC when FASPID = AESPID') and header annotations (e.g., 'DM = Demographics') "
            "are excluded from quote normalization."
        )
        general_form.addRow("Normalize Quotes:", self.normalize_quotes)

        # Reset button for General Settings
        general_reset_button = QPushButton("Reset to Default")
        general_reset_button.setMinimumHeight(35)
        general_reset_button.setMinimumWidth(140)
        general_reset_button.setStyleSheet("""
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
        general_reset_button.clicked.connect(self.reset_general_settings)
        general_reset_button.setToolTip("Reset General Settings to default values")
        general_reset_layout = QHBoxLayout()
        general_reset_layout.addWidget(general_reset_button)
        general_reset_layout.addStretch()
        general_form.addRow("", general_reset_layout)

        validation_layout.addWidget(general_group)

        # Three Column Layout for Resize, Alignment, and Color Settings
        columns_layout = QHBoxLayout()

        # Column 1: Resize Settings
        resize_group = QGroupBox("Resize Settings")
        resize_form = QFormLayout(resize_group)

        # Auto-resize Textboxes
        self.auto_resize_textboxes = QCheckBox()
        self.auto_resize_textboxes.setChecked(True)  # Enabled by default
        self.auto_resize_textboxes.setToolTip(
            "Automatically resize textbox annotations to fit content\n\n"
            "When enabled:\n"
            "• Detects annotations with insufficient space\n"
            "• Calculates required dimensions\n"
            "• Expands boxes to display full text\n\n"
            "Note: May cause overlaps with form content"
        )
        self.auto_resize_textboxes.setWhatsThis(
            "<b>Auto-Resize Textboxes</b><br><br>"
            "Enable automatic resizing of textbox annotations during standardization. "
            "The system will detect when text doesn't fit and expand the annotation box "
            "to accommodate the full content. Use with caution as resized boxes may overlap "
            "with CRF form text."
        )
        resize_form.addRow("Auto-Resize Textboxes:", self.auto_resize_textboxes)

        # Resize max width expansion
        resize_width_layout = QHBoxLayout()
        self.resize_max_width = QDoubleSpinBox()
        self.resize_max_width.setRange(0, 500)
        self.resize_max_width.setValue(200.0)
        self.resize_max_width.setSuffix(" pt")
        self.resize_max_width.setMaximumWidth(120)
        self.resize_max_width.setToolTip(
            "Maximum width expansion in points\n\n"
            "Default: 200 pt\n"
            "Limits how much wider textboxes can grow\n"
            "Prevents boxes from becoming too wide"
        )
        resize_width_layout.addWidget(self.resize_max_width)
        resize_form.addRow("Max Width Expansion:", resize_width_layout)

        # Resize max height expansion
        resize_height_layout = QHBoxLayout()
        self.resize_max_height = QDoubleSpinBox()
        self.resize_max_height.setRange(0, 500)
        self.resize_max_height.setValue(300.0)
        self.resize_max_height.setSuffix(" pt")
        self.resize_max_height.setMaximumWidth(120)
        self.resize_max_height.setToolTip(
            "Maximum height expansion in points\n\n"
            "Default: 300 pt\n"
            "Limits how much taller textboxes can grow\n"
            "Prevents boxes from becoming too tall"
        )
        resize_height_layout.addWidget(self.resize_max_height)
        resize_form.addRow("Max Height Expansion:", resize_height_layout)

        # Resize skip pages
        self.resize_skip_pages = QLineEdit()
        self.resize_skip_pages.setPlaceholderText("e.g., 1, 5, 10")
        self.resize_skip_pages.setMaximumWidth(300)
        self.resize_skip_pages.setToolTip(
            "Page numbers to skip from auto-resizing\n\n"
            "Format: Comma-separated page numbers (1-indexed)\n"
            "Example: 1, 5, 10\n\n"
            "Useful for pages with complex CRF layouts where\n"
            "auto-resizing may cause layout issues.\n\n"
            "Other standardization (colors, fonts) will still\n"
            "be applied to skipped pages."
        )
        self.resize_skip_pages.setWhatsThis(
            "<b>Skip Pages for Auto-Resize</b><br><br>"
            "Enter comma-separated page numbers (starting from 1) that should be "
            "skipped during auto-resize operations. This is useful for pages with "
            "complex CRF layouts where auto-resizing textboxes may cause layout issues. "
            "Other standardization features (colors, fonts, alignment) will still be "
            "applied to these pages."
        )
        resize_form.addRow("Skip Pages:", self.resize_skip_pages)

        # Reset button for Resize Settings
        resize_reset_button = QPushButton("Reset to Default")
        resize_reset_button.setMinimumHeight(35)
        resize_reset_button.setMinimumWidth(140)
        resize_reset_button.setStyleSheet("""
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
        resize_reset_button.clicked.connect(self.reset_resize_settings)
        resize_reset_button.setToolTip("Reset Resize Settings to default values")
        resize_reset_layout = QHBoxLayout()
        resize_reset_layout.addWidget(resize_reset_button)
        resize_reset_layout.addStretch()
        resize_form.addRow("", resize_reset_layout)

        columns_layout.addWidget(resize_group)

        # Column 2: Alignment Settings
        align_group = QGroupBox("Alignment Settings")
        align_form = QFormLayout(align_group)

        # Auto-align Annotations
        self.auto_align_annotations = QCheckBox()
        self.auto_align_annotations.setChecked(True)  # Enabled by default
        self.auto_align_annotations.setToolTip(
            "Automatically align annotations that are close to each other\n\n"
            "When enabled:\n"
            "• Detects annotations nearly aligned horizontally or vertically\n"
            "• Aligns them to a common position\n"
            "• Creates cleaner, more professional appearance\n\n"
            "Useful for: Variable labels, form fields, table annotations"
        )
        self.auto_align_annotations.setWhatsThis(
            "<b>Auto-Align Annotations</b><br><br>"
            "Enable automatic alignment of annotations during standardization. "
            "The system will detect annotations that are almost aligned (within tolerance) "
            "and align them to a common horizontal or vertical position. "
            "This creates a cleaner, more professional appearance."
        )
        align_form.addRow("Auto-Align Annotations:", self.auto_align_annotations)

        # Alignment type checkboxes
        align_type_layout = QHBoxLayout()
        self.align_horizontal = QCheckBox("Horizontal")
        self.align_horizontal.setChecked(True)
        self.align_horizontal.setToolTip(
            "Align annotations horizontally (same top edge)\n"
            "Groups annotations with similar Y-coordinates"
        )
        self.align_vertical = QCheckBox("Vertical")
        self.align_vertical.setChecked(True)
        self.align_vertical.setToolTip(
            "Align annotations vertically (same left edge)\n"
            "Groups annotations with similar X-coordinates"
        )
        align_type_layout.addWidget(self.align_horizontal)
        align_type_layout.addWidget(self.align_vertical)
        align_type_layout.addStretch()
        align_form.addRow("Align Types:", align_type_layout)

        # Horizontal tolerance
        h_tolerance_layout = QHBoxLayout()
        self.horizontal_tolerance = QDoubleSpinBox()
        self.horizontal_tolerance.setRange(1, 50)
        self.horizontal_tolerance.setValue(1.0)
        self.horizontal_tolerance.setSuffix(" pt")
        self.horizontal_tolerance.setMaximumWidth(120)
        self.horizontal_tolerance.setToolTip(
            "Vertical distance tolerance for horizontal alignment\n\n"
            "Default: 1 pt\n"
            "Annotations within this distance (Y-axis) are grouped\n"
            "Lower values: stricter alignment, fewer groups\n"
            "Higher values: more lenient, more groups"
        )
        h_tolerance_layout.addWidget(self.horizontal_tolerance)
        align_form.addRow("Horizontal Tolerance:", h_tolerance_layout)

        # Vertical tolerance
        v_tolerance_layout = QHBoxLayout()
        self.vertical_tolerance = QDoubleSpinBox()
        self.vertical_tolerance.setRange(1, 50)
        self.vertical_tolerance.setValue(10.0)
        self.vertical_tolerance.setSuffix(" pt")
        self.vertical_tolerance.setMaximumWidth(120)
        self.vertical_tolerance.setToolTip(
            "Horizontal distance tolerance for vertical alignment\n\n"
            "Default: 10 pt\n"
            "Annotations within this distance (X-axis) are grouped\n"
            "Lower values: stricter alignment, fewer groups\n"
            "Higher values: more lenient, more groups"
        )
        v_tolerance_layout.addWidget(self.vertical_tolerance)
        align_form.addRow("Vertical Tolerance:", v_tolerance_layout)

        # Align skip pages
        self.align_skip_pages = QLineEdit()
        self.align_skip_pages.setPlaceholderText("e.g., 1, 5, 10")
        self.align_skip_pages.setMaximumWidth(300)
        self.align_skip_pages.setToolTip(
            "Page numbers to skip from auto-alignment\n\n"
            "Format: Comma-separated page numbers (1-indexed)\n"
            "Example: 1, 5, 10\n\n"
            "Useful for pages with complex CRF layouts where\n"
            "auto-alignment may cause layout issues.\n\n"
            "Other standardization (colors, fonts, resize) will still\n"
            "be applied to skipped pages."
        )
        self.align_skip_pages.setWhatsThis(
            "<b>Skip Pages for Auto-Align</b><br><br>"
            "Enter comma-separated page numbers (starting from 1) that should be "
            "skipped during auto-alignment operations. This is useful for pages with "
            "complex CRF layouts where auto-aligning annotations may cause layout issues. "
            "Other standardization features (colors, fonts, resize) will still be "
            "applied to these pages."
        )
        align_form.addRow("Skip Pages:", self.align_skip_pages)

        # Reset button for Alignment Settings
        align_reset_button = QPushButton("Reset to Default")
        align_reset_button.setMinimumHeight(35)
        align_reset_button.setMinimumWidth(140)
        align_reset_button.setStyleSheet("""
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
        align_reset_button.clicked.connect(self.reset_alignment_settings)
        align_reset_button.setToolTip("Reset Alignment Settings to default values")
        align_reset_layout = QHBoxLayout()
        align_reset_layout.addWidget(align_reset_button)
        align_reset_layout.addStretch()
        align_form.addRow("", align_reset_layout)

        columns_layout.addWidget(align_group)

        # Column 3: Color Settings
        color_group = QGroupBox("Color Settings")
        color_form = QFormLayout(color_group)

        # Apply XFDF Colors
        self.apply_xfdf_colors = QCheckBox()
        self.apply_xfdf_colors.setChecked(True)  # Enabled by default
        self.apply_xfdf_colors.setToolTip(
            "Apply standardized colors via XFDF export-import workflow\n\n"
            "When enabled:\n"
            "• Exports annotations to XFDF format after standardization\n"
            "• Applies standardized colors (Blue, Red, Green, etc.)\n"
            "• Imports XFDF back to ensure reliable color rendering\n\n"
            "This ensures colors display correctly in Adobe Acrobat."
        )
        self.apply_xfdf_colors.setWhatsThis(
            "<b>Apply XFDF Colors</b><br><br>"
            "Enable color standardization via XFDF export-import workflow. "
            "After all other standardization steps complete, annotations are exported to XFDF format, "
            "colors are standardized to pure Blue/Red/Green, and then imported back. "
            "This approach ensures that font colors are reliably applied in Adobe Acrobat."
        )
        color_form.addRow("Apply XFDF Colors:", self.apply_xfdf_colors)
        
        # Standard Red Color
        red_color_layout = QHBoxLayout()
        self.red_color_button = QPushButton()
        self.red_color_button.setFixedSize(60, 30)
        self.red_color_button.setToolTip(
            "Click to select the standardized red color\n\n"
            "This color will be used when standardizing red annotations.\n"
            "Default: RGB(255, 0, 0)"
        )
        self.red_color_button.clicked.connect(lambda: self.pick_color("red"))
        self.red_color_rgb_label = QLabel("RGB(255, 0, 0)")
        self.red_color_rgb_label.setMinimumWidth(120)
        red_color_layout.addWidget(self.red_color_button)
        red_color_layout.addWidget(self.red_color_rgb_label)
        red_color_layout.addStretch()
        color_form.addRow("Red Text Color:", red_color_layout)
        
        # Standard Blue Color
        blue_color_layout = QHBoxLayout()
        self.blue_color_button = QPushButton()
        self.blue_color_button.setFixedSize(60, 30)
        self.blue_color_button.setToolTip(
            "Click to select the standardized blue color\n\n"
            "This color will be used when standardizing blue annotations.\n"
            "Default: RGB(0, 0, 255)"
        )
        self.blue_color_button.clicked.connect(lambda: self.pick_color("blue"))
        self.blue_color_rgb_label = QLabel("RGB(0, 0, 255)")
        self.blue_color_rgb_label.setMinimumWidth(120)
        blue_color_layout.addWidget(self.blue_color_button)
        blue_color_layout.addWidget(self.blue_color_rgb_label)
        blue_color_layout.addStretch()
        color_form.addRow("Blue Text Color:", blue_color_layout)
        
        # Standard Green Color
        green_color_layout = QHBoxLayout()
        self.green_color_button = QPushButton()
        self.green_color_button.setFixedSize(60, 30)
        self.green_color_button.setToolTip(
            "Click to select the standardized green color\n\n"
            "This color will be used when standardizing green annotations.\n"
            "Default: RGB(0, 124, 0)"
        )
        self.green_color_button.clicked.connect(lambda: self.pick_color("green"))
        self.green_color_rgb_label = QLabel("RGB(0, 124, 0)")
        self.green_color_rgb_label.setMinimumWidth(120)
        green_color_layout.addWidget(self.green_color_button)
        green_color_layout.addWidget(self.green_color_rgb_label)
        green_color_layout.addStretch()
        color_form.addRow("Green Text Color:", green_color_layout)
        
        # Background Color (for XFDF annotations)
        background_color_layout = QHBoxLayout()
        self.background_color_button = QPushButton()
        self.background_color_button.setFixedSize(60, 30)
        self.background_color_button.setStyleSheet("background-color: rgb(0, 255, 255);")  # Cyan default
        self.background_color_button.setToolTip(
            "Click to select the background color for annotations\n\n"
            "This color will be used as the fill/background color for all annotations.\n"
            "Default: RGB(0, 255, 255) - Cyan"
        )
        self.background_color_button.clicked.connect(lambda: self.pick_color("background"))
        self.background_color_rgb_label = QLabel("RGB(0, 255, 255)")
        self.background_color_rgb_label.setMinimumWidth(120)
        background_color_layout.addWidget(self.background_color_button)
        background_color_layout.addWidget(self.background_color_rgb_label)
        background_color_layout.addStretch()
        color_form.addRow("Background Color:", background_color_layout)
        
        # Textbox Border Color (for XFDF annotations)
        border_color_layout = QHBoxLayout()
        self.border_color_button = QPushButton()
        self.border_color_button.setFixedSize(60, 30)
        self.border_color_button.setStyleSheet("background-color: rgb(0, 0, 0);")  # Black default
        self.border_color_button.setToolTip(
            "Click to select the border color for textbox annotations\n\n"
            "This color will be used as the border/stroke color for all annotations.\n"
            "Default: RGB(0, 0, 0) - Black"
        )
        self.border_color_button.clicked.connect(lambda: self.pick_color("border"))
        self.border_color_rgb_label = QLabel("RGB(0, 0, 0)")
        self.border_color_rgb_label.setMinimumWidth(120)
        border_color_layout.addWidget(self.border_color_button)
        border_color_layout.addWidget(self.border_color_rgb_label)
        border_color_layout.addStretch()
        color_form.addRow("Textbox Border Color:", border_color_layout)

        # Reset button for Color Settings
        color_reset_button = QPushButton("Reset to Default")
        color_reset_button.setMinimumHeight(35)
        color_reset_button.setMinimumWidth(140)
        color_reset_button.setStyleSheet("""
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
        color_reset_button.clicked.connect(self.reset_color_settings)
        color_reset_button.setToolTip("Reset Color Settings to default values")
        color_reset_layout = QHBoxLayout()
        color_reset_layout.addWidget(color_reset_button)
        color_reset_layout.addStretch()
        color_form.addRow("", color_reset_layout)

        columns_layout.addWidget(color_group)

        # Add columns layout to main validation layout
        validation_layout.addLayout(columns_layout)

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

    def pick_color(self, color_type: str):
        """Open color picker dialog and update the selected color."""
        # Get current color from button
        if color_type == "red":
            button = self.red_color_button
            label = self.red_color_rgb_label
            default_rgb = [255, 0, 0]
        elif color_type == "blue":
            button = self.blue_color_button
            label = self.blue_color_rgb_label
            default_rgb = [0, 0, 255]
        elif color_type == "green":
            button = self.green_color_button
            label = self.green_color_rgb_label
            default_rgb = [0, 124, 0]
        elif color_type == "background":
            button = self.background_color_button
            label = self.background_color_rgb_label
            default_rgb = [0, 255, 255]  # Cyan
        elif color_type == "border":
            button = self.border_color_button
            label = self.border_color_rgb_label
            default_rgb = [0, 0, 0]  # Black
        else:
            return
        
        # Extract current RGB values from label text (e.g., "RGB(255, 0, 0)")
        current_rgb = default_rgb
        label_text = label.text()
        try:
            # Parse RGB values from label text
            rgb_str = label_text.replace("RGB(", "").replace(")", "").strip()
            rgb_values = [int(x.strip()) for x in rgb_str.split(",")]
            if len(rgb_values) == 3:
                current_rgb = rgb_values
        except:
            # If parsing fails, use defaults
            pass
        
        # Create QColor from current RGB values
        current_color = QColor(current_rgb[0], current_rgb[1], current_rgb[2])
        
        # Open color picker dialog with current color pre-selected
        color = QColorDialog.getColor(current_color, self, f"Select Standard {color_type.capitalize()} Color")
        
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            # Update button color
            button.setStyleSheet(f"background-color: rgb({r}, {g}, {b});")
            # Update label
            label.setText(f"RGB({r}, {g}, {b})")
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
                config.annotation_patterns["settings"].get("fuzzy_threshold", 0.85))
            self.ignore_domains.setText(
                ",".join(config.validation.get("ignore_domains", [])))
            self.ignore_variables.setText(
                ",".join(config.validation.get("ignore_variables", [])))
            self.generic_author_name.setText(
                config.validation.get("generic_author_name", "Geron"))
            self.form_bookmark_label.setText(
                config.validation.get("form_bookmark_label", "Form_bookmarks"))
            self.sdtm_bookmark_label.setText(
                config.validation.get("sdtm_bookmark_label", "SDTM"))
            self.auto_resize_textboxes.setChecked(
                config.validation.get("auto_resize_textboxes", True))
            self.resize_max_width.setValue(
                config.validation.get("resize_max_width_expansion", 200.0))
            self.resize_max_height.setValue(
                config.validation.get("resize_max_height_expansion", 300.0))
            self.resize_skip_pages.setText(
                config.validation.get("resize_skip_pages", ""))
            
            # Load alignment settings
            self.auto_align_annotations.setChecked(
                config.validation.get("align_annotations", True))
            self.align_horizontal.setChecked(
                config.validation.get("align_horizontal", True))
            self.align_vertical.setChecked(
                config.validation.get("align_vertical", True))
            self.horizontal_tolerance.setValue(
                config.validation.get("horizontal_tolerance", 1.0))
            self.vertical_tolerance.setValue(
                config.validation.get("vertical_tolerance", 10.0))
            self.align_skip_pages.setText(
                config.validation.get("align_skip_pages", ""))
            
            # Load XFDF color setting
            self.apply_xfdf_colors.setChecked(
                config.validation.get("apply_xfdf_colors", True))
            
            # Load normalize quotes setting
            self.normalize_quotes.setChecked(
                config.validation.get("normalize_quotes", True))
            
            # Load color settings with backward compatibility
            red_color = config.validation.get("standard_red_color", [255, 0, 0])
            blue_color = config.validation.get("standard_blue_color", [0, 0, 255])
            green_color = config.validation.get("standard_green_color", [0, 124, 0])
            
            # Ensure colors are lists (handle tuple format from old configs)
            if isinstance(red_color, tuple):
                red_color = list(red_color)
            if isinstance(blue_color, tuple):
                blue_color = list(blue_color)
            if isinstance(green_color, tuple):
                green_color = list(green_color)
            
            # Update red color button and label
            self.red_color_button.setStyleSheet(
                f"background-color: rgb({red_color[0]}, {red_color[1]}, {red_color[2]});")
            self.red_color_rgb_label.setText(f"RGB({red_color[0]}, {red_color[1]}, {red_color[2]})")
            
            # Update blue color button and label
            self.blue_color_button.setStyleSheet(
                f"background-color: rgb({blue_color[0]}, {blue_color[1]}, {blue_color[2]});")
            self.blue_color_rgb_label.setText(f"RGB({blue_color[0]}, {blue_color[1]}, {blue_color[2]})")
            
            # Update green color button and label
            self.green_color_button.setStyleSheet(
                f"background-color: rgb({green_color[0]}, {green_color[1]}, {green_color[2]});")
            self.green_color_rgb_label.setText(f"RGB({green_color[0]}, {green_color[1]}, {green_color[2]})")
            
            # Load background and border colors with backward compatibility
            background_color = config.validation.get("background_color", [0, 255, 255])
            border_color = config.validation.get("textbox_border_color", [0, 0, 0])
            
            # Ensure colors are lists (handle tuple format from old configs)
            if isinstance(background_color, tuple):
                background_color = list(background_color)
            if isinstance(border_color, tuple):
                border_color = list(border_color)
            
            # Update background color button and label
            self.background_color_button.setStyleSheet(
                f"background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]});")
            self.background_color_rgb_label.setText(f"RGB({background_color[0]}, {background_color[1]}, {background_color[2]})")
            
            # Update border color button and label
            self.border_color_button.setStyleSheet(
                f"background-color: rgb({border_color[0]}, {border_color[1]}, {border_color[2]});")
            self.border_color_rgb_label.setText(f"RGB({border_color[0]}, {border_color[1]}, {border_color[2]})")

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

            # Extract color values from RGB labels
            def extract_rgb_from_label(label_text: str) -> list:
                """Extract RGB values from label text like 'RGB(255, 0, 0)'."""
                try:
                    # Remove 'RGB(' and ')' and split by comma
                    rgb_str = label_text.replace("RGB(", "").replace(")", "").strip()
                    rgb_values = [int(x.strip()) for x in rgb_str.split(",")]
                    return rgb_values
                except:
                    # Return defaults if parsing fails
                    if "red" in label_text.lower():
                        return [255, 0, 0]
                    elif "blue" in label_text.lower():
                        return [0, 0, 255]
                    elif "green" in label_text.lower():
                        return [0, 124, 0]
                    elif "background" in label_text.lower():
                        return [0, 255, 255]  # Cyan
                    elif "border" in label_text.lower():
                        return [0, 0, 0]  # Black
                    else:
                        return [255, 0, 0]  # Default to red
            
            red_rgb = extract_rgb_from_label(self.red_color_rgb_label.text())
            blue_rgb = extract_rgb_from_label(self.blue_color_rgb_label.text())
            green_rgb = extract_rgb_from_label(self.green_color_rgb_label.text())
            background_rgb = extract_rgb_from_label(self.background_color_rgb_label.text())
            border_rgb = extract_rgb_from_label(self.border_color_rgb_label.text())
            
            # Collect validation settings
            validation = {
                "ignore_domains": [d.strip() for d in self.ignore_domains.text().split(",") if d.strip()],
                "ignore_variables": [v.strip() for v in self.ignore_variables.text().split(",") if v.strip()],
                "generic_author_name": self.generic_author_name.text().strip() or "Geron",
                "form_bookmark_label": self.form_bookmark_label.text().strip() or "Form_bookmarks",
                "sdtm_bookmark_label": self.sdtm_bookmark_label.text().strip() or "SDTM",
                "auto_resize_textboxes": self.auto_resize_textboxes.isChecked(),
                "resize_max_width_expansion": self.resize_max_width.value(),
                "resize_max_height_expansion": self.resize_max_height.value(),
                "resize_skip_pages": self.resize_skip_pages.text().strip(),
                "align_annotations": self.auto_align_annotations.isChecked(),
                "align_horizontal": self.align_horizontal.isChecked(),
                "align_vertical": self.align_vertical.isChecked(),
                "horizontal_tolerance": self.horizontal_tolerance.value(),
                "vertical_tolerance": self.vertical_tolerance.value(),
                "align_skip_pages": self.align_skip_pages.text().strip(),
                "apply_xfdf_colors": self.apply_xfdf_colors.isChecked(),
                "normalize_quotes": self.normalize_quotes.isChecked(),
                "standard_red_color": red_rgb,
                "standard_blue_color": blue_rgb,
                "standard_green_color": green_rgb,
                "background_color": background_rgb,
                "textbox_border_color": border_rgb
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

    def reset_general_settings(self):
        """Reset General Settings to default values."""
        config = self.config_manager.get_config()
        # Update only general settings
        config.annotation_patterns["settings"]["fuzzy_matching"] = True
        config.annotation_patterns["settings"]["fuzzy_threshold"] = 0.85
        config.validation["ignore_domains"] = []
        config.validation["ignore_variables"] = ["STUDYID", "USUBJID"]
        config.validation["generic_author_name"] = "Geron"
        config.validation["form_bookmark_label"] = "Form_bookmarks"
        config.validation["sdtm_bookmark_label"] = "SDTM"
        # Save and reload
        self.config_manager.update_config({
            "paths": config.paths,
            "annotation_patterns": config.annotation_patterns,
            "validation": config.validation
        })
        self.load_configuration()
        self.config_changed.emit()

    def reset_resize_settings(self):
        """Reset Resize Settings to default values."""
        config = self.config_manager.get_config()
        # Update only resize settings
        config.validation["auto_resize_textboxes"] = True
        config.validation["resize_max_width_expansion"] = 200.0
        config.validation["resize_max_height_expansion"] = 300.0
        config.validation["resize_skip_pages"] = ""
        # Save and reload
        self.config_manager.update_config({
            "paths": config.paths,
            "annotation_patterns": config.annotation_patterns,
            "validation": config.validation
        })
        self.load_configuration()
        self.config_changed.emit()

    def reset_alignment_settings(self):
        """Reset Alignment Settings to default values."""
        config = self.config_manager.get_config()
        # Update only alignment settings
        config.validation["align_annotations"] = True
        config.validation["align_horizontal"] = True
        config.validation["align_vertical"] = True
        config.validation["horizontal_tolerance"] = 1.0
        config.validation["vertical_tolerance"] = 10.0
        config.validation["align_skip_pages"] = ""
        # Save and reload
        self.config_manager.update_config({
            "paths": config.paths,
            "annotation_patterns": config.annotation_patterns,
            "validation": config.validation
        })
        self.load_configuration()
        self.config_changed.emit()

    def reset_color_settings(self):
        """Reset Color Settings to default values."""
        config = self.config_manager.get_config()
        # Update only color settings
        config.validation["apply_xfdf_colors"] = True
        config.validation["normalize_quotes"] = True
        config.validation["standard_red_color"] = [255, 0, 0]
        config.validation["standard_blue_color"] = [0, 0, 255]
        config.validation["standard_green_color"] = [0, 124, 0]
        config.validation["background_color"] = [0, 255, 255]
        config.validation["textbox_border_color"] = [0, 0, 0]
        # Save and reload
        self.config_manager.update_config({
            "paths": config.paths,
            "annotation_patterns": config.annotation_patterns,
            "validation": config.validation
        })
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
