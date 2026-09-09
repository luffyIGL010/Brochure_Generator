import io
import sys
import subprocess

def _ensure_dependencies():
    try:
        import markdown
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
        import markdown

    try:
        from xhtml2pdf import pisa
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "xhtml2pdf"])
        from xhtml2pdf import pisa

    return markdown, pisa

def convert_markdown_to_pdf(markdown_text: str) -> bytes:
    """
    Converts markdown brochure text into a professionally styled PDF binary stream.
    Automatically installs dependencies if missing in the running Python environment.
    """
    if not markdown_text or not markdown_text.strip():
        raise ValueError("Markdown content is empty.")

    markdown_module, pisa_module = _ensure_dependencies()

    # Convert markdown to HTML with standard extensions
    try:
        html_content = markdown_module.markdown(
            markdown_text,
            extensions=['tables', 'fenced_code', 'toc', 'attr_list']
        )
    except Exception:
        html_content = markdown_module.markdown(markdown_text)

    # Custom CSS for corporate brochure PDF formatting compatible with xhtml2pdf
    css_styles = """
    <style>
        @page {
            size: letter portrait;
            margin: 2cm 1.5cm 2cm 1.5cm;
        }
        
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            color: #1F2937;
            line-height: 1.6;
            font-size: 10pt;
        }
        
        h1 {
            color: #1E3A8A;
            font-size: 22pt;
            font-weight: bold;
            border-bottom: 2px solid #2563EB;
            padding-bottom: 8px;
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        h2 {
            color: #1D4ED8;
            font-size: 15pt;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
            border-bottom: 1px solid #E5E7EB;
            padding-bottom: 4px;
        }
        
        h3 {
            color: #374151;
            font-size: 12pt;
            font-weight: bold;
            margin-top: 14px;
            margin-bottom: 6px;
        }
        
        p {
            margin-top: 0;
            margin-bottom: 10px;
        }
        
        ul, ol {
            margin-top: 0;
            margin-bottom: 12px;
            padding-left: 20px;
        }
        
        li {
            margin-bottom: 4px;
        }
        
        strong {
            color: #111827;
        }
        
        blockquote {
            background-color: #F3F4F6;
            border-left: 4px solid #2563EB;
            padding: 8px 12px;
            margin: 12px 0;
            font-style: italic;
            color: #4B5563;
        }
        
        table {
            width: 100%;
            margin-bottom: 16px;
        }
        
        th, td {
            border: 1px solid #D1D5DB;
            padding: 8px;
            text-align: left;
            font-size: 9.5pt;
        }
        
        th {
            background-color: #F3F4F6;
            color: #1E3A8A;
            font-weight: bold;
        }
        
        hr {
            border: 0;
            height: 1px;
            background: #E5E7EB;
            margin: 20px 0;
        }
    </style>
    """
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {css_styles}
</head>
<body>
    {html_content}
</body>
</html>
"""

    pdf_stream = io.BytesIO()
    pisa_status = pisa_module.CreatePDF(io.StringIO(full_html), dest=pdf_stream)
    
    if pisa_status.err:
        raise RuntimeError(f"Error generating PDF: {pisa_status.err}")
        
    return pdf_stream.getvalue()
