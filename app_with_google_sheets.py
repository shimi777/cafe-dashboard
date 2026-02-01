"""
דוח פעולות ודוח מכירות יומי - קומקום
גרסה משולבת עם תמיכה ב-Google Sheets
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
    check_connection_status
)
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

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
            if connection_status['can_read']:
                st.info("📖 קריאה: פעיל")
            if connection_status['can_write']:
                st.info("✏️ כתיבה: פעיל")
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
        "יעד הכנסות שבועי (₪)",
        value=st.session_state.goals['revenue_weekly'],
        min_value=1000,
        step=1000
    )
    st.session_state.goals['revenue_monthly'] = st.number_input(
        "יעד הכנסות חודשי (₪)",
        value=st.session_state.goals['revenue_monthly'],
        min_value=10000,
        step=1000
    )

    st.markdown("### אירועים")
    st.session_state.goals['events_monthly'] = st.number_input(
        "יעד אירועים חודשי",
        value=st.session_state.goals['events_monthly'],
        min_value=1
    )
    st.session_state.goals['actual_events'] = st.number_input(
        "אירועים בפועל",
        value=st.session_state.goals['actual_events'],
        min_value=0
    )

# Display current goals
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 יעדים נוכחיים")
st.sidebar.metric("הכנסה חודשית", f"₪ {st.session_state.goals['revenue_monthly']:,.0f}")
st.sidebar.metric("הכנסה שבועית", f"₪ {st.session_state.goals['revenue_weekly']:,.0f}")

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

# Load from Cloud
if data_source in ['cloud', 'combined'] and st.session_state.cloud_connected:
    with st.spinner("טוען מהענן..."):
        cloud_df = get_cloud_history()
        if not cloud_df.empty:
            cloud_transactions = cloud_data_to_transactions(cloud_df)
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
                st.sidebar.success(f"✅ נוספו {added} רשומות!")
                st.rerun()
            else:
                st.sidebar.info("אין רשומות חדשות")

# Main Content
if not transactions:
    st.info("👈 בחר מקור נתונים והעלה קבצים או התחבר לענן")

    with st.expander("📚 הוראות הגדרה", expanded=True):
        st.markdown("""
        ### הגדרת Google Sheets

        צור קובץ `.streamlit/secrets.toml`:

        ```toml
        [google]
        type = "service_account"
        project_id = "your-project"
        private_key_id = "..."
        private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
        client_email = "your-sa@project.iam.gserviceaccount.com"
        client_id = "..."
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"

        spreadsheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ID"
        ```
        """)
else:
    # Create DataFrames
    daily_df = create_daily_summary(transactions)
    if 'date' in daily_df.columns:
        daily_df['date'] = pd.to_datetime(daily_df['date'])

    trans_df = create_detailed_transactions_df(transactions)
    items_df = create_items_summary_df(transactions)

    trans_df['Date'] = pd.to_datetime(trans_df['Date'])
    trans_df['WeekStart'] = trans_df['Date'] - trans_df['Date'].dt.weekday.apply(lambda x: pd.Timedelta(days=x))
    source_map = {'html': 'HTML', 'cloud': 'ענן', 'combined': 'משולב'}
    st.success(f"✅ {len(transactions)} טרנזקציות | מקור: {source_map.get(data_source, data_source)}")    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 דוח יומי", "🛍️ ניתוח מוצרים", "📊 סיכום פריטים",
        "📉 ניתוח מתקדם", "⬇️ הורד דוחות", "🎯 יעדים"
    ])

    # Tab 1: Daily Report
    with tab1:
        st.markdown("### 📈 דוח יומי")

        col1, col2, col3 = st.columns(3)

        daily_total = trans_df['Total Amount'].sum()
        monthly_goal = st.session_state.goals['revenue_monthly']
        achievement = (daily_total / monthly_goal * 100) if monthly_goal > 0 else 0

        col1.metric("סה״כ הכנסה", f"₪ {daily_total:,.0f}", f"{achievement:.1f}% מהיעד")
        col2.metric("ממוצע יומי", f"₪ {daily_total / max(len(daily_df), 1):,.0f}")
        col3.metric("מספר עסקאות", f"{len(trans_df):,}")

        st.markdown("---")

        col_chart, col_table = st.columns([2, 1])

        with col_chart:
            fig = px.bar(daily_df, x='date', y='total_sales', title='מכירות יומיות',
                         color='total_sales', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.dataframe(daily_df, use_container_width=True, hide_index=True)

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

        fig = px.bar(items_df.head(10).sort_values('total_amount', ascending=True),
                     x='total_amount', y='item_name', orientation='h',
                     title='10 מוצרים מובילים', color='total_amount',
                     color_continuous_scale='RdYlGn')
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(items_df, use_container_width=True, hide_index=True)

    # Tab 3: Items Summary
    with tab3:
        st.markdown("### 📊 סיכום פריטים")

        fig = px.bar(items_df.head(10), x='item_name', y='total_amount',
                     color='quantity', title='10 פריטים מובילים')
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(items_df, use_container_width=True, hide_index=True)

    # Tab 4: Advanced Analysis
    with tab4:
        st.markdown("### 📉 ניתוח מתקדם")

        weeks = sorted(trans_df['WeekStart'].unique())

        weekly_stats = []
        for i, week in enumerate(weeks, 1):
            week_data = trans_df[trans_df['WeekStart'] == week]
            rev = week_data['Total Amount'].sum()
            weekly_stats.append({
                'שבוע': f'שבוע {i}',
                'הכנסה': rev,
                'עסקאות': len(week_data),
                'תרומה ליעד (%)': (rev / monthly_goal * 100) if monthly_goal > 0 else 0
            })

        if weekly_stats:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("שבועות", len(weeks))
            col2.metric("שבוע מוביל", max(weekly_stats, key=lambda x: x['הכנסה'])['שבוע'])
            col3.metric("סה״כ", f"₪ {trans_df['Total Amount'].sum():,.0f}")
            col4.metric("ממוצע שבועי", f"₪ {trans_df['Total Amount'].sum() / max(len(weeks), 1):,.0f}")

            st.markdown("---")

            weekly_df = pd.DataFrame(weekly_stats)

            fig = go.Figure()
            for i, row in weekly_df.iterrows():
                color = '#10B981' if row['תרומה ליעד (%)'] >= 30 else '#F59E0B' if row[
                                                                                       'תרומה ליעד (%)'] >= 20 else '#EF4444'
                fig.add_trace(go.Bar(x=[row['שבוע']], y=[row['תרומה ליעד (%)']],
                                     marker_color=color, showlegend=False,
                                     text=f"{row['תרומה ליעד (%)']:.1f}%", textposition='outside'))

            if weeks:
                fig.add_hline(y=100 / len(weeks), line_dash="dash", line_color="gray",
                              annotation_text=f"יעד: {100 / len(weeks):.1f}%")

            fig.update_layout(title="תרומה שבועית ליעד החודשי", height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(weekly_df, use_container_width=True, hide_index=True)

    # Tab 5: Download
    with tab5:
        st.markdown("### ⬇️ הורד דוחות")

        col1, col2 = st.columns(2)

        with col1:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                daily_df.to_excel(writer, sheet_name='Daily', index=False)
                trans_df.to_excel(writer, sheet_name='Transactions', index=False)
                items_df.to_excel(writer, sheet_name='Items', index=False)

            st.download_button("📥 Excel", output.getvalue(),
                               f"report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with col2:
            csv = trans_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV", csv,
                               f"transactions_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

    # Tab 6: Goals
    with tab6:
        st.markdown("## 🎯 יעדים")

        goal_tab1, goal_tab2 = st.tabs(["📊 חודשי", "📈 שבועי"])

        with goal_tab1:
            st.markdown("### סיכום חודשי")

            monthly_total = trans_df['Total Amount'].sum()
            rev_pct = (monthly_total / monthly_goal * 100) if monthly_goal > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("הכנסה", f"₪ {monthly_total:,.0f}", f"יעד: ₪ {monthly_goal:,.0f}")
            col2.metric("התקדמות", f"{rev_pct:.1f}%",
                        "✅" if rev_pct >= 100 else "⏳" if rev_pct >= 80 else "❌")
            col3.metric("הפרש", f"₪ {monthly_total - monthly_goal:,.0f}")
            col4.metric("עסקאות", f"{len(trans_df):,}")

            st.markdown("---")

            # Category progress
            category_goals = st.session_state.goals['category_monthly']
            progress_data = []

            for cat, goal in category_goals.items():
                count = sum(item['quantity'] for t in transactions for item in t['items'] if cat in item['name'])
                progress_data.append({'קטגוריה': cat, 'יעד': goal, 'בפועל': count,
                                      'התקדמות': (count / goal * 100) if goal > 0 else 0})

            progress_data.append({'קטגוריה': 'הכנסות', 'יעד': monthly_goal,
                                  'בפועל': monthly_total, 'התקדמות': rev_pct})

            progress_df = pd.DataFrame(progress_data)

            fig = px.bar(progress_df, x='קטגוריה', y='התקדמות', title='התקדמות חודשית',
                         color='התקדמות', color_continuous_scale='RdYlGn', range_color=[0, 150],
                         text='התקדמות')
            fig.update_traces(texttemplate='%{y:.0f}%', textposition='outside')
            fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="יעד 100%")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(progress_df, use_container_width=True, hide_index=True)

        with goal_tab2:
            st.markdown("### ניתוח שבועי")

            weeks = sorted(trans_df['WeekStart'].unique())

            if weeks:
                week_idx = st.selectbox("בחר שבוע", range(len(weeks)),
                                        format_func=lambda x: f"שבוע {x + 1}: {weeks[x].strftime('%d/%m/%Y')}")

                selected = weeks[week_idx]
                week_trans = [t for t in transactions
                              if pd.to_datetime(t['date']).date() >= selected.date()
                              and pd.to_datetime(t['date']).date() < (selected + pd.Timedelta(days=7)).date()]

                weekly_rev = trans_df[trans_df['WeekStart'] == selected]['Total Amount'].sum()
                weekly_goal = st.session_state.goals['revenue_weekly']
                weekly_pct = (weekly_rev / weekly_goal * 100) if weekly_goal > 0 else 0

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("הכנסה", f"₪ {weekly_rev:,.0f}", f"יעד: ₪ {weekly_goal:,.0f}")
                col2.metric("התקדמות", f"{weekly_pct:.1f}%",
                            "✅" if weekly_pct >= 100 else "⏳" if weekly_pct >= 80 else "❌")
                col3.metric("הפרש", f"₪ {weekly_rev - weekly_goal:,.0f}")
                col4.metric("עסקאות", f"{len(trans_df[trans_df['WeekStart'] == selected]):,}")

                st.markdown("---")

                # Weekly category progress
                category_goals_w = st.session_state.goals['category_weekly']
                progress_w = []

                for cat, goal in category_goals_w.items():
                    count = sum(item['quantity'] for t in week_trans for item in t['items'] if cat in item['name'])
                    progress_w.append({'קטגוריה': cat, 'יעד': goal, 'בפועל': count,
                                       'התקדמות': (count / goal * 100) if goal > 0 else 0})

                progress_w.append({'קטגוריה': 'הכנסות', 'יעד': weekly_goal,
                                   'בפועל': weekly_rev, 'התקדמות': weekly_pct})

                progress_w_df = pd.DataFrame(progress_w)

                fig = px.bar(progress_w_df, x='קטגוריה', y='התקדמות',
                             title=f'התקדמות שבוע {week_idx + 1}',
                             color='התקדמות', color_continuous_scale='RdYlGn', range_color=[0, 150],
                             text='התקדמות')
                fig.update_traces(texttemplate='%{y:.0f}%', textposition='outside')
                fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="יעד 100%")
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(progress_w_df, use_container_width=True, hide_index=True)
            else:
                st.warning("אין נתונים שבועיים")
