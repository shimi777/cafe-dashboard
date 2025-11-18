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

# CSS מותאם לתמיכה בעברית וקלפי יעדים
st.markdown("""
    <style>
    .stMetric {
        direction: rtl;
    }
    .metric-label {
        direction: rtl;
        text-align: right;
    }
    
    /* עיצוב קלפי יעדים */
    .goal-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px;
    }
    
    .goal-title {
        font-size: 14px;
        color: #666;
        margin-bottom: 10px;
    }
    
    .goal-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .goal-percentage {
        font-size: 28px;
        font-weight: bold;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
    }
    
    .goal-success {
        background-color: #90EE90;
        color: #006400;
    }
    
    .goal-danger {
        background-color: #FFB6C1;
        color: #8B0000;
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

# סייד-בר להעלאת קבצים
with st.sidebar:
    st.header("העלאת נתונים")
    
    # קובץ נתונים כללי (90 ימים)
    uploaded_file = st.file_uploader("העלה קובץ Excel - נתונים כלליים", type=['xlsx', 'xls'], key='main_file')
    
    st.markdown("---")
    
    # קובץ נתונים חודשי ליעדים
    st.header("עמידה ביעדים")
    monthly_file = st.file_uploader("העלה קובץ Excel - נתונים חודשיים", type=['xlsx', 'xls'], key='monthly_file')
    
    # הגדרת יעדים
    st.markdown("### הגדרת יעדים חודשיים")
    
    goal_muffins = st.number_input("יעד מגדלים", value=125, step=5)
    goal_sandwiches = st.number_input("יעד טוסט אבוקדו + כריך סלמון", value=100, step=5)
    goal_tea_cups = st.number_input("יעד כוסות תה", value=80, step=5)
    goal_revenue = st.number_input("יעד הכנסות (₪)", value=110000, step=1000)
    
    st.markdown("---")
    st.markdown("### מידע על הנתונים")
    st.info("תקופה כללית: 90 ימי עבודה")

# פונקציה לחישוב עמידה ביעדים
def calculate_goal_performance(df, item_names, goal_value, is_revenue=False):
    """
    מחשב ביצועים ביחס ליעד
    
    Args:
        df: DataFrame עם הנתונים
        item_names: רשימת שמות מוצרים לחיפוש (או None אם זה הכנסות)
        goal_value: ערך היעד
        is_revenue: האם זה יעד הכנסות
    
    Returns:
        actual: ערך בפועל
        percentage: אחוז עמידה ביעד
    """
    if is_revenue:
        # סה"כ הכנסות
        actual = df['סכום כולל מעמ'].sum()
    else:
        # סינון לפי שמות מוצרים
        if isinstance(item_names, str):
            item_names = [item_names]
        
        # חיפוש גמיש - כולל חלקי טקסט
        mask = pd.Series([False] * len(df))
        for item in item_names:
            mask = mask | df['תאור'].str.contains(item, case=False, na=False)
        
        actual = df[mask]['כמות'].sum()
    
    percentage = (actual / goal_value * 100) if goal_value > 0 else 0
    
    return actual, percentage

# פונקציה ליצירת קלף יעד
def create_goal_card(title, actual, goal, is_currency=False):
    """יוצר HTML של קלף יעד"""
    percentage = (actual / goal * 100) if goal > 0 else 0
    color_class = "goal-success" if percentage >= 100 else "goal-danger"
    
    if is_currency:
        actual_text = f"₪{actual:,.0f}"
    else:
        actual_text = f"{actual:,.0f}"
    
    return f"""
    <div class="goal-card">
        <div class="goal-title">{title}</div>
        <div class="goal-value">{actual_text}</div>
        <div class="goal-percentage {color_class}">{percentage:.0f}%</div>
    </div>
    """

if uploaded_file is not None:
    # טעינת הנתונים הכלליים
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 עמידה ביעדים",
        "📊 מבט על", 
        "🏆 מוצרים מובילים", 
        "📈 ניתוח פארטו",
        "🎯 המלצות לקידום",
        "📋 טבלת נתונים"
    ])
    
    with tab1:
        st.header("🎯 עמידה ביעדים חודשיים")
        
        # בדיקה אם הועלה קובץ חודשי
        if monthly_file is not None:
            df_monthly = load_data(monthly_file)
            
            # חישוב ביצועים
            muffins_actual, muffins_pct = calculate_goal_performance(
                df_monthly, ['מגדל', 'מאפינס'], goal_muffins
            )
            
            sandwiches_actual, sandwiches_pct = calculate_goal_performance(
                df_monthly, ['טוסט אבוקדו', 'כריך סלמון'], goal_sandwiches
            )
            
            tea_actual, tea_pct = calculate_goal_performance(
                df_monthly, ['כוס תה', 'כוסות תה'], goal_tea_cups
            )
            
            revenue_actual, revenue_pct = calculate_goal_performance(
                df_monthly, None, goal_revenue, is_revenue=True
            )
            
            # שורה עליונה - ביצועים בפועל
            st.subheader("📊 ביצועים בפועל")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "מגדלים",
                    f"{muffins_actual:,.0f}",
                    f"{muffins_actual - goal_muffins:+.0f}",
                    delta_color="normal"
                )
            
            with col2:
                st.metric(
                    "טוסט אבוקדו + כריך סלמון",
                    f"{sandwiches_actual:,.0f}",
                    f"{sandwiches_actual - goal_sandwiches:+.0f}",
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "כוסות תה",
                    f"{tea_actual:,.0f}",
                    f"{tea_actual - goal_tea_cups:+.0f}",
                    delta_color="normal"
                )
            
            with col4:
                st.metric(
                    "סך הכנסות",
                    f"₪{revenue_actual:,.0f}",
                    f"₪{revenue_actual - goal_revenue:+,.0f}",
                    delta_color="normal"
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # שורה תחתונה - אחוזי עמידה ביעד
            st.subheader("📈 אחוז עמידה ביעד")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                color = "🟢" if muffins_pct >= 100 else "🔴"
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: {'#90EE90' if muffins_pct >= 100 else '#FFB6C1'}; 
                            border-radius: 10px; color: {'#006400' if muffins_pct >= 100 else '#8B0000'}'>
                    <h2>{muffins_pct:.0f}%</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                color = "🟢" if sandwiches_pct >= 100 else "🔴"
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: {'#90EE90' if sandwiches_pct >= 100 else '#FFB6C1'}; 
                            border-radius: 10px; color: {'#006400' if sandwiches_pct >= 100 else '#8B0000'}'>
                    <h2>{sandwiches_pct:.0f}%</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                color = "🟢" if tea_pct >= 100 else "🔴"
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: {'#90EE90' if tea_pct >= 100 else '#FFB6C1'}; 
                            border-radius: 10px; color: {'#006400' if tea_pct >= 100 else '#8B0000'}'>
                    <h2>{tea_pct:.0f}%</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                color = "🟢" if revenue_pct >= 100 else "🔴"
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: {'#90EE90' if revenue_pct >= 100 else '#FFB6C1'}; 
                            border-radius: 10px; color: {'#006400' if revenue_pct >= 100 else '#8B0000'}'>
                    <h2>{revenue_pct:.0f}%</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # גרף סיכום
            st.markdown("---")
            st.subheader("📊 תצוגה גרפית")
            
            goals_data = pd.DataFrame({
                'יעד': ['מגדלים', 'טוסט+כריך', 'כוסות תה', 'הכנסות'],
                'אחוז_עמידה': [muffins_pct, sandwiches_pct, tea_pct, revenue_pct],
                'ביצוע': [muffins_actual, sandwiches_actual, tea_actual, revenue_actual],
                'יעד_ערך': [goal_muffins, goal_sandwiches, goal_tea_cups, goal_revenue]
            })
            
            fig = go.Figure()
            
            # עמודות - ביצוע בפועל
            fig.add_trace(go.Bar(
                x=goals_data['יעד'],
                y=goals_data['אחוז_עמידה'],
                name='אחוז עמידה ביעד',
                marker_color=['green' if x >= 100 else 'red' for x in goals_data['אחוז_עמידה']],
                text=[f"{x:.0f}%" for x in goals_data['אחוז_עמידה']],
                textposition='outside'
            ))
            
            # קו יעד
            fig.add_hline(y=100, line_dash="dash", line_color="blue", 
                         annotation_text="יעד (100%)", annotation_position="right")
            
            fig.update_layout(
                title="עמידה ביעדים חודשיים",
                yaxis_title="אחוז עמידה (%)",
                xaxis_title="",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # טבלת פירוט
            st.markdown("---")
            st.subheader("📋 פירוט מלא")
            
            summary_df = pd.DataFrame({
                'יעד': ['מגדלים', 'טוסט אבוקדו + כריך סלמון', 'כוסות תה', 'סך הכנסות'],
                'ערך יעד': [goal_muffins, goal_sandwiches, goal_tea_cups, f"₪{goal_revenue:,}"],
                'ביצוע בפועל': [
                    f"{muffins_actual:,.0f}", 
                    f"{sandwiches_actual:,.0f}", 
                    f"{tea_actual:,.0f}", 
                    f"₪{revenue_actual:,.0f}"
                ],
                'פער': [
                    f"{muffins_actual - goal_muffins:+.0f}",
                    f"{sandwiches_actual - goal_sandwiches:+.0f}",
                    f"{tea_actual - goal_tea_cups:+.0f}",
                    f"₪{revenue_actual - goal_revenue:+,.0f}"
                ],
                'אחוז עמידה': [
                    f"{muffins_pct:.1f}%",
                    f"{sandwiches_pct:.1f}%",
                    f"{tea_pct:.1f}%",
                    f"{revenue_pct:.1f}%"
                ],
                'סטטוס': [
                    '✅ עומד ביעד' if muffins_pct >= 100 else '❌ מתחת ליעד',
                    '✅ עומד ביעד' if sandwiches_pct >= 100 else '❌ מתחת ליעד',
                    '✅ עומד ביעד' if tea_pct >= 100 else '❌ מתחת ליעד',
                    '✅ עומד ביעד' if revenue_pct >= 100 else '❌ מתחת ליעד'
                ]
            })
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
        else:
            st.warning("⚠️ יש להעלות קובץ Excel של נתונים חודשיים בסייד-בר")
            st.info("""
            💡 **הוראות:**
            1. הכן קובץ Excel עם הנתונים של החודש הנוכחי
            2. העלה אותו בסייד-בר תחת "עמידה ביעדים"
            3. הגדר את היעדים החודשיים בסייד-בר
            4. הדשבורד יחשב אוטומטית את אחוזי העמידה
            """)
    
    with tab2:
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
    
    with tab3:
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
    
    with tab4:
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
    
    with tab5:
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
    
    with tab6:
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
    
    1. **עמידה ביעדים** 🆕 - מעקב אחר יעדים חודשיים
    2. **מבט על** - סטטיסטיקות כלליות והתפלגות לפי קטגוריות
    3. **מוצרים מובילים** - המוצרים הכי מצליחים והכי חלשים
    4. **ניתוח פארטו** - זיהוי 20% המוצרים שמייצרים 80% מההכנסות
    5. **המלצות לקידום** - מטריצת BCG והמלצות ספציפיות
    6. **טבלת נתונים** - צפייה וסינון של כל הנתונים
    
    ### דרישות הקובץ:
    - **קובץ כללי:** פורמט Excel, עמודות: תאור, כמות, סכום, סכום כולל מעמ, מחיר למנה, קטגוריה
    - **קובץ חודשי ליעדים:** אותו פורמט, רק עם נתוני החודש הנוכחי
    """)
