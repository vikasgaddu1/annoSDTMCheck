"""Test Arial vs Helvetica font names in PyMuPDF."""
import fitz

print("Testing different font name variations:")
print("=" * 60)

# Test various font names for text_length (indication they're recognized)
test_fonts = [
    "helv", "hebo", "heit", "hebi",
    "Arial", "arial", 
    "Arial-Bold", "Arial-Italic", "Arial-BoldItalic",
    "arbo", "arit", "arbi"  # Possible Arial abbreviations
]

test_text = "Test123"
for fontname in test_fonts:
    try:
        length = fitz.get_text_length(test_text, fontname=fontname, fontsize=10)
        print(f"✓ {fontname:25s} works (length={length:.2f})")
    except Exception as e:
        print(f"✗ {fontname:25s} ERROR: {str(e)[:50]}")

print("=" * 60)
print("\nTesting annotation update compatibility:")
print("-" * 60)

# Create a test PDF to see which font names work in annot.update()
doc = fitz.open()
page = doc.new_page()

test_fonts_for_annot = ["helv", "hebi", "Arial", "Arial-BoldItalic"]
y_pos = 50

for fontname in test_fonts_for_annot:
    try:
        rect = fitz.Rect(50, y_pos, 200, y_pos + 30)
        annot = page.add_freetext_annot(rect, f"Font: {fontname}", fontsize=10)
        annot.update(fontname=fontname, fontsize=10)
        print(f"✓ {fontname:25s} works in annot.update()")
        y_pos += 40
    except Exception as e:
        print(f"✗ {fontname:25s} ERROR: {str(e)[:50]}")

doc.close()
print("=" * 60)


