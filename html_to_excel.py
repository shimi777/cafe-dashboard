"""
סקריפט להמרת קבצי HTML (מקבלות/חשבוניות) לפורמט Excel
"""

from bs4 import BeautifulSoup
import pandas as pd
import sys

def html_to_excel(html_file_path, output_excel_path='cafe_data.xlsx'):
    """
    ממיר קובץ HTML עם טבלאות div לקובץ Excel
    
    Args:
        html_file_path: נתיב לקובץ HTML
        output_excel_path: נתיב לקובץ Excel פלט
    """
    
    print(f"קורא קובץ: {html_file_path}")
    
    # קריאת הקובץ
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # מציאת כל טבלאות ה-div
    table_divs = soup.find_all('div', class_='table')
    
    print(f"נמצאו {len(table_divs)} טבלאות")
    
    if len(table_divs) == 0:
        print("❌ לא נמצאו טבלאות בקובץ!")
        return
    
    all_rows = []
    
    for table_num, table_div in enumerate(table_divs, 1):
        print(f"מעבד טבלה {table_num}...")
        
        # חילוץ כותרות
        headers = []
        header_div = table_div.find('div', class_='table-header item-header')
        
        if header_div:
            # כותרות טקסט
            text_headers = header_div.find_all('div', class_='text')
            for h in text_headers:
                headers.append(h.get_text(strip=True))
            
            # כותרות מספריות
            num_headers = header_div.find_all('div', class_='num')
            for h in num_headers:
                headers.append(h.get_text(strip=True))
        
        # אם אין כותרות, השתמש בכותרות ברירת מחדל
        if not headers:
            headers = ['פריט', 'תאור', 'כמות', 'סכום', 'סכום כולל מעמ']
        
        # חילוץ שורות
        item_rows = table_div.find_all('div', class_='item-row')
        
        for row in item_rows:
            row_data = []
            
            # עמודות טקסט
            text_cols = row.find_all('div', class_='text')
            for col in text_cols:
                row_data.append(col.get_text(strip=True))
            
            # עמודות מספריות
            num_cols = row.find_all('div', class_='num')
            for col in num_cols:
                text = col.get_text(strip=True)
                # ניסיון להמיר למספר
                try:
                    # הסרת פסיקים וסימנים מיוחדים
                    clean_text = text.replace(',', '').replace('₪', '').strip()
                    if clean_text:
                        row_data.append(float(clean_text))
                    else:
                        row_data.append(text)
                except:
                    row_data.append(text)
            
            if row_data:
                all_rows.append(row_data)
    
    # יצירת DataFrame
    if all_rows:
        # וידוא שכל השורות באותו אורך
        max_cols = max(len(row) for row in all_rows)
        
        # השלמת שורות קצרות עם None
        for row in all_rows:
            while len(row) < max_cols:
                row.append(None)
        
        # וידוא שהכותרות באותו אורך
        while len(headers) < max_cols:
            headers.append(f'עמודה_{len(headers)+1}')
        
        df = pd.DataFrame(all_rows, columns=headers[:max_cols])
        
        # הוספת עמודות מחושבות נוספות
        if 'סכום כולל מעמ' in df.columns and 'כמות' in df.columns:
            # חישוב מחיר למנה
            df['מחיר למנה'] = df['סכום כולל מעמ'] / df['כמות'].replace(0, 1)
            df['מחיר למנה'] = df['מחיר למנה'].round(2)
        
        # שמירה ל-Excel
        df.to_excel(output_excel_path, index=False, engine='openpyxl')
        
        print(f"\n✅ הקובץ נשמר בהצלחה!")
        print(f"📁 נתיב: {output_excel_path}")
        print(f"📊 מספר שורות: {len(df)}")
        print(f"📊 מספר עמודות: {len(df.columns)}")
        print(f"\nעמודות בקובץ: {', '.join(df.columns)}")
        
        # הצגת דוגמה
        print("\n🔍 דוגמה מהנתונים (5 שורות ראשונות):")
        print(df.head())
        
        return df
    else:
        print("❌ לא נמצאו נתונים לייצא!")
        return None


if __name__ == "__main__":
    # בדיקה אם הועבר נתיב קובץ
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'cafe_data.xlsx'
    else:
        # דוגמה לשימוש
        html_file = input("הכנס נתיב לקובץ HTML: ")
        output_file = input("הכנס נתיב לקובץ פלט (Enter לברירת מחדל 'cafe_data.xlsx'): ") or 'cafe_data.xlsx'
    
    html_to_excel(html_file, output_file)
