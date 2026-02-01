import os

secrets_path = ".streamlit/secrets.toml"

print("=" * 70)
print("📄 CONTENTS OF .streamlit/secrets.toml")
print("=" * 70)
print()

try:
    with open(secrets_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}\n")
    
    for i, line in enumerate(lines, 1):
        # Show line number and content
        # Use repr to show whitespace clearly
        display_line = line.rstrip('\n')
        
        # Highlight spreadsheet_url
        if 'spreadsheet_url' in line:
            print(f"Line {i:3d} ▶️  {display_line}")
        # Highlight section markers
        elif '[google]' in line:
            print(f"Line {i:3d} 📍 {display_line}")
        elif line.strip() == '':
            print(f"Line {i:3d}    (blank line)")
        else:
            print(f"Line {i:3d}    {display_line}")
    
    print()
    print("=" * 70)
    print("ANALYSIS:")
    print("=" * 70)
    
    # Find [google] section
    google_line = None
    spreadsheet_url_line = None
    
    for i, line in enumerate(lines, 1):
        if '[google]' in line:
            google_line = i
        if 'spreadsheet_url' in line:
            spreadsheet_url_line = i
    
    if google_line:
        print(f"✅ [google] section found at line: {google_line}")
    else:
        print(f"❌ [google] section NOT found")
    
    if spreadsheet_url_line:
        print(f"✅ spreadsheet_url found at line: {spreadsheet_url_line}")
        
        if google_line and spreadsheet_url_line > google_line:
            # Check if there's another section between them
            has_section_after = False
            for i in range(google_line, spreadsheet_url_line):
                if i < len(lines) and lines[i].startswith('[') and '[google]' not in lines[i]:
                    has_section_after = True
                    break
            
            # Count how many lines until next section or end
            next_section = None
            for i in range(google_line + 1, len(lines)):
                if lines[i].strip().startswith('[') and '[google]' not in lines[i]:
                    next_section = i + 1
                    break
            
            if next_section is None:
                next_section = len(lines) + 1
            
            if spreadsheet_url_line < next_section:
                print(f"❌ Problem: spreadsheet_url is INSIDE [google] section")
                print(f"   [google] starts at line {google_line}")
                print(f"   spreadsheet_url is at line {spreadsheet_url_line}")
                print(f"   Next section/end is at line {next_section}")
                print()
                print("   SOLUTION: Move spreadsheet_url to AFTER line", next_section - 1)
            else:
                print(f"✅ spreadsheet_url appears to be OUTSIDE [google]")
    else:
        print(f"❌ spreadsheet_url NOT found")
    
    print()
    print("=" * 70)
    
except FileNotFoundError:
    print(f"❌ File not found: {secrets_path}")
except Exception as e:
    print(f"❌ Error: {e}")
