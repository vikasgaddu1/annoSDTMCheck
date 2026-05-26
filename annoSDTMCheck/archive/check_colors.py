import fitz

# Check original annotation colors
doc = fitz.open('input/aCRF.pdf')

# Check page 136 (index 135) for FA annotations
page = doc[135]
annots = list(page.annots())

print(f"Page 136 has {len(annots)} annotations")
print("-" * 50)

for i, annot in enumerate(annots[:10]):
    if annot:
        info = annot.info
        colors = annot.colors
        da = info.get("DA", "")
        content = info.get("content", "")[:30]
        
        print(f"Annotation {i+1}:")
        print(f"  Content: {content}")
        print(f"  Colors: {colors}")
        print(f"  DA string: {da}")
        print()

doc.close()

# Also check page 1 for comparison
print("\n" + "=" * 50)
print("Page 2 (CM annotations):")
print("-" * 50)
doc = fitz.open('input/aCRF.pdf')
page = doc[1]
annots = list(page.annots())
print(f"Page 2 has {len(annots)} annotations")

for i, annot in enumerate(annots[:5]):
    if annot:
        info = annot.info
        colors = annot.colors
        da = info.get("DA", "")
        content = info.get("content", "")[:30]
        
        print(f"Annotation {i+1}:")
        print(f"  Content: {content}")
        print(f"  Colors: {colors}")
        print(f"  DA string: {da}")
        print()

doc.close()

