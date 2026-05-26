import fitz  # PyMuPDF
import re
from collections import defaultdict

def extract_form_info(pdf_path):
    """Extract form names and their associated domains from the PDF"""
    doc = fitz.open(pdf_path)

    forms = []  # List of (page_num, form_name, domains)
    current_form = None
    current_domains = set()

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Look for form name pattern: "Form: <form_name>"
        form_match = re.search(r'Form:\s*(.+?)(?:\n|$)', text)
        if form_match:
            form_name = form_match.group(1).strip()

            # Check if this is a NEW form (different name) or same form continuing
            if current_form is None or current_form['name'] != form_name:
                # Save previous form if exists
                if current_form:
                    forms.append((current_form['page'], current_form['name'], list(current_domains)))

                # Start new form
                current_form = {
                    'page': page_num,
                    'name': form_name
                }
                current_domains = set()

        # Look for domain headers in annotations (e.g., "DM=DEMOGRAPHICS")
        # Collect domains even if it's a continuation of the same form
        annot = page.first_annot
        while annot:
            content = annot.info.get('content', '')
            # Check if it matches domain pattern: XX=DOMAIN NAME
            if re.match(r'^[A-Z]{2}\s*=\s*[A-Z\s]+$', content.strip()):
                domain_code = content.split('=')[0].strip()
                current_domains.add(domain_code)
            annot = annot.next

    # Don't forget the last form
    if current_form:
        forms.append((current_form['page'], current_form['name'], list(current_domains)))

    doc.close()
    return forms

def create_bookmarks(input_pdf, output_pdf):
    """Create bookmarks in the PDF"""
    doc = fitz.open(input_pdf)

    # Clear existing bookmarks
    doc.set_toc([])

    # Extract form information
    print("Extracting form and domain information...")
    forms = extract_form_info(input_pdf)

    print(f"\nFound {len(forms)} forms:")
    for page, name, domains in forms:
        print(f"  Page {page + 1}: {name} - Domains: {', '.join(domains) if domains else 'None'}")

    # Build bookmark structure
    toc = []

    # 1. Create "Form_bookmarks" section
    toc.append([1, "Form_bookmarks", 1])  # Level 1, title, page 1

    for page, form_name, domains in forms:
        toc.append([2, form_name, page + 1])  # Level 2, form name, page number (1-indexed)

    # 2. Create "SDTM" section with domain-based bookmarks
    toc.append([1, "SDTM", 1])  # Level 1, title, page 1

    # Group forms by domain
    domain_forms = defaultdict(list)
    for page, form_name, domains in forms:
        for domain in domains:
            domain_forms[domain].append((page, form_name))

    # Sort domains alphabetically
    for domain in sorted(domain_forms.keys()):
        # Add domain as level 2
        toc.append([2, domain, domain_forms[domain][0][0] + 1])  # Link to first form's page

        # Add forms under this domain as level 3
        for page, form_name in domain_forms[domain]:
            toc.append([3, form_name, page + 1])

    # Set the table of contents
    print("\nCreating bookmarks...")
    doc.set_toc(toc)

    # Save the PDF
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()

    print(f"\n{'='*70}")
    print(f"Bookmarks created successfully!")
    print(f"Output saved to: {output_pdf}")
    print(f"{'='*70}")

if __name__ == "__main__":
    input_file = "output/aCRF_standardized_v4.pdf"
    output_file = "output/aCRF_with_bookmarks.pdf"

    create_bookmarks(input_file, output_file)
