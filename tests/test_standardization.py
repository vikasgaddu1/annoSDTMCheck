#!/usr/bin/env python3
"""Test the actual standardization process"""
import sys
sys.path.insert(0, 'src')

from sdtm_checker.core.annotation_standardizer import AnnotationStandardizer
from sdtm_checker.config_manager import ConfigManager
import fitz

# Run standardization
config = ConfigManager()
standardizer = AnnotationStstandardizer(config)

input_pdf = "tests/incorrect.pdf"
output_pdf = "tests/output_test.pdf"

print(f"\n=== Standardizing {input_pdf} ===\n")

result = standardizer.standardize_pdf(input_pdf, output_pdf)

print(f"\nStandardization complete!")
print(f"Stats: {result}\n")

# Now inspect the output to see what colors were actually written
print("=== Inspecting OUTPUT PDF ===\n")

doc = fitz.open(output_pdf)

for page_num in range(len(doc)):
    page = doc[page_num]
    annot = page.first_annot
    annot_num = 0
    
    while annot:
        annot_num += 1
        
        if annot.type[0] == 2:  # FreeText
            content = annot.info.get('content', '')[:60]
            da = annot.info.get('DA', '')
            
            # Extract color from DA
            import re
            color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
            if color_match:
                r = float(color_match.group(1))
                g = float(color_match.group(2))
                b = float(color_match.group(3))
                rgb_255 = (int(r*255), int(g*255), int(b*255))
                
                print(f"Annotation #{annot_num}: {content}")
                print(f"  DA string: {da}")
                print(f"  Text color in output: RGB{rgb_255}")
                print()
        
        annot = annot.next

doc.close()
print(f"\nOutput saved to: {output_pdf}")

