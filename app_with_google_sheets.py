"""
דוח פעולות ודוח מכירות יומי - קומקום
גרסה משולבת עם תמיכה ב-Google Sheets וסינון תאריכים
אופטימיזציה לביצועים
"""

import streamlit as st
import pandas as pd
from html_to_excel import (
    parse_html_transactions,
    create_daily_summary,
    create_detailed_transactions_df,
    create_items_summary_df
)
from google_sheets_connector import (
    init_gsheets_connection,
    get_cloud_history,
    save_to_cloud,
    transactions_to_flat_df,
    cloud_data_to_transactions,
    check_connection_status,
    clear_cloud_cache
)
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io

# ============================================================
# CACHED FUNCTIONS - לשיפור ביצועים
# ============================================================

def get_transactions_hash(transactions):
    """יצירת hash מרשימת טרנזקציות לצורך cache key"""
    if not transactions:
        return "empty"
    # יצירת מחרוזת ייחודית מהנתונים
    key_parts = [f"{t['order_id']}_{t['date']}_{t['total']}" for t in transactions]
    return hash(tuple(key_parts))

@st.cache_data(ttl=600, show_spinner=False)
def cached_create_daily_summary(cache_key, _transactions):
    """יצירת סיכום יומי עם cache"""
    return create_daily_summary(_transactions)

@st.cache_data(ttl=600, show_spinner=False)
def cached_create_trans_df(cache_key, _transactions):
    """יצירת DataFrame טרנזקציות עם cache"""
    return create_detailed_transactions_df(_transactions)

@st.cache_data(ttl=600, show_spinner=False)
def cached_create_items_df(cache_key, _transactions):
    """יצירת DataFrame פריטים עם cache"""
    return create_items_summary_df(_transactions)

# Page Configuration
st.set_page_config(
    page_title="דוח פעולות ודוח מכירות יומי - קומקום",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session State Initialization
if 'goals' not in st.session_state:
    st.session_state.goals = {
        'category_weekly': {'טוסט אבוקדו': 24, 'כריך סלמון': 30, 'מגדל מגדנות': 54, 'סקונס': 120},
        'category_monthly': {'טוסט אבוקדו': 108, 'כריך סלמון': 135, 'מגדל מגדנות': 243, 'סקונס': 540},
        'revenue_weekly': 32500,
        'revenue_monthly': 130000,
        'events_monthly': 20,
        'actual_events': 0
    }

if 'data_source' not in st.session_state:
    st.session_state.data_source = 'html'

if 'transactions' not in st.session_state:
    st.session_state.transactions = []

if 'cloud_connected' not in st.session_state:
    st.session_state.cloud_connected = False

# Title
st.markdown("# 📊 דוח פעולות ודוח מכירות יומי - קומקום")

# Sidebar - Data Source Selection
st.sidebar.markdown("## 📁 מקור נתונים")

data_source = st.sidebar.radio(
    "בחר מקור נתונים:",
    options=['html', 'cloud', 'combined'],
    format_func=lambda x: {
        'html': '📄 קבצי HTML (מקומי)',
        'cloud': '☁️ Google Sheets (ענן)',
        'combined': '🔄 משולב (HTML + ענן)'
    }[x],
    key='data_source_selector'
)
st.session_state.data_source = data_source

# Sidebar - Google Sheets Connection Status
if data_source in ['cloud', 'combined']:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ☁️ חיבור לענן")

    with st.sidebar.expander("סטטוס חיבור", expanded=False):
        connection_status = check_connection_status()

        if connection_status['connected']:
            st.success("✅ מחובר ל-Google Sheets")
            st.session_state.cloud_connected = True
        else:
            st.error("❌ לא מחובר")
            st.session_state.cloud_connected = False
            if not connection_status['has_credentials']:
                st.warning("⚠️ חסרים credentials")
            if not connection_status['has_url']:
                st.warning("⚠️ חסר spreadsheet_url")

# Sidebar - HTML File Upload
uploaded_files = None
if data_source in ['html', 'combined']:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 העלאת קבצי HTML")

    uploaded_files = st.sidebar.file_uploader(
        "בחר קובץ/קבצי HTML",
        type=['html'],
        accept_multiple_files=True,
        help="בחר קבצי דוח פעולות"
    )

# Data Loading
transactions = []
html_transactions = []
cloud_transactions = []

# Load from HTML
if data_source in ['html', 'combined'] and uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            html_content = uploaded_file.read().decode('utf-8')
            file_transactions = parse_html_transactions(html_content)
            html_transactions.extend(file_transactions)
        except Exception as e:
            st.sidebar.error(f"❌ שגיאה: {str(e)}")

    if html_transactions:
        st.sidebar.success(f"✅ {len(html_transactions)} טרנזקציות מ-HTML")

# Load from Cloud - with session state caching
if data_source in ['cloud', 'combined'] and st.session_state.cloud_connected:
    # בדוק אם כבר יש נתונים ב-session state
    cache_key = 'cloud_transactions_cache'

    if cache_key not in st.session_state or st.session_state.get('force_reload', False):
        with st.spinner("טוען מהענן..."):
            cloud_df = get_cloud_history()
            if not cloud_df.empty:
                cloud_transactions = cloud_data_to_transactions(cloud_df)
                st.session_state[cache_key] = cloud_transactions
                st.session_state['force_reload'] = False
            else:
                st.session_state[cache_key] = []

    cloud_transactions = st.session_state.get(cache_key, [])
    if cloud_transactions:
        st.sidebar.success(f"✅ {len(cloud_transactions)} טרנזקציות מהענן")

# Combine transactions
if data_source == 'html':
    transactions = html_transactions
elif data_source == 'cloud':
    transactions = cloud_transactions
else:
    all_trans = html_transactions + cloud_transactions
    seen = set()
    for t in all_trans:
        if t['order_id'] not in seen:
            transactions.append(t)
            seen.add(t['order_id'])

st.session_state.transactions = transactions

# Cloud Sync Button
if data_source == 'combined' and html_transactions and st.session_state.cloud_connected:
    st.sidebar.markdown("---")
    if st.sidebar.button("📤 שמור לענן", type="primary"):
        with st.spinner("שומר..."):
            flat_df = transactions_to_flat_df(html_transactions)
            added = save_to_cloud(flat_df)
            if added > 0:
                clear_cloud_cache()  # ניקוי cache אחרי שמירה
                st.sidebar.success(f"✅ נוספו {added} רשומות!")
                st.rerun()
            else:
                st.sidebar.info("אין רשומות חדשות")

# Refresh button for cloud data
if data_source in ['cloud', 'combined'] and st.session_state.cloud_connected:
    if st.sidebar.button("🔄 רענן נתונים מהענן"):
        clear_cloud_cache()
        st.session_state['force_reload'] = True
        if 'cloud_transactions_cache' in st.session_state:
            del st.session_state['cloud_transactions_cache']
        st.rerun()

# DATE FILTER SECTION
start_date = None
end_date = None

if transactions:
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📅 סינון תאריכים")

    all_dates = [t['date'] for t in transactions]
    min_date = min(all_dates)
    max_date = max(all_dates)

    filter_option = st.sidebar.selectbox(
        "בחר תקופה מהירה:",
        options=['all', 'custom', 'today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month'],
        format_func=lambda x: {
            'custom': '📆 בחירה ידנית',
            'today': '📍 היום',
            'yesterday': '⬅️ אתמול',
            'this_week': '📅 השבוע הנוכחי (א׳-ש׳)',
            'last_week': '📅 השבוע שעבר',
            'this_month': '🗓️ החודש הנוכחי',
            'last_month': '🗓️ החודש שעבר',
            'all': '📊 כל הנתונים'
        }[x]
    )

    today = datetime.now().date()

    # חישוב תחילת השבוע הישראלי (יום ראשון)
    # weekday(): Sunday=6, Monday=0, ..., Saturday=5
    # אנחנו רוצים שיום ראשון יהיה תחילת השבוע
    days_since_sunday = (today.weekday() + 1) % 7  # Sunday=0, Monday=1, ..., Saturday=6

    if filter_option == 'today':
        calc_start = today
        calc_end = today
    elif filter_option == 'yesterday':
        calc_start = today - timedelta(days=1)
        calc_end = today - timedelta(days=1)
    elif filter_option == 'this_week':
        # השבוע הנוכחי - מיום ראשון
        calc_start = today - timedelta(days=days_since_sunday)
        calc_end = today
    elif filter_option == 'last_week':
        # השבוע שעבר - מיום ראשון ליום שבת
        this_week_start = today - timedelta(days=days_since_sunday)
        calc_start = this_week_start - timedelta(days=7)
        calc_end = this_week_start - timedelta(days=1)
    elif filter_option == 'this_month':
        calc_start = today.replace(day=1)
        calc_end = today
    elif filter_option == 'last_month':
        first_of_this_month = today.replace(day=1)
        calc_end = first_of_this_month - timedelta(days=1)
        calc_start = calc_end.replace(day=1)
    elif filter_option == 'all':
        calc_start = min_date
        calc_end = max_date
    else:  # custom
        calc_start = min_date
        calc_end = max_date

    # התאמת התאריכים לטווח הנתונים הקיים
    # אם התאריך המבוקש מחוץ לטווח, התאם אותו
    start_date = max(calc_start, min_date)
    end_date = min(calc_end, max_date)

    # ודא ש-start_date לא גדול מ-end_date
    if start_date > end_date:
        start_date = min_date
        end_date = max_date
        st.sidebar.warning(f"⚠️ התקופה המבוקשת מחוץ לטווח הנתונים. מציג את כל הנתונים.")

    # הצגת התאריכים המחושבים vs מה שזמין
    if filter_option not in ['all', 'custom']:
        if calc_start < min_date or calc_end > max_date:
            st.sidebar.info(f"📌 נתונים זמינים: {min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')}")

    col_date1, col_date2 = st.sidebar.columns(2)

    with col_date1:
        start_date = st.date_input(
            "מתאריך",
            value=start_date,
            min_value=min_date,
            max_value=max_date,
            key='start_date'
        )

    with col_date2:
        end_date = st.date_input(
            "עד תאריך",
            value=end_date,
            min_value=min_date,
            max_value=max_date,
            key='end_date'
        )

    # ודא שוב ש-start <= end אחרי בחירת המשתמש
    if start_date > end_date:
        st.sidebar.error("⚠️ תאריך התחלה חייב להיות לפני תאריך סיום")
        start_date, end_date = end_date, start_date

    filtered_transactions = [t for t in transactions if start_date <= t['date'] <= end_date]

    if len(filtered_transactions) == 0:
        st.sidebar.warning(f"⚠️ אין נתונים בטווח התאריכים הנבחר")
    elif len(filtered_transactions) != len(transactions):
        st.sidebar.info(f"🔍 מוצגות {len(filtered_transactions)} מתוך {len(transactions)} טרנזקציות")
    else:
        st.sidebar.success(f"📊 מוצגות כל {len(transactions)} הטרנזקציות")

    transactions = filtered_transactions

# Sidebar - Goals Settings
st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ הגדרות יעדים")

with st.sidebar.expander("📝 עדכן יעדים", expanded=False):
    st.markdown("### יעדי קטגוריה שבועיים")
    for category in list(st.session_state.goals['category_weekly'].keys()):
        st.session_state.goals['category_weekly'][category] = st.number_input(
            f"{category} (שבועי)",
            value=st.session_state.goals['category_weekly'][category],
            min_value=1,
            key=f"weekly_{category}"
        )

    st.markdown("### יעדי הכנסות")
    st.session_state.goals['revenue_weekly'] = st.number_input(
        "יעד הכנסות שבועי (₪)", value=st.session_state.goals['revenue_weekly'], min_value=1000, step=1000
    )
    st.session_state.goals['revenue_monthly'] = st.number_input(
        "יעד הכנסות חודשי (₪)", value=st.session_state.goals['revenue_monthly'], min_value=10000, step=1000
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 יעדים נוכחיים")
st.sidebar.metric("הכנסה חודשית", f"₪ {st.session_state.goals['revenue_monthly']:,.0f}")
st.sidebar.metric("הכנסה שבועית", f"₪ {st.session_state.goals['revenue_weekly']:,.0f}")

# Main Content
if not transactions:
    st.info("👈 בחר מקור נתונים והעלה קבצים או התחבר לענן")

    with st.expander("📚 הוראות הגדרה", expanded=True):
        st.markdown("""
        ### הגדרת Google Sheets
        
        צור קובץ `.streamlit/secrets.toml` עם credentials של Google Service Account.
        """)
elif len(transactions) == 0:
    st.warning("⚠️ אין נתונים בטווח התאריכים הנבחר. נסה לבחור טווח תאריכים אחר.")
else:
    # Display Filter Status Bar
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        st.metric("📅 תקופה", f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    with filter_col2:
        days_in_range = (end_date - start_date).days + 1
        st.metric("📆 ימים", f"{days_in_range}")
    with filter_col3:
        st.metric("🔢 טרנזקציות", f"{len(transactions):,}")
    with filter_col4:
        source_label = {'html': 'HTML', 'cloud': 'ענן', 'combined': 'משולב'}[data_source]
        st.metric("📁 מקור", source_label)

    st.markdown("---")

    # Create cache key from filtered transactions
    cache_key = get_transactions_hash(transactions)

    # Create DataFrames with caching
    daily_df = cached_create_daily_summary(cache_key, transactions)
    if 'date' in daily_df.columns:
        daily_df = daily_df.copy()
        daily_df['date'] = pd.to_datetime(daily_df['date'])

    trans_df = cached_create_trans_df(cache_key, transactions)
    trans_df = trans_df.copy()
    items_df = cached_create_items_df(cache_key, transactions)

    trans_df['Date'] = pd.to_datetime(trans_df['Date'])
    # שבוע ישראלי - מתחיל ביום ראשון
    # weekday(): Monday=0, Sunday=6
    # נחשב כמה ימים עברו מיום ראשון: (weekday + 1) % 7
    trans_df['WeekStart'] = trans_df['Date'] - trans_df['Date'].dt.weekday.apply(
        lambda x: pd.Timedelta(days=(x + 1) % 7)
    )

    monthly_goal = st.session_state.goals['revenue_monthly']

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 דוח יומי", "🛍️ ניתוח מוצרים", "📊 סיכום פריטים",
        "📉 ניתוח מתקדם", "⬇️ הורד דוחות", "🎯 יעדים"
    ])

    # Tab 1: Daily Report
    with tab1:
        st.markdown("### 📈 דוח יומי")

        col1, col2, col3, col4 = st.columns(4)
        daily_total = trans_df['Total Amount'].sum()
        achievement = (daily_total / monthly_goal * 100) if monthly_goal > 0 else 0

        col1.metric("סה״כ הכנסה", f"₪ {daily_total:,.0f}", f"{achievement:.1f}% מהיעד")
        col2.metric("ממוצע יומי", f"₪ {daily_total / max(len(daily_df), 1):,.0f}")
        col3.metric("מספר עסקאות", f"{len(trans_df):,}")
        col4.metric("ממוצע לעסקה", f"₪ {daily_total / max(len(trans_df), 1):,.0f}")

        st.markdown("---")

        col_chart, col_table = st.columns([2, 1])

        with col_chart:
            fig = px.bar(daily_df, x='date', y='total_sales', title='מכירות יומיות',
                        color='total_sales', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            display_daily = daily_df.copy()
            display_daily['date'] = display_daily['date'].dt.strftime('%d/%m/%Y')
            display_daily['total_sales'] = display_daily['total_sales'].apply(lambda x: f"₪ {x:,.0f}")
            display_daily.columns = ['תאריך', 'סה״כ', 'עסקאות', 'פריטים', 'מע״מ']
            st.dataframe(display_daily, use_container_width=True, hide_index=True)

    # Tab 2: Products Analysis
    with tab2:
        st.markdown("### 🛍️ ניתוח מוצרים")

        col1, col2, col3, col4 = st.columns(4)
        total_qty = items_df['quantity'].sum()
        total_rev = items_df['total_amount'].sum()

        col1.metric("פריטים ייחודיים", f"{len(items_df):,}")
        col2.metric("כמות נמכרת", f"{total_qty:,.0f}")
        col3.metric("סה״כ הכנסה", f"₪ {total_rev:,.0f}")
        col4.metric("מחיר ממוצע", f"₪ {total_rev / max(total_qty, 1):,.0f}")

        st.markdown("---")

        fig = px.bar(items_df.head(15).sort_values('total_amount', ascending=True),
                    x='total_amount', y='item_name', orientation='h',
                    title='15 מוצרים מובילים', color='total_amount', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(items_df, use_container_width=True, hide_index=True)

    # Tab 3: Items Summary
    with tab3:
        st.markdown("### 📊 סיכום פריטים")

        col1, col2 = st.columns(2)

        with col1:
            fig_pie = px.pie(items_df.head(10), values='total_amount', names='item_name',
                            title='התפלגות הכנסות - 10 מובילים')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            fig_pie2 = px.pie(items_df.nlargest(10, 'quantity'), values='quantity', names='item_name',
                             title='התפלגות כמויות - 10 מובילים')
            st.plotly_chart(fig_pie2, use_container_width=True)

        fig_scatter = px.scatter(items_df, x='quantity', y='total_amount',
                                size='total_amount', color='transaction_count',
                                hover_data=['item_name'], title='כמות מול הכנסה')
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Tab 4: Advanced Analysis
    with tab4:
        st.markdown("### 📉 ניתוח מתקדם")

        weeks = sorted(trans_df['WeekStart'].unique())

        if weeks:
            weekly_stats = []
            for i, week in enumerate(weeks, 1):
                week_data = trans_df[trans_df['WeekStart'] == week]
                rev = week_data['Total Amount'].sum()
                weekly_stats.append({
                    'שבוע': f'שבוע {i}', 'תאריך': week.strftime('%d/%m/%Y'),
                    'הכנסה': rev, 'עסקאות': len(week_data),
                    'תרומה ליעד (%)': (rev / monthly_goal * 100) if monthly_goal > 0 else 0
                })

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("שבועות", len(weeks))
            col2.metric("שבוע מוביל", max(weekly_stats, key=lambda x: x['הכנסה'])['שבוע'])
            col3.metric("סה״כ", f"₪ {trans_df['Total Amount'].sum():,.0f}")
            col4.metric("ממוצע שבועי", f"₪ {trans_df['Total Amount'].sum() / max(len(weeks), 1):,.0f}")

            st.markdown("---")
            weekly_df = pd.DataFrame(weekly_stats)

            fig = go.Figure()
            for i, row in weekly_df.iterrows():
                color = '#10B981' if row['תרומה ליעד (%)'] >= 30 else '#F59E0B' if row['תרומה ליעד (%)'] >= 20 else '#EF4444'
                fig.add_trace(go.Bar(x=[row['שבוע']], y=[row['תרומה ליעד (%)']],
                                    marker_color=color, showlegend=False,
                                    text=f"{row['תרומה ליעד (%)']:.1f}%", textposition='outside'))

            fig.add_hline(y=100/len(weeks), line_dash="dash", line_color="gray")
            fig.update_layout(title="תרומה שבועית ליעד", height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(weekly_df, use_container_width=True, hide_index=True)

    # Tab 5: Download Reports
    with tab5:
        st.markdown("### ⬇️ הורד דוחות")
        st.info(f"📅 תקופה: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

        col1, col2, col3 = st.columns(3)

        with col1:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                daily_df.to_excel(writer, sheet_name='דוח יומי', index=False)
                trans_df.to_excel(writer, sheet_name='טרנזקציות', index=False)
                items_df.to_excel(writer, sheet_name='פריטים', index=False)

            st.download_button("📥 Excel מלא", output.getvalue(),
                f"report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with col2:
            st.download_button("📥 טרנזקציות CSV",
                trans_df.to_csv(index=False).encode('utf-8-sig'),
                f"transactions_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv", "text/csv")

        with col3:
            st.download_button("📥 פריטים CSV",
                items_df.to_csv(index=False).encode('utf-8-sig'),
                f"items_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv", "text/csv")

    # Tab 6: Goals Dashboard
    with tab6:
        st.markdown("## 🎯 יעדים")

        goal_tab1, goal_tab2 = st.tabs(["📊 סיכום תקופה", "📈 ניתוח שבועי"])

        with goal_tab1:
            st.markdown(f"### סיכום: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

            period_total = trans_df['Total Amount'].sum()
            days_in_period = (end_date - start_date).days + 1
            proportional_goal = monthly_goal * (days_in_period / 30)
            rev_pct = (period_total / proportional_goal * 100) if proportional_goal > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("הכנסה בתקופה", f"₪ {period_total:,.0f}")
            col2.metric("יעד יחסי", f"₪ {proportional_goal:,.0f}")
            col3.metric("התקדמות", f"{rev_pct:.1f}%", "✅" if rev_pct >= 100 else "⏳" if rev_pct >= 80 else "❌")
            col4.metric("הפרש", f"₪ {period_total - proportional_goal:,.0f}")

            st.markdown("---")

            category_goals = st.session_state.goals['category_monthly']
            progress_data = []

            for cat, goal in category_goals.items():
                prop_goal = goal * (days_in_period / 30)
                count = sum(item['quantity'] for t in transactions for item in t['items'] if cat in item['name'])
                progress_data.append({'קטגוריה': cat, 'יעד': round(prop_goal, 1), 'בפועל': count,
                                     'התקדמות': (count / prop_goal * 100) if prop_goal > 0 else 0})

            progress_data.append({'קטגוריה': 'הכנסות', 'יעד': proportional_goal,
                                 'בפועל': period_total, 'התקדמות': rev_pct})

            progress_df = pd.DataFrame(progress_data)

            fig = px.bar(progress_df, x='קטגוריה', y='התקדמות', title='התקדמות בתקופה',
                        color='התקדמות', color_continuous_scale='RdYlGn', range_color=[0, 150], text='התקדמות')
            fig.update_traces(texttemplate='%{y:.0f}%', textposition='outside')
            fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="יעד 100%")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(progress_df, use_container_width=True, hide_index=True)

        with goal_tab2:
            st.markdown("### ניתוח שבועי")
            weeks = sorted(trans_df['WeekStart'].unique())

            if weeks:
                week_idx = st.selectbox("בחר שבוע", range(len(weeks)),
                                       format_func=lambda x: f"שבוע {x+1}: {weeks[x].strftime('%d/%m/%Y')}")

                selected = weeks[week_idx]
                week_trans = [t for t in transactions
                             if pd.to_datetime(t['date']).date() >= selected.date()
                             and pd.to_datetime(t['date']).date() < (selected + pd.Timedelta(days=7)).date()]

                weekly_rev = trans_df[trans_df['WeekStart'] == selected]['Total Amount'].sum()
                weekly_goal = st.session_state.goals['revenue_weekly']
                weekly_pct = (weekly_rev / weekly_goal * 100) if weekly_goal > 0 else 0

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("הכנסה", f"₪ {weekly_rev:,.0f}")
                col2.metric("יעד", f"₪ {weekly_goal:,.0f}")
                col3.metric("התקדמות", f"{weekly_pct:.1f}%", "✅" if weekly_pct >= 100 else "⏳" if weekly_pct >= 80 else "❌")
                col4.metric("הפרש", f"₪ {weekly_rev - weekly_goal:,.0f}")

                st.markdown("---")

                category_goals_w = st.session_state.goals['category_weekly']
                progress_w = []

                for cat, goal in category_goals_w.items():
                    count = sum(item['quantity'] for t in week_trans for item in t['items'] if cat in item['name'])
                    progress_w.append({'קטגוריה': cat, 'יעד': goal, 'בפועל': count,
                                      'התקדמות': (count / goal * 100) if goal > 0 else 0})

                progress_w.append({'קטגוריה': 'הכנסות', 'יעד': weekly_goal, 'בפועל': weekly_rev, 'התקדמות': weekly_pct})
                progress_w_df = pd.DataFrame(progress_w)

                fig = px.bar(progress_w_df, x='קטגוריה', y='התקדמות', title=f'שבוע {week_idx + 1}',
                            color='התקדמות', color_continuous_scale='RdYlGn', range_color=[0, 150], text='התקדמות')
                fig.update_traces(texttemplate='%{y:.0f}%', textposition='outside')
                fig.add_hline(y=100, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(progress_w_df, use_container_width=True, hide_index=True)
            else:
                st.warning("אין נתונים שבועיים")