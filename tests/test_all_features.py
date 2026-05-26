"""Test all features together."""
from src.sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer, 
    StandardizationConfig
)

# Configure with all features enabled
config = StandardizationConfig(
    use_domain_colors=True,       # Use domain-based colors
    align_annotations=True,        # Enable alignment
    align_horizontal=True,
    align_vertical=True,
    standardize_font_size=True,
    standardize_font_type=True,
    auto_resize_textboxes=False   # Keep this off for now
)

standardizer = AnnotationStandardizer(config)
stats = standardizer.standardize_pdf('input/aCRF.pdf', 'output/aCRF_all_features_final.pdf')

print("\n=== All Features Test Results ===")
print(f"Annotations processed: {stats.get('annotations_processed', 0)}")
print(f"Annotations modified: {stats.get('annotations_modified', 0)}")
print(f"Red annotations (FA/AE/DS/DD/MH): {stats.get('red_annotations', 0)}")
print(f"Blue annotations (other domains): {stats.get('blue_annotations', 0)}")
print(f"Horizontally aligned: {stats.get('annotations_aligned_horizontal', 0)}")
print(f"Vertically aligned: {stats.get('annotations_aligned_vertical', 0)}")
print(f"Headers found: {stats.get('headers_found', 0)}")
print(f"Bookmarks created: {stats.get('bookmarks_created', 0)}")
