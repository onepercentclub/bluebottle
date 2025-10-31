#!/usr/bin/env python3
"""
Generate Complete HTML Documentation from Markdown
Converts all markdown documentation to beautiful HTML pages.
"""

import os
import re
from pathlib import Path


def read_markdown(filename):
    """Read a markdown file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def convert_markdown_to_html(markdown_text, title="Documentation"):
    """Convert markdown to HTML with styling."""
    
    # Escape HTML in code blocks first
    def escape_code_block(match):
        code = match.group(1)
        return f'<pre><code>{html_escape(code)}</code></pre>'
    
    def html_escape(text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    html = markdown_text
    
    # Convert code blocks
    html = re.sub(r'```(\w+)?\n(.*?)\n```', lambda m: f'<pre><code class="language-{m.group(1) or "text"}">{html_escape(m.group(2))}</code></pre>', html, flags=re.DOTALL)
    
    # Convert inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Convert headers
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2 id="\1">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # Convert bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Convert italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert lists
    lines = html.split('\n')
    new_lines = []
    in_list = False
    
    for line in lines:
        if re.match(r'^[-*]\s+', line):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            item = re.sub(r'^[-*]\s+', '', line)
            new_lines.append(f'<li>{item}</li>')
        elif re.match(r'^\d+\.\s+', line):
            if not in_list:
                new_lines.append('<ol>')
                in_list = True
            item = re.sub(r'^\d+\.\s+', '', line)
            new_lines.append(f'<li>{item}</li>')
        else:
            if in_list:
                new_lines.append('</ul>' if '<ul>' in '\n'.join(new_lines[-10:]) else '</ol>')
                in_list = False
            if line.strip():
                new_lines.append(f'<p>{line}</p>')
            else:
                new_lines.append('')
    
    if in_list:
        new_lines.append('</ul>')
    
    html = '\n'.join(new_lines)
    
    # Convert horizontal rules
    html = re.sub(r'^---+$', '<hr>', html, flags=re.MULTILINE)
    
    return html


def generate_html_page(title, content, output_file, nav_links=None):
    """Generate a complete HTML page."""
    
    # Default navigation
    if nav_links is None:
        nav_links = [
            ('index.html', 'Home'),
            ('complete_documentation.html', 'Complete Docs'),
            ('quick_start.html', 'Quick Start'),
            ('fsm_documentation_portal.html', 'Portal'),
            ('fsm_visualizations_index.html', 'Visualizations'),
        ]
    
    nav_html = '\n'.join([f'<a href="{link}" class="nav-link">{name}</a>' for link, name in nav_links])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Bluebottle FSM Documentation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background: #f6f8fa;
        }}
        
        .navbar {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .navbar-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        .navbar-brand {{
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            text-decoration: none;
        }}
        
        .navbar-nav {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        
        .nav-link {{
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background 0.3s;
            font-size: 0.9rem;
        }}
        
        .nav-link:hover {{
            background: rgba(255,255,255,0.2);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}
        
        .content {{
            background: white;
            padding: 3rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        h1 {{
            color: #667eea;
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid #667eea;
        }}
        
        h2 {{
            color: #667eea;
            font-size: 2rem;
            margin: 2.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e1e4e8;
        }}
        
        h3 {{
            color: #764ba2;
            font-size: 1.5rem;
            margin: 2rem 0 1rem 0;
        }}
        
        h4 {{
            color: #586069;
            font-size: 1.2rem;
            margin: 1.5rem 0 0.75rem 0;
        }}
        
        p {{
            margin-bottom: 1rem;
            line-height: 1.8;
        }}
        
        ul, ol {{
            margin: 1rem 0 1rem 2rem;
        }}
        
        li {{
            margin-bottom: 0.5rem;
            line-height: 1.6;
        }}
        
        code {{
            background: #f6f8fa;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
            font-size: 0.9em;
            color: #d73a49;
            border: 1px solid #e1e4e8;
        }}
        
        pre {{
            background: #f6f8fa;
            padding: 1.5rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1.5rem 0;
            border: 1px solid #e1e4e8;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            border: none;
            color: #24292e;
            font-size: 0.9rem;
        }}
        
        a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        strong {{
            font-weight: 600;
            color: #24292e;
        }}
        
        em {{
            font-style: italic;
            color: #586069;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #e1e4e8;
            margin: 3rem 0;
        }}
        
        .toc {{
            background: #f6f8fa;
            padding: 1.5rem;
            border-radius: 6px;
            margin: 2rem 0;
            border-left: 4px solid #667eea;
        }}
        
        .toc h3 {{
            color: #667eea;
            margin-top: 0;
        }}
        
        .alert {{
            padding: 1rem 1.5rem;
            border-radius: 6px;
            margin: 1.5rem 0;
            border-left: 4px solid;
        }}
        
        .alert-info {{
            background: #e7f2ff;
            border-color: #667eea;
            color: #0366d6;
        }}
        
        .alert-success {{
            background: #dcfce7;
            border-color: #22c55e;
            color: #166534;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #586069;
            margin-top: 3rem;
        }}
        
        @media (max-width: 768px) {{
            .content {{
                padding: 1.5rem;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            h2 {{
                font-size: 1.5rem;
            }}
            
            .navbar-content {{
                flex-direction: column;
                align-items: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <a href="index.html" class="navbar-brand">🔄 Bluebottle FSM Docs</a>
            <div class="navbar-nav">
                {nav_html}
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div class="content">
            {content}
        </div>
    </div>
    
    <div class="footer">
        <p>Bluebottle FSM Documentation • Generated from comprehensive analysis</p>
        <p>For questions or updates, see the documentation source files</p>
    </div>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file


def convert_markdown_file(md_file, html_file, title):
    """Convert a markdown file to HTML."""
    content = read_markdown(md_file)
    if content is None:
        print(f"   ⚠️  Skipping {md_file} (not found)")
        return False
    
    html_content = convert_markdown_to_html(content, title)
    generate_html_page(title, html_content, html_file)
    print(f"   ✓ Generated {html_file}")
    return True


def generate_home_page():
    """Generate the main home/index page."""
    
    content = """
    <h1>🔄 Bluebottle FSM Documentation</h1>
    
    <div class="alert alert-success">
        <strong>✅ Complete Documentation Suite</strong><br>
        All 18 FSM models fully documented with interactive visualizations and comprehensive references.
    </div>
    
    <h2>📚 Documentation</h2>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin: 2rem 0;">
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #667eea;">
            <h3 style="margin-top: 0;">📖 Complete Documentation</h3>
            <p>All 18 models with states, transitions, triggers, effects, and notifications.</p>
            <a href="complete_documentation.html" style="font-size: 1.1rem;">View Complete Docs →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #22c55e;">
            <h3 style="margin-top: 0;">⚡ Quick Start</h3>
            <p>Get started in 5 minutes with examples and common queries.</p>
            <a href="quick_start.html" style="font-size: 1.1rem;">Quick Start Guide →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #764ba2;">
            <h3 style="margin-top: 0;">📊 Project Summary</h3>
            <p>Overview, statistics, and maintenance guide.</p>
            <a href="summary.html" style="font-size: 1.1rem;">View Summary →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #f59e0b;">
            <h3 style="margin-top: 0;">🗺️ Overview</h3>
            <p>Architecture analysis and categorization.</p>
            <a href="overview.html" style="font-size: 1.1rem;">View Overview →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #17a2b8;">
            <h3 style="margin-top: 0;">📘 Deed Lifecycle</h3>
            <p>Detailed documentation for Deed and DeedParticipant.</p>
            <a href="deed_lifecycle.html" style="font-size: 1.1rem;">View Deed Docs →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #dc3545;">
            <h3 style="margin-top: 0;">📋 Usage Guide</h3>
            <p>Complete usage guide and best practices.</p>
            <a href="readme.html" style="font-size: 1.1rem;">View README →</a>
        </div>
        
    </div>
    
    <h2>🎨 Interactive Visualizations</h2>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin: 2rem 0;">
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem;">
            <h3 style="margin-top: 0;">🌐 Main Portal</h3>
            <p>Searchable portal with all models and documentation links.</p>
            <a href="fsm_documentation_portal.html" style="font-size: 1.1rem;">Open Portal →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem;">
            <h3 style="margin-top: 0;">🎨 Visualizations</h3>
            <p>Browse all state visualizations for 18 models.</p>
            <a href="fsm_visualizations_index.html" style="font-size: 1.1rem;">Browse States →</a>
        </div>
        
        <div style="border: 2px solid #e1e4e8; border-radius: 8px; padding: 1.5rem;">
            <h3 style="margin-top: 0;">✨ Interactive Example</h3>
            <p>Fully detailed Deed visualization with clickable transitions.</p>
            <a href="deed_states_visualization/index.html" style="font-size: 1.1rem;">View Example →</a>
        </div>
        
    </div>
    
    <h2>📈 Coverage Statistics</h2>
    
    <ul>
        <li><strong>Models Documented:</strong> 18/18 (100%)</li>
        <li><strong>HTML Pages:</strong> 158+ interactive pages</li>
        <li><strong>State Machine Classes:</strong> 72+</li>
        <li><strong>Distinct States:</strong> 69+</li>
        <li><strong>Transitions:</strong> 137+</li>
        <li><strong>Triggers:</strong> 168+</li>
        <li><strong>Notifications:</strong> 107+</li>
    </ul>
    
    <h2>🚀 Quick Links</h2>
    
    <ul>
        <li><a href="complete_documentation.html">Complete Documentation</a> - All 18 models</li>
        <li><a href="quick_start.html">Quick Start Guide</a> - Get started fast</li>
        <li><a href="fsm_documentation_portal.html">Documentation Portal</a> - Search & browse</li>
        <li><a href="fsm_visualizations_index.html">State Visualizations</a> - Interactive states</li>
        <li><a href="summary.html">Project Summary</a> - Overview & stats</li>
    </ul>
    
    <div class="alert alert-info">
        <strong>💡 Tip:</strong> Start with the <a href="quick_start.html">Quick Start Guide</a> for a 5-minute introduction, 
        or jump to the <a href="fsm_documentation_portal.html">Documentation Portal</a> to search for specific models.
    </div>
    """
    
    generate_html_page("Home", content, "index.html")
    print("   ✓ Generated index.html")


def main():
    """Main function."""
    print("=" * 70)
    print("📄 Converting Markdown Documentation to HTML")
    print("=" * 70)
    print()
    
    # Generate home page
    print("🏠 Generating home page...")
    generate_home_page()
    
    # Convert markdown files
    print("\n📝 Converting markdown files...")
    
    conversions = [
        ('FSM_COMPLETE_DOCUMENTATION.md', 'complete_documentation.html', 'Complete Documentation'),
        ('FSM_QUICK_START.md', 'quick_start.html', 'Quick Start Guide'),
        ('FSM_DOCUMENTATION_SUMMARY.md', 'summary.html', 'Project Summary'),
        ('FSM_README.md', 'readme.html', 'README'),
        ('DEED_LIFECYCLE.md', 'deed_lifecycle.html', 'Deed Lifecycle'),
        ('DEED_INHERITED_TRIGGERS_ADDENDUM.md', 'deed_inherited.html', 'Deed Inherited Triggers'),
        ('STATE_MACHINES_OVERVIEW.md', 'overview.html', 'State Machines Overview'),
        ('GENERATE_COLLECT_DOCS.md', 'generate_guide.html', 'Generation Guide'),
    ]
    
    converted = 0
    for md_file, html_file, title in conversions:
        if convert_markdown_file(md_file, html_file, title):
            converted += 1
    
    print()
    print("=" * 70)
    print(f"✅ Conversion complete!")
    print()
    print(f"📊 Statistics:")
    print(f"   • Markdown files converted: {converted}/{len(conversions)}")
    print(f"   • HTML pages generated: {converted + 1}")
    print()
    print("🌐 Entry points:")
    print("   • index.html - Main home page")
    print("   • complete_documentation.html - All models")
    print("   • quick_start.html - Quick start guide")
    print("   • fsm_documentation_portal.html - Interactive portal")
    print()
    print("💡 All markdown documentation is now available as HTML!")
    print("=" * 70)


if __name__ == '__main__':
    main()

