"""
Google Sheets Connector Module - מודול לחיבור וסנכרון עם Google Sheets
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json


# --- הגדרות ---
REQUIRED_COLUMNS = [
    "Transaction_ID", "Date", "Time", "Order_ID", "Invoice_Num",
    "Payment_Method", "Item_Name", "Item_Code", "Quantity",
    "Unit_Price", "Taxable_Amount", "Sale_Price", "VAT_Amount",
    "Cashier", "Register"
]


@st.cache_resource
def init_gsheets_connection():
    """
    יוזם את חיבור Google Sheets באמצעות Service Account
    
    דרישות:
    1. צור Service Account ב-Google Cloud Console
    2. הורד את קובץ ה-JSON של ה-credentials
    3. שתף את ה-Spreadsheet עם כתובת המייל של ה-Service Account
    4. הוסף את ה-credentials ל-Streamlit secrets
    """
    try:
        # קריאת credentials מ-Streamlit secrets
        if "google" not in st.secrets:
            st.warning("⚠️ לא נמצאו Google credentials ב-secrets")
            return None
        
        creds_dict = dict(st.secrets["google"])
        
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
        return None


def get_spreadsheet_url():
    """קבלת URL של ה-Spreadsheet מ-secrets"""
    # נסה מספר מיקומים אפשריים
    if "spreadsheet_url" in st.secrets:
        return st.secrets["spreadsheet_url"]
    if "app" in st.secrets and "spreadsheet_url" in st.secrets["app"]:
        return st.secrets["app"]["spreadsheet_url"]
    if "google" in st.secrets and "spreadsheet_url" in st.secrets["google"]:
        return st.secrets["google"]["spreadsheet_url"]
    return None


@st.cache_resource(ttl=300)  # Cache for 5 minutes
def get_worksheet(_gc, sheet_name: str):
    """
    קבלת worksheet ספציפי
    
    Args:
        _gc: gspread client (underscore prefix to prevent hashing)
        sheet_name: שם הגיליון
    """
    if _gc is None:
        return None
    
    try:
        spreadsheet_url = get_spreadsheet_url()
        
        if not spreadsheet_url:
            st.error("❌ spreadsheet_url לא הוגדר ב-secrets")
            return None
        
        sh = _gc.open_by_url(spreadsheet_url)
        
        # נסה לקבל את הגיליון, או צור אותו אם לא קיים
        try:
            return sh.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            # צור גיליון חדש עם headers
            ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            ws.append_row(REQUIRED_COLUMNS)
            return ws
    
    except Exception as e:
        st.error(f"❌ שגיאה בקבלת worksheet '{sheet_name}': {str(e)}")
        return None


def get_cloud_history(sheet_name: str = "History") -> pd.DataFrame:
    """
    קריאת כל ההיסטוריה מ-Google Sheets
    
    Args:
        sheet_name: שם הגיליון (ברירת מחדל: "History")
    
    Returns:
        DataFrame עם כל הנתונים
    """
    gc = init_gsheets_connection()
    if gc is None:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    try:
        ws = get_worksheet(gc, sheet_name)
        if ws is None:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
        
        # קריאת כל הנתונים
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
        
        df = pd.DataFrame(data)
        
        # המרת עמודות מספריות
        numeric_columns = ['Quantity', 'Unit_Price', 'Taxable_Amount', 'Sale_Price', 'VAT_Amount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # המרת תאריכים
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        return df
    
    except Exception as e:
        st.error(f"❌ שגיאה בקריאת נתונים מהענן: {str(e)}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)


def transactions_to_flat_df(transactions: list) -> pd.DataFrame:
    """
    המרת רשימת טרנזקציות ל-DataFrame שטוח (שורה לכל פריט)
    
    Args:
        transactions: רשימת טרנזקציות מה-parser
    
    Returns:
        DataFrame עם שורה לכל פריט נמכר
    """
    if not transactions:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    records = []
    
    for trans in transactions:
        # קבל את שיטת התשלום העיקרית
        payment_method = ""
        if trans.get('payments'):
            positive_payments = [p for p in trans['payments'] if p.get('amount', 0) > 0]
            if positive_payments:
                payment_method = max(positive_payments, key=lambda x: x.get('amount', 0)).get('method', '')
        
        for item in trans['items']:
            # יצירת מזהה ייחודי
            unique_id = f"{trans['date']}_{trans['order_id']}_{item['name']}_{item['quantity']}"
            
            records.append({
                "Transaction_ID": unique_id,
                "Date": trans['date'].isoformat() if hasattr(trans['date'], 'isoformat') else str(trans['date']),
                "Time": str(trans['time']) if trans['time'] else "",
                "Order_ID": trans['order_id'],
                "Invoice_Num": trans['invoice_num'],
                "Payment_Method": payment_method,
                "Item_Name": item['name'],
                "Item_Code": item.get('code', ''),
                "Quantity": item['quantity'],
                "Unit_Price": item['unit_price'],
                "Taxable_Amount": item.get('taxable_amount', 0),
                "Sale_Price": item['total_price'],
                "VAT_Amount": item.get('vat_amount', 0),
                "Cashier": item.get('cashier', ''),
                "Register": trans.get('register', '')
            })
    
    return pd.DataFrame(records)


def save_to_cloud(new_df: pd.DataFrame, sheet_name: str = "History") -> int:
    """
    שמירת נתונים חדשים ל-Google Sheets (ללא כפילויות)
    
    Args:
        new_df: DataFrame עם נתונים חדשים
        sheet_name: שם הגיליון
    
    Returns:
        מספר השורות שנוספו
    """
    if new_df.empty:
        return 0
    
    gc = init_gsheets_connection()
    if gc is None:
        return 0
    
    try:
        ws = get_worksheet(gc, sheet_name)
        if ws is None:
            return 0
        
        # קרא נתונים קיימים
        existing_data = ws.get_all_records()
        existing_ids = set()
        
        if existing_data:
            existing_df = pd.DataFrame(existing_data)
            if 'Transaction_ID' in existing_df.columns:
                existing_ids = set(existing_df['Transaction_ID'].astype(str))
        
        # סנן רק שורות חדשות
        new_df['Transaction_ID'] = new_df['Transaction_ID'].astype(str)
        new_rows = new_df[~new_df['Transaction_ID'].isin(existing_ids)]
        
        if new_rows.empty:
            return 0
        
        # המר ל-list של lists והוסף
        rows_to_add = new_rows.values.tolist()
        
        # הוסף בקבוצות של 100 שורות (מגבלת API)
        batch_size = 100
        added_count = 0
        
        for i in range(0, len(rows_to_add), batch_size):
            batch = rows_to_add[i:i + batch_size]
            ws.append_rows(batch, value_input_option='USER_ENTERED')
            added_count += len(batch)
        
        # נקה את ה-cache
        get_worksheet.clear()
        
        return added_count
    
    except Exception as e:
        st.error(f"❌ שגיאה בשמירה לענן: {str(e)}")
        return 0


def delete_from_cloud(transaction_ids: list, sheet_name: str = "History") -> int:
    """
    מחיקת טרנזקציות מ-Google Sheets
    
    Args:
        transaction_ids: רשימת מזהי טרנזקציות למחיקה
        sheet_name: שם הגיליון
    
    Returns:
        מספר השורות שנמחקו
    """
    if not transaction_ids:
        return 0
    
    gc = init_gsheets_connection()
    if gc is None:
        return 0
    
    try:
        ws = get_worksheet(gc, sheet_name)
        if ws is None:
            return 0
        
        # קרא את כל הנתונים
        all_data = ws.get_all_values()
        if len(all_data) <= 1:  # רק headers
            return 0
        
        headers = all_data[0]
        
        # מצא את אינדקס של Transaction_ID
        try:
            id_col = headers.index('Transaction_ID')
        except ValueError:
            return 0
        
        # מצא שורות למחיקה (מהסוף להתחלה כדי לא לשבש אינדקסים)
        rows_to_delete = []
        for i, row in enumerate(all_data[1:], start=2):  # התחל מ-2 (אחרי headers)
            if len(row) > id_col and row[id_col] in transaction_ids:
                rows_to_delete.append(i)
        
        # מחק מהסוף להתחלה
        deleted_count = 0
        for row_idx in sorted(rows_to_delete, reverse=True):
            ws.delete_rows(row_idx)
            deleted_count += 1
        
        # נקה את ה-cache
        get_worksheet.clear()
        
        return deleted_count
    
    except Exception as e:
        st.error(f"❌ שגיאה במחיקה מהענן: {str(e)}")
        return 0


def cloud_data_to_transactions(df: pd.DataFrame) -> list:
    """
    המרת DataFrame מהענן חזרה למבנה transactions
    (לתאימות עם הפונקציות הקיימות)
    
    Args:
        df: DataFrame מ-Google Sheets
    
    Returns:
        רשימת טרנזקציות
    """
    if df.empty:
        return []
    
    # קבץ לפי Order_ID
    transactions = []
    
    for order_id, group in df.groupby('Order_ID'):
        first_row = group.iloc[0]
        
        items = []
        for _, row in group.iterrows():
            items.append({
                'name': row.get('Item_Name', ''),
                'code': row.get('Item_Code', ''),
                'quantity': float(row.get('Quantity', 0)),
                'unit_price': float(row.get('Unit_Price', 0)),
                'taxable_amount': float(row.get('Taxable_Amount', 0)),
                'total_price': float(row.get('Sale_Price', 0)),
                'vat_amount': float(row.get('VAT_Amount', 0)),
                'cashier': row.get('Cashier', '')
            })
        
        # Parse date
        date_val = first_row.get('Date')
        if isinstance(date_val, str):
            try:
                date_val = datetime.strptime(date_val, '%Y-%m-%d').date()
            except:
                try:
                    date_val = pd.to_datetime(date_val).date()
                except:
                    date_val = datetime.now().date()
        elif hasattr(date_val, 'date'):
            date_val = date_val.date()
        
        # Parse time
        time_val = first_row.get('Time', '')
        if isinstance(time_val, str) and time_val:
            try:
                time_val = datetime.strptime(time_val, '%H:%M:%S').time()
            except:
                try:
                    time_val = datetime.strptime(time_val, '%H:%M').time()
                except:
                    time_val = datetime.strptime('00:00', '%H:%M').time()
        elif not time_val:
            time_val = datetime.strptime('00:00', '%H:%M').time()
        
        transactions.append({
            'order_id': str(order_id),
            'invoice_num': str(first_row.get('Invoice_Num', '')),
            'date': date_val,
            'time': time_val,
            'register': first_row.get('Register', ''),
            'items': items,
            'payments': [{'method': first_row.get('Payment_Method', ''), 'amount': group['Sale_Price'].sum()}],
            'total_items': group['Taxable_Amount'].sum(),
            'total_vat': group['VAT_Amount'].sum(),
            'total': group['Sale_Price'].sum()
        })
    
    return transactions


def check_connection_status() -> dict:
    """
    בדיקת סטטוס החיבור ל-Google Sheets
    
    Returns:
        מילון עם סטטוס החיבור
    """
    status = {
        'connected': False,
        'has_credentials': False,
        'has_url': False,
        'can_read': False,
        'can_write': False,
        'error': None
    }
    
    # בדוק credentials
    if "google" in st.secrets:
        status['has_credentials'] = True
    
    # בדוק URL
    if get_spreadsheet_url():
        status['has_url'] = True
    
    # נסה להתחבר
    gc = init_gsheets_connection()
    if gc:
        status['connected'] = True
        
        # נסה לקרוא
        try:
            ws = get_worksheet(gc, "History")
            if ws:
                ws.get_all_values()
                status['can_read'] = True
                status['can_write'] = True
        except Exception as e:
            status['error'] = str(e)
    
    return status
