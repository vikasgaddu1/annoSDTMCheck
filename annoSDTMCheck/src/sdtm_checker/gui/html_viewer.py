"""
HTML Viewer utility for displaying documentation in a browser.

This module converts markdown documentation to HTML and opens it in the user's default browser,
ensuring everyone can view the documentation regardless of whether they have a markdown editor.
"""

import os
import sys
import webbrowser
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# Minimal markdown to HTML conversion (no external dependencies)
def markdown_to_html(markdown_text: str, title: str = "Documentation") -> str:
    """
    Convert markdown text to HTML with basic styling.
    
    This is a simple conversion that handles common markdown elements:
    - Headers (# ## ###)
    - Bold (**text** or __text__)
    - Italic (*text* or _text_)
    - Code blocks (```language)
    - Inline code (`code`)
    - Lists (- or * or numbered)
    - Links [text](url)
    - Horizontal rules (---)
    
    Args:
        markdown_text: The markdown content to convert
        title: The HTML page title
    
    Returns:
        Complete HTML document as a string
    """
    import re
    
    html_body = markdown_text
    
    # Escape HTML entities first
    # html_body = html_body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Code blocks (must be done before inline code)
    def replace_code_block(match):
        code = match.group(2).strip()
        lang = match.group(1) if match.group(1) else ""
        # Escape HTML in code blocks
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'\n<pre><code class="language-{lang}">{code}</code></pre>\n'
    
    html_body = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, html_body, flags=re.DOTALL)
    
    # Inline code
    html_body = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_body)
    
    # Headers
    html_body = re.sub(r'^######\s+(.+)$', r'<h6>\1</h6>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^#####\s+(.+)$', r'<h5>\1</h5>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
    
    # Bold
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html_body)
    
    # Italic
    html_body = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_body)
    html_body = re.sub(r'_(.+?)_', r'<em>\1</em>', html_body)
    
    # Links
    html_body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_body)
    
    # Horizontal rules
    html_body = re.sub(r'^---+$', r'<hr>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^\*\*\*+$', r'<hr>', html_body, flags=re.MULTILINE)
    
    # Process lists and paragraphs line by line
    lines = html_body.split('\n')
    processed_lines = []
    in_ul = False
    in_ol = False
    in_paragraph = False
    current_paragraph = []
    
    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            processed_lines.append('</ul>')
            in_ul = False
        if in_ol:
            processed_lines.append('</ol>')
            in_ol = False
    
    def close_paragraph():
        nonlocal in_paragraph, current_paragraph
        if in_paragraph and current_paragraph:
            para_text = ' '.join(current_paragraph)
            processed_lines.append(f'<p>{para_text}</p>')
            current_paragraph = []
            in_paragraph = False
    
    for line in lines:
        stripped = line.strip()
        
        # Empty line - close any open paragraph or add spacing
        if not stripped:
            close_paragraph()
            continue
        
        # Check if line is a block-level element (already processed)
        is_block = any(stripped.startswith(f'<{tag}') for tag in 
                      ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'hr']) or stripped == '</pre>'
        
        if is_block:
            close_paragraph()
            close_lists()
            processed_lines.append(line)
            continue
        
        # Unordered list
        if stripped.startswith('- ') or stripped.startswith('* '):
            close_paragraph()
            if in_ol:
                processed_lines.append('</ol>')
                in_ol = False
            if not in_ul:
                processed_lines.append('<ul>')
                in_ul = True
            item_text = stripped[2:]  # Remove "- " or "* "
            processed_lines.append(f'<li>{item_text}</li>')
            continue
        
        # Ordered list
        if re.match(r'^\d+\.\s+', stripped):
            close_paragraph()
            if in_ul:
                processed_lines.append('</ul>')
                in_ul = False
            if not in_ol:
                processed_lines.append('<ol>')
                in_ol = True
            item_text = re.sub(r'^\d+\.\s+', '', stripped)
            processed_lines.append(f'<li>{item_text}</li>')
            continue
        
        # Regular text - add to paragraph
        close_lists()
        if not in_paragraph:
            in_paragraph = True
        current_paragraph.append(stripped)
    
    # Close any remaining open elements
    close_paragraph()
    close_lists()
    
    html_body = '\n'.join(processed_lines)
    
    # Create complete HTML document with styling
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        h2 {{
            color: #2980b9;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
            margin-top: 35px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 25px;
            margin-bottom: 12px;
        }}
        h4, h5, h6 {{
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        code {{
            background-color: #f8f8f8;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
            padding: 2px 6px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            color: #d73a49;
        }}
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            line-height: 1.4;
            margin: 15px 0;
            max-width: 100%;
        }}
        pre code {{
            background: none;
            border: none;
            padding: 0;
            color: #333;
        }}
        p {{
            margin: 12px 0;
            line-height: 1.7;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f9f9f9;
            font-style: italic;
        }}
        .note {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""
    
    return html_template


def find_documentation_file(filename: str) -> str:
    """
    Find a documentation file in various possible locations.
    
    Args:
        filename: Name of the file to find (e.g., "USER_GUIDE.md")
    
    Returns:
        Full path to the file if found, empty string otherwise
    """
    # Find project root by going up from this file
    current_file = os.path.abspath(__file__)
    gui_dir = os.path.dirname(current_file)  # src/sdtm_checker/gui
    sdtm_checker_dir = os.path.dirname(gui_dir)  # src/sdtm_checker
    src_dir = os.path.dirname(sdtm_checker_dir)  # src
    project_root = os.path.dirname(src_dir)  # annoSDTMCheck
    
    # Try multiple possible locations
    possible_paths = [
        os.path.join(project_root, "docs", filename),
        os.path.join(project_root, filename),
        os.path.join(sys._MEIPASS, "docs", filename) if getattr(sys, 'frozen', False) else None,
        os.path.join(sys._MEIPASS, filename) if getattr(sys, 'frozen', False) else None,
        os.path.join(os.getcwd(), "docs", filename),
        os.path.join(os.getcwd(), filename),
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            logger.info(f"Found documentation file at: {path}")
            return path
    
    logger.warning(f"Documentation file '{filename}' not found in any expected location")
    return ""


def open_markdown_as_html(markdown_path: str, title: str = "Documentation") -> bool:
    """
    Convert a markdown file to HTML and open it in the default browser.
    
    Args:
        markdown_path: Path to the markdown file
        title: Title for the HTML page
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read markdown file
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert to HTML
        html_content = markdown_to_html(markdown_content, title)
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.html', delete=False) as f:
            temp_path = f.name
            f.write(html_content)
        
        # Open in browser
        webbrowser.open('file://' + temp_path)
        logger.info(f"Opened documentation in browser: {markdown_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to open documentation: {str(e)}")
        return False


def open_documentation(filename: str, title: str = "Documentation") -> tuple[bool, str]:
    """
    Find and open a documentation file as HTML in the browser.
    
    Args:
        filename: Name of the documentation file (e.g., "USER_GUIDE.md")
        title: Title for the HTML page
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Find the file
    doc_path = find_documentation_file(filename)
    
    if not doc_path:
        # Find project root for error message
        current_file = os.path.abspath(__file__)
        gui_dir = os.path.dirname(current_file)
        sdtm_checker_dir = os.path.dirname(gui_dir)
        src_dir = os.path.dirname(sdtm_checker_dir)
        project_root = os.path.dirname(src_dir)
        
        return False, f"{title} not found in expected locations.\n\nPlease check the docs/ folder at:\n{project_root}"
    
    # Open the file
    if open_markdown_as_html(doc_path, title):
        return True, f"Opened {title} in your browser."
    else:
        return False, f"Found {title} at:\n{doc_path}\n\nBut could not open it automatically."

