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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📈 דוח יומי", "🛍️ ניתוח מוצרים", "📊 סיכום פריטים",
        "📉 ניתוח מתקדם", "📅 השוואת חודשים", "🕐 שעות שיא",
        "🛒 ניתוח סל", "🏆 הישגים", "⬇️ הורד דוחות", "🎯 יעדים"
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

    # Tab 5: Month Comparison
    with tab5:
        st.markdown("## 📅 השוואת חודשים")

        # Get all transactions (not filtered) for comparison
        all_trans_for_comparison = st.session_state.transactions

        if not all_trans_for_comparison:
            st.warning("אין נתונים להשוואה")
        else:
            # Get available months from all data
            all_dates = [t['date'] for t in all_trans_for_comparison]

            # Create month options
            months_available = sorted(set((d.year, d.month) for d in all_dates), reverse=True)

            if len(months_available) < 2:
                st.warning("נדרשים לפחות 2 חודשים של נתונים להשוואה")
            else:
                # Month selectors
                col_m1, col_m2 = st.columns(2)

                month_names_heb = {
                    1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
                    5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
                    9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
                }

                def format_month(ym):
                    return f"{month_names_heb[ym[1]]} {ym[0]}"

                with col_m1:
                    current_month_idx = st.selectbox(
                        "חודש נוכחי:",
                        options=range(len(months_available)),
                        format_func=lambda x: format_month(months_available[x]),
                        index=0,
                        key='current_month_select'
                    )
                    current_month = months_available[current_month_idx]

                with col_m2:
                    # Filter out the current month from previous options
                    prev_options = [i for i in range(len(months_available)) if i != current_month_idx]
                    default_prev = prev_options[0] if prev_options else 0

                    previous_month_idx = st.selectbox(
                        "חודש קודם:",
                        options=prev_options,
                        format_func=lambda x: format_month(months_available[x]),
                        index=0,
                        key='previous_month_select'
                    )
                    previous_month = months_available[previous_month_idx]

                # Filter transactions for each month
                def get_month_transactions(transactions, year, month):
                    return [t for t in transactions if t['date'].year == year and t['date'].month == month]

                current_trans = get_month_transactions(all_trans_for_comparison, current_month[0], current_month[1])
                previous_trans = get_month_transactions(all_trans_for_comparison, previous_month[0], previous_month[1])

                st.markdown("---")

                # === REVENUE COMPARISON ===
                st.markdown("### 💰 השוואת הכנסות")

                current_revenue = sum(t['total'] for t in current_trans)
                previous_revenue = sum(t['total'] for t in previous_trans)

                revenue_diff = current_revenue - previous_revenue
                revenue_pct_change = ((current_revenue / previous_revenue) - 1) * 100 if previous_revenue > 0 else 0

                col_rev1, col_rev2, col_rev3, col_rev4 = st.columns(4)

                with col_rev1:
                    st.metric(
                        f"📊 {format_month(current_month)}",
                        f"₪ {current_revenue:,.0f}",
                        delta=None
                    )

                with col_rev2:
                    st.metric(
                        f"📊 {format_month(previous_month)}",
                        f"₪ {previous_revenue:,.0f}",
                        delta=None
                    )

                with col_rev3:
                    delta_str = f"₪ {revenue_diff:+,.0f}"
                    st.metric(
                        "הפרש",
                        f"₪ {abs(revenue_diff):,.0f}",
                        delta=delta_str,
                        delta_color="normal"
                    )

                with col_rev4:
                    st.metric(
                        "שינוי באחוזים",
                        f"{revenue_pct_change:+.1f}%",
                        delta="עלייה 📈" if revenue_pct_change > 0 else "ירידה 📉" if revenue_pct_change < 0 else "ללא שינוי",
                        delta_color="normal" if revenue_pct_change >= 0 else "inverse"
                    )

                # Revenue comparison chart
                revenue_comparison_df = pd.DataFrame({
                    'חודש': [format_month(previous_month), format_month(current_month)],
                    'הכנסה': [previous_revenue, current_revenue]
                })

                fig_revenue = px.bar(
                    revenue_comparison_df,
                    x='חודש',
                    y='הכנסה',
                    title='השוואת הכנסות בין חודשים',
                    color='חודש',
                    color_discrete_sequence=['#94a3b8', '#3b82f6'],
                    text='הכנסה'
                )
                fig_revenue.update_traces(texttemplate='₪%{text:,.0f}', textposition='outside')
                fig_revenue.update_layout(showlegend=False, yaxis_title='הכנסה (₪)')
                st.plotly_chart(fig_revenue, use_container_width=True)

                st.markdown("---")

                # === TRANSACTIONS COMPARISON ===
                st.markdown("### 🧾 השוואת עסקאות")

                current_trans_count = len(current_trans)
                previous_trans_count = len(previous_trans)
                trans_diff = current_trans_count - previous_trans_count
                trans_pct_change = ((current_trans_count / previous_trans_count) - 1) * 100 if previous_trans_count > 0 else 0

                current_avg = current_revenue / current_trans_count if current_trans_count > 0 else 0
                previous_avg = previous_revenue / previous_trans_count if previous_trans_count > 0 else 0
                avg_diff = current_avg - previous_avg

                col_trans1, col_trans2, col_trans3, col_trans4 = st.columns(4)

                with col_trans1:
                    st.metric(f"עסקאות {format_month(current_month)}", f"{current_trans_count:,}")

                with col_trans2:
                    st.metric(f"עסקאות {format_month(previous_month)}", f"{previous_trans_count:,}")

                with col_trans3:
                    st.metric("שינוי בעסקאות", f"{trans_diff:+,}", delta=f"{trans_pct_change:+.1f}%")

                with col_trans4:
                    st.metric("שינוי בממוצע לעסקה", f"₪ {avg_diff:+,.0f}",
                             delta=f"נוכחי: ₪{current_avg:,.0f}")

                st.markdown("---")

                # === CATEGORY COMPARISON ===
                st.markdown("### 📦 השוואה לפי קטגוריות מוצרים")

                # Define categories to track
                categories = list(st.session_state.goals['category_monthly'].keys())

                # Calculate category totals for each month
                def get_category_stats(transactions, categories):
                    stats = {}
                    for cat in categories:
                        count = sum(
                            item['quantity']
                            for t in transactions
                            for item in t['items']
                            if cat in item['name']
                        )
                        revenue = sum(
                            item['total_price']
                            for t in transactions
                            for item in t['items']
                            if cat in item['name']
                        )
                        stats[cat] = {'quantity': count, 'revenue': revenue}
                    return stats

                current_cat_stats = get_category_stats(current_trans, categories)
                previous_cat_stats = get_category_stats(previous_trans, categories)

                # Create comparison dataframe
                category_comparison = []
                for cat in categories:
                    curr_qty = current_cat_stats[cat]['quantity']
                    prev_qty = previous_cat_stats[cat]['quantity']
                    curr_rev = current_cat_stats[cat]['revenue']
                    prev_rev = previous_cat_stats[cat]['revenue']

                    qty_change = curr_qty - prev_qty
                    qty_pct = ((curr_qty / prev_qty) - 1) * 100 if prev_qty > 0 else (100 if curr_qty > 0 else 0)

                    rev_change = curr_rev - prev_rev
                    rev_pct = ((curr_rev / prev_rev) - 1) * 100 if prev_rev > 0 else (100 if curr_rev > 0 else 0)

                    category_comparison.append({
                        'קטגוריה': cat,
                        f'כמות {format_month(previous_month)}': prev_qty,
                        f'כמות {format_month(current_month)}': curr_qty,
                        'שינוי כמות': qty_change,
                        'שינוי %': qty_pct,
                        f'הכנסה {format_month(previous_month)}': prev_rev,
                        f'הכנסה {format_month(current_month)}': curr_rev,
                        'שינוי הכנסה': rev_change
                    })

                category_df = pd.DataFrame(category_comparison)

                # Category quantity comparison chart
                cat_qty_data = []
                for cat in categories:
                    cat_qty_data.append({'קטגוריה': cat, 'חודש': format_month(previous_month),
                                        'כמות': previous_cat_stats[cat]['quantity']})
                    cat_qty_data.append({'קטגוריה': cat, 'חודש': format_month(current_month),
                                        'כמות': current_cat_stats[cat]['quantity']})

                cat_qty_df = pd.DataFrame(cat_qty_data)

                fig_cat_qty = px.bar(
                    cat_qty_df,
                    x='קטגוריה',
                    y='כמות',
                    color='חודש',
                    barmode='group',
                    title='השוואת כמויות לפי קטגוריה',
                    color_discrete_sequence=['#94a3b8', '#10b981'],
                    text='כמות'
                )
                fig_cat_qty.update_traces(textposition='outside')
                st.plotly_chart(fig_cat_qty, use_container_width=True)

                # Category revenue comparison chart
                cat_rev_data = []
                for cat in categories:
                    cat_rev_data.append({'קטגוריה': cat, 'חודש': format_month(previous_month),
                                        'הכנסה': previous_cat_stats[cat]['revenue']})
                    cat_rev_data.append({'קטגוריה': cat, 'חודש': format_month(current_month),
                                        'הכנסה': current_cat_stats[cat]['revenue']})

                cat_rev_df = pd.DataFrame(cat_rev_data)

                fig_cat_rev = px.bar(
                    cat_rev_df,
                    x='קטגוריה',
                    y='הכנסה',
                    color='חודש',
                    barmode='group',
                    title='השוואת הכנסות לפי קטגוריה',
                    color_discrete_sequence=['#94a3b8', '#f59e0b'],
                    text='הכנסה'
                )
                fig_cat_rev.update_traces(texttemplate='₪%{text:,.0f}', textposition='outside')
                fig_cat_rev.update_layout(yaxis_title='הכנסה (₪)')
                st.plotly_chart(fig_cat_rev, use_container_width=True)

                # Detailed comparison table
                st.markdown("#### 📋 טבלת השוואה מפורטת")

                display_cat_df = category_df.copy()

                # Format columns
                for col in display_cat_df.columns:
                    if 'הכנסה' in col and col != 'שינוי הכנסה':
                        display_cat_df[col] = display_cat_df[col].apply(lambda x: f"₪ {x:,.0f}")
                    elif col == 'שינוי הכנסה':
                        display_cat_df[col] = display_cat_df[col].apply(lambda x: f"₪ {x:+,.0f}")
                    elif col == 'שינוי %':
                        display_cat_df[col] = display_cat_df[col].apply(lambda x: f"{x:+.1f}%")
                    elif col == 'שינוי כמות':
                        display_cat_df[col] = display_cat_df[col].apply(lambda x: f"{x:+.0f}")

                st.dataframe(display_cat_df, use_container_width=True, hide_index=True)

                st.markdown("---")

                # === TOP PRODUCTS COMPARISON ===
                st.markdown("### 🏆 השוואת מוצרים מובילים")

                # Get top products for each month
                def get_top_products(transactions, n=10):
                    products = {}
                    for t in transactions:
                        for item in t['items']:
                            name = item['name']
                            if name not in products:
                                products[name] = {'quantity': 0, 'revenue': 0}
                            products[name]['quantity'] += item['quantity']
                            products[name]['revenue'] += item['total_price']

                    # Sort by revenue
                    sorted_products = sorted(products.items(), key=lambda x: x[1]['revenue'], reverse=True)
                    return dict(sorted_products[:n])

                current_top = get_top_products(current_trans, 10)
                previous_top = get_top_products(previous_trans, 10)

                # Combine unique products
                all_top_products = set(current_top.keys()) | set(previous_top.keys())

                top_products_comparison = []
                for product in all_top_products:
                    curr_rev = current_top.get(product, {}).get('revenue', 0)
                    prev_rev = previous_top.get(product, {}).get('revenue', 0)
                    change = curr_rev - prev_rev

                    top_products_comparison.append({
                        'מוצר': product,
                        f'{format_month(previous_month)}': prev_rev,
                        f'{format_month(current_month)}': curr_rev,
                        'שינוי': change
                    })

                # Sort by current month revenue
                top_products_df = pd.DataFrame(top_products_comparison)
                top_products_df = top_products_df.sort_values(f'{format_month(current_month)}', ascending=False).head(15)

                # Format for display
                display_top_df = top_products_df.copy()
                for col in display_top_df.columns:
                    if col != 'מוצר':
                        if col == 'שינוי':
                            display_top_df[col] = display_top_df[col].apply(lambda x: f"₪ {x:+,.0f}")
                        else:
                            display_top_df[col] = display_top_df[col].apply(lambda x: f"₪ {x:,.0f}")

                st.dataframe(display_top_df, use_container_width=True, hide_index=True)

    # Tab 6: Peak Hours Analysis
    with tab6:
        st.markdown("## 🕐 ניתוח שעות שיא")
        st.info("ניתוח דפוסי מכירות לפי שעות ביום וימים בשבוע - לאופטימיזציה של משמרות ושיווק")

        if not transactions:
            st.warning("אין נתונים לניתוח")
        else:
            # Prepare hourly data
            hourly_data = []
            daily_data_by_day = []

            day_names_heb = {
                6: 'ראשון', 0: 'שני', 1: 'שלישי', 2: 'רביעי',
                3: 'חמישי', 4: 'שישי', 5: 'שבת'
            }

            for t in transactions:
                if t['time']:
                    hour = t['time'].hour
                    # Get day of week (Sunday = 0 in Israeli week)
                    day_num = (t['date'].weekday() + 1) % 7
                    day_name = day_names_heb.get(t['date'].weekday(), 'לא ידוע')

                    hourly_data.append({
                        'hour': hour,
                        'day_num': day_num,
                        'day_name': day_name,
                        'revenue': t['total'],
                        'items': len(t['items'])
                    })

            if hourly_data:
                hourly_df = pd.DataFrame(hourly_data)

                # === HOURLY SUMMARY ===
                st.markdown("### ⏰ סיכום לפי שעות")

                hourly_summary = hourly_df.groupby('hour').agg({
                    'revenue': ['sum', 'count', 'mean']
                }).round(2)
                hourly_summary.columns = ['סה״כ הכנסה', 'מספר עסקאות', 'ממוצע לעסקה']
                hourly_summary = hourly_summary.reset_index()
                hourly_summary.columns = ['שעה', 'סה״כ הכנסה', 'מספר עסקאות', 'ממוצע לעסקה']

                # Find peak hours
                peak_hour = hourly_summary.loc[hourly_summary['סה״כ הכנסה'].idxmax(), 'שעה']
                peak_revenue = hourly_summary['סה״כ הכנסה'].max()
                low_hour = hourly_summary.loc[hourly_summary['סה״כ הכנסה'].idxmin(), 'שעה']

                col_h1, col_h2, col_h3, col_h4 = st.columns(4)

                with col_h1:
                    st.metric("🔥 שעת שיא", f"{int(peak_hour):02d}:00", delta=f"₪ {peak_revenue:,.0f}")

                with col_h2:
                    st.metric("😴 שעה חלשה", f"{int(low_hour):02d}:00")

                with col_h3:
                    morning_rev = hourly_df[hourly_df['hour'].between(6, 12)]['revenue'].sum()
                    st.metric("🌅 בוקר (6-12)", f"₪ {morning_rev:,.0f}")

                with col_h4:
                    afternoon_rev = hourly_df[hourly_df['hour'].between(12, 18)]['revenue'].sum()
                    st.metric("☀️ צהריים (12-18)", f"₪ {afternoon_rev:,.0f}")

                # Hourly revenue chart
                fig_hourly = px.bar(
                    hourly_summary,
                    x='שעה',
                    y='סה״כ הכנסה',
                    title='הכנסות לפי שעה ביום',
                    color='סה״כ הכנסה',
                    color_continuous_scale='RdYlGn',
                    text='מספר עסקאות'
                )
                fig_hourly.update_traces(texttemplate='%{text} עסקאות', textposition='outside')
                fig_hourly.update_layout(xaxis=dict(dtick=1), yaxis_title='הכנסה (₪)')
                st.plotly_chart(fig_hourly, use_container_width=True)

                st.markdown("---")

                # === DAILY SUMMARY ===
                st.markdown("### 📅 סיכום לפי ימים בשבוע")

                # Sort by Israeli week order
                day_order = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']

                daily_summary = hourly_df.groupby('day_name').agg({
                    'revenue': ['sum', 'count', 'mean']
                }).round(2)
                daily_summary.columns = ['סה״כ הכנסה', 'מספר עסקאות', 'ממוצע לעסקה']
                daily_summary = daily_summary.reset_index()
                daily_summary.columns = ['יום', 'סה״כ הכנסה', 'מספר עסקאות', 'ממוצע לעסקה']

                # Sort by day order
                daily_summary['sort_order'] = daily_summary['יום'].apply(lambda x: day_order.index(x) if x in day_order else 7)
                daily_summary = daily_summary.sort_values('sort_order').drop('sort_order', axis=1)

                # Find best and worst days
                best_day = daily_summary.loc[daily_summary['סה״כ הכנסה'].idxmax(), 'יום']
                worst_day = daily_summary.loc[daily_summary['סה״כ הכנסה'].idxmin(), 'יום']

                col_d1, col_d2 = st.columns(2)

                with col_d1:
                    st.metric("🏆 יום הכי חזק", best_day)

                with col_d2:
                    st.metric("📉 יום הכי חלש", worst_day)

                fig_daily = px.bar(
                    daily_summary,
                    x='יום',
                    y='סה״כ הכנסה',
                    title='הכנסות לפי יום בשבוע',
                    color='סה״כ הכנסה',
                    color_continuous_scale='Viridis',
                    text='מספר עסקאות'
                )
                fig_daily.update_traces(texttemplate='%{text}', textposition='outside')
                fig_daily.update_layout(yaxis_title='הכנסה (₪)')
                st.plotly_chart(fig_daily, use_container_width=True)

                st.markdown("---")

                # === HEATMAP ===
                st.markdown("### 🗺️ מפת חום - שעות × ימים")

                # Create pivot table for heatmap
                heatmap_data = hourly_df.groupby(['day_name', 'hour'])['revenue'].sum().reset_index()
                heatmap_pivot = heatmap_data.pivot(index='day_name', columns='hour', values='revenue').fillna(0)

                # Reorder days
                heatmap_pivot = heatmap_pivot.reindex(day_order)
                heatmap_pivot = heatmap_pivot.dropna(how='all')

                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    labels=dict(x="שעה", y="יום", color="הכנסה (₪)"),
                    title='מפת חום: הכנסות לפי יום ושעה',
                    color_continuous_scale='RdYlGn',
                    aspect='auto'
                )
                fig_heatmap.update_layout(
                    xaxis=dict(dtick=1),
                    height=400
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

                st.markdown("---")

                # === RECOMMENDATIONS ===
                st.markdown("### 💡 המלצות")

                col_rec1, col_rec2 = st.columns(2)

                with col_rec1:
                    st.success(f"""
                    **שעות שיא למשמרות מחוזקות:**
                    - שעת השיא: {int(peak_hour):02d}:00
                    - מומלץ לחזק איוש בשעות אלו
                    - שקול מבצעים בשעות החלשות ({int(low_hour):02d}:00)
                    """)

                with col_rec2:
                    st.info(f"""
                    **ימים להתמקדות:**
                    - היום החזק: {best_day}
                    - היום החלש: {worst_day}
                    - שקול פעילות שיווקית ב{worst_day}
                    """)

                # Detailed tables
                with st.expander("📋 טבלאות מפורטות"):
                    st.markdown("**לפי שעות:**")
                    display_hourly = hourly_summary.copy()
                    display_hourly['סה״כ הכנסה'] = display_hourly['סה״כ הכנסה'].apply(lambda x: f"₪ {x:,.0f}")
                    display_hourly['ממוצע לעסקה'] = display_hourly['ממוצע לעסקה'].apply(lambda x: f"₪ {x:,.0f}")
                    display_hourly['שעה'] = display_hourly['שעה'].apply(lambda x: f"{int(x):02d}:00")
                    st.dataframe(display_hourly, use_container_width=True, hide_index=True)

                    st.markdown("**לפי ימים:**")
                    display_daily = daily_summary.copy()
                    display_daily['סה״כ הכנסה'] = display_daily['סה״כ הכנסה'].apply(lambda x: f"₪ {x:,.0f}")
                    display_daily['ממוצע לעסקה'] = display_daily['ממוצע לעסקה'].apply(lambda x: f"₪ {x:,.0f}")
                    st.dataframe(display_daily, use_container_width=True, hide_index=True)
            else:
                st.warning("אין נתוני שעות בטרנזקציות")

    # Tab 7: Basket Analysis
    with tab7:
        st.markdown("## 🛒 ניתוח סל קניות")
        st.info("גלה אילו מוצרים נקנים יחד - לבניית קומבינציות ומבצעים")

        if not transactions:
            st.warning("אין נתונים לניתוח")
        else:
            # Analyze baskets with 2+ items
            multi_item_transactions = [t for t in transactions if len(t['items']) >= 2]

            if not multi_item_transactions:
                st.warning("אין עסקאות עם יותר ממוצר אחד")
            else:
                st.markdown(f"### 📊 סטטיסטיקות כלליות")

                total_trans = len(transactions)
                multi_trans = len(multi_item_transactions)
                avg_basket_size = sum(len(t['items']) for t in transactions) / total_trans if total_trans > 0 else 0
                avg_basket_value = sum(t['total'] for t in transactions) / total_trans if total_trans > 0 else 0

                col_b1, col_b2, col_b3, col_b4 = st.columns(4)

                with col_b1:
                    st.metric("סה״כ עסקאות", f"{total_trans:,}")

                with col_b2:
                    pct_multi = (multi_trans / total_trans * 100) if total_trans > 0 else 0
                    st.metric("עסקאות עם 2+ מוצרים", f"{multi_trans:,}", delta=f"{pct_multi:.1f}%")

                with col_b3:
                    st.metric("ממוצע פריטים לסל", f"{avg_basket_size:.1f}")

                with col_b4:
                    st.metric("ממוצע ערך סל", f"₪ {avg_basket_value:,.0f}")

                st.markdown("---")

                # === PRODUCT PAIRS ===
                st.markdown("### 👫 זוגות מוצרים פופולריים")
                st.caption("מוצרים שנקנים יחד באותה עסקה")

                from collections import Counter
                from itertools import combinations

                # Count product pairs
                pair_counter = Counter()

                for t in multi_item_transactions:
                    # Get unique product names in transaction
                    products = list(set(item['name'] for item in t['items']))

                    if len(products) >= 2:
                        # Generate all pairs
                        for pair in combinations(sorted(products), 2):
                            pair_counter[pair] += 1

                # Get top pairs
                top_pairs = pair_counter.most_common(20)

                if top_pairs:
                    pairs_data = []
                    for pair, count in top_pairs:
                        pairs_data.append({
                            'מוצר 1': pair[0],
                            'מוצר 2': pair[1],
                            'מספר עסקאות משותפות': count,
                            'אחוז מעסקאות מרובות': round(count / multi_trans * 100, 1)
                        })

                    pairs_df = pd.DataFrame(pairs_data)

                    # Top pairs chart
                    top_10_pairs = pairs_df.head(10).copy()
                    top_10_pairs['זוג'] = top_10_pairs['מוצר 1'] + ' + ' + top_10_pairs['מוצר 2']

                    fig_pairs = px.bar(
                        top_10_pairs.sort_values('מספר עסקאות משותפות', ascending=True),
                        x='מספר עסקאות משותפות',
                        y='זוג',
                        orientation='h',
                        title='10 זוגות המוצרים הפופולריים ביותר',
                        color='מספר עסקאות משותפות',
                        color_continuous_scale='Greens',
                        text='מספר עסקאות משותפות'
                    )
                    fig_pairs.update_traces(textposition='outside')
                    fig_pairs.update_layout(height=500, yaxis_title='', xaxis_title='מספר עסקאות')
                    st.plotly_chart(fig_pairs, use_container_width=True)

                    # Pairs table
                    st.markdown("#### 📋 טבלת זוגות מלאה")
                    display_pairs = pairs_df.copy()
                    display_pairs['אחוז מעסקאות מרובות'] = display_pairs['אחוז מעסקאות מרובות'].apply(lambda x: f"{x}%")
                    st.dataframe(display_pairs, use_container_width=True, hide_index=True)

                st.markdown("---")

                # === FREQUENTLY BOUGHT WITH ===
                st.markdown("### 🔗 לקוחות שקנו X קנו גם...")

                # Get all unique products
                all_products = set()
                for t in transactions:
                    for item in t['items']:
                        all_products.add(item['name'])

                selected_product = st.selectbox(
                    "בחר מוצר:",
                    options=sorted(all_products),
                    key='basket_product_select'
                )

                if selected_product:
                    # Find transactions containing this product
                    related_trans = [t for t in multi_item_transactions
                                    if any(item['name'] == selected_product for item in t['items'])]

                    if related_trans:
                        # Count other products in these transactions
                        related_products = Counter()
                        for t in related_trans:
                            for item in t['items']:
                                if item['name'] != selected_product:
                                    related_products[item['name']] += 1

                        top_related = related_products.most_common(10)

                        if top_related:
                            st.markdown(f"**מוצרים שנקנו יחד עם '{selected_product}':**")

                            related_data = []
                            for product, count in top_related:
                                pct = count / len(related_trans) * 100
                                related_data.append({
                                    'מוצר': product,
                                    'מספר פעמים': count,
                                    'אחוז': pct
                                })

                            related_df = pd.DataFrame(related_data)

                            fig_related = px.bar(
                                related_df,
                                x='מוצר',
                                y='אחוז',
                                title=f'מוצרים שנקנים עם "{selected_product}"',
                                color='אחוז',
                                color_continuous_scale='Blues',
                                text='מספר פעמים'
                            )
                            fig_related.update_traces(texttemplate='%{text} פעמים', textposition='outside')
                            fig_related.update_layout(yaxis_title='אחוז מהעסקאות (%)')
                            st.plotly_chart(fig_related, use_container_width=True)
                        else:
                            st.info("לא נמצאו מוצרים קשורים")
                    else:
                        st.info(f"'{selected_product}' לא נקנה יחד עם מוצרים אחרים")

                st.markdown("---")

                # === BASKET SIZE ANALYSIS ===
                st.markdown("### 📦 ניתוח גודל סל")

                basket_sizes = [len(t['items']) for t in transactions]
                basket_values = [t['total'] for t in transactions]

                basket_analysis = []
                for size in sorted(set(basket_sizes)):
                    matching = [(s, v) for s, v in zip(basket_sizes, basket_values) if s == size]
                    avg_value = sum(v for _, v in matching) / len(matching)
                    basket_analysis.append({
                        'גודל סל': size,
                        'מספר עסקאות': len(matching),
                        'ממוצע ערך': avg_value
                    })

                basket_df = pd.DataFrame(basket_analysis)

                col_bs1, col_bs2 = st.columns(2)

                with col_bs1:
                    fig_size = px.bar(
                        basket_df,
                        x='גודל סל',
                        y='מספר עסקאות',
                        title='התפלגות גודל סל',
                        color='מספר עסקאות',
                        color_continuous_scale='Purples'
                    )
                    st.plotly_chart(fig_size, use_container_width=True)

                with col_bs2:
                    fig_value = px.bar(
                        basket_df,
                        x='גודל סל',
                        y='ממוצע ערך',
                        title='ערך ממוצע לפי גודל סל',
                        color='ממוצע ערך',
                        color_continuous_scale='Oranges',
                        text='ממוצע ערך'
                    )
                    fig_value.update_traces(texttemplate='₪%{text:,.0f}', textposition='outside')
                    fig_value.update_layout(yaxis_title='ערך ממוצע (₪)')
                    st.plotly_chart(fig_value, use_container_width=True)

                # === COMBO RECOMMENDATIONS ===
                st.markdown("### 💡 המלצות לקומבינציות")

                if top_pairs and len(top_pairs) >= 3:
                    top_3_pairs = top_pairs[:3]

                    st.success(f"""
                    **קומבינציות מומלצות למבצעים:**
                    
                    1. 🥇 **{top_3_pairs[0][0][0]}** + **{top_3_pairs[0][0][1]}** ({top_3_pairs[0][1]} עסקאות משותפות)
                    2. 🥈 **{top_3_pairs[1][0][0]}** + **{top_3_pairs[1][0][1]}** ({top_3_pairs[1][1]} עסקאות משותפות)
                    3. 🥉 **{top_3_pairs[2][0][0]}** + **{top_3_pairs[2][0][1]}** ({top_3_pairs[2][1]} עסקאות משותפות)
                    """)

    # Tab 8: Achievements
    with tab8:
        st.markdown("## 🏆 לוח הישגים")
        st.info("שיאים, הישגים ואבני דרך")

        if not transactions:
            st.warning("אין נתונים להצגה")
        else:
            all_trans_for_achievements = st.session_state.transactions

            st.markdown("### 🎖️ שיאים אישיים")

            # === REVENUE RECORDS ===
            col_r1, col_r2, col_r3 = st.columns(3)

            # Best day ever
            daily_totals = {}
            for t in all_trans_for_achievements:
                date = t['date']
                if date not in daily_totals:
                    daily_totals[date] = 0
                daily_totals[date] += t['total']

            if daily_totals:
                best_day = max(daily_totals.items(), key=lambda x: x[1])
                worst_day = min(daily_totals.items(), key=lambda x: x[1])

                with col_r1:
                    st.metric(
                        "🏆 יום המכירות הכי טוב",
                        f"₪ {best_day[1]:,.0f}",
                        delta=best_day[0].strftime('%d/%m/%Y')
                    )

                with col_r2:
                    # Biggest single transaction
                    biggest_trans = max(all_trans_for_achievements, key=lambda x: x['total'])
                    st.metric(
                        "💰 העסקה הגדולה ביותר",
                        f"₪ {biggest_trans['total']:,.0f}",
                        delta=f"הזמנה #{biggest_trans['order_id']}"
                    )

                with col_r3:
                    # Most transactions in a day
                    daily_trans_count = {}
                    for t in all_trans_for_achievements:
                        date = t['date']
                        if date not in daily_trans_count:
                            daily_trans_count[date] = 0
                        daily_trans_count[date] += 1

                    busiest_day = max(daily_trans_count.items(), key=lambda x: x[1])
                    st.metric(
                        "🔥 היום הכי עמוס",
                        f"{busiest_day[1]} עסקאות",
                        delta=busiest_day[0].strftime('%d/%m/%Y')
                    )

            st.markdown("---")

            # === PRODUCT RECORDS ===
            st.markdown("### 🥇 שיאי מוצרים")

            col_p1, col_p2, col_p3 = st.columns(3)

            # Best selling product (by quantity)
            product_qty = {}
            product_revenue = {}

            for t in all_trans_for_achievements:
                for item in t['items']:
                    name = item['name']
                    if name not in product_qty:
                        product_qty[name] = 0
                        product_revenue[name] = 0
                    product_qty[name] += item['quantity']
                    product_revenue[name] += item['total_price']

            if product_qty:
                top_qty_product = max(product_qty.items(), key=lambda x: x[1])
                top_revenue_product = max(product_revenue.items(), key=lambda x: x[1])

                with col_p1:
                    st.metric(
                        "📦 המוצר הנמכר ביותר (כמות)",
                        top_qty_product[0][:20] + ('...' if len(top_qty_product[0]) > 20 else ''),
                        delta=f"{top_qty_product[1]:,.0f} יחידות"
                    )

                with col_p2:
                    st.metric(
                        "💵 המוצר המכניס ביותר",
                        top_revenue_product[0][:20] + ('...' if len(top_revenue_product[0]) > 20 else ''),
                        delta=f"₪ {top_revenue_product[1]:,.0f}"
                    )

                with col_p3:
                    # Unique products sold
                    unique_products = len(product_qty)
                    st.metric(
                        "🎨 מגוון מוצרים שנמכרו",
                        f"{unique_products} מוצרים",
                        delta=None
                    )

            st.markdown("---")

            # === STREAKS AND MILESTONES ===
            st.markdown("### 🎯 אבני דרך")

            total_revenue = sum(t['total'] for t in all_trans_for_achievements)
            total_transactions = len(all_trans_for_achievements)
            total_items = sum(len(t['items']) for t in all_trans_for_achievements)
            total_days = len(daily_totals) if daily_totals else 0

            # Milestone cards
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)

            with col_m1:
                milestone_revenue = (total_revenue // 10000) * 10000
                next_milestone = milestone_revenue + 10000
                progress = (total_revenue - milestone_revenue) / 10000 * 100
                st.metric(
                    "💰 אבן דרך הכנסות",
                    f"₪ {milestone_revenue:,.0f}",
                    delta=f"{progress:.0f}% ל-₪{next_milestone:,.0f}"
                )

            with col_m2:
                milestone_trans = (total_transactions // 100) * 100
                st.metric(
                    "🧾 אבן דרך עסקאות",
                    f"{milestone_trans:,}",
                    delta=f"סה״כ: {total_transactions:,}"
                )

            with col_m3:
                milestone_items = (total_items // 500) * 500
                st.metric(
                    "📦 אבן דרך פריטים",
                    f"{milestone_items:,}",
                    delta=f"סה״כ: {total_items:,}"
                )

            with col_m4:
                st.metric(
                    "📅 ימי פעילות",
                    f"{total_days} ימים",
                    delta=f"ממוצע: ₪{total_revenue/max(total_days,1):,.0f}/יום"
                )

            st.markdown("---")

            # === ACHIEVEMENTS BADGES ===
            st.markdown("### 🏅 תגי הישגים")

            achievements = []

            # Check achievements
            if total_revenue >= 100000:
                achievements.append(("💎", "מאה אלף", "הגעת ל-₪100,000 הכנסות!"))
            if total_revenue >= 50000:
                achievements.append(("🥇", "חמישים אלף", "הגעת ל-₪50,000 הכנסות!"))
            if total_revenue >= 10000:
                achievements.append(("🥈", "עשרת אלפים", "הגעת ל-₪10,000 הכנסות!"))

            if total_transactions >= 1000:
                achievements.append(("🔥", "אלף עסקאות", "ביצעת 1,000 עסקאות!"))
            if total_transactions >= 500:
                achievements.append(("⭐", "500 עסקאות", "ביצעת 500 עסקאות!"))
            if total_transactions >= 100:
                achievements.append(("✨", "100 עסקאות", "ביצעת 100 עסקאות!"))

            if daily_totals:
                if best_day[1] >= 10000:
                    achievements.append(("🚀", "יום עשרת אלפים", f"יום עם ₪10,000+ ({best_day[0].strftime('%d/%m')})"))
                if best_day[1] >= 5000:
                    achievements.append(("💪", "יום חמשת אלפים", f"יום עם ₪5,000+ ({best_day[0].strftime('%d/%m')})"))

            if len(product_qty) >= 50:
                achievements.append(("🎨", "מגוון רחב", "מכרת 50+ מוצרים שונים!"))

            if biggest_trans['total'] >= 500:
                achievements.append(("👑", "עסקת VIP", f"עסקה של ₪500+ (#{biggest_trans['order_id']})"))

            if achievements:
                cols = st.columns(min(len(achievements), 4))
                for i, (emoji, title, desc) in enumerate(achievements):
                    with cols[i % 4]:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin: 5px;">
                            <span style="font-size: 40px;">{emoji}</span>
                            <h4 style="color: white; margin: 10px 0 5px 0;">{title}</h4>
                            <p style="color: #e0e0e0; font-size: 12px; margin: 0;">{desc}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("המשך למכור כדי לפתוח הישגים! 🎮")

            st.markdown("---")

            # === LEADERBOARD ===
            st.markdown("### 📊 לוח מובילים - ימים")

            if daily_totals:
                top_days = sorted(daily_totals.items(), key=lambda x: x[1], reverse=True)[:10]

                leaderboard_data = []
                for rank, (date, revenue) in enumerate(top_days, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                    leaderboard_data.append({
                        'דירוג': medal,
                        'תאריך': date.strftime('%d/%m/%Y'),
                        'יום': ['שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת', 'ראשון'][date.weekday()],
                        'הכנסה': f"₪ {revenue:,.0f}",
                        'עסקאות': daily_trans_count.get(date, 0)
                    })

                leaderboard_df = pd.DataFrame(leaderboard_data)
                st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)

    # Tab 9: Download Reports
    with tab9:
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

    # Tab 10: Goals Dashboard
    with tab10:
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
                st.warning("איןעןא  נתונים שבועיים")