
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='CRM Intelligence Dashboard', layout='wide')

st.title('CRM Intelligence Dashboard')

st.sidebar.header('Upload Excel Files')

buyer_file = st.sidebar.file_uploader(
    'Upload Buyer Master File',
    type=['xlsx']
)

visit_file = st.sidebar.file_uploader(
    'Upload Visit Activity File',
    type=['xlsx']
)

if buyer_file and visit_file:

    # =========================
    # LOAD ALL MONTHS
    # =========================

    xls = pd.ExcelFile(buyer_file)

    buyer_frames = []

    for sheet in xls.sheet_names:
        if 'Buyer_Master_' in sheet:
            df = pd.read_excel(buyer_file, sheet_name=sheet)
            df['Period'] = sheet.replace('Buyer_Master_', '')
            buyer_frames.append(df)

    buyer_df = pd.concat(buyer_frames, ignore_index=True)

    visit_df = pd.read_excel(
        visit_file,
        sheet_name='01_Visit_Activity_Log'
    )

    demand_df = pd.read_excel(
        visit_file,
        sheet_name='02_Visit_Car_Demand_Log'
    )

    feedback_df = pd.read_excel(
        visit_file,
        sheet_name='03_Visit_Feedback_Log'
    )

    # =========================
    # FILTERS
    # =========================

    st.sidebar.header('Global Filters')

    period_filter = st.sidebar.multiselect(
        'Period',
        sorted(buyer_df['Period'].dropna().unique())
    )

    province_filter = st.sidebar.multiselect(
        'Province',
        sorted(buyer_df['Province'].dropna().unique())
    )

    ae_filter = st.sidebar.multiselect(
        'AE Name',
        sorted(buyer_df['AE_Name'].dropna().unique())
    )

    filtered = buyer_df.copy()

    if period_filter:
        filtered = filtered[
            filtered['Period'].isin(period_filter)
        ]

    if province_filter:
        filtered = filtered[
            filtered['Province'].isin(province_filter)
        ]

    if ae_filter:
        filtered = filtered[
            filtered['AE_Name'].isin(ae_filter)
        ]

    # =========================
    # HEAT CLASSIFICATION
    # =========================

    def classify(row):
        buy = row.get('Buy_Count', 0)
        login = row.get('Login_Count', 0)

        if buy >= 5 and login >= 5:
            return 'HOT'
        elif buy >= 2 or login >= 3:
            return 'WARM'
        elif login > 0:
            return 'COOL'
        else:
            return 'COLD'

    filtered['Heat_Status'] = filtered.apply(classify, axis=1)

    # =========================
    # EXECUTIVE KPI
    # =========================

    st.header('Executive Command Center')

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        'Total Buyers',
        filtered['Customer_No'].nunique()
    )

    col2.metric(
        'Total Purchase',
        int(filtered['Buy_Count'].sum())
    )

    col3.metric(
        'Total Login',
        int(filtered['Login_Count'].sum())
    )

    col4.metric(
        'Total Provinces',
        filtered['Province'].nunique()
    )

    col5.metric(
        'Total AE',
        filtered['AE_Name'].nunique()
    )

    st.info('Purpose: ดูภาพรวม CRM ทั้งองค์กร')

    # =========================
    # HEAT DISTRIBUTION
    # =========================

    st.header('Buyer Heat Distribution')

    heat = filtered.groupby(
        'Heat_Status'
    ).size().reset_index(name='Count')

    fig_heat = px.pie(
        heat,
        names='Heat_Status',
        values='Count',
        title='Hot / Warm / Cool / Cold'
    )

    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('''
    ### Formula
    - HOT = Buy สูง + Login สูง
    - WARM = มี Activity สม่ำเสมอ
    - COOL = Activity เริ่มลด
    - COLD = ไม่มี Activity
    ''')

    # =========================
    # PROVINCE ANALYSIS
    # =========================

    st.header('Province Opportunity Matrix')

    province_summary = filtered.groupby('Province').agg(
        Buyers=('Customer_No', 'nunique'),
        Purchase=('Buy_Count', 'sum'),
        Login=('Login_Count', 'sum')
    ).reset_index()

    visit_summary = visit_df.groupby(
        'Province'
    ).size().reset_index(name='Visits')

    province_summary = province_summary.merge(
        visit_summary,
        on='Province',
        how='left'
    )

    province_summary['Visits'] = province_summary['Visits'].fillna(0)

    province_summary['Opportunity_Score'] = (
        province_summary['Buyers'] * 2
        +
        province_summary['Login'] * 0.15
        +
        province_summary['Purchase'] * 0.30
        -
        province_summary['Visits'] * 0.20
    )

    fig = px.scatter(
        province_summary,
        x='Visits',
        y='Purchase',
        size='Buyers',
        color='Opportunity_Score',
        hover_name='Province',
        title='Province Opportunity Matrix'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('''
    ### Opportunity Score Formula

    Opportunity Score =
    (Buyers × 2)
    + (Login × 0.15)
    + (Purchase × 0.30)
    - (Visits × 0.20)

    Purpose:
    หาพื้นที่ที่มี Potential สูงแต่ Visit ต่ำ
    ''')

    # =========================
    # AE PERFORMANCE
    # =========================

    st.header('AE Performance')

    ae = filtered.groupby('AE_Name').agg(
        Buyers=('Customer_No', 'nunique'),
        Purchase=('Buy_Count', 'sum'),
        Login=('Login_Count', 'sum')
    ).reset_index()

    fig2 = px.bar(
        ae,
        x='AE_Name',
        y='Purchase',
        color='Buyers',
        title='Revenue by AE'
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('''
    ### Purpose
    ใช้วัด Productivity ของ AE
    ''')

    # =========================
    # BUYER HEALTH
    # =========================

    st.header('Buyer Health Score')

    filtered['Health_Score'] = (
        filtered['Login_Count'] * 1
        +
        filtered['Buy_Count'] * 3
    )

    health = filtered[[
        'Customer_No',
        'Province',
        'AE_Name',
        'Health_Score',
        'Heat_Status'
    ]].sort_values(
        'Health_Score',
        ascending=False
    ).head(20)

    st.dataframe(health)

    st.markdown('''
    ### Formula
    Health Score =
    (Login × 1)
    + (Buy × 3)

    Purpose:
    ใช้ดูความแข็งแรงของลูกค้า
    ''')

    # =========================
    # DEMAND
    # =========================

    st.header('Demand Intelligence')

    demand = demand_df.groupby(
        'Vehicle_Segment'
    ).size().reset_index(name='Demand')

    fig3 = px.pie(
        demand,
        names='Vehicle_Segment',
        values='Demand',
        title='Vehicle Segment Demand'
    )

    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('Purpose: ดูตลาดต้องการรถประเภทไหน')

    # =========================
    # FEEDBACK
    # =========================

    st.header('Feedback Intelligence')

    if 'Feedback_Category' in feedback_df.columns:

        fb = feedback_df.groupby(
            'Feedback_Category'
        ).size().reset_index(name='Count')

        fig4 = px.bar(
            fb,
            x='Feedback_Category',
            y='Count',
            title='Feedback Category'
        )

        st.plotly_chart(fig4, use_container_width=True)

    st.markdown('Purpose: ดู Pain Point ของลูกค้า')

    # =========================
    # NEXT BEST ACTION
    # =========================

    st.header('AI Recommendation')

    recommend = province_summary.sort_values(
        'Opportunity_Score',
        ascending=False
    )[[[
        'Province',
        'Opportunity_Score',
        'Buyers',
        'Visits'
    ]]].head(10)

    st.dataframe(recommend)

    st.markdown('Purpose: แนะนำจังหวัดที่ควรเข้าไปหา')

else:
    st.info('Upload both Excel files to start dashboard')
