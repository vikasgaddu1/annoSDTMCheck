"""
Example script to demonstrate SDTM dataset reading functionality with debug output.
"""

from sdtm_checker.sdtm_reader import SDTMDatasetManager, SDTMFileError
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))


def main():
    print("[DEBUG] Script started.")
    # Initialize the SDTM dataset manager
    sdtm_dir = Path("sdtm")
    if not sdtm_dir.exists():
        print(f"[ERROR] SDTM directory not found: {sdtm_dir.resolve()}")
        return
    print(f"[DEBUG] SDTM directory found: {sdtm_dir.resolve()}")
    try:
        manager = SDTMDatasetManager(str(sdtm_dir))
    except Exception as e:
        print(f"[ERROR] Failed to initialize SDTMDatasetManager: {e}")
        return

    # Get list of all domains
    domains = manager.get_all_domains()
    print(f"\nFound {len(domains)} SDTM domains:")
    for domain in sorted(domains):
        print(f"- {domain}")
    if not domains:
        print(
            "[ERROR] No SDTM domains found. Check if .sas7bdat files are present and readable.")
        return

    # Example: Get detailed information about the DM domain
    print("\nDetailed information for DM domain:")
    try:
        dm_dataset = manager.get_dataset("DM")
        if dm_dataset:
            print(f"Number of variables: {len(dm_dataset.variables)}")
            print("\nVariables in DM:")
            for var_name, var_meta in dm_dataset.variables.items():
                print(
                    f"- {var_name}: {var_meta.type} ({var_meta.length}) - {var_meta.label}")
        else:
            print("[WARNING] DM domain not found.")
    except SDTMFileError as e:
        print(f"[ERROR] Failed to load DM domain: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error loading DM domain: {e}")

    # Example: Get detailed information about the LB domain
    print("\nDetailed information for LB domain:")
    try:
        lb_dataset = manager.get_dataset("LB")
        if lb_dataset:
            print(f"Number of variables: {len(lb_dataset.variables)}")
            print("\nVariables in LB:")
            for var_name, var_meta in lb_dataset.variables.items():
                print(
                    f"- {var_name}: {var_meta.type} ({var_meta.length}) - {var_meta.label}")
        else:
            print("[WARNING] LB domain not found.")
    except SDTMFileError as e:
        print(f"[ERROR] Failed to load LB domain: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error loading LB domain: {e}")

    # Example: Validate some domain-variable combinations
    print("\nValidating domain-variable combinations:")
    test_cases = [
        ("DM", "SUBJID"),
        ("DM", "AGE"),
        ("LB", "LBTEST"),
        ("LB", "LBORRES"),
        ("AE", "AETERM"),
        ("VS", "VSTEST")
    ]

    for domain, variable in test_cases:
        try:
            is_valid = manager.validate_domain_variable(domain, variable)
            print(
                f"- {domain}.{variable}: {'✓ Valid' if is_valid else '✗ Invalid'}")
        except Exception as e:
            print(f"[ERROR] Validation failed for {domain}.{variable}: {e}")

    # Example: Get variable metadata
    print("\nVariable metadata examples:")
    for domain, variable in test_cases:
        try:
            metadata = manager.get_variable_metadata(domain, variable)
            if metadata:
                print(f"- {domain}.{variable}:")
                print(f"  Type: {metadata.type}")
                print(f"  Length: {metadata.length}")
                print(f"  Label: {metadata.label}")
                if metadata.format:
                    print(f"  Format: {metadata.format}")
                if metadata.informat:
                    print(f"  Informat: {metadata.informat}")
            else:
                print(f"[WARNING] No metadata found for {domain}.{variable}")
        except Exception as e:
            print(
                f"[ERROR] Failed to get metadata for {domain}.{variable}: {e}")


if __name__ == "__main__":
    main()
