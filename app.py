import streamlit as st
import pandas as pd
from html_to_excel import parse_html_transactions, create_daily_summary, create_detailed_transactions_df, create_items_summary_df
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="דוח פעולות ודוח מכירות יומי",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for goals
if 'goals' not in st.session_state:
    st.session_state.goals = {
        'category_weekly': {'טוסט אבוקדו': 24, 'כריך סלמון': 30, 'מגדל מגדנות': 54, 'סקונס': 120},
        'category_monthly': {'טוסט אבוקדו': 108, 'כריך סלמון': 135, 'מגדל מגדנות': 243, 'סקונס': 540},
        'revenue_weekly': 32500,
        'revenue_monthly': 130000,
        'events_monthly': 20,
        'actual_events': 0
    }

# Title
st.markdown("# 📊 דוח פעולות ודוח מכירות יומי")
st.markdown("עלה קובץ HTML של דוח פעולות וקבל ניתוח מקיף של המכירות היומיות")

# Sidebar
st.sidebar.markdown("## הגדרות")

# Settings section in sidebar - BEFORE file upload so goals are set
st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ הגדרות יעדים")

with st.sidebar.expander("📝 עדכן יעדים", expanded=False):
    st.markdown("### יעדי קטגוריה שבועיים")
    for category in st.session_state.goals['category_weekly'].keys():
        st.session_state.goals['category_weekly'][category] = st.number_input(
            f"{category} (שבועי)",
            value=st.session_state.goals['category_weekly'][category],
            min_value=1,
            key=f"weekly_{category}"
        )
    
    st.markdown("### יעדי קטגוריה חודשיים")
    for category in st.session_state.goals['category_monthly'].keys():
        st.session_state.goals['category_monthly'][category] = st.number_input(
            f"{category} (חודשי)",
            value=st.session_state.goals['category_monthly'][category],
            min_value=1,
            key=f"monthly_{category}"
        )
    
    st.markdown("### יעדי הכנסות")
    st.session_state.goals['revenue_weekly'] = st.number_input(
        "יעד הכנסות שבועי (₪)",
        value=st.session_state.goals['revenue_weekly'],
        min_value=1000,
        step=1000,
        key="revenue_weekly"
    )
    
    st.session_state.goals['revenue_monthly'] = st.number_input(
        "יעד הכנסות חודשי (₪)",
        value=st.session_state.goals['revenue_monthly'],
        min_value=10000,
        step=1000,
        key="revenue_monthly"
    )
    
    st.markdown("### יעדים אחרים")
    st.session_state.goals['events_monthly'] = st.number_input(
        "יעד מספר אירועים חודשי",
        value=st.session_state.goals['events_monthly'],
        min_value=1,
        key="events_monthly"
    )
    
    st.success("✅ היעדים עודכנו!")

# Display current goals in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 יעדים נוכחיים")
st.sidebar.metric("הכנסה חודשית (יעד)", f"₪ {st.session_state.goals['revenue_monthly']:,.0f}")
st.sidebar.metric("הכנסה שבועית (יעד)", f"₪ {st.session_state.goals['revenue_weekly']:,.0f}")

# Multiple files upload
uploaded_files = st.sidebar.file_uploader(
    "בחר קובץ/קבצי HTML",
    type=['html'],
    accept_multiple_files=True,
    help="בחר קבצי דוח פעולות - תוכל לבחור מספר קבצים שיצטברו"
)

if uploaded_files and len(uploaded_files) > 0:
    # Read and parse all HTML files
    all_transactions = []
    file_count = 0
    
    try:
        for uploaded_file in uploaded_files:
            # Read and parse HTML
            html_content = uploaded_file.read().decode('utf-8')
            
            # Parse transactions
            file_transactions = parse_html_transactions(html_content)
            all_transactions.extend(file_transactions)
            file_count += 1
        
        transactions = all_transactions
        
        if len(transactions) == 0:
            st.error("לא נמצאו טרנזקציות בקבצי ה-HTML")
        else:
            st.success(f"✅ טוען {file_count} קבצ{'ים' if file_count > 1 else ''} עם {len(transactions)} טרנזקציות")
            
            # Create DataFrames from transactions
            daily_df = create_daily_summary(transactions)
            # Ensure date column is datetime in daily_df
            if 'date' in daily_df.columns:
                daily_df['date'] = pd.to_datetime(daily_df['date'])
            
            trans_df = create_detailed_transactions_df(transactions)
            items_df = create_items_summary_df(transactions)
            
            # Add WeekStart column for weekly analysis - fix for Series
            trans_df['Date'] = pd.to_datetime(trans_df['Date'])
            trans_df['WeekStart'] = trans_df['Date'] - trans_df['Date'].dt.weekday.apply(lambda x: pd.Timedelta(days=x))
            
            # Create tabs
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📈 דוח יומי",
                "🛍️ ניתוח מוצרים",
                "📊 סיכום פריטים",
                "📉 ניתוח מתקדם",
                "⬇️ הורד דוחות",
                "🎯 יעדים"
            ])
            
            # Tab 1: Daily Report with Goals
            with tab1:
                st.markdown("### 📈 דוח יומי")
                
                # Display metrics with goals
                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                
                with col_metrics1:
                    daily_total = trans_df['Total Amount'].sum()
                    monthly_goal = st.session_state.goals['revenue_monthly']
                    achievement_pct = (daily_total / monthly_goal * 100) if monthly_goal > 0 else 0
                    st.metric(
                        "סה״כ הכנסה",
                        f"₪ {daily_total:,.0f}",
                        delta=f"{achievement_pct:.1f}% מהיעד"
                    )
                
                with col_metrics2:
                    avg_daily = daily_total / len(daily_df) if len(daily_df) > 0 else 0
                    st.metric(
                        "ממוצע יומי",
                        f"₪ {avg_daily:,.0f}",
                        delta=None
                    )
                
                with col_metrics3:
                    transaction_count = len(trans_df)
                    st.metric(
                        "מספר עסקאות",
                        f"{transaction_count:,}",
                        delta=None
                    )
                
                st.markdown("---")
                
                # Daily sales chart
                col_daily1, col_daily2 = st.columns([2, 1])
                
                with col_daily1:
                    fig_daily = px.bar(
                        daily_df,
                        x='date',
                        y='total_sales',
                        title='מכירות יומיות',
                        labels={'date': 'תאריך', 'total_sales': 'סכום (₪)'},
                        color='total_sales',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_daily, use_container_width=True)
                
                with col_daily2:
                    st.dataframe(daily_df, use_container_width=True, hide_index=True)
            
            # Tab 2: Products Analysis (REPLACED from transactions)
            with tab2:
                st.markdown("### 🛍️ ניתוח מוצרים ופריטים")
                
                # Summary metrics
                col_prod1, col_prod2, col_prod3, col_prod4 = st.columns(4)
                
                with col_prod1:
                    st.metric("מספר פריטים ייחודיים", f"{len(items_df):,}")
                
                with col_prod2:
                    total_quantity = items_df['quantity'].sum()
                    st.metric("סה״כ כמות נמכרת", f"{total_quantity:,}")
                
                with col_prod3:
                    total_revenue_items = items_df['total_amount'].sum()
                    st.metric("סה״כ הכנסה", f"₪ {total_revenue_items:,.0f}")
                
                with col_prod4:
                    avg_price = total_revenue_items / total_quantity if total_quantity > 0 else 0
                    st.metric("מחיר ממוצע למוצר", f"₪ {avg_price:,.0f}")
                
                st.markdown("---")
                
                # Products sorted by revenue
                st.markdown("#### 📊 מוצרים לפי הכנסה (מהגבוה לנמוך)")
                
                items_sorted = items_df.sort_values('total_amount', ascending=False)
                
                # Create detailed product table
                product_detail = items_sorted[['item_name', 'quantity', 'total_amount']].copy()
                product_detail['הכנסה ממוצעת'] = (product_detail['total_amount'] / product_detail['quantity']).round(2)
                product_detail = product_detail.rename(columns={
                    'item_name': 'שם מוצר',
                    'quantity': 'כמות',
                    'total_amount': 'סה״כ הכנסה (₪)'
                })
                
                # Format for display
                product_detail['סה״כ הכנסה (₪)'] = product_detail['סה״כ הכנסה (₪)'].apply(lambda x: f"₪ {x:,.0f}")
                product_detail['הכנסה ממוצעת'] = product_detail['הכנסה ממוצעת'].apply(lambda x: f"₪ {x:,.0f}")
                
                st.dataframe(product_detail, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                
                # Chart: Top 10 products
                st.markdown("#### 📈 10 מוצרים המובילים")
                
                fig_products = px.bar(
                    items_df.head(10).sort_values('total_amount', ascending=True),
                    x='total_amount',
                    y='item_name',
                    title='10 מוצרים המובילים לפי הכנסה',
                    labels={'item_name': 'שם מוצר', 'total_amount': 'הכנסה (₪)'},
                    color='total_amount',
                    color_continuous_scale='RdYlGn',
                    orientation='h'
                )
                st.plotly_chart(fig_products, use_container_width=True)
                
                st.markdown("---")
                
                # Chart: Quantity vs Revenue
                st.markdown("#### 📊 כמות מול הכנסה (צפצוף)")
                
                fig_scatter = px.scatter(
                    items_df,
                    x='quantity',
                    y='total_amount',
                    size='total_amount',
                    color='total_amount',
                    hover_data=['item_name'],
                    title='כמות מול הכנסה',
                    labels={'quantity': 'כמות', 'total_amount': 'הכנסה (₪)'},
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Tab 3: Items Summary (legacy - can remove or modify)
            with tab3:
                st.markdown("### 📊 סיכום פריטים (ארכיון)")
                
                # Top items chart
                fig_items = px.bar(
                    items_df.head(10),
                    x='item_name',
                    y='total_amount',
                    color='quantity',
                    title='10 פריטים המובילים לפי הכנסה',
                    labels={'item_name': 'שם פריט', 'total_amount': 'הכנסה (₪)', 'quantity': 'כמות'}
                )
                st.plotly_chart(fig_items, use_container_width=True)
                
                st.dataframe(items_df, use_container_width=True, hide_index=True)
            
            # Tab 4: Analysis
            with tab4:
                st.markdown("### 📉 ניתוח מתקדם וכלים אנליטיים")
                
                # Calculate weekly statistics
                weekly_stats = []
                weeks_list = sorted(trans_df['WeekStart'].unique())
                
                for week_num, week_start in enumerate(weeks_list, 1):
                    week_data = trans_df[trans_df['WeekStart'] == week_start]
                    
                    week_revenue = week_data['Total Amount'].sum()
                    week_transactions = len(week_data)
                    week_days = week_data['Date'].nunique()
                    
                    # Calculate percentage contribution to monthly goal
                    total_monthly_revenue = trans_df['Total Amount'].sum()
                    revenue_percentage = (week_revenue / total_monthly_revenue * 100) if total_monthly_revenue > 0 else 0
                    
                    # Calculate contribution to monthly revenue goal - USE CURRENT SESSION STATE
                    monthly_goal = st.session_state.goals['revenue_monthly']
                    goal_contribution = (week_revenue / monthly_goal * 100) if monthly_goal > 0 else 0
                    
                    weekly_stats.append({
                        'שבוע': f'שבוע {week_num}',
                        'תאריך התחלה': week_start,
                        'הכנסה (₪)': week_revenue,
                        'עסקאות': week_transactions,
                        'ימים': week_days,
                        'משקל בחודש (%)': revenue_percentage,
                        'תרומה ליעד חודשי (%)': goal_contribution
                    })
                
                # Display metrics
                st.markdown("### 📊 סטטיסטיקת שבועות")
                
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                
                with metrics_col1:
                    st.metric(
                        "סה״כ שבועות",
                        f"{len(weeks_list)}",
                        delta=None
                    )
                
                # Calculate best week
                best_week_revenue = trans_df.groupby('WeekStart')['Total Amount'].sum()
                best_week_date = best_week_revenue.idxmax()
                best_week_num = len([w for w in weeks_list if w <= best_week_date])
                
                with metrics_col2:
                    st.metric(
                        "שבוע מחזק",
                        f"שבוע {best_week_num}",
                        delta=None
                    )
                
                with metrics_col3:
                    total_revenue = trans_df['Total Amount'].sum()
                    st.metric(
                        "סה״כ הכנסה",
                        f"₪ {total_revenue:,.0f}",
                        delta=None
                    )
                
                with metrics_col4:
                    st.metric(
                        "ממוצע לשבוע",
                        f"₪ {total_revenue / len(weeks_list):,.0f}",
                        delta=None
                    )
                
                st.markdown("---")
                
                # Stacked bar chart - Weekly contribution to monthly goal
                st.markdown("### 📈 משקל כל שבוע בעמידה ביעד החודשי")
                st.info(f"הגרף מציג את תרומת כל שבוע ליעד ההכנסה החודשי (יעד: ₪{st.session_state.goals['revenue_monthly']:,.0f}). הקו המפריד מציין את גבול היעד (100%)")
                
                # Create stacked bar chart
                weekly_contribution_df = pd.DataFrame(weekly_stats)
                
                fig_weekly_contribution = go.Figure()
                
                colors = ['#EF4444', '#F59E0B', '#10B981', '#06B6D4']  # Red, Amber, Green, Cyan
                
                for idx, (week_label, week_data) in enumerate(zip(
                    weekly_contribution_df['שבוע'],
                    weekly_contribution_df['תרומה ליעד חודשי (%)']
                )):
                    # Determine color based on contribution
                    if week_data >= 50:
                        color = colors[2]  # Green - good
                    elif week_data >= 30:
                        color = colors[1]  # Amber - okay
                    else:
                        color = colors[0]  # Red - low
                    
                    fig_weekly_contribution.add_trace(go.Bar(
                        x=[week_label],
                        y=[week_data],
                        name=week_label,
                        text=f'<b>{week_data:.1f}%</b><br/>שבוע {idx+1}',
                        textposition='outside',
                        marker_color=color,
                        hovertemplate=f'<b>{week_label}</b><br/>תרומה: {week_data:.1f}%<br/>הכנסה: ₪{weekly_contribution_df.iloc[idx]["הכנסה (₪)"]:,.0f}<extra></extra>',
                        showlegend=False
                    ))
                
                # Add 100% reference line
                fig_weekly_contribution.add_hline(
                    y=100/len(weeks_list),
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"יעד לשבוע: {100/len(weeks_list):.1f}%",
                    annotation_position="right"
                )
                
                fig_weekly_contribution.update_layout(
                    title=f"משקל כל שבוע בעמידה ביעד החודשי (סה״כ {st.session_state.goals['revenue_monthly']:,.0f}₪)",
                    xaxis_title="שבוע",
                    yaxis_title="תרומה ליעד (%)",
                    height=450,
                    template='plotly_white',
                    hovermode='x unified',
                    barmode='group'
                )
                
                st.plotly_chart(fig_weekly_contribution, use_container_width=True)
                
                st.markdown("---")
                
                # Weekly detailed table
                st.markdown("### 📋 טבלת פרטי שבועות")
                
                display_df = weekly_contribution_df[['שבוע', 'הכנסה (₪)', 'עסקאות', 'ימים', 'משקל בחודש (%)', 'תרומה ליעד חודשי (%)']].copy()
                
                # Format the dataframe for display
                display_df['הכנסה (₪)'] = display_df['הכנסה (₪)'].apply(lambda x: f"₪ {x:,.0f}")
                display_df['משקל בחודש (%)'] = display_df['משקל בחודש (%)'].apply(lambda x: f"{x:.1f}%")
                display_df['תרומה ליעד חודשי (%)'] = display_df['תרומה ליעד חודשי (%)'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("---")
                
                # Advanced statistics
                st.markdown("### 📊 סטטיסטיקה מתקדמת")
                
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                
                with stats_col1:
                    week_revenues = [w['הכנסה (₪)'] for w in weekly_stats]
                    avg_revenue = sum(week_revenues) / len(week_revenues) if week_revenues else 0
                    st.metric(
                        "הכנסה ממוצעת לשבוע",
                        f"₪ {avg_revenue:,.0f}",
                        delta=None
                    )
                
                with stats_col2:
                    std_dev = (sum((x - avg_revenue) ** 2 for x in week_revenues) / len(week_revenues)) ** 0.5 if week_revenues else 0
                    st.metric(
                        "סטיית תקן",
                        f"₪ {std_dev:,.0f}",
                        delta="תנודתיות גבוהה" if std_dev > avg_revenue * 0.3 else "תנודתיות נמוכה"
                    )
                
                with stats_col3:
                    best_week = max(weekly_stats, key=lambda x: x['הכנסה (₪)'])
                    best_week_num = weekly_stats.index(best_week) + 1
                    st.metric(
                        "השבוע הטוב ביותר",
                        f"שבוע {best_week_num}",
                        delta=f"₪ {best_week['הכנסה (₪)']:,.0f}"
                    )
            
            # Tab 5: Download
            with tab5:
                st.markdown("### ⬇️ הורד דוחות")
                
                # Export to Excel (placeholder)
                st.info("הדוח מכיל 3 גיליונות: דוח יומי, טרנזקציות מפורטות וסיכום פריטים")
            
            # Tab 6: Goals Dashboard
            with tab6:
                st.markdown("## 🎯 עמידה ביעדים שבועיים וחודשיים")
                
                # Define category goals from session state
                category_goals_weekly = st.session_state.goals['category_weekly']
                category_goals_monthly = st.session_state.goals['category_monthly']
                monthly_revenue_goal = st.session_state.goals['revenue_monthly']
                weekly_revenue_goal = st.session_state.goals['revenue_weekly']
                events_monthly_goal = st.session_state.goals['events_monthly']
                
                # Create two main tabs: Monthly Summary and Weekly Analysis
                goal_tab1, goal_tab2 = st.tabs(["📊 סיכום חודשי מצטבר", "📈 ניתוח שבועי בלבד"])
                
                # ==================== MONTHLY SUMMARY TAB ====================
                with goal_tab1:
                    st.markdown("### 📊 סיכום חודשי מצטבר (כל השבועות)")
                    st.info("התצוגה הזו מציגה את סיכום כל הנתונים המעובדים - היא מוקדשת לחיתוכים בין שבועות בלבד")
                    
                    # Calculate monthly totals across all data
                    monthly_category_totals = {}
                    for category in category_goals_monthly.keys():
                        count = 0
                        for trans in transactions:
                            for item in trans['items']:
                                if category in item['name']:
                                    count += item['quantity']
                        monthly_category_totals[category] = count
                    
                    # Calculate monthly revenue
                    monthly_total_revenue = trans_df['Total Amount'].sum()
                    
                    # Create monthly progress
                    monthly_progress = []
                    for category, goal in category_goals_monthly.items():
                        count = monthly_category_totals.get(category, 0)
                        percentage = (count / goal * 100) if goal > 0 else 0
                        monthly_progress.append({
                            'קטגוריה': category,
                            'יעד': goal,
                            'בפועל': count,
                            'אחוז התקדמות': percentage
                        })
                    
                    # Add revenue progress
                    revenue_percentage = (monthly_total_revenue / monthly_revenue_goal * 100) if monthly_revenue_goal > 0 else 0
                    
                    # Display KPI cards
                    col_monthly1, col_monthly2, col_monthly3, col_monthly4 = st.columns(4)
                    
                    with col_monthly1:
                        st.metric(
                            "סה״כ הכנסה",
                            f"₪ {monthly_total_revenue:,.0f}",
                            delta=f"יעד: ₪ {monthly_revenue_goal:,.0f}"
                        )
                    
                    with col_monthly2:
                        st.metric(
                            "התקדמות הכנסה",
                            f"{revenue_percentage:.1f}%",
                            delta="✅ הושג!" if revenue_percentage >= 100 else "⏳ קרוב ליעד" if revenue_percentage >= 80 else "❌ רחוק"
                        )
                    
                    with col_monthly3:
                        st.metric(
                            "הפרש מהיעד",
                            f"₪ {monthly_total_revenue - monthly_revenue_goal:,.0f}",
                            delta=None
                        )
                    
                    with col_monthly4:
                        st.metric(
                            "מספר עסקאות",
                            f"{len(trans_df):,}",
                            delta=None
                        )
                    
                    st.markdown("---")
                    
                    # Monthly progress chart
                    monthly_summary_data = {
                        'קטגוריה': [item['קטגוריה'] for item in monthly_progress] + ['הכנסות'],
                        'אחוז התקדמות (%)': [item['אחוז התקדמות'] for item in monthly_progress] + [revenue_percentage]
                    }
                    
                    monthly_summary_df = pd.DataFrame(monthly_summary_data)
                    
                    fig_monthly = px.bar(
                        monthly_summary_df,
                        x='קטגוריה',
                        y='אחוז התקדמות (%)',
                        title="סיכום חודשי - התקדמות באחוזים",
                        color='אחוז התקדמות (%)',
                        color_continuous_scale='RdYlGn',
                        range_color=[0, 150],
                        text='אחוז התקדמות (%)'
                    )
                    
                    fig_monthly.update_traces(textposition='outside', texttemplate='%{y:.0f}%')
                    
                    fig_monthly.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="יעד (100%)", annotation_position="right")
                    
                    fig_monthly.update_layout(
                        yaxis_title='התקדמות (%)',
                        height=450,
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig_monthly, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Monthly progress table
                    st.markdown("### 📋 טבלת התקדמות חודשית לפי קטגוריה")
                    
                    progress_display = pd.DataFrame(monthly_progress)
                    progress_display['יעד'] = progress_display['יעד'].astype(int)
                    progress_display['בפועל'] = progress_display['בפועל'].astype(int)
                    progress_display['אחוז התקדמות'] = progress_display['אחוז התקדמות'].apply(lambda x: f"{x:.1f}%")
                    progress_display = progress_display.rename(columns={'קטגוריה': 'קטגוריה', 'יעד': 'יעד', 'בפועל': 'בפועל', 'אחוז התקדמות': 'התקדמות (%)'})
                    
                    st.dataframe(progress_display, use_container_width=True, hide_index=True)
                
                # ==================== WEEKLY ANALYSIS TAB ====================
                with goal_tab2:
                    st.markdown("### 📈 ניתוח שבועי בלבד")
                    st.info("בחר שבוע לצפייה בניתוח מפורט של שבוע זה")
                    
                    # Get unique weeks
                    available_weeks = sorted(trans_df['WeekStart'].unique())
                    
                    if len(available_weeks) > 0:
                        # Week selector
                        selected_week_idx = st.selectbox(
                            "בחר שבוע",
                            options=range(len(available_weeks)),
                            format_func=lambda x: f"שבוע {x+1}: {available_weeks[x].strftime('%d/%m/%Y')}"
                        )
                        
                        selected_week = available_weeks[selected_week_idx]
                        
                        # Filter data for selected week
                        filtered_transactions = [t for t in transactions if pd.to_datetime(t['date']).date() >= selected_week.date() and pd.to_datetime(t['date']).date() < (selected_week + pd.Timedelta(days=7)).date()]
                        
                        # Calculate weekly totals
                        weekly_category_totals = {}
                        for category in category_goals_weekly.keys():
                            count = 0
                            for trans in filtered_transactions:
                                for item in trans['items']:
                                    if category in item['name']:
                                        count += item['quantity']
                            weekly_category_totals[category] = count
                        
                        # Calculate weekly revenue
                        weekly_total_revenue = trans_df[trans_df['WeekStart'] == selected_week]['Total Amount'].sum()
                        
                        # Create progress for week
                        weekly_progress = []
                        for category, goal in category_goals_weekly.items():
                            count = weekly_category_totals.get(category, 0)
                            percentage = (count / goal * 100) if goal > 0 else 0
                            weekly_progress.append({
                                'קטגוריה': category,
                                'יעד': goal,
                                'בפועל': count,
                                'אחוז התקדמות': percentage
                            })
                        
                        # Revenue progress
                        weekly_revenue_percentage = (weekly_total_revenue / weekly_revenue_goal * 100) if weekly_revenue_goal > 0 else 0
                        
                        # Display KPI cards
                        col_weekly1, col_weekly2, col_weekly3, col_weekly4 = st.columns(4)
                        
                        with col_weekly1:
                            st.metric(
                                "סה״כ הכנסה",
                                f"₪ {weekly_total_revenue:,.0f}",
                                delta=f"יעד: ₪ {weekly_revenue_goal:,.0f}"
                            )
                        
                        with col_weekly2:
                            st.metric(
                                "התקדמות הכנסה",
                                f"{weekly_revenue_percentage:.1f}%",
                                delta="✅ הושג!" if weekly_revenue_percentage >= 100 else "⏳ קרוב ליעד" if weekly_revenue_percentage >= 80 else "❌ רחוק"
                            )
                        
                        with col_weekly3:
                            st.metric(
                                "הפרש מהיעד",
                                f"₪ {weekly_total_revenue - weekly_revenue_goal:,.0f}",
                                delta=None
                            )
                        
                        with col_weekly4:
                            st.metric(
                                "מספר עסקאות",
                                f"{len(trans_df[trans_df['WeekStart'] == selected_week]):,}",
                                delta=None
                            )
                        
                        st.markdown("---")
                        
                        # Weekly progress chart
                        weekly_summary_data = {
                            'קטגוריה': [item['קטגוריה'] for item in weekly_progress] + ['הכנסות'],
                            'אחוז התקדמות (%)': [item['אחוז התקדמות'] for item in weekly_progress] + [weekly_revenue_percentage]
                        }
                        
                        weekly_summary_df = pd.DataFrame(weekly_summary_data)
                        
                        fig_goals = px.bar(
                            weekly_summary_df,
                            x='קטגוריה',
                            y='אחוז התקדמות (%)',
                            title=f"שבוע {selected_week_idx + 1} - התקדמות באחוזים",
                            color='אחוז התקדמות (%)',
                            color_continuous_scale='RdYlGn',
                            range_color=[0, 150],
                            text='אחוז התקדמות (%)'
                        )
                        
                        fig_goals.update_traces(textposition='outside', texttemplate='%{y:.0f}%')
                        
                        fig_goals.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="יעד (100%)", annotation_position="right")
                        
                        fig_goals.update_layout(
                            yaxis_title='התקדמות (%)',
                            height=450,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig_goals, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # Weekly progress table
                        st.markdown(f"### 📋 טבלת התקדמות לשבוע {selected_week_idx + 1}")
                        
                        progress_display_weekly = pd.DataFrame(weekly_progress)
                        progress_display_weekly['יעד'] = progress_display_weekly['יעד'].astype(int)
                        progress_display_weekly['בפועל'] = progress_display_weekly['בפועל'].astype(int)
                        progress_display_weekly['אחוז התקדמות'] = progress_display_weekly['אחוז התקדמות'].apply(lambda x: f"{x:.1f}%")
                        progress_display_weekly = progress_display_weekly.rename(columns={'קטגוריה': 'קטגוריה', 'יעד': 'יעד', 'בפועל': 'בפועל', 'אחוז התקדמות': 'התקדמות (%)'})
                        
                        st.dataframe(progress_display_weekly, use_container_width=True, hide_index=True)
                    else:
                        st.warning("אין נתונים שבועיים זמינים")
    
    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ: {str(e)}")

else:
    st.info("👈 בחר קבצי HTML מהסיידבר כדי להתחיל")
