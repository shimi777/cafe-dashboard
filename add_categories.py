"""
סקריפט עזר להוספת עמודת קטגוריה אוטומטית למוצרים
במקרה שהקובץ המקורי לא כולל קטגוריות
"""

import pandas as pd
import re

def auto_categorize(description):
    """
    מזהה קטגוריה אוטומטית לפי תיאור המוצר
    
    Args:
        description: תיאור המוצר
        
    Returns:
        קטגוריה משוערת
    """
    description = str(description).lower()
    
    # מילות מפתח לכל קטגוריה
    categories_keywords = {
        'קפה חם': ['אספרסו', 'קפה הפוך', 'קפוצ\'ינו', 'אמריקנו', 'מקיאטו', 'לאטה', 'קורטדו', 'פלט וויט'],
        'קפה קר': ['אייס', 'פרפה', 'פרדו', 'קולד ברו', 'פראפה', 'קר', 'שייק קפה'],
        'תה': ['תה', 'נענע', 'לואיזה', 'צמחים', 'ירוק', 'שחור', 'הרבלי', 'אינפוזיה'],
        'משקאות קרים': ['מיץ', 'לימונדה', 'סודה', 'קוקה', 'ספרייט', 'פאנטה', 'מים', 'פוזה'],
        'מאפים': ['קרואסון', 'בורקס', 'מאפה', 'סנדוויץ', 'טוסט', 'בגט'],
        'עוגות': ['עוגה', 'עוגת', 'בראוניז', 'מאפינס', 'קאפקייק', 'טארט', 'פאי'],
        'מתוקים': ['עוגיה', 'עוגיות', 'שוקולד', 'ממתקים', 'בראוניז', 'מקרון'],
        'ארוחות': ['סלט', 'פסטה', 'פיצה', 'סנדוויץ', 'טוסט', 'שקשוקה', 'ביצים'],
        'כלים': ['כוס', 'צלחת', 'קנקן', 'ספל', 'סט', 'קומקום', 'מגש', 'פילטר'],
        'אבקות ותה': ['אבקה', 'תה לבית', 'חליטה', 'קפה טחון', 'פולי קפה']
    }
    
    # חיפוש התאמה
    for category, keywords in categories_keywords.items():
        for keyword in keywords:
            if keyword in description:
                return category
    
    return 'אחר'  # קטגוריית ברירת מחדל


def add_categories_to_excel(input_file, output_file=None, category_column='קטגוריה'):
    """
    מוסיף עמודת קטגוריה אוטומטית לקובץ Excel
    
    Args:
        input_file: נתיב לקובץ Excel קלט
        output_file: נתיב לקובץ Excel פלט (אם None, ידרוס את הקובץ המקורי)
        category_column: שם העמודה לקטגוריה
    """
    
    print(f"📖 קורא קובץ: {input_file}")
    df = pd.read_excel(input_file)
    
    print(f"📊 נמצאו {len(df)} שורות")
    
    # בדיקה אם כבר יש עמודת קטגוריה
    if category_column in df.columns:
        print(f"⚠️ עמודת '{category_column}' כבר קיימת!")
        choice = input("האם לדרוס? (y/n): ")
        if choice.lower() != 'y':
            print("❌ בוטל")
            return
    
    # זיהוי עמודת התיאור
    description_col = None
    for col in ['תאור', 'תיאור', 'שם', 'מוצר', 'פריט']:
        if col in df.columns:
            description_col = col
            break
    
    if not description_col:
        print("❌ לא נמצאה עמודת תיאור!")
        print(f"עמודות זמינות: {', '.join(df.columns)}")
        description_col = input("הכנס שם עמודת התיאור: ")
    
    print(f"🔍 משתמש בעמודה: '{description_col}'")
    
    # הוספת קטגוריות
    print("🏷️ מוסיף קטגוריות...")
    df[category_column] = df[description_col].apply(auto_categorize)
    
    # סטטיסטיקה
    print("\n📊 התפלגות קטגוריות:")
    category_counts = df[category_column].value_counts()
    for cat, count in category_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {cat}: {count} ({percentage:.1f}%)")
    
    # שמירה
    if output_file is None:
        output_file = input_file
    
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n✅ נשמר בהצלחה: {output_file}")
    
    # הצגת דוגמה
    print("\n🔍 דוגמה מהתוצאות:")
    print(df[[description_col, category_column]].head(10))
    
    return df


def interactive_categorize(input_file):
    """
    מצב אינטראקטיבי - מאפשר למשתמש לתקן קטגוריות
    """
    df = pd.read_excel(input_file)
    
    # זיהוי עמודת תיאור
    description_col = None
    for col in ['תאור', 'תיאור', 'שם', 'מוצר', 'פריט']:
        if col in df.columns:
            description_col = col
            break
    
    if not description_col:
        print("❌ לא נמצאה עמודת תיאור!")
        return
    
    # הוספת קטגוריות אוטומטיות
    df['קטגוריה'] = df[description_col].apply(auto_categorize)
    
    print("🎯 מצב אינטראקטיבי - תקן קטגוריות")
    print("הקלד 'done' לסיום, 'skip' לדלג על מוצר\n")
    
    # מוצרים שסווגו כ'אחר' - דורשים תשומת לב
    other_products = df[df['קטגוריה'] == 'אחר'].index
    
    if len(other_products) > 0:
        print(f"⚠️ נמצאו {len(other_products)} מוצרים ללא קטגוריה ברורה\n")
        
        for idx in other_products:
            product = df.loc[idx, description_col]
            current_cat = df.loc[idx, 'קטגוריה']
            
            print(f"\nמוצר: {product}")
            print(f"קטגוריה נוכחית: {current_cat}")
            
            new_cat = input("קטגוריה חדשה (או Enter לשמור/skip/done): ").strip()
            
            if new_cat.lower() == 'done':
                break
            elif new_cat.lower() == 'skip' or new_cat == '':
                continue
            else:
                df.loc[idx, 'קטגוריה'] = new_cat
    
    # שמירה
    output_file = input_file.replace('.xlsx', '_categorized.xlsx')
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"\n✅ נשמר: {output_file}")
    print("\n📊 סיכום קטגוריות:")
    print(df['קטגוריה'].value_counts())
    
    return df


if __name__ == "__main__":
    import sys
    
    print("🏷️ סקריפט הוספת קטגוריות אוטומטית\n")
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = input("הכנס נתיב לקובץ Excel: ")
    
    mode = input("בחר מצב (1=אוטומטי, 2=אינטראקטיבי): ")
    
    if mode == '2':
        interactive_categorize(input_file)
    else:
        output_file = input("נתיב קובץ פלט (Enter לדרוס את המקור): ") or None
        add_categories_to_excel(input_file, output_file)
