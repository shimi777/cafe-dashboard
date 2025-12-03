# 🚀 הנחיות התחלה מהירה

## צעד 1️⃣: התקנת Python
- הורד Python 3.8+ מ: https://www.python.org
- בעת ההתקנה, סמן את "Add Python to PATH"

## צעד 2️⃣: הורדת הפרויקט
- שמור את כל הקבצים בתיקייה אחת

## צעד 3️⃣: התקנת ספריות
פתח Command Prompt/Terminal בתיקייה של הפרויקט והרץ:

```bash
pip install -r requirements.txt
```

## צעד 4️⃣: הרצת האפליקציה

```bash
streamlit run app.py
```

זה יפתח דפדפן אוטומטי עם הממשק.

---

## 📊 אחרי ההתקנה:

1. **בחר קובץ HTML** - לחץ על כפתור ה"בחר" בתפריט הצד
2. **הנתונים יעובדו אוטומטית**
3. **ראה דוחות וגרפים**
4. **הורד Excel** - בטאב "הורד"

---

## ✅ רשימת בדיקה

- [ ] Python מותקן
- [ ] pip עובד
- [ ] requirements.txt מותקן
- [ ] app.py בתיקייה
- [ ] streamlit פועל

---

## 🎯 מה אתה יכול לעשות:

### 1. בדיקה עם דוגמה
```bash
python -c "from html_to_excel import parse_html_transactions; print('✓ Module works!')"
```

### 2. הרצה של Streamlit
```bash
streamlit run app.py --logger.level=debug
```

### 3. ריצה מסוימת

```python
# test_parser.py
from old_dasboard.html_to_excel import parse_html_transactions, create_daily_summary

with open('example_report.html', 'r', encoding='utf-8') as f:
    html = f.read()

transactions = parse_html_transactions(html)
daily = create_daily_summary(transactions)

print(f"Found {len(transactions)} transactions")
print(daily)
```

---

## 🔗 קישורים שימושיים

- Streamlit Docs: https://docs.streamlit.io
- Pandas Docs: https://pandas.pydata.org
- Plotly Docs: https://plotly.com/python

---

## ❓ שאלות נפוצות

**Q: איך אני עוצר את האפליקציה?**  
A: לחץ Ctrl+C בטרמינל

**Q: האם אוכל להשתמש בקבצי HTML אחרים?**  
A: כן, אם הם בפורמט AccuPOS או דומה

**Q: איך אני מוודא שהקובץ HTML תקין?**  
A: פתח אותו בדפדפן - אתה צריך לראות טבלה של טרנזקציות

**Q: האם ניתן לשנות את הדוח?**  
A: כן! שנה את html_to_excel.py לפי הצרכים שלך

---

## 📞 עזרה

אם אתה צריך עזרה:
1. ודא שכל הספריות מותקנות: `pip list`
2. בדוק את המסנן: `python -c "import streamlit; print(streamlit.__version__)"`
3. בדוק את קובץ ה-HTML בדפדפן

---

**מוכן? הרץ את זה:**
```bash
streamlit run app.py
```

🎉 זהו! האפליקציה שלך פועלת!
