"""Setup configuration for SDTM Annotation Checker."""

from setuptools import setup, find_packages

setup(
    name="sdtm_checker",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.1.0",
        "pandas>=1.5.0",
        "pyreadstat>=1.2.0",
        "openpyxl>=3.1.0",
        "PyMuPDF>=1.22.0",
        "PyYAML>=6.0",
        "rich>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest==8.0.0",
            "black==24.1.1",
            "flake8==7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Removed CLI entry point
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for validating SDTM annotations in PDF files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sdtm_checker",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
) 