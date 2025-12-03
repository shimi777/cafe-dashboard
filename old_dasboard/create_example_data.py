"""
יצירת קובץ Excel דוגמה למטרות בדיקה
"""

import pandas as pd
import numpy as np

# יצירת נתוני דוגמה
np.random.seed(42)

# קטגוריות
categories = ['קפה חם', 'קפה קר', 'תה', 'מאפים', 'עוגות', 'כלים']

# מוצרים לדוגמה
products = {
    'קפה חם': ['אספרסו', 'קפה הפוך', 'קפוצ\'ינו', 'אמריקנו', 'מקיאטו'],
    'קפה קר': ['קר', 'פרפה', 'אייס לאטה', 'קולד ברו', 'פרדו'],
    'תה': ['תה ירוק', 'תה שחור', 'תה צמחים', 'תה פירות', 'תה לואיזה'],
    'מאפים': ['קרואסון', 'בורקס', 'מאפה שוקולד', 'מאפה גבינה', 'עוגיות'],
    'עוגות': ['עוגת שוקולד', 'עוגת גבינה', 'עוגת לימון', 'בראוניז', 'מאפינס'],
    'כלים': ['כוס זכוכית', 'כוס קרמיקה', 'צלחת', 'סט תה', 'קנקן תה']
}

# יצירת רשימת מוצרים
data = []
for category, items in products.items():
    for item in items:
        # יצירת מחיר בהתאם לקטגוריה
        if category in ['קפה חם', 'קפה קר']:
            base_price = np.random.uniform(10, 18)
            quantity = np.random.randint(200, 1500)
        elif category == 'תה':
            base_price = np.random.uniform(12, 20)
            quantity = np.random.randint(50, 400)
        elif category in ['מאפים', 'עוגות']:
            base_price = np.random.uniform(8, 25)
            quantity = np.random.randint(100, 800)
        else:  # כלים
            base_price = np.random.uniform(30, 150)
            quantity = np.random.randint(5, 50)
        
        price_per_unit = round(base_price, 2)
        total_before_vat = round(quantity * price_per_unit / 1.17, 2)
        total_with_vat = round(quantity * price_per_unit, 2)
        
        data.append({
            'תאור': item,
            'קטגוריה': category,
            'כמות': quantity,
            'סכום': total_before_vat,
            'סכום כולל מעמ': total_with_vat,
            'מחיר למנה': price_per_unit
        })

# יצירת DataFrame
df = pd.DataFrame(data)

# ערבוב השורות
df = df.sample(frac=1).reset_index(drop=True)

# שמירה ל-Excel
output_file = 'cafe_data_example.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"✅ נוצר קובץ דוגמה: {output_file}")
print(f"📊 מספר מוצרים: {len(df)}")
print(f"💰 סה\"כ הכנסות: ₪{df['סכום כולל מעמ'].sum():,.2f}")
print(f"\nפירוט לפי קטגוריה:")
print(df.groupby('קטגוריה')['סכום כולל מעמ'].sum().sort_values(ascending=False))
