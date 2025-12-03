# 📊 מערכת דוח פעולות ודוח מכירות יומי - מדריך שלם

## ✅ מה בנינו לך?

יישום מלא עם:

1. **Parser HTML מתקדם** - חלץ נתונים מקובץ דוח הפעולות
2. **Streamlit Dashboard** - ממשק ידידותי בעברית
3. **ניתוח נתונים** - דוחות יומיים, פריטים מובילים וגרפיקה
4. **יצוא Excel** - הורדת דוח מלא עם 3 גיליונות
5. **בדיקות אוטומטיות** - וידוא שהכל עובד

---

## 📁 קבצים בפרויקט

```
project/
├── app.py                      # אפליקציית Streamlit (הממשק הראשי)
├── html_to_excel.py            # מודול עיבוד HTML
├── test_parser.py              # סקריפט בדיקה
├── requirements.txt            # תלויות Python
├── example_report.html         # דוגמה לקובץ HTML
├── README.md                   # תיעוד מלא
├── QUICK_START.md              # הנחיות התחלה מהירה
└── SETUP_GUIDE.md             # מדריך זה
```

---

## 🚀 ריצה מהירה (3 שלבים)

### 1. התקנה

```bash
# בטרמינל/Command Prompt
pip install -r requirements.txt
```

### 2. בדיקה

```bash
python test_parser.py
```

יוצא צפוי:
```
SUCCESS - All tests passed!
Ready to run:
  streamlit run app.py
```

### 3. הרצה

```bash
streamlit run app.py
```

✅ בדפדפן: http://localhost:8501

---

## 🎯 איך להשתמש בממשק

### שלב 1: בחירת קובץ
1. בתפריט הצד משמאל - לחץ "בחר קובץ HTML"
2. בחר את קובץ דוח הפעולות

### שלב 2: צפייה בדוחות
- **דוח יומי** - מכירות כל יום
- **טרנזקציות** - רשימה מפורטת עם סינון
- **פריטים** - מוצרים מובילים
- **גרפיקה** - תרשימים וניתוח
- **הורדה** - קובץ Excel

### שלב 3: הורדה
בטאב "הורד" - לחץ על כפתור להורדת ה-Excel

---

## 📊 מה מקבלים?

### דוח יומי
```
תאריך      | מכירות | עסקאות | פריטים
01/12/2025 | 3213   | 36     | 42
```

### טרנזקציות
```
Order   | Invoice | Date | Time  | Items | Total
57345   | 56629   | ... | 18:05 | 1     | 60.00
```

### פריטים מובילים
```
שם        | כמות | סה"כ | עסקאות
מגדל      | 1.0  | 540  | 3
```

### גרפיקה
- בר-צ'ארט של מכירות יומיות
- בר-צ'ארט של עסקאות
- 15 הפריטים המובילים
- Pie chart של התפלגות
- טבלת סטטיסטיקה

---

## 🔧 ממשק Python

### שימוש בסיסי

```python
from html_to_excel import parse_html_transactions, create_daily_summary

# קרא HTML
with open('report.html') as f:
    html = f.read()

# חלץ נתונים
transactions = parse_html_transactions(html)

# סכום לפי יום
daily = create_daily_summary(transactions)

# הדפס
print(daily)
```

### Pandas DataFrames

```python
# דוח יומי
daily_df  # date, total_sales, transaction_count, items_count

# טרנזקציות
trans_df  # Order ID, Invoice, Date, Time, Item Count, Total Amount

# פריטים
items_df  # item_name, quantity, total_amount, transaction_count
```

---

## 📈 דוגמה מלאה

```python
import pandas as pd
from html_to_excel import (
    parse_html_transactions,
    create_daily_summary,
    create_items_summary_df
)

# 1. קרא ועבד
with open('transaction_history.html') as f:
    transactions = parse_html_transactions(f.read())

# 2. סכם לפי יום
daily = create_daily_summary(transactions)
print(f"Total: {daily['total_sales'].sum()}")

# 3. מוצרים מובילים
items = create_items_summary_df(transactions)
print(items.head(10))

# 4. יצוא
daily.to_csv('sales_daily.csv', index=False)
items.to_csv('sales_items.csv', index=False)
```

---

## 🐛 פתרון בעיות נפוצות

### בעיה: "No module named 'streamlit'"
```bash
pip install streamlit
```

### בעיה: "ModuleNotFoundError"
```bash
pip install -r requirements.txt --force-reinstall
```

### בעיה: "לא נמצאו טרנזקציות"
- בדוק שה-HTML מ-AccuPOS
- בדוק קידוד (UTF-8)
- פתח בדפדפן - אתה צריך לראות טבלה

### בעיה: קריאה ל-Unicode
```python
# תמיד שתמש ב:
with open('file.html', encoding='utf-8') as f:
    ...
```

### בעיה: "Port 8501 in use"
```bash
streamlit run app.py --server.port 8502
```

---

## 🎨 התאמה אישית

### שנה צבעים (app.py)
```python
# שורה ~230
PatternFill(start_color="366092", end_color="366092", ...)
# שנה "366092" לצבע אחר (hex)
```

### שנה כותרות (app.py)
```python
st.markdown("# 📊 הכותרת שלך")
```

### שנה עמודות (html_to_excel.py)
```python
# פונקציה create_daily_summary
# הוסף עמודות כפי שצריך
```

---

## 📦 דרישות מערכת

- Python 3.8+
- 100MB מקום (עם צפיפות)
- Connection לאינטרנט (ראשונית)

## 📚 ספריות המשומשות

| Lib | גרסה | תפקיד |
|-----|------|--------|
| streamlit | 1.28+ | ממשק משתמש |
| pandas | 2.0+ | עיבוד נתונים |
| openpyxl | 3.10+ | יצוא Excel |
| plotly | 5.17+ | גרפיקה |
| beautifulsoup4 | 4.12+ | parsing HTML |

---

## ✨ יתרונות המערכת

✅ **קל להשתמש** - ממשק בעברית  
✅ **מהיר** - עיבוד מידי  
✅ **כללי** - עבד כל HTML דומה  
✅ **חכם** - ניתוח עמוק  
✅ **יוצא** - Excel מלא  
✅ **בדוק** - כולל בדיקות  

---

## 🎯 מקרי שימוש

1. **בעל קפה** - בדוק מכירות יומיות
2. **מנהל** - דוח למעלה יום יום
3. **רו"ח** - דוח מפורט לחשבונאות
4. **בעל מסעדה** - מוצרים פופולריים
5. **מנהל מלאי** - מה חסר?

---

## 🚀 צעדים הבאים

1. **חקור את הקוד** - קרא את html_to_excel.py
2. **שנה לצרכיך** - הוסף עמודות/מדדים
3. **אוטומציה** - תזמן ריצה יומית
4. **אחסון** - שמור ל-Google Drive/Dropbox
5. **שיתוף** - שתוף דוח עם צוות

---

## 📞 תמיכה

### בדוק הגדרה
```bash
python -c "import streamlit, pandas, openpyxl, plotly, bs4; print('OK')"
```

### הרץ עם Debug
```bash
streamlit run app.py --logger.level=debug
```

### בדוק HTML
```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
blocks = soup.find_all('div', class_='data-block')
print(f"Found {len(blocks)} blocks")
```

---

## 📝 רישיון

קוד פתוח - בחינם להשתמש ולשנות

---

## 📅 עדכון האחרון

- ✅ Parser HTML עובד (36 טרנזקציות בדוגמה)
- ✅ Streamlit Dashboard מלא
- ✅ 5 טבים שונים
- ✅ גרפיקה עם Plotly
- ✅ יצוא Excel
- ✅ בדיקות אוטומטיות

---

**מוכן? התחל:**

```bash
# 1. התקן
pip install -r requirements.txt

# 2. בדוק
python test_parser.py

# 3. הרץ
streamlit run app.py
```

🎉 **זהו! העמוד שלך פועל!**

---

**טיפ:** שמור את הקובצים בתיקייה אחת ובאותו ממקום לתפעול חלק.
