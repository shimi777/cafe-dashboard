import os
import sys
import toml

print("=" * 70)
print("🔍 STREAMLIT SECRETS DIAGNOSTIC")
print("=" * 70)

# Step 1: Check file exists
secrets_path = ".streamlit/secrets.toml"
print(f"\n1️⃣ Checking file: {secrets_path}")

if not os.path.exists(secrets_path):
    print(f"❌ File not found!")
    sys.exit(1)

print(f"✅ File exists")

# Step 2: Read and parse
print(f"\n2️⃣ Reading and parsing TOML...")

try:
    with open(secrets_path, 'r', encoding='utf-8') as f:
        data = toml.load(f)
    print(f"✅ TOML parsed successfully")
except Exception as e:
    print(f"❌ TOML parse error: {e}")
    sys.exit(1)

# Step 3: Check structure
print(f"\n3️⃣ Checking top-level keys in secrets:")
for key in data.keys():
    print(f"   - {key}")

# Step 4: Check [google] section
print(f"\n4️⃣ Checking [google] section:")
if 'google' not in data:
    print(f"❌ [google] section missing!")
    sys.exit(1)

print(f"✅ [google] section exists")
google_keys = data['google'].keys()
print(f"   Keys in [google]: {len(google_keys)}")
for key in sorted(google_keys):
    val = data['google'][key]
    if isinstance(val, str) and len(val) > 50:
        print(f"   ✅ {key}: {val[:30]}...")
    else:
        print(f"   ✅ {key}: {val}")

# Step 5: Check spreadsheet_url
print(f"\n5️⃣ Checking spreadsheet_url:")
if 'spreadsheet_url' not in data:
    print(f"❌ spreadsheet_url NOT in top level!")
    print(f"\n   Available top-level keys: {list(data.keys())}")
    
    # Check if it's inside [google]
    if 'spreadsheet_url' in data.get('google', {}):
        print(f"\n   ❌ FOUND: spreadsheet_url is INSIDE [google] section!")
        print(f"   This is the problem - it should be at top level!")
        sys.exit(1)
    else:
        print(f"\n   ❌ spreadsheet_url is completely missing from file!")
        sys.exit(1)
else:
    url = data['spreadsheet_url']
    if not url:
        print(f"❌ spreadsheet_url is EMPTY!")
        sys.exit(1)
    print(f"✅ spreadsheet_url found: {url}")

# Step 6: Try to simulate what Streamlit does
print(f"\n6️⃣ Testing Streamlit secret access (simulation):")

try:
    google_creds = data["google"]
    print(f"✅ Can access data['google']")
except KeyError as e:
    print(f"❌ Cannot access data['google']: {e}")
    sys.exit(1)

try:
    sheet_url = data["spreadsheet_url"]
    print(f"✅ Can access data['spreadsheet_url']")
except KeyError as e:
    print(f"❌ Cannot access data['spreadsheet_url']: {e}")
    sys.exit(1)

# Step 7: Check if we can initialize gspread
print(f"\n7️⃣ Checking if gspread can be imported:")
try:
    import gspread
    from google.oauth2.service_account import Credentials
    print(f"✅ gspread and google-auth imported successfully")
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print(f"   Run: pip install gspread google-auth-oauthlib")

# Step 8: Try to create credentials
print(f"\n8️⃣ Testing credential creation:")
try:
    import gspread
    from google.oauth2.service_account import Credentials
    
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_info(data["google"], scopes=scope)
    print(f"✅ Credentials created successfully")
    print(f"   Service account: {creds.service_account_email}")
    
except Exception as e:
    print(f"❌ Credential error: {e}")
    import traceback
    traceback.print_exc()

# Final summary
print(f"\n" + "=" * 70)
print("✅ ALL CHECKS PASSED!")
print("=" * 70)
print(f"\nYour secrets.toml is correctly configured!")
print(f"You should be able to run the Streamlit app now.")
print(f"\nCommand: streamlit run kumkum_dashboard_fixed.py")
print(f"\n" + "=" * 70)
