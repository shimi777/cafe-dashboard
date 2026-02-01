"""
מודול לשמירה וקריאה מ-Google Sheets
תשתית ישירה ופשוטה - בדיוק כמו בקוד המקורי
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


@st.cache_resource
def init_gsheets_connection():
    """יוזם את חיבור Google Sheets"""
    try:
        # קריאת credentials מ-Streamlit secrets
        creds_dict = st.secrets["google"]

        # הגדרת ה-scopes הנדרשות
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # יצירת credentials
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

        # חיבור ל-gspread
        gc = gspread.authorize(creds)
        return gc
    except Exception as e:
        st.error(f"❌ שגיאה בחיבור ל-Google Sheets: {str(e)}")
        st.info("💡 וודא שהוגדרו secrets בקובץ .streamlit/secrets.toml")
        return None


@st.cache_resource
def get_worksheet(sheet_name: str):
    """קבלת worksheet ספציפי"""
    gc = init_gsheets_connection()
    if gc is None:
        return None

    try:
        # קריאת ה-URL מ-secrets (מנסה שני מיקומים)
        spreadsheet_url = st.secrets.get("spreadsheet_url", "")
        if not spreadsheet_url:
            # נסה בסעיף app אם קיים
            spreadsheet_url = st.secrets.get("app", {}).get("spreadsheet_url", "")

        if not spreadsheet_url:
            st.error("❌ spreadsheet_url לא הוגדר ב-secrets")
            return None

        sh = gc.open_by_url(spreadsheet_url)
        return sh.worksheet(sheet_name)
    except Exception as e:
        st.error(f"❌ שגיאה בקבלת worksheet: {str(e)}")
        return None


def get_cloud_history():
    """קריאת כל ההיסטוריה מ-Google Sheets"""
    try:
        ws = get_worksheet("History")
        if ws is None:
            return pd.DataFrame(
                columns=["Transaction_ID", "Date", "Item_ID", "Item_Name", "Quantity", "Price", "Total Amount"]
            )

        # קריאת כל הנתונים
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(
                columns=["Transaction_ID", "Date", "Item_ID", "Item_Name", "Quantity", "Price", "Total Amount"]
            )

        df = pd.DataFrame(data)

        # המרת עמודות מספריות
        numeric_columns = ['Quantity', 'Price', 'Total Amount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"❌ שגיאה בקריאת נתונים: {str(e)}")
        return pd.DataFrame(
            columns=["Transaction_ID", "Date", "Item_ID", "Item_Name", "Quantity", "Price", "Total Amount"]
        )


def save_to_cloud(new_df):
    """שמירת נתונים חדשים ל-Google Sheets (עם מניעת כפילויות)"""
    if new_df.empty:
        return 0

    try:
        ws = get_worksheet("History")
        if ws is None:
            st.error("❌ לא ניתן לתחובר ל-worksheet History")
            return 0

        # קריאת כל ה-Transaction_IDs הקיימים
        existing_data = ws.get_all_records()
        existing_ids = set([row.get('Transaction_ID', '') for row in existing_data])

        # סינון כפילויות
        filtered_new = new_df[~new_df['Transaction_ID'].isin(existing_ids)]

        if filtered_new.empty:
            return 0

        # המרה לרשימה של ערכים
        rows_to_add = filtered_new.values.tolist()

        # הוספה ל-Google Sheet (מתחת לשורה האחרונה)
        ws.append_rows(rows_to_add, value_input_option='USER_ENTERED')

        return len(filtered_new)

    except Exception as e:
        st.error(f"❌ שגיאה בשמירה ל-Google Sheets: {str(e)}")
        return 0