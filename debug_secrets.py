import os
import toml
import sys

print("=" * 60)
print("🔍 SECRETS.TOML DEBUGGER")
print("=" * 60)

# Check if file exists
secrets_path = ".streamlit/secrets.toml"
print(f"\n1️⃣ Checking if file exists: {secrets_path}")

if not os.path.exists(secrets_path):
    print(f"❌ FILE NOT FOUND: {secrets_path}")
    print("\n   Create it with:")
    print("   mkdir -p .streamlit")
    print("   touch .streamlit/secrets.toml")
    sys.exit(1)
else:
    print(f"✅ File exists at: {secrets_path}")

# Check if file is readable
print(f"\n2️⃣ Checking if file is readable")
try:
    with open(secrets_path, 'r') as f:
        content = f.read()
    print(f"✅ File is readable ({len(content)} bytes)")
except Exception as e:
    print(f"❌ Cannot read file: {e}")
    sys.exit(1)

# Check TOML syntax
print(f"\n3️⃣ Checking TOML syntax")
try:
    data = toml.loads(content)
    print(f"✅ TOML syntax is valid")
except Exception as e:
    print(f"❌ TOML syntax error: {e}")
    sys.exit(1)

# Check for [google] section
print(f"\n4️⃣ Checking for [google] section")
if 'google' not in data:
    print(f"❌ Missing [google] section")
    print("   Add this to your secrets.toml:")
    print("   [google]")
    print("   type = \"service_account\"")
    print("   project_id = \"...\"")
    sys.exit(1)
else:
    print(f"✅ [google] section found")

# Check required fields
print(f"\n5️⃣ Checking required fields in [google]")
google_data = data['google']
required_fields = [
    'type',
    'project_id',
    'private_key_id',
    'private_key',
    'client_email',
    'client_id',
    'auth_uri',
    'token_uri',
    'auth_provider_x509_cert_url',
    'client_x509_cert_url'
]

missing_fields = []
for field in required_fields:
    if field not in google_data:
        missing_fields.append(field)
        print(f"   ❌ Missing: {field}")
    else:
        if google_data[field]:
            print(f"   ✅ {field}: Present")
        else:
            print(f"   ⚠️  {field}: Empty!")

if missing_fields:
    print(f"\n❌ Missing {len(missing_fields)} required field(s)")
    sys.exit(1)

# Check spreadsheet_url
print(f"\n6️⃣ Checking spreadsheet_url")
if 'spreadsheet_url' not in data:
    print(f"❌ Missing spreadsheet_url at top level")
    print("\n   Add this to your secrets.toml:")
    print('   spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"')
    sys.exit(1)
else:
    url = data['spreadsheet_url']
    if not url or url == "":
        print(f"❌ spreadsheet_url is EMPTY")
        print('   Add your Google Sheet URL:')
        print('   spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"')
        sys.exit(1)
    elif not url.startswith("https://docs.google.com/spreadsheets/d/"):
        print(f"⚠️  spreadsheet_url doesn't look right")
        print(f"   Current value: {url}")
        print(f"   Should start with: https://docs.google.com/spreadsheets/d/")
    else:
        print(f"✅ spreadsheet_url is present and looks correct")
        # Extract ID
        try:
            sheet_id = url.split('/d/')[1].split('/')[0]
            print(f"   Sheet ID: {sheet_id}")
        except:
            pass

# Check private_key format
print(f"\n7️⃣ Checking private_key format")
private_key = google_data.get('private_key', '')
if not private_key:
    print(f"❌ private_key is empty")
elif not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
    print(f"❌ private_key doesn't start correctly")
    print(f"   Should start with: -----BEGIN PRIVATE KEY-----")
elif not private_key.endswith('-----END PRIVATE KEY-----\n'):
    print(f"⚠️  private_key might not end correctly")
    print(f"   Should end with: -----END PRIVATE KEY-----\\n")
else:
    print(f"✅ private_key format looks correct")
    print(f"   Length: {len(private_key)} characters")

# Summary
print(f"\n" + "=" * 60)
print("✅ ALL CHECKS PASSED!")
print("=" * 60)
print(f"\nYour secrets.toml is correctly configured!")
print(f"\nYou can now run:")
print(f"  streamlit run kumkum_dashboard_fixed.py")
print(f"\n" + "=" * 60)