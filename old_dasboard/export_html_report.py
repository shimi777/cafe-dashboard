"""
יצירת דוח HTML סטטי מנתוני המכירות
חלופה לייצוא דשבורד Streamlit - מתאים לשיתוף עם בעל העסק
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from datetime import datetime

def create_html_report(excel_file, output_html='cafe_report.html'):
    """
    יוצר דוח HTML אינטראקטיבי מקובץ Excel
    
    Args:
        excel_file: נתיב לקובץ Excel
        output_html: נתיב לקובץ HTML פלט
    """
    
    print(f"📖 קורא נתונים מ-{excel_file}...")
    df = pd.read_excel(excel_file)
    
    # חישובים
    df['מחזור_ליום'] = df['סכום כולל מעמ'] / 90
    df['כמות_ליום'] = df['כמות'] / 90
    df['אחוז_מההכנסות'] = (df['סכום כולל מעמ'] / df['סכום כולל מעמ'].sum()) * 100
    
    # מיון לפארטו
    df_sorted = df.sort_values('סכום כולל מעמ', ascending=False).reset_index(drop=True)
    df_sorted['אחוז_מצטבר'] = df_sorted['אחוז_מההכנסות'].cumsum()
    
    # KPIs
    total_revenue = df['סכום כולל מעמ'].sum()
    avg_daily = total_revenue / 90
    total_items = df['כמות'].sum()
    avg_price = df['מחיר למנה'].mean()
    
    print("📊 יוצר גרפים...")
    
    # 1. גרף עוגה - הכנסות לפי קטגוריה
    category_revenue = df.groupby('קטגוריה')['סכום כולל מעמ'].sum().sort_values(ascending=False)
    fig1 = px.pie(
        values=category_revenue.values,
        names=category_revenue.index,
        title="התפלגות הכנסות לפי קטגוריה",
        hole=0.4
    )
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    
    # 2. טופ 10 מוצרים
    top10 = df.nlargest(10, 'סכום כולל מעמ')
    fig2 = px.bar(
        top10,
        x='סכום כולל מעמ',
        y='תאור',
        orientation='h',
        title="10 המוצרים המובילים בהכנסות",
        color='קטגוריה',
        text='סכום כולל מעמ'
    )
    fig2.update_traces(texttemplate='₪%{text:,.0f}', textposition='outside')
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    
    # 3. גרף פארטו
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig3.add_trace(
        go.Bar(
            x=df_sorted['תאור'][:20],
            y=df_sorted['סכום כולל מעמ'][:20],
            name="הכנסות",
            marker_color='lightblue'
        ),
        secondary_y=False
    )
    
    fig3.add_trace(
        go.Scatter(
            x=df_sorted['תאור'][:20],
            y=df_sorted['אחוז_מצטבר'][:20],
            name="אחוז מצטבר",
            mode='lines+markers',
            marker_color='red',
            line=dict(width=3)
        ),
        secondary_y=True
    )
    
    fig3.add_hline(y=80, line_dash="dash", line_color="green", 
                   annotation_text="80%", secondary_y=True)
    
    fig3.update_xaxes(title_text="מוצר", tickangle=-45)
    fig3.update_yaxes(title_text="הכנסות (₪)", secondary_y=False)
    fig3.update_yaxes(title_text="אחוז מצטבר (%)", secondary_y=True, range=[0, 100])
    fig3.update_layout(title="ניתוח פארטו (80/20)", height=500)
    
    # 4. כמויות לפי קטגוריה
    category_qty = df.groupby('קטגוריה')['כמות'].sum().sort_values(ascending=False)
    fig4 = px.bar(
        x=category_qty.values,
        y=category_qty.index,
        orientation='h',
        title="כמויות נמכרו לפי קטגוריה",
        labels={'x': 'כמות', 'y': 'קטגוריה'},
        text=category_qty.values
    )
    fig4.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig4.update_layout(yaxis={'categoryorder':'total ascending'})
    
    # סיווג ABC
    products_for_80 = len(df_sorted[df_sorted['אחוז_מצטבר'] <= 80])
    products_for_95 = len(df_sorted[df_sorted['אחוז_מצטבר'] <= 95])
    
    df_sorted['סיווג_ABC'] = 'C'
    df_sorted.loc[df_sorted['אחוז_מצטבר'] <= 95, 'סיווג_ABC'] = 'B'
    df_sorted.loc[df_sorted['אחוז_מצטבר'] <= 80, 'סיווג_ABC'] = 'A'
    
    # סיווג BCG
    df_sorted['ביקוש'] = pd.qcut(df_sorted['כמות'], q=3, labels=['נמוך', 'בינוני', 'גבוה'])
    df_sorted['רווחיות'] = pd.qcut(df_sorted['מחיר למנה'], q=3, labels=['נמוכה', 'בינונית', 'גבוהה'])
    
    stars = df_sorted[(df_sorted['ביקוש'] == 'גבוה') & (df_sorted['רווחיות'] == 'גבוהה')]
    cash_cows = df_sorted[(df_sorted['ביקוש'] == 'גבוה') & (df_sorted['רווחיות'].isin(['בינונית', 'נמוכה']))]
    question_marks = df_sorted[(df_sorted['ביקוש'].isin(['נמוך', 'בינוני'])) & (df_sorted['רווחיות'] == 'גבוהה')]
    dogs = df_sorted[(df_sorted['ביקוש'] == 'נמוך') & (df_sorted['רווחיות'].isin(['נמוכה', 'בינונית']))]
    
    # סטטיסטיקות לפי קטגוריה
    category_stats = df.groupby('קטגוריה').agg({
        'סכום כולל מעמ': 'sum',
        'כמות': 'sum',
        'מחיר למנה': 'mean',
        'תאור': 'count'
    }).round(2)
    category_stats.columns = ['סה"כ הכנסות', 'סה"כ כמות', 'ממוצע מחיר', 'מספר מוצרים']
    
    # מוצרים חלשים
    threshold_qty = df['כמות'].quantile(0.1)
    weak_products = df[df['כמות'] <= threshold_qty][['תאור', 'קטגוריה', 'כמות', 'כמות_ליום']].sort_values('כמות').head(10)
    
    print("📝 בונה דוח HTML...")
    
    # בניית HTML
    html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>דוח ניתוח מכירות - בית קפה</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            direction: rtl;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .kpi-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .kpi-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        
        .kpi-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 10px;
        }}
        
        .kpi-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #2d3436;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .chart-container {{
            margin-bottom: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }}
        
        .recommendations {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .recommendation-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .recommendation-card.success {{
            border-right: 5px solid #28a745;
        }}
        
        .recommendation-card.info {{
            border-right: 5px solid #17a2b8;
        }}
        
        .recommendation-card.warning {{
            border-right: 5px solid #ffc107;
        }}
        
        .recommendation-card.danger {{
            border-right: 5px solid #dc3545;
        }}
        
        .recommendation-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        
        .recommendation-subtitle {{
            font-size: 0.95em;
            color: #6c757d;
            margin-bottom: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: right;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
            text-align: right;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .footer {{
            background: #2d3436;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .abc-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .badge-a {{
            background: #28a745;
            color: white;
        }}
        
        .badge-b {{
            background: #ffc107;
            color: black;
        }}
        
        .badge-c {{
            background: #dc3545;
            color: white;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>☕ דוח ניתוח מכירות - בית קפה</h1>
            <p>תקופה: 90 ימי עבודה | נוצר ב-{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <!-- KPIs -->
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-label">סה"כ הכנסות</div>
                <div class="kpi-value">₪{total_revenue:,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">ממוצע יומי</div>
                <div class="kpi-value">₪{avg_daily:,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">סה"כ פריטים נמכרו</div>
                <div class="kpi-value">{total_items:,.0f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">ממוצע מחיר למנה</div>
                <div class="kpi-value">₪{avg_price:,.1f}</div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="section">
            <h2 class="section-title">📊 מבט על כללי</h2>
            
            <div class="chart-container">
                <div id="chart1"></div>
            </div>
            
            <div class="chart-container">
                <div id="chart4"></div>
            </div>
        </div>
        
        <!-- Top Products -->
        <div class="section">
            <h2 class="section-title">🏆 מוצרים מובילים</h2>
            
            <div class="chart-container">
                <div id="chart2"></div>
            </div>
        </div>
        
        <!-- Pareto Analysis -->
        <div class="section">
            <h2 class="section-title">📈 ניתוח פארטו (80/20)</h2>
            
            <div class="chart-container">
                <div id="chart3"></div>
            </div>
            
            <div class="recommendations">
                <div class="recommendation-card success">
                    <div class="recommendation-title">קטגוריה A</div>
                    <div class="kpi-value" style="font-size: 1.5em;">{products_for_80}</div>
                    <div class="recommendation-subtitle">מוצרים ({products_for_80/len(df)*100:.1f}%)</div>
                    <p>מייצרים 80% מההכנסות</p>
                </div>
                
                <div class="recommendation-card info">
                    <div class="recommendation-title">קטגוריה B</div>
                    <div class="kpi-value" style="font-size: 1.5em;">{products_for_95 - products_for_80}</div>
                    <div class="recommendation-subtitle">מוצרים ({(products_for_95-products_for_80)/len(df)*100:.1f}%)</div>
                    <p>מייצרים 15% מההכנסות</p>
                </div>
                
                <div class="recommendation-card warning">
                    <div class="recommendation-title">קטגוריה C</div>
                    <div class="kpi-value" style="font-size: 1.5em;">{len(df) - products_for_95}</div>
                    <div class="recommendation-subtitle">מוצרים ({(len(df)-products_for_95)/len(df)*100:.1f}%)</div>
                    <p>מייצרים 5% מההכנסות</p>
                </div>
            </div>
        </div>
        
        <!-- BCG Matrix -->
        <div class="section">
            <h2 class="section-title">🎯 המלצות לקידום - מטריצת BCG</h2>
            
            <div class="recommendations">
                <div class="recommendation-card success">
                    <div class="recommendation-title">⭐ כוכבים ({len(stars)} מוצרים)</div>
                    <div class="recommendation-subtitle">ביקוש גבוה + רווחיות גבוהה</div>
                    <p><strong>פעולה מומלצת:</strong> המשך להשקיע, הבטח זמינות, שמור על איכות</p>
                    {"<ul>" + "".join([f"<li>{row['תאור']} (₪{row['סכום כולל מעמ']:,.0f})</li>" for _, row in stars.head(5).iterrows()]) + "</ul>" if len(stars) > 0 else "<p>לא נמצאו מוצרים בקטגוריה זו</p>"}
                </div>
                
                <div class="recommendation-card info">
                    <div class="recommendation-title">🐄 פרות מזומנים ({len(cash_cows)} מוצרים)</div>
                    <div class="recommendation-subtitle">ביקוש גבוה + רווחיות בינונית/נמוכה</div>
                    <p><strong>פעולה מומלצת:</strong> אופטימיזציה של עלויות, שקול העלאת מחיר</p>
                    {"<ul>" + "".join([f"<li>{row['תאור']} (₪{row['סכום כולל מעמ']:,.0f})</li>" for _, row in cash_cows.head(5).iterrows()]) + "</ul>" if len(cash_cows) > 0 else "<p>לא נמצאו מוצרים בקטגוריה זו</p>"}
                </div>
                
                <div class="recommendation-card warning">
                    <div class="recommendation-title">❓ סימני שאלה ({len(question_marks)} מוצרים)</div>
                    <div class="recommendation-subtitle">ביקוש נמוך + רווחיות גבוהה</div>
                    <p><strong>פעולה מומלצת:</strong> קידום אגרסיבי, מבצעים, שילוב עם מוצרים פופולריים</p>
                    {"<ul>" + "".join([f"<li>{row['תאור']} (₪{row['מחיר למנה']:.1f} למנה)</li>" for _, row in question_marks.head(5).iterrows()]) + "</ul>" if len(question_marks) > 0 else "<p>לא נמצאו מוצרים בקטגוריה זו</p>"}
                </div>
                
                <div class="recommendation-card danger">
                    <div class="recommendation-title">🐕 כלבים ({len(dogs)} מוצרים)</div>
                    <div class="recommendation-subtitle">ביקוש נמוך + רווחיות נמוכה</div>
                    <p><strong>פעולה מומלצת:</strong> שקול הסרה מהתפריט או מבצע אחרון</p>
                    {"<ul>" + "".join([f"<li>{row['תאור']} ({row['כמות_ליום']:.1f} ליום)</li>" for _, row in dogs.head(5).iterrows()]) + "</ul>" if len(dogs) > 0 else "<p>לא נמצאו מוצרים בקטגוריה זו</p>"}
                </div>
            </div>
        </div>
        
        <!-- Category Stats -->
        <div class="section">
            <h2 class="section-title">📋 סטטיסטיקות לפי קטגוריה</h2>
            
            <table>
                <thead>
                    <tr>
                        <th>קטגוריה</th>
                        <th>סה"כ הכנסות</th>
                        <th>סה"כ כמות</th>
                        <th>ממוצע מחיר</th>
                        <th>מספר מוצרים</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td><strong>{cat}</strong></td><td>₪{row['סה\"כ הכנסות']:,.2f}</td><td>{row['סה\"כ כמות']:,.0f}</td><td>₪{row['ממוצע מחיר']:.2f}</td><td>{row['מספר מוצרים']:.0f}</td></tr>" for cat, row in category_stats.sort_values('סה\"כ הכנסות', ascending=False).iterrows()])}
                </tbody>
            </table>
        </div>
        
        <!-- Weak Products -->
        <div class="section">
            <h2 class="section-title">⚠️ מוצרים בעלי ביצועים נמוכים</h2>
            <p style="margin-bottom: 20px;">מוצרים שכדאי לשקול הסרה או קידום מיוחד</p>
            
            <table>
                <thead>
                    <tr>
                        <th>מוצר</th>
                        <th>קטגוריה</th>
                        <th>כמות כוללת</th>
                        <th>כמות ליום ממוצעת</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td>{row['תאור']}</td><td>{row['קטגוריה']}</td><td>{row['כמות']:,.0f}</td><td>{row['כמות_ליום']:.2f}</td></tr>" for _, row in weak_products.iterrows()])}
                </tbody>
            </table>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>דוח זה נוצר אוטומטית ממערכת ניתוח המכירות</p>
            <p style="margin-top: 10px; opacity: 0.8;">לשאלות נוספות או להרחבת הניתוח, צור קשר</p>
        </div>
    </div>
    
    <script>
        // Chart 1 - Pie Chart
        {fig1.to_html(include_plotlyjs=False, div_id='chart1')}
        
        // Chart 2 - Top 10
        {fig2.to_html(include_plotlyjs=False, div_id='chart2')}
        
        // Chart 3 - Pareto
        {fig3.to_html(include_plotlyjs=False, div_id='chart3')}
        
        // Chart 4 - Quantities
        {fig4.to_html(include_plotlyjs=False, div_id='chart4')}
    </script>
</body>
</html>
    """
    
    # שמירה
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ הדוח נוצר בהצלחה!")
    print(f"📁 שמור ב: {output_html}")
    print(f"📊 גודל קובץ: {len(html_content) / 1024:.1f} KB")
    print(f"\n💡 פתח את הקובץ בדפדפן כדי לצפות בדוח")
    print(f"💡 ניתן לשלוח את הקובץ בדוא\"ל או ב-WhatsApp")
    
    return output_html


if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'cafe_report.html'
    else:
        excel_file = input("הכנס נתיב לקובץ Excel: ")
        output_file = input("הכנס שם קובץ פלט (Enter לברירת מחדל 'cafe_report.html'): ") or 'cafe_report.html'
    
    try:
        create_html_report(excel_file, output_file)
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
