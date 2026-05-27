
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='CRM Intelligence Dashboard', layout='wide')

st.title('CRM Intelligence Dashboard')

st.sidebar.header('Upload Files')

buyer_file = st.sidebar.file_uploader(
    'Upload Buyer Master File',
    type=['xlsx']
)

visit_file = st.sidebar.file_uploader(
    'Upload Visit Activity File',
    type=['xlsx']
)

if buyer_file and visit_file:

    buyer_df = pd.read_excel(
        buyer_file,
        sheet_name='Buyer_Master_Apr26'
    )

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

    st.sidebar.header('Filters')

    province_filter = st.sidebar.multiselect(
        'Province',
        sorted(buyer_df['Province'].dropna().unique())
    )

    ae_filter = st.sidebar.multiselect(
        'AE Name',
        sorted(buyer_df['AE_Name'].dropna().unique())
    )

    filtered = buyer_df.copy()

    if province_filter:
        filtered = filtered[
            filtered['Province'].isin(province_filter)
        ]

    if ae_filter:
        filtered = filtered[
            filtered['AE_Name'].isin(ae_filter)
        ]

    st.header('Executive KPI')

    col1, col2, col3, col4 = st.columns(4)

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
        'Active Provinces',
        filtered['Province'].nunique()
    )

    st.header('Province Intelligence')

    province_summary = filtered.groupby('Province').agg(
        Buyers=('Customer_No', 'nunique'),
        Purchase=('Buy_Count', 'sum'),
        Login=('Login_Count', 'sum')
    ).reset_index()

    fig1 = px.bar(
        province_summary.sort_values(
            'Buyers',
            ascending=False
        ),
        x='Province',
        y='Buyers',
        title='Buyers by Province'
    )

    st.plotly_chart(fig1, use_container_width=True)

    st.header('AE Performance')

    ae_summary = filtered.groupby('AE_Name').agg(
        Buyers=('Customer_No', 'nunique'),
        Purchase=('Buy_Count', 'sum')
    ).reset_index()

    fig2 = px.bar(
        ae_summary,
        x='AE_Name',
        y='Purchase',
        color='Buyers',
        title='Purchase by AE'
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.header('Opportunity Dashboard')

    visit_summary = visit_df.groupby('Province').size().reset_index(name='Visits')

    opp = province_summary.merge(
        visit_summary,
        on='Province',
        how='left'
    )

    opp['Visits'] = opp['Visits'].fillna(0)

    opp['Opportunity_Score'] = (
        opp['Buyers'] * 2 +
        opp['Login'] * 0.5 -
        opp['Visits']
    )

    opp = opp.sort_values(
        'Opportunity_Score',
        ascending=False
    )

    st.dataframe(opp)

    fig3 = px.scatter(
        opp,
        x='Visits',
        y='Purchase',
        size='Buyers',
        color='Opportunity_Score',
        hover_name='Province',
        title='Province Opportunity Matrix'
    )

    st.plotly_chart(fig3, use_container_width=True)

    st.header('Buyer Health')

    filtered['Health_Score'] = (
        filtered['Login_Count'] * 1 +
        filtered['Buy_Count'] * 3
    )

    health = filtered[[
        'Customer_No',
        'Province',
        'AE_Name',
        'Health_Score'
    ]].sort_values(
        'Health_Score',
        ascending=False
    ).head(20)

    st.dataframe(health)

    st.header('Demand Intelligence')

    demand_summary = demand_df.groupby(
        'Vehicle_Segment'
    ).size().reset_index(name='Demand')

    fig4 = px.pie(
        demand_summary,
        names='Vehicle_Segment',
        values='Demand',
        title='Vehicle Segment Demand'
    )

    st.plotly_chart(fig4, use_container_width=True)

    st.header('Feedback Intelligence')

    if 'Feedback_Category' in feedback_df.columns:

        fb = feedback_df.groupby(
            'Feedback_Category'
        ).size().reset_index(name='Count')

        fig5 = px.bar(
            fb,
            x='Feedback_Category',
            y='Count',
            title='Feedback Category'
        )

        st.plotly_chart(fig5, use_container_width=True)

    st.header('AI Recommendation')

    st.dataframe(
        opp[[
            'Province',
            'Opportunity_Score',
            'Buyers',
            'Visits'
        ]].head(10)
    )

else:
    st.info('Upload both Excel files to start.')
