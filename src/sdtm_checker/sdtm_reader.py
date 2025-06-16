from dataclasses import dataclass
from typing import Dict, List, Optional, Any

import logging
from pathlib import Path
import pandas as pd
import pyreadstat
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class VariableMetadata:
    """Metadata for a SDTM variable."""
    name: str
    type: str  # 'numeric' or 'character'
    length: int
    label: str
    format: Optional[str] = None
    informat: Optional[str] = None


class SDTMError(Exception):
    """Base exception for SDTM dataset errors."""


class SDTMFileError(SDTMError):
    """Raised when there are issues with the SDTM file."""


class SDTMDataset:
    """Class to handle SDTM dataset operations."""

    def __init__(self, file_path: str):
        """
        Initialize SDTM dataset from a SAS7BDAT file.

        Args:
            file_path: Path to the SAS7BDAT file

        Raises:
            SDTMFileError: If file cannot be read or is invalid
        """
        self.file_path = Path(file_path)
        self.domain_name = self.file_path.stem.upper()
        self.variables: Dict[str, VariableMetadata] = {}
        self._df: Optional[pd.DataFrame] = None
        self.label: Optional[str] = None
        self._load_metadata()

    @property
    def df(self) -> pd.DataFrame:
        """The dataset's DataFrame, loaded on demand."""
        if self._df is None:
            self._load_data()
        return self._df

    def _load_metadata(self) -> None:
        """Load the dataset's metadata without loading the full data."""
        try:
            # Read only the metadata
            _, meta = pyreadstat.read_sas7bdat(
                self.file_path,
                metadataonly=True
            )

            self.label = getattr(meta, 'file_label', None)

            # Use pyreadstat's current metadata attributes
            col_names = getattr(meta, 'column_names', [])
            col_labels = getattr(meta, 'column_labels', [])
            col_types = getattr(meta, 'column_types', {})
            col_lengths = getattr(meta, 'column_storage_lengths', {})
            col_formats = getattr(meta, 'column_formats', {})
            col_informats = getattr(meta, 'column_informats', {})

            for idx, var_name in enumerate(col_names):
                original_var_name = var_name
                var_label = col_labels[idx] if idx < len(col_labels) else ''
                var_type = 'numeric' if col_types.get(
                    original_var_name) == 'numeric' else 'character'
                var_length = col_lengths.get(original_var_name, 0)
                var_format = col_formats.get(original_var_name)
                var_informat = col_informats.get(original_var_name)

                self.variables[var_name] = VariableMetadata(
                    name=var_name,
                    type=var_type,
                    length=var_length,
                    label=var_label,
                    format=var_format,
                    informat=var_informat
                )

            logger.info(
                f"Loaded metadata for {self.domain_name} with {len(self.variables)} variables")

        except Exception as e:
            raise SDTMFileError(
                f"Error loading metadata for {self.file_path}: {str(e)}")

    def _load_data(self) -> None:
        """Load the full dataset into a pandas DataFrame."""
        try:
            df, _ = pyreadstat.read_sas7bdat(
                self.file_path,
                metadataonly=False,
                dates_as_pandas_datetime=True
            )
            self._df = df

        except Exception as e:
            raise SDTMFileError(
                f"Error loading data for {self.file_path}: {str(e)}")

    def get_variable_list(self) -> List[str]:
        """Get list of variable names in the dataset."""
        return list(self.variables.keys())

    def get_variable_metadata(self, var_name: str) -> Optional[VariableMetadata]:
        """Get metadata for a specific variable."""
        return self.variables.get(var_name)

    def validate_variable(self, var_name: str) -> bool:
        """Check if a variable exists in the dataset."""
        return var_name in self.variables

    def get_domain_name(self) -> str:
        """Get the domain name of the dataset."""
        return self.domain_name

    def get_sample_data(self, var_name: str, n: int = 5) -> List[Any]:
        """Get sample values for a variable."""
        if not self.validate_variable(var_name):
            return []
        return self.df[var_name].head(n).tolist()


class SDTMDatasetManager:
    """Manager class for handling multiple SDTM datasets."""

    def __init__(self, sdtm_dir: str):
        """
        Initialize the SDTM dataset manager.

        Args:
            sdtm_dir: Directory containing SDTM datasets
        """
        self.sdtm_dir = Path(sdtm_dir)
        self.datasets: Dict[str, SDTMDataset] = {}
        self.dataset_paths: Dict[str, Path] = {}
        self._scan_for_datasets()

    def _scan_for_datasets(self) -> None:
        """Scan for all SDTM datasets in the directory and store their paths."""
        try:
            for file_path in self.sdtm_dir.glob("*.sas7bdat"):
                domain_name = file_path.stem.upper()
                self.dataset_paths[domain_name] = file_path
            logger.info(f"Found {len(self.dataset_paths)} SDTM datasets")
        except Exception as e:
            logger.error(f"Error scanning SDTM directory: {str(e)}")

    @lru_cache(maxsize=100)
    def get_dataset(self, domain_name: str) -> Optional[SDTMDataset]:
        """Get a specific dataset by domain name, loading it if necessary."""
        domain_name = domain_name.upper()
        if domain_name in self.datasets:
            return self.datasets[domain_name]

        if domain_name in self.dataset_paths:
            try:
                dataset = SDTMDataset(str(self.dataset_paths[domain_name]))
                self.datasets[domain_name] = dataset
                return dataset
            except SDTMFileError as e:
                logger.error(
                    f"Error loading dataset {self.dataset_paths[domain_name]}: {str(e)}")
                return None

        return self.datasets.get(domain_name)

    def get_all_domains(self) -> List[str]:
        """Get list of all domain names."""
        return list(self.dataset_paths.keys())

    def validate_domain_variable(self, domain: str, variable: str) -> bool:
        """
        Validate if a variable exists in a domain.

        Args:
            domain: Domain name
            variable: Variable name

        Returns:
            bool: True if variable exists in domain
        """
        dataset = self.get_dataset(domain)
        return dataset is not None and dataset.validate_variable(variable)

    def get_variable_metadata(self, domain: str, variable: str) -> Optional[VariableMetadata]:
        """Get metadata for a variable in a domain."""
        dataset = self.get_dataset(domain)
        if dataset:
            return dataset.get_variable_metadata(variable)
        return None

    def refresh_datasets(self) -> None:
        """Reload all datasets from disk."""
        self.datasets.clear()
        self.dataset_paths.clear()
        self._scan_for_datasets()
        # Clear the LRU cache
        self.get_dataset.cache_clear()

    def get_dm_variables(self) -> List[str]:
        """Get list of variables in the DM domain."""
        dm_dataset = self.get_dataset("DM")
        return dm_dataset.get_variable_list() if dm_dataset else []
