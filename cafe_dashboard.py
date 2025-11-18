import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# הגדרות עמוד
st.set_page_config(
    page_title="ניתוח מכירות בית קפה",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS לתמיכה בעברית
st.markdown("""
    <style>
    .stMetric {
        direction: rtl;
    }
    .metric-label {
        direction: rtl;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# כותרת ראשית
st.title("☕ דשבורד ניתוח מכירות - בית קפה")
st.markdown("---")

# טעינת נתונים
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    return df

# סייד-בר להעלאת קובץ
with st.sidebar:
    st.header("העלאת נתונים")
    uploaded_file = st.file_uploader("העלה קובץ Excel", type=['xlsx', 'xls'])
    
    st.markdown("---")
    st.markdown("### מידע על הנתונים")
    st.info("תקופה: 90 ימי עבודה")

if uploaded_file is not None:
    # טעינת הנתונים
    df = load_data(uploaded_file)
    
    # ניקוי ושמות עמודות
    # הנח שהעמודות הן: תאור, כמות, סכום, סכום כולל מעמ, מחיר למנה, קטגוריה
    
    # חישובים נוספים
    df['מחזור_ליום'] = df['סכום כולל מעמ'] / 90
    df['כמות_ליום'] = df['כמות'] / 90
    df['אחוז_מההכנסות'] = (df['סכום כולל מעמ'] / df['סכום כולל מעמ'].sum()) * 100
    
    # חישוב מצטבר לפארטו
    df_sorted = df.sort_values('סכום כולל מעמ', ascending=False).reset_index(drop=True)
    df_sorted['אחוז_מצטבר'] = df_sorted['אחוז_מההכנסות'].cumsum()
    df_sorted['דירוג'] = range(1, len(df_sorted) + 1)
    
    # KPIs עיקריים
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_revenue = df['סכום כולל מעמ'].sum()
        st.metric("סה\"כ הכנסות", f"₪{total_revenue:,.0f}")
    
    with col2:
        avg_daily_revenue = total_revenue / 90
        st.metric("ממוצע יומי", f"₪{avg_daily_revenue:,.0f}")
    
    with col3:
        total_items_sold = df['כמות'].sum()
        st.metric("סה\"כ פריטים נמכרו", f"{total_items_sold:,.0f}")
    
    with col4:
        avg_transaction = df['מחיר למנה'].mean()
        st.metric("ממוצע מחיר למנה", f"₪{avg_transaction:,.1f}")
    
    with col5:
        num_products = len(df)
        st.metric("מספר מוצרים", num_products)
    
    st.markdown("---")
    
    # טאבים לניתוחים שונים
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 מבט על", 
        "🏆 מוצרים מובילים", 
        "📈 ניתוח פארטו",
        "🎯 המלצות לקידום",
        "📋 טבלת נתונים"
    ])
    
    with tab1:
        st.header("מבט על כללי")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # הכנסות לפי קטגוריה
            category_revenue = df.groupby('קטגוריה')['סכום כולל מעמ'].sum().sort_values(ascending=False)
            
            fig_cat = px.pie(
                values=category_revenue.values,
                names=category_revenue.index,
                title="התפלגות הכנסות לפי קטגוריה",
                hole=0.4
            )
            fig_cat.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # כמויות לפי קטגוריה
            category_quantity = df.groupby('קטגוריה')['כמות'].sum().sort_values(ascending=False)
            
            fig_qty = px.bar(
                x=category_quantity.values,
                y=category_quantity.index,
                orientation='h',
                title="כמויות נמכרו לפי קטגוריה",
                labels={'x': 'כמות', 'y': 'קטגוריה'}
            )
            fig_qty.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_qty, use_container_width=True)
        
        # ממוצעים לפי קטגוריה
        st.subheader("סטטיסטיקות לפי קטגוריה")
        category_stats = df.groupby('קטגוריה').agg({
            'סכום כולל מעמ': 'sum',
            'כמות': 'sum',
            'מחיר למנה': 'mean',
            'תאור': 'count'
        }).round(2)
        category_stats.columns = ['סה"כ הכנסות', 'סה"כ כמות', 'ממוצע מחיר', 'מספר מוצרים']
        category_stats['הכנסה ממוצעת למוצר'] = (category_stats['סה"כ הכנסות'] / category_stats['מספר מוצרים']).round(2)
        st.dataframe(category_stats.sort_values('סה"כ הכנסות', ascending=False), use_container_width=True)
    
    with tab2:
        st.header("מוצרים מובילים")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # טופ 15 מוצרים לפי הכנסות
            top_products_revenue = df.nlargest(15, 'סכום כולל מעמ')[['תאור', 'סכום כולל מעמ', 'כמות', 'קטגוריה']]
            
            fig_top_rev = px.bar(
                top_products_revenue,
                x='סכום כולל מעמ',
                y='תאור',
                color='קטגוריה',
                orientation='h',
                title="15 המוצרים המובילים בהכנסות",
                labels={'סכום כולל מעמ': 'הכנסות (₪)', 'תאור': 'מוצר'}
            )
            fig_top_rev.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_rev, use_container_width=True)
        
        with col2:
            # טופ 15 מוצרים לפי כמות
            top_products_qty = df.nlargest(15, 'כמות')[['תאור', 'כמות', 'סכום כולל מעמ', 'קטגוריה']]
            
            fig_top_qty = px.bar(
                top_products_qty,
                x='כמות',
                y='תאור',
                color='קטגוריה',
                orientation='h',
                title="15 המוצרים הנמכרים ביותר (כמות)",
                labels={'כמות': 'כמות', 'תאור': 'מוצר'}
            )
            fig_top_qty.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_qty, use_container_width=True)
        
        # מוצרים חלשים
        st.subheader("🔍 מוצרים בעלי ביצועים נמוכים")
        st.markdown("מוצרים עם כמות מכירה נמוכה או הכנסות נמוכות שכדאי לשקול להסיר או לקדם:")
        
        # מוצרים עם כמות נמוכה ביותר (מתחת ל-5 אחוזונים)
        threshold_qty = df['כמות'].quantile(0.1)
        threshold_revenue = df['סכום כולל מעמ'].quantile(0.1)
        
        weak_products = df[
            (df['כמות'] <= threshold_qty) | 
            (df['סכום כולל מעמ'] <= threshold_revenue)
        ][['תאור', 'קטגוריה', 'כמות', 'סכום כולל מעמ', 'מחיר למנה', 'כמות_ליום']].sort_values('כמות')
        
        weak_products['כמות_ליום'] = weak_products['כמות_ליום'].round(2)
        st.dataframe(weak_products, use_container_width=True)
        st.caption(f"מציג {len(weak_products)} מוצרים עם ביצועים נמוכים")
    
    with tab3:
        st.header("ניתוח פארטו (80/20)")
        st.markdown("**עקרון פארטו:** 20% מהמוצרים מייצרים 80% מההכנסות")
        
        # גרף פארטו
        fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_pareto.add_trace(
            go.Bar(
                x=df_sorted['תאור'][:30],
                y=df_sorted['סכום כולל מעמ'][:30],
                name="הכנסות",
                marker_color='lightblue'
            ),
            secondary_y=False
        )
        
        fig_pareto.add_trace(
            go.Scatter(
                x=df_sorted['תאור'][:30],
                y=df_sorted['אחוז_מצטבר'][:30],
                name="אחוז מצטבר",
                mode='lines+markers',
                marker_color='red',
                line=dict(width=3)
            ),
            secondary_y=True
        )
        
        # קו 80%
        fig_pareto.add_hline(y=80, line_dash="dash", line_color="green", 
                            annotation_text="80%", secondary_y=True)
        
        fig_pareto.update_xaxes(title_text="מוצר", tickangle=-45)
        fig_pareto.update_yaxes(title_text="הכנסות (₪)", secondary_y=False)
        fig_pareto.update_yaxes(title_text="אחוז מצטבר (%)", secondary_y=True, range=[0, 100])
        
        fig_pareto.update_layout(
            title="ניתוח פארטו - 30 המוצרים המובילים",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_pareto, use_container_width=True)
        
        # חישוב מוצרי A,B,C
        products_for_80 = len(df_sorted[df_sorted['אחוז_מצטבר'] <= 80])
        products_for_95 = len(df_sorted[df_sorted['אחוז_מצטבר'] <= 95])
        
        df_sorted['סיווג_ABC'] = 'C'
        df_sorted.loc[df_sorted['אחוז_מצטבר'] <= 95, 'סיווג_ABC'] = 'B'
        df_sorted.loc[df_sorted['אחוז_מצטבר'] <= 80, 'סיווג_ABC'] = 'A'
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("מוצרים בקטגוריה A", f"{products_for_80} ({products_for_80/len(df)*100:.1f}%)")
            st.caption("מייצרים 80% מההכנסות")
        
        with col2:
            st.metric("מוצרים בקטגוריה B", f"{products_for_95 - products_for_80} ({(products_for_95-products_for_80)/len(df)*100:.1f}%)")
            st.caption("מייצרים 15% מההכנסות")
        
        with col3:
            st.metric("מוצרים בקטגוריה C", f"{len(df) - products_for_95} ({(len(df)-products_for_95)/len(df)*100:.1f}%)")
            st.caption("מייצרים 5% מההכנסות")
        
        # טבלת ABC
        st.subheader("פירוט מוצרים לפי סיווג ABC")
        abc_table = df_sorted[['תאור', 'קטגוריה', 'סכום כולל מעמ', 'כמות', 'אחוז_מההכנסות', 'אחוז_מצטבר', 'סיווג_ABC']].copy()
        abc_table['אחוז_מההכנסות'] = abc_table['אחוז_מההכנסות'].round(2)
        abc_table['אחוז_מצטבר'] = abc_table['אחוז_מצטבר'].round(2)
        
        # פילטר לפי ABC
        abc_filter = st.multiselect(
            "סנן לפי סיווג ABC:",
            options=['A', 'B', 'C'],
            default=['A', 'B', 'C']
        )
        
        filtered_abc = abc_table[abc_table['סיווג_ABC'].isin(abc_filter)]
        st.dataframe(filtered_abc, use_container_width=True, hide_index=True)
    
    with tab4:
        st.header("🎯 המלצות לקידום מוצרים")
        
        # הגדרת קריטריונים
        df_analysis = df_sorted.copy()
        df_analysis['ביקוש'] = pd.qcut(df_analysis['כמות'], q=3, labels=['נמוך', 'בינוני', 'גבוה'])
        df_analysis['רווחיות'] = pd.qcut(df_analysis['מחיר למנה'], q=3, labels=['נמוכה', 'בינונית', 'גבוהה'])
        
        st.subheader("מטריצת BCG מותאמת")
        st.markdown("""
        - **כוכבים ⭐:** ביקוש גבוה + רווחיות גבוהה → המשך להשקיע
        - **פרות מזומנים 🐄:** ביקוש גבוה + רווחיות בינונית/נמוכה → אופטימיזציה של עלויות
        - **סימני שאלה ❓:** ביקוש נמוך + רווחיות גבוהה → השקעה בשיווק
        - **כלבים 🐕:** ביקוש נמוך + רווחיות נמוכה → שקול הסרה
        """)
        
        # חישוב קטגוריות
        stars = df_analysis[(df_analysis['ביקוש'] == 'גבוה') & (df_analysis['רווחיות'] == 'גבוהה')]
        cash_cows = df_analysis[(df_analysis['ביקוש'] == 'גבוה') & (df_analysis['רווחיות'].isin(['בינונית', 'נמוכה']))]
        question_marks = df_analysis[(df_analysis['ביקוש'].isin(['נמוך', 'בינוני'])) & (df_analysis['רווחיות'] == 'גבוהה')]
        dogs = df_analysis[(df_analysis['ביקוש'] == 'נמוך') & (df_analysis['רווחיות'].isin(['נמוכה', 'בינונית']))]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"### ⭐ כוכבים ({len(stars)} מוצרים)")
            st.markdown("**פעולה מומלצת:** המשך להשקיע, הבטח זמינות, שמור על איכות")
            if len(stars) > 0:
                st.dataframe(
                    stars[['תאור', 'קטגוריה', 'כמות', 'סכום כולל מעמ', 'מחיר למנה']].head(10),
                    hide_index=True
                )
            
            st.info(f"### 🐄 פרות מזומנים ({len(cash_cows)} מוצרים)")
            st.markdown("**פעולה מומלצת:** אופטימיזציה של עלויות, שקול העלאת מחיר")
            if len(cash_cows) > 0:
                st.dataframe(
                    cash_cows[['תאור', 'קטגוריה', 'כמות', 'סכום כולל מעמ', 'מחיר למנה']].head(10),
                    hide_index=True
                )
        
        with col2:
            st.warning(f"### ❓ סימני שאלה ({len(question_marks)} מוצרים)")
            st.markdown("**פעולה מומלצת:** קידום אגרסיבי, מבצעים, שילוב עם מוצרים פופולריים")
            if len(question_marks) > 0:
                st.dataframe(
                    question_marks[['תאור', 'קטגוריה', 'כמות', 'סכום כולל מעמ', 'מחיר למנה']].head(10),
                    hide_index=True
                )
            
            st.error(f"### 🐕 כלבים ({len(dogs)} מוצרים)")
            st.markdown("**פעולה מומלצת:** שקול הסרה מהתפריט או מבצע אחרון")
            if len(dogs) > 0:
                st.dataframe(
                    dogs[['תאור', 'קטגוריה', 'כמות', 'סכום כולל מעמ', 'מחיר למנה']].head(10),
                    hide_index=True
                )
        
        # המלצות ספציפיות
        st.markdown("---")
        st.subheader("💡 המלצות מותאמות אישית")
        
        # מוצרים לקידום
        st.markdown("#### מוצרים מומלצים לקידום:")
        promo_candidates = df_analysis[
            (df_analysis['מחיר למנה'] > df_analysis['מחיר למנה'].median()) &
            (df_analysis['כמות'] < df_analysis['כמות'].median()) &
            (df_analysis['אחוז_מצטבר'] > 50)
        ][['תאור', 'קטגוריה', 'כמות', 'מחיר למנה', 'כמות_ליום']].head(10)
        
        if len(promo_candidates) > 0:
            st.dataframe(promo_candidates, hide_index=True)
            st.caption("מוצרים עם מחיר גבוה אך מכירות נמוכות - פוטנציאל להגדלת הכנסות")
        else:
            st.info("לא נמצאו מוצרים מתאימים לקידום בקריטריונים אלה")
        
        # מוצרים לשקול הסרה
        st.markdown("#### מוצרים לשקול הסרה:")
        removal_candidates = df_analysis[
            (df_analysis['כמות_ליום'] < 0.5) & 
            (df_analysis['מחיר למנה'] < df_analysis['מחיר למנה'].median())
        ][['תאור', 'קטגוריה', 'כמות', 'כמות_ליום', 'מחיר למנה']].head(10)
        
        if len(removal_candidates) > 0:
            st.dataframe(removal_candidates, hide_index=True)
            st.caption("מוצרים שנמכרים פחות מפעם ביומיים בממוצע ומחירם נמוך")
        else:
            st.info("לא נמצאו מוצרים מתאימים להסרה בקריטריונים אלה")
    
    with tab5:
        st.header("טבלת נתונים מלאה")
        
        # סינונים
        col1, col2 = st.columns(2)
        
        with col1:
            categories = ['הכל'] + list(df['קטגוריה'].unique())
            selected_category = st.selectbox("סנן לפי קטגוריה:", categories)
        
        with col2:
            sort_by = st.selectbox(
                "מיין לפי:",
                ['סכום כולל מעמ', 'כמות', 'מחיר למנה', 'תאור']
            )
        
        # הצגת טבלה
        display_df = df_sorted.copy()
        
        if selected_category != 'הכל':
            display_df = display_df[display_df['קטגוריה'] == selected_category]
        
        display_df = display_df.sort_values(sort_by, ascending=False)
        
        # עיצוב הטבלה
        display_columns = ['תאור', 'קטגוריה', 'כמות', 'סכום כולל מעמ', 'מחיר למנה', 
                          'אחוז_מההכנסות', 'כמות_ליום', 'סיווג_ABC']
        
        st.dataframe(
            display_df[display_columns].style.format({
                'סכום כולל מעמ': '₪{:,.2f}',
                'מחיר למנה': '₪{:,.2f}',
                'אחוז_מההכנסות': '{:.2f}%',
                'כמות_ליום': '{:.2f}',
                'כמות': '{:,.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # כפתור הורדה
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 הורד נתונים כ-CSV",
            data=csv,
            file_name="cafe_analysis.csv",
            mime="text/csv"
        )

else:
    st.info("👈 אנא העלה קובץ Excel בסייד-בר כדי להתחיל")
    
    st.markdown("""
    ### מה הדשבורד כולל?
    
    1. **מבט על** - סטטיסטיקות כלליות והתפלגות לפי קטגוריות
    2. **מוצרים מובילים** - המוצרים הכי מצליחים והכי חלשים
    3. **ניתוח פארטו** - זיהוי 20% המוצרים שמייצרים 80% מההכנסות
    4. **המלצות לקידום** - מטריצת BCG והמלצות ספציפיות
    5. **טבלת נתונים** - צפייה וסינון של כל הנתונים
    
    ### דרישות הקובץ:
    - פורמט: Excel (.xlsx או .xls)
    - עמודות נדרשות: תאור, כמות, סכום, סכום כולל מעמ, מחיר למנה, קטגוריה
    """)
