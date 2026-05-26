# SDTM Annotation Checker - TODO List

## Project Status
This document tracks pending tasks, improvements, and known issues for the SDTM Annotation Checker project.

## Legend
- [x] Completed
- [ ] Pending
- [~] In Progress
- [!] High Priority
- [-] Removed/Deprecated

## Core Features

### Annotation Processing
- [x] Extract annotations from PDF files
- [x] Export annotations to XFDF format (~~Command-line~~ removed: integrated into GUI)
- [x] Parse SDTM domain/variable patterns
- [x] Support multiple annotation formats (DOMAIN.VAR, DOMAIN-VAR, etc.)
- [ ] Support for multi-page annotation relationships
- [ ] Handle nested/complex annotations

### SDTM Validation
- [x] Read SAS7BDAT files using pyreadstat
- [x] Validate annotations against SDTM datasets
- [x] Identify mismatches and missing variables
- [ ] Support for SUPPQUAL domains
- [ ] Cross-domain relationship validation

### Reporting
- [x] Generate Excel reports with multiple sheets
- [x] Summary statistics
- [x] Detailed validation results
- [ ] PDF report generation
- [ ] Customizable report templates
- [ ] Interactive HTML reports

## User Interface

### GUI Features (Primary Interface)
- [x] Main window with tabs (Configuration, Validation)
- [x] Configuration management (load/save/edit)
- [x] File selection dialogs
- [x] Progress bars and status updates
- [x] Results preview
- [ ] Dark mode support
- [ ] Batch processing interface
- [ ] Results filtering and sorting

### Usability Improvements
- [ ] Drag-and-drop file selection
- [ ] Recent files menu
- [ ] Keyboard shortcuts
- [ ] Context-sensitive help
- [ ] Undo/redo for configuration changes

## Technical Improvements

### Performance
- [ ] Parallel processing for large datasets
- [ ] Memory optimization for large PDFs
- [ ] Caching mechanism for repeated validations
- [ ] Progress estimation accuracy

### Error Handling
- [x] Basic error handling and logging
- [ ] Detailed error messages with solutions
- [ ] Recovery from partial failures
- [ ] Validation warnings vs errors distinction

### Testing
- [x] Basic unit tests
- [ ] Integration tests
- [ ] GUI tests using pytest-qt
- [ ] Performance benchmarks
- [ ] Test coverage > 80%

## Configuration & Flexibility

### Pattern Management
- [x] YAML-based configuration
- [x] Custom regex patterns
- [x] Pattern testing interface
- [ ] Pattern library/templates
- [ ] Import patterns from Define.xml

### Validation Rules
- [x] Ignore specific domains/variables
- [x] Fuzzy matching with threshold
- [ ] Custom validation rules
- [ ] Rule priority/severity levels
- [ ] Conditional rules based on study type

## Data Format Support

### Input Formats
- [x] PDF annotations
- [x] SAS7BDAT datasets
- [ ] XPT (SAS transport) files
- [ ] CSV/Excel as SDTM source
- [ ] Define.xml validation

### Output Formats
- [x] Excel reports
- [x] XFDF annotation export
- [ ] JSON export
- [ ] Define.xml generation
- [ ] REDCap data dictionary

## Integration & Deployment

### Distribution
- [x] Windows executable (.exe)
- [x] Source distribution
- [ ] macOS app bundle
- [ ] Linux AppImage/snap
- [ ] Web-based version

### Integration
- [ ] REST API for external tools
- [ ] Integration with SAS environments
- [ ] Integration with EDC systems
- [ ] Plugin architecture

## Documentation

### User Documentation
- [x] README with quick start
- [x] Comprehensive user guide
- [x] FAQ section
- [ ] Video tutorials
- [ ] Sample datasets and workflows

### Technical Documentation
- [x] Code structure documentation
- [ ] API documentation
- [ ] Developer guide
- [ ] Architecture diagrams

## Security & Compliance

### Security Features
- [x] Path traversal prevention
- [x] Input validation
- [ ] Audit trail/logging
- [ ] User authentication (for web version)
- [ ] Data encryption at rest

### Compliance
- [ ] 21 CFR Part 11 compliance features
- [ ] GDPR compliance for EU data
- [ ] Validation documentation for regulatory submission

## Future Enhancements

### Advanced Features
- [ ] Machine learning for pattern recognition
- [ ] Automatic annotation suggestion
- [ ] Historical validation comparison
- [ ] Multi-study validation dashboard
- [ ] Real-time collaboration features

### Domain-Specific Features
- [ ] ADaM dataset validation
- [ ] Protocol deviation checking
- [ ] Data review workflow management
- [ ] Integration with clinical metadata repository

## Bug Fixes & Known Issues

### Current Issues
- [ ] Large PDF files (>100MB) may cause memory issues
- [ ] Some Unicode characters in annotations not properly handled
- [ ] Fuzzy matching performance on large datasets

### Resolved Issues
- [x] PyQt6 compatibility issues
- [x] Configuration file path handling on Windows
- [x] XFDF export encoding issues

## Maintenance & Optimization

### Code Quality
- [ ] Refactor validation engine for better modularity
- [ ] Improve error message consistency
- [ ] Remove deprecated code
- [ ] Optimize import statements

### Dependencies
- [ ] Update to latest pandas version
- [ ] Evaluate alternative PDF libraries
- [ ] Review and minimize dependencies

## Notes
- Priority should be given to items marked with [!]
- Items marked [-] have been removed or are no longer applicable
- This list is updated regularly based on user feedback and development progress

Last Updated: [Current Date] 