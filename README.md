# SDTM Annotation Checker

A Python application with graphical user interface for validating CRF (Case Report Form) annotations against SDTM (Study Data Tabulation Model) datasets.

## Overview

This application extracts annotations from PDF CRFs, parses them to identify SDTM domains and variables, and validates them against actual SDTM datasets (SAS7BDAT files) to identify mismatches and ensure data consistency.

## Features

- Extract annotations from PDF files
- Export annotations to XFDF format
- Parse annotations to identify SDTM domains, variables, and values
- Read and analyze SAS7BDAT files (SDTM datasets)
- Validate annotations against actual SDTM variables
- Generate comprehensive mismatch reports in Excel format
- User-friendly graphical interface

## Project Structure

```
annoSDTMCheck/
├── src/
│   └── sdtm_checker/
│       ├── core/           # Core functionality (PDF processing, XFDF conversion)
│       ├── gui/            # Graphical user interface
│       ├── models/         # Data models and classes
│       ├── utils/          # Utility functions
│       ├── validators/     # Validation logic
│       └── reporters/      # Report generation
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data
├── docs/                  # Documentation
├── config/                # Configuration files
├── scripts/               # Utility scripts
├── archive/               # Archived/deprecated code
└── output/                # Output directory for reports
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd annoSDTMCheck
```

2. Create a virtual environment:
```bash
# On Windows, using 'py' launcher is recommended
py -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.venv\Scripts\activate.bat
# On Unix/MacOS:
source .venv/bin/activate
```

3. Install dependencies:
```bash
# Make sure your virtual environment is activated before running this command.
pip install -r requirements.txt
```

## Usage

### Running the Application

To run the application, simply double-click the `annocheck-gui.exe` file in the `dist` folder, or run:

```bash
py -m sdtm_checker
```

The graphical user interface will open, allowing you to:
1. Select your CRF PDF file
2. Choose the SDTM datasets directory
3. Configure validation settings
4. Run the validation
5. View and export the results

## Development Status

This project is currently under active development. See [docs/TODO.md](docs/TODO.md) for the current task list and [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the development timeline.

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

[Add license information here]

## Contact

[Add contact information here] 