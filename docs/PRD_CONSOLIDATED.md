# Product Requirements Document (PRD) - SDTM Annotation Checker
## Version 2.0 - Consolidated

### 1. Executive Summary
The SDTM Annotation Checker is a comprehensive Python application designed to validate CRF (Case Report Form) annotations against SDTM (Study Data Tabulation Model) datasets. The tool provides a user-friendly graphical interface for extracting, parsing, and validating annotations to ensure data consistency and regulatory compliance in clinical trials.

### 2. Problem Statement
Clinical data managers manually annotate CRF PDFs with SDTM domain and variable information. Manual processes are error-prone and there's no automated way to verify that these annotations correctly correspond to actual SDTM datasets. This leads to:
- Data inconsistencies between CRFs and SDTM datasets
- Quality issues in regulatory submissions
- Time-consuming manual verification processes
- Risk of missing critical data mapping errors

### 3. Solution Overview
A comprehensive automated application that:
- Extracts annotations from PDF CRFs using advanced PDF processing
- Parses annotation content using configurable patterns and fuzzy matching
- Validates annotations against actual SDTM datasets (SAS7BDAT files)
- Provides an intuitive graphical user interface for ease of use
- Generates comprehensive validation reports in multiple formats
- Offers flexible configuration management for different study requirements

### 4. Target Users
- **Primary Users**: Clinical Data Managers, SDTM Programmers
- **Secondary Users**: Data Quality Assurance Teams, Clinical Trial Coordinators
- **Tertiary Users**: Regulatory Affairs Personnel, Clinical Data Scientists

### 5. Functional Requirements

#### 5.1 PDF Annotation Extraction
- **FR-001**: Extract all text annotations from PDF files using PyMuPDF
- **FR-003**: Export annotations to XFDF format for archival and sharing
- **FR-004**: Export annotations to Excel format for analysis
- **FR-005**: Handle various PDF annotation types (text, highlights, comments)
- **FR-006**: Preserve annotation metadata (page numbers, positions, timestamps)

#### 5.2 Dynamic Annotation Parsing
- **FR-007**: Parse annotation content using configurable regex patterns
- **FR-008**: Support multiple annotation formats:
  - Domain.Variable (e.g., DM.SUBJID)
  - Domain-Variable (e.g., DM-SUBJID)
  - Variable only (e.g., SUBJID)
  - Custom patterns via configuration
- **FR-009**: Fuzzy matching for annotations with typos or variations
- **FR-010**: Configurable fuzzy matching threshold
- **FR-011**: Handle complex annotations with conditions and suppxx variables
- **FR-012**: Parse relative record (RELREC) annotations

#### 5.3 SDTM Dataset Integration
- **FR-013**: Read SAS7BDAT files (SDTM datasets) using pyreadstat
- **FR-014**: Extract comprehensive variable metadata including:
  - Variable names, types, lengths, labels
  - Dataset structure and relationships
  - Domain-specific characteristics
- **FR-015**: Support for all standard SDTM domains
- **FR-016**: Handle supplemental (SUPP--) datasets
- **FR-017**: Manage DM domain variables for subject identification

#### 5.4 Comprehensive Validation Engine
- **FR-018**: Multi-level validation including:
  - Domain existence validation
  - Variable existence validation
  - Condition-based validation
  - Supplemental variable validation
  - Relative record validation
- **FR-019**: Configurable validation rules and thresholds
- **FR-020**: Support for ignored domains and variables
- **FR-021**: Severity-based validation results (ERROR, WARNING, INFO)
- **FR-022**: Detailed validation messaging with actionable recommendations

#### 5.5 Advanced Reporting
- **FR-023**: Generate comprehensive Excel reports with:
  - Summary statistics dashboard
  - Detailed validation results
  - Annotation inventory
  - Mismatch analysis
- **FR-024**: Multiple report formats (Excel, CSV, HTML)
- **FR-025**: Interactive report sections with filtering and sorting
- **FR-026**: Visual indicators for different validation severities
- **FR-027**: Export capabilities for further analysis

#### 5.6 Configuration Management System
- **FR-028**: YAML-based configuration with validation
- **FR-029**: Configurable file paths and directories
- **FR-030**: Custom annotation pattern management
- **FR-031**: Validation rule customization
- **FR-032**: Configuration templates and sharing
- **FR-033**: GUI-based configuration editor
- **FR-034**: Configuration validation and error reporting

#### 5.7 User Interface
- **FR-035**: Graphical user interface with:
  - Intuitive file selection dialogs
  - Visual configuration management
  - Real-time validation progress monitoring
  - Interactive results visualization
  - Tab-based organization for different functions
- **FR-036**: Rich visual feedback with progress indicators
- **FR-037**: Comprehensive help and documentation
- **FR-038**: Context-sensitive tooltips and guidance

#### 5.8 Security and Safety
- **FR-039**: Path validation to prevent directory traversal
- **FR-040**: File operation security with permission checks
- **FR-041**: Encryption support for sensitive data
- **FR-042**: Secure file handling and cleanup
- **FR-043**: Access logging and audit trails

### 6. Non-Functional Requirements

#### 6.1 Performance
- **NFR-001**: Process 100-page PDFs in under 30 seconds
- **NFR-002**: Handle SDTM datasets up to 1GB efficiently
- **NFR-003**: Memory-efficient processing for large datasets
- **NFR-004**: Responsive UI with non-blocking operations

#### 6.2 Usability
- **NFR-005**: Intuitive GUI with modern design principles
- **NFR-006**: Clear, actionable error messages
- **NFR-007**: Comprehensive logging with configurable levels
- **NFR-008**: Context-sensitive help and tooltips
- **NFR-009**: Keyboard shortcuts and accessibility features

#### 6.3 Reliability
- **NFR-010**: Graceful error handling and recovery
- **NFR-012**: Data integrity validation
- **NFR-013**: Automatic backup and recovery mechanisms

#### 6.4 Compatibility
- **NFR-014**: Cross-platform support (Windows, macOS, Linux)
- **NFR-015**: Python 3.8+ compatibility
- **NFR-016**: Multiple PDF library support
- **NFR-017**: SAS transport file compatibility

#### 6.5 Maintainability
- **NFR-018**: Modular architecture with clear separation of concerns
- **NFR-019**: Comprehensive unit and integration tests
- **NFR-020**: Detailed API documentation
- **NFR-021**: Extensible validator and reporter framework

### 7. Technical Architecture

#### 7.1 Core Components
- **AnnotationExtractor**: PDF processing and annotation extraction
- **DynamicAnnotationParser**: Configurable annotation parsing
- **SDTMDatasetManager**: SDTM dataset reading and management
- **ValidationEngine**: Multi-level validation orchestration
- **ReportGenerator**: Comprehensive report generation
- **ConfigurationManager**: Configuration handling and validation

#### 7.2 Validation Framework
- **BaseValidator**: Abstract validator interface
- **DomainValidator**: Domain-level validation
- **VariableValidator**: Variable-level validation
- **ConditionValidator**: Conditional logic validation
- **SuppxxValidator**: Supplemental dataset validation
- **RelrecValidator**: Relative record validation

#### 7.3 Technology Stack
- **Language**: Python 3.8+
- **PDF Processing**: PyMuPDF (fitz)
- **Data Processing**: pandas, numpy
- **Excel Processing**: openpyxl
- **SAS Files**: pyreadstat
- **GUI Framework**: PyQt6
- **Configuration**: PyYAML
- **Logging**: Python logging framework

### 8. User Experience Design

#### 8.1 Graphical User Interface
The application features a modern, tab-based interface with:
- **Configuration Tab**: Manage annotation patterns, validation rules, and file paths
- **Validation Tab**: Select files, run validation, and view results
- **Results Display**: Interactive viewing of validation results with filtering
- **Progress Monitoring**: Real-time updates during processing

#### 8.2 Configuration Examples
```yaml
# paths configuration
paths:
  pdf_directory: "crf/"
  sdtm_directory: "sdtm_data/"
  output_directory: "output/"

# annotation patterns
annotation_patterns:
  patterns:
    - name: "DOMAIN_VAR"
      regex: "^([A-Z]{2})\.([A-Z0-9_]+)$"
      groups:
        domain: 1
        variable: 2
  settings:
    fuzzy_matching: true
    fuzzy_threshold: 0.85

# validation settings
validation:
  ignore_domains: ["RELREC"]
  ignore_variables: ["STUDYID", "USUBJID"]
```

### 9. Implementation Status

#### 9.1 Completed Features
- ✅ PDF annotation extraction (PyMuPDF)
- ✅ XFDF and Excel export capabilities
- ✅ Dynamic annotation parsing with fuzzy matching
- ✅ SDTM dataset reading (SAS7BDAT)
- ✅ Multi-level validation engine
- ✅ Comprehensive Excel report generation
- ✅ Configuration management system
- ✅ Graphical user interface with PyQt6
- ✅ Security and path validation

#### 9.2 Architecture Highlights
- **Modular Design**: Clean separation between extraction, parsing, validation, and reporting
- **Configurable Validation**: Extensible validator framework
- **User-Friendly Interface**: Intuitive GUI for all user levels
- **Security First**: Built-in security features and safe file handling
- **Performance Optimized**: Efficient memory usage and processing

### 10. Success Metrics
- **Accuracy**: >95% annotation extraction accuracy
- **Detection**: 100% validation rule coverage
- **Performance**: <1 minute processing for typical CRFs
- **Reliability**: Zero data corruption incidents
- **Usability**: <5 minutes for new user onboarding

### 11. Future Enhancements
- Enhanced web-based GUI interface
- CDISC Library API integration
- Machine learning for annotation pattern recognition
- Cloud-based processing capabilities
- Multi-user collaboration features
- ODM and Define.xml validation support
- Real-time validation during annotation
- Advanced analytics and predictive quality metrics

### 12. Risk Mitigation
- **PDF Compatibility**: Robust PyMuPDF integration handles various formats
- **Performance**: Efficient algorithms and memory management
- **Data Security**: Comprehensive security framework with encryption
- **User Adoption**: Intuitive GUI design for ease of use

### 13. Conclusion
The SDTM Annotation Checker represents a comprehensive solution for clinical data validation, providing the functionality and flexibility needed for modern clinical trial operations. With its robust architecture, comprehensive feature set, and user-friendly graphical interface, it addresses the critical need for automated annotation validation in clinical research.

The application successfully bridges the gap between manual annotation processes and automated validation, providing clinical data professionals with the tools needed to ensure data quality and regulatory compliance while significantly reducing manual effort and error rates. 