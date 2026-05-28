import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CRM Intelligence Dashboard v9", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #eef3ff 0%, #f8fbff 100%);
    border-right: 1px solid #dbe7f5;
}
div[data-testid="metric-container"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
    border-radius: 18px;
    padding: 16px;
    border: 1px solid #dfe8f4;
    box-shadow: 0 10px 24px rgba(31,60,136,0.08);
}
h1, h2, h3 {color: #21324f; letter-spacing: -0.02em;}
.stPlotlyChart {
    background: white;
    border-radius: 18px;
    padding: 8px;
    box-shadow: 0 8px 22px rgba(31,60,136,0.06);
    border: 1px solid #edf2f7;
}
.small-note {color:#667085; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

HEALTH_ORDER = ["HOT", "WARM", "COOL", "COLD"]
LOGIN_ORDER = ["HOT", "WARM", "COOL", "COLD"]
BUY_ORDER = ["HIGH", "MODERATE", "LOW", "COLD"]
OPP_ORDER = ["HIGH", "MEDIUM", "LOW", "VERY LOW"]
STATUS_COLORS = {
    "HOT": "#16A34A",
    "WARM": "#F59E0B",
    "COOL": "#2563EB",
    "COLD": "#DC2626",
    "HIGH": "#16A34A",
    "MODERATE": "#F59E0B",
    "LOW": "#2563EB",
    "MEDIUM": "#F59E0B",
    "VERY LOW": "#DC2626",
    "Inactive": "#64748B",
    "Churn Risk": "#DC2626",
    "At Risk": "#F59E0B",
    "Healthy": "#16A34A",
}


def section_title(title, description=""):
    st.subheader(title)
    if description:
        st.caption(description)


def chart_or_note(df, note="ไม่มีข้อมูลเพียงพอสำหรับกราฟนี้"):
    if df is None or df.empty:
        st.info(note)
        return False
    return True


def find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def load_buyer_file(file):
    xls = pd.ExcelFile(file)
    frames = []
    for sheet in xls.sheet_names:
        if sheet.startswith("Buyer_Master_"):
            temp = pd.read_excel(file, sheet_name=sheet)
            if "Snapshot_Month" not in temp.columns:
                temp["Snapshot_Month"] = sheet.replace("Buyer_Master_", "")
            temp["Source_Sheet"] = sheet
            frames.append(temp)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["Snapshot_Month"] = df["Snapshot_Month"].astype(str)
    for col in ["Snapshot_Date", "Performance_Period_Start", "Performance_Period_End", "Last_Login_Date", "Registration_Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["Login_Count", "Bid_Count", "Buy_Count", "Period_Purchase_Units", "Lifetime_Purchase_Units"]:
        if col in df.columns:
            df[col] = to_num(df[col])
    return df


def load_visit_file(file):
    visit = pd.read_excel(file, sheet_name="01_Visit_Activity_Log")
    try:
        demand = pd.read_excel(file, sheet_name="02_Visit_Car_Demand_Log")
    except Exception:
        demand = pd.DataFrame()
    try:
        feedback = pd.read_excel(file, sheet_name="03_Visit_Feedback_Log")
    except Exception:
        feedback = pd.DataFrame()
    if "Visit_Date" in visit.columns:
        visit["Visit_Date"] = pd.to_datetime(visit["Visit_Date"], errors="coerce")
    if "Report_Month" in visit.columns:
        visit["Report_Month"] = visit["Report_Month"].astype(str)
    return visit, demand, feedback


def login_status_and_score(total_login_3m):
    login_pct = min(total_login_3m / 30, 1.0)
    if login_pct >= 0.65:
        return 100, "HOT", login_pct
    if login_pct >= 0.35:
        return 70, "WARM", login_pct
    if login_pct > 0:
        return 40, "COOL", login_pct
    return 0, "COLD", 0.0


def buy_status_and_score(units_per_month):
    if units_per_month >= 14:
        return 100, "HIGH"
    if units_per_month >= 5:
        return 70, "MODERATE"
    if units_per_month > 0:
        return 40, "LOW"
    return 0, "COLD"


def final_health_status(score):
    if score >= 80:
        return "HOT"
    if score >= 50:
        return "WARM"
    if score > 0:
        return "COOL"
    return "COLD"


def build_rolling_health(history_df, snapshot_month, customer_col, province_col, ae_col, login_col, bid_col, buy_count_col, unit_col):
    months = sorted(history_df["Snapshot_Month"].dropna().unique().tolist())
    if snapshot_month not in months:
        snapshot_month = months[-1]
    idx = months.index(snapshot_month)
    rolling_months = months[max(0, idx - 2): idx + 1]
    roll = history_df[history_df["Snapshot_Month"].isin(rolling_months)].copy()
    current = history_df[history_df["Snapshot_Month"] == snapshot_month].copy()
    current_keys = current[[customer_col, province_col, ae_col, "Customer_Name"] if "Customer_Name" in current.columns else [customer_col, province_col, ae_col]].drop_duplicates(customer_col)
    agg = roll.groupby(customer_col, dropna=False).agg(
        Total_Login_3M=(login_col, "sum"),
        Total_Bid_3M=(bid_col, "sum"),
        Total_Buy_Count_3M=(buy_count_col, "sum"),
        Total_Buy_Units_3M=(unit_col, "sum"),
    ).reset_index()
    out = current_keys.merge(agg, on=customer_col, how="left").fillna({
        "Total_Login_3M": 0, "Total_Bid_3M": 0, "Total_Buy_Count_3M": 0, "Total_Buy_Units_3M": 0
    })
    out["Buy_Units_Per_Month"] = out["Total_Buy_Units_3M"] / max(1, len(rolling_months))
    login_scores = out["Total_Login_3M"].apply(login_status_and_score)
    out["Login_Score"] = [x[0] for x in login_scores]
    out["Login_Status"] = [x[1] for x in login_scores]
    out["Login_Pct"] = [x[2] for x in login_scores]
    buy_scores = out["Buy_Units_Per_Month"].apply(buy_status_and_score)
    out["Buy_Score"] = [x[0] for x in buy_scores]
    out["Buy_Status"] = [x[1] for x in buy_scores]
    out["Health_Score"] = (out["Login_Score"] * 0.5 + out["Buy_Score"] * 0.5).round(1)
    out["Health_Status"] = out["Health_Score"].apply(final_health_status)
    out["Rolling_Months"] = ", ".join(rolling_months)
    out["Inactive_Flag"] = out.apply(lambda r: "Inactive" if r["Total_Login_3M"] == 0 and r["Total_Buy_Units_3M"] == 0 else "Active", axis=1)
    out["Churn_Risk"] = out.apply(
        lambda r: "Inactive" if r["Total_Login_3M"] == 0 and r["Total_Buy_Units_3M"] == 0
        else ("Churn Risk" if r["Total_Login_3M"] > 0 and r["Total_Buy_Units_3M"] == 0
              else ("At Risk" if r["Health_Status"] in ["COOL", "COLD"] else "Healthy")), axis=1
    )
    return out, rolling_months


def status_summary(df, col, order):
    total = max(1, len(df))
    out = df.groupby(col).size().reindex(order, fill_value=0).reset_index()
    out.columns = [col, "Buyers"]
    out["%"] = (out["Buyers"] / total * 100).round(1)
    return out


def complete_status_grid(df, index_col, status_col, value_col="Count", status_order=HEALTH_ORDER):
    base = pd.MultiIndex.from_product([sorted(df[index_col].dropna().unique()), status_order], names=[index_col, status_col]).to_frame(index=False)
    merged = base.merge(df, on=[index_col, status_col], how="left")
    merged[value_col] = merged[value_col].fillna(0).astype(int)
    return merged


def show_health_distribution(buyer_health, title="Buyer Health Distribution"):
    dist = status_summary(buyer_health, "Health_Status", HEALTH_ORDER)
    st.markdown(f"#### {title}")
    cols = st.columns(4)
    for i, status in enumerate(HEALTH_ORDER):
        row = dist[dist["Health_Status"] == status].iloc[0]
        cols[i].metric(f"{status} Buyers", f"{int(row['Buyers']):,}", f"{row['%']:.1f}%")
    fig = px.bar(
        dist, y="Health_Status", x="Buyers", orientation="h", text=dist.apply(lambda r: f"{int(r['Buyers']):,} ({r['%']:.1f}%)", axis=1),
        color="Health_Status", color_discrete_map=STATUS_COLORS, category_orders={"Health_Status": HEALTH_ORDER}
    )
    fig.update_layout(showlegend=False, height=300, yaxis_title=None, xaxis_title="Buyers")
    fig.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Health Status คำนวณจาก Rolling 3M: Login % = Total Login 3M / 30 และ Buy Units/Month = Total Units 3M / 3")
    return dist


def score_bid(total_bid):
    if total_bid >= 10:
        return 100
    if total_bid >= 5:
        return 75
    if total_bid >= 2:
        return 50
    if total_bid > 0:
        return 25
    return 0


def opportunity_level(score):
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    if score >= 40:
        return "LOW"
    return "VERY LOW"


def coverage_gap_score(coverage_rate):
    if coverage_rate == 0:
        return 100
    if coverage_rate < 10:
        return 85
    if coverage_rate < 25:
        return 65
    if coverage_rate < 50:
        return 40
    return 15


st.title("CRM Intelligence Dashboard v9")
st.sidebar.header("Upload Excel Files")
buyer_file = st.sidebar.file_uploader("Upload Buyer Master File", type=["xlsx"])
visit_file = st.sidebar.file_uploader("Upload Visit Activity File", type=["xlsx"])

if not buyer_file or not visit_file:
    st.info("Upload both Excel files to start dashboard")
    st.stop()

buyer_df = load_buyer_file(buyer_file)
if buyer_df.empty:
    st.error("ไม่พบ sheet ที่ขึ้นต้นด้วย Buyer_Master_ ใน Buyer Master File")
    st.stop()
visit_df, demand_df, feedback_df = load_visit_file(visit_file)

customer_col = find_col(buyer_df, ["Customer_No", "Customer No", "Customer_ID", "Buyer_ID"])
province_col = find_col(buyer_df, ["Province", "จังหวัด"])
ae_col = find_col(buyer_df, ["AE_Name", "AE Name", "AE_Lead", "AE"])
login_col = find_col(buyer_df, ["Login_Count", "Login Count", "Login"])
bid_col = find_col(buyer_df, ["Bid_Count", "Bid Count", "Bid"])
buy_count_col = find_col(buyer_df, ["Buy_Count", "Buy Count", "Buy"])
unit_col = find_col(buyer_df, ["Period_Purchase_Units", "Purchase_Units", "Buy_Units", "Buy_Count"])

required = [customer_col, province_col, ae_col, login_col, bid_col, buy_count_col, unit_col]
if not all(required):
    st.error("ไฟล์ Buyer Master ขาดคอลัมน์หลัก เช่น Customer_No, Province, AE_Name, Login_Count, Bid_Count, Buy_Count, Period_Purchase_Units")
    st.stop()

visit_customer_col = find_col(visit_df, ["Customer_No", "Customer No", "Customer_ID", "Buyer_ID"])
visit_province_col = find_col(visit_df, ["Province", "จังหวัด"])
visit_ae_col = find_col(visit_df, ["AE_Lead", "AE_Name", "AE Name", "AE"])
visit_date_col = find_col(visit_df, ["Visit_Date", "Visit Date", "Date", "วันที่"])
visit_purpose_col = find_col(visit_df, ["Visit_Objective_Detail", "Visit_Purpose", "Purpose", "Visit Objective"])

months = sorted(buyer_df["Snapshot_Month"].dropna().astype(str).unique().tolist())
latest_month = months[-1]
st.sidebar.header("Data View")
selected_month = st.sidebar.selectbox("Snapshot Month", months, index=len(months)-1, help="Snapshot View ใช้เดือนนี้เท่านั้น ส่วน Health ใช้ rolling 3 เดือนล่าสุดนับจากเดือนนี้")
view_mode = st.sidebar.radio("KPI Mode", ["Snapshot", "Accumulated"], index=0, help="Snapshot = เดือนเดียว, Accumulated = รวมข้อมูลตั้งแต่ต้นจนถึงเดือนที่เลือก")

st.sidebar.header("Global Filters")
province_filter = st.sidebar.multiselect("Province", sorted(buyer_df[province_col].dropna().astype(str).unique().tolist()))
ae_filter = st.sidebar.multiselect("AE Name", sorted(buyer_df[ae_col].dropna().astype(str).unique().tolist()))
page = st.sidebar.radio("Dashboard Page", [
    "1 Executive Command Center",
    "2 Geography & Territory",
    "3 AE Performance",
    "4 Buyer Health",
    "5 Opportunity",
    "6 Visit & Coverage",
    "7 Demand Intelligence",
    "8 Feedback Intelligence",
    "9 Follow-up Command",
    "10 Recommendation"
])

# Base snapshot and accumulated layers
snapshot_df = buyer_df[buyer_df["Snapshot_Month"] == selected_month].copy()
accum_df = buyer_df[buyer_df["Snapshot_Month"].isin([m for m in months if m <= selected_month])].copy()
historical_df = buyer_df[buyer_df["Snapshot_Month"].isin([m for m in months if m <= selected_month])].copy()

for df in [snapshot_df, accum_df, historical_df]:
    if province_filter:
        df.drop(df[~df[province_col].astype(str).isin(province_filter)].index, inplace=True)
    if ae_filter:
        df.drop(df[~df[ae_col].astype(str).isin(ae_filter)].index, inplace=True)

current_kpi_df = snapshot_df if view_mode == "Snapshot" else accum_df
buyer_health, rolling_months = build_rolling_health(historical_df, selected_month, customer_col, province_col, ae_col, login_col, bid_col, buy_count_col, unit_col)

# Visit filters
visit_filtered = visit_df.copy()
if province_filter and visit_province_col:
    visit_filtered = visit_filtered[visit_filtered[visit_province_col].astype(str).isin(province_filter)]
if ae_filter and visit_ae_col:
    visit_filtered = visit_filtered[visit_filtered[visit_ae_col].astype(str).isin(ae_filter)]
if visit_date_col and visit_filtered[visit_date_col].notna().any():
    min_date = visit_filtered[visit_date_col].min().date()
    max_date = visit_filtered[visit_date_col].max().date()
    date_range = st.sidebar.date_input("Visit Date Range", value=(min_date, max_date))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        visit_filtered = visit_filtered[(visit_filtered[visit_date_col].dt.date >= start_date) & (visit_filtered[visit_date_col].dt.date <= end_date)]

# Demand/feedback are mapped through Visit_ID where possible
valid_visit_ids = set(visit_filtered["Visit_ID"].dropna().astype(str)) if "Visit_ID" in visit_filtered.columns else set()
demand_filtered = demand_df.copy()
feedback_filtered = feedback_df.copy()
if valid_visit_ids and "Visit_ID" in demand_filtered.columns:
    demand_filtered = demand_filtered[demand_filtered["Visit_ID"].astype(str).isin(valid_visit_ids)]
if valid_visit_ids and "Visit_ID" in feedback_filtered.columns:
    feedback_filtered = feedback_filtered[feedback_filtered["Visit_ID"].astype(str).isin(valid_visit_ids)]

# Province opportunity / coverage
province_summary = current_kpi_df.groupby(province_col).agg(
    Buyers=(customer_col, "nunique"),
    Total_Login=(login_col, "sum"),
    Total_Bid=(bid_col, "sum"),
    Total_Buy=(buy_count_col, "sum"),
    Total_Units=(unit_col, "sum"),
).reset_index().rename(columns={province_col: "Province"})
if visit_province_col and visit_customer_col and not visit_filtered.empty:
    reg_visit = visit_filtered[visit_filtered[visit_customer_col].notna() & (visit_filtered[visit_customer_col].astype(str).str.strip() != "-")].copy()
    visit_summary = reg_visit.groupby(visit_province_col)[visit_customer_col].nunique().reset_index(name="Unique_Buyers_Visited").rename(columns={visit_province_col: "Province"})
else:
    visit_summary = pd.DataFrame(columns=["Province", "Unique_Buyers_Visited"])
province_opp = province_summary.merge(visit_summary, on="Province", how="left")
province_opp["Unique_Buyers_Visited"] = province_opp["Unique_Buyers_Visited"].fillna(0).astype(int)
province_opp["Coverage_Rate"] = (province_opp["Unique_Buyers_Visited"] / province_opp["Buyers"].replace(0, pd.NA) * 100).fillna(0).round(1)
province_opp["Bid_Score"] = province_opp["Total_Bid"].apply(score_bid)
province_opp["Buyer_Size_Score"] = (province_opp["Buyers"] / max(1, province_opp["Buyers"].max()) * 100).round(1)
province_opp["Coverage_Gap_Score"] = province_opp["Coverage_Rate"].apply(coverage_gap_score)
province_opp["Opportunity_Score"] = (province_opp["Bid_Score"] * 0.5 + province_opp["Buyer_Size_Score"] * 0.3 + province_opp["Coverage_Gap_Score"] * 0.2).round(1)
province_opp["Opportunity_Level"] = province_opp["Opportunity_Score"].apply(opportunity_level)

# Buyer opportunity and visit flag
if visit_customer_col and not visit_filtered.empty:
    reg_visit = visit_filtered[visit_filtered[visit_customer_col].notna() & (visit_filtered[visit_customer_col].astype(str).str.strip() != "-")]
    buyer_visit = reg_visit.groupby(visit_customer_col).size().reset_index(name="Visit_Count").rename(columns={visit_customer_col: customer_col})
else:
    buyer_visit = pd.DataFrame(columns=[customer_col, "Visit_Count"])
buyer_opp = buyer_health.merge(buyer_visit, on=customer_col, how="left")
buyer_opp["Visit_Count"] = buyer_opp["Visit_Count"].fillna(0).astype(int)
buyer_opp["Visited_Flag"] = buyer_opp["Visit_Count"].apply(lambda x: 1 if x > 0 else 0)
buyer_opp["Coverage_Gap_Score"] = buyer_opp["Visited_Flag"].apply(lambda x: 20 if x else 100)
buyer_opp["Bid_Score"] = buyer_opp["Total_Bid_3M"].apply(score_bid)
buyer_opp["Opportunity_Score"] = (buyer_opp["Bid_Score"] * 0.55 + buyer_opp["Coverage_Gap_Score"] * 0.25 + (100 - buyer_opp["Health_Score"]) * 0.20).round(1)
buyer_opp["Opportunity_Level"] = buyer_opp["Opportunity_Score"].apply(opportunity_level)

with st.sidebar.expander("Score Definitions", expanded=False):
    st.write("Health Score")
    st.code("""Rolling window: latest 3 snapshot months up to selected Snapshot Month

Login % = Total Login ล่าสุด 3 เดือน / 30
Login Status:
HOT  >= 65%
WARM >= 35% and < 65%
COOL > 0% and < 35%
COLD = 0%

Buy Units/Month = Total Period_Purchase_Units ล่าสุด 3 เดือน / 3
Buy Status:
HIGH     >= 14 units/month
MODERATE >= 5 and < 14
LOW      > 0 and < 5
COLD     = 0

Health Score = (Login Score x 50%) + (Buy Score x 50%)""")
    st.write("Data Layers")
    st.code("""Snapshot = selected Snapshot_Month only
Historical = monthly time series by Snapshot_Month
Rolling 3M = latest 3 snapshot months for health score
Accumulated = sum from first month to selected month""")

st.caption(f"Buyer Snapshot: {selected_month} | KPI Mode: {view_mode} | Rolling Health Months: {', '.join(rolling_months)}")
if visit_date_col and visit_df[visit_date_col].notna().any():
    st.caption(f"Visit data available: {visit_df[visit_date_col].min().date()} ถึง {visit_df[visit_date_col].max().date()} | Buyer snapshot latest: {latest_month}")

if page.startswith("1 "):
    st.header("Executive Command Center")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Buyers", f"{current_kpi_df[customer_col].nunique():,.0f}")
    c2.metric("Login", f"{int(current_kpi_df[login_col].sum()):,.0f}")
    c3.metric("Bid", f"{int(current_kpi_df[bid_col].sum()):,.0f}")
    c4.metric("Buy", f"{int(current_kpi_df[buy_count_col].sum()):,.0f}")
    c5.metric("Visits", f"{len(visit_filtered):,.0f}")

    section_title("Buyer Health Distribution", "แทนที่ legend ลอยด้วย distribution จริง แสดงครบ HOT / WARM / COOL / COLD เสมอ")
    show_health_distribution(buyer_health)

    section_title("Historical CRM Trend", "แนวโน้มรายเดือน ไม่ปนกับ Snapshot KPI")
    trend = historical_df.groupby("Snapshot_Month").agg(Login=(login_col, "sum"), Bid=(bid_col, "sum"), Buy=(buy_count_col, "sum"), Units=(unit_col, "sum"), Buyers=(customer_col, "nunique")).reset_index()
    if chart_or_note(trend):
        fig = px.line(trend.melt(id_vars="Snapshot_Month", value_vars=["Login", "Bid", "Buy", "Units"], var_name="Metric", value_name="Value"), x="Snapshot_Month", y="Value", color="Metric", markers=True)
        fig.update_layout(xaxis_title="Snapshot Month", yaxis_title="Value")
        st.plotly_chart(fig, use_container_width=True)

    section_title("Top Provinces by Buy", "จังหวัดที่สร้าง Buy สูงสุดตาม KPI Mode ที่เลือก")
    top_province = province_summary.sort_values("Total_Buy", ascending=False).head(15)
    if chart_or_note(top_province):
        st.plotly_chart(px.bar(top_province, x="Total_Buy", y="Province", orientation="h", text="Total_Buy"), use_container_width=True)

    section_title("AE Snapshot", "ภาพรวมฐานลูกค้าและ activity แยกตาม AE")
    ae_snapshot = current_kpi_df.groupby(ae_col).agg(Buyers=(customer_col, "nunique"), Login=(login_col, "sum"), Bid=(bid_col, "sum"), Buy=(buy_count_col, "sum"), Units=(unit_col, "sum")).reset_index().sort_values("Buy", ascending=False)
    st.dataframe(ae_snapshot, use_container_width=True)

elif page.startswith("2 "):
    st.header("Geography & Territory Intelligence")
    section_title("Buyers by Province", "ฐานลูกค้าตามจังหวัดจาก Snapshot/KPI Mode ที่เลือก")
    if chart_or_note(province_summary):
        st.plotly_chart(px.bar(province_summary.sort_values("Buyers", ascending=False).head(25), x="Province", y="Buyers", text="Buyers"), use_container_width=True)

    section_title("Province Opportunity Matrix", "X = Coverage %, Y = Buy Units, Bubble = Buyers, Color = Opportunity Level")
    if chart_or_note(province_opp):
        st.plotly_chart(px.scatter(province_opp, x="Coverage_Rate", y="Total_Units", size="Buyers", color="Opportunity_Level", hover_name="Province", color_discrete_map=STATUS_COLORS, category_orders={"Opportunity_Level": OPP_ORDER}), use_container_width=True)

    section_title("Coverage Gap by Province", "Coverage = Unique Registered Buyers Visited / Buyers Assigned")
    st.dataframe(province_opp.sort_values(["Coverage_Rate", "Buyers"], ascending=[True, False]), use_container_width=True)

    section_title("Province Health Mix", "แสดง status ครบแม้ count = 0")
    hp = buyer_health.groupby(["Province", "Health_Status"]).size().reset_index(name="Count")
    hp = complete_status_grid(hp, "Province", "Health_Status")
    if chart_or_note(hp):
        st.plotly_chart(px.bar(hp, x="Province", y="Count", color="Health_Status", color_discrete_map=STATUS_COLORS, category_orders={"Health_Status": HEALTH_ORDER}), use_container_width=True)

elif page.startswith("3 "):
    st.header("AE Performance & Conversion")
    ae_base = current_kpi_df.groupby(ae_col).agg(Buyers_Assigned=(customer_col, "nunique"), Login=(login_col, "sum"), Bid=(bid_col, "sum"), Buy=(buy_count_col, "sum"), Units=(unit_col, "sum")).reset_index().rename(columns={ae_col: "AE"})
    if visit_ae_col and visit_customer_col:
        reg_visit = visit_filtered[visit_filtered[visit_customer_col].notna() & (visit_filtered[visit_customer_col].astype(str).str.strip() != "-")]
        ae_visit = reg_visit.groupby(visit_ae_col).agg(Visits=(visit_customer_col, "size"), Unique_Buyers_Visited=(visit_customer_col, "nunique")).reset_index().rename(columns={visit_ae_col: "AE"})
    else:
        ae_visit = pd.DataFrame(columns=["AE", "Visits", "Unique_Buyers_Visited"])
    ae_perf = ae_base.merge(ae_visit, on="AE", how="left").fillna({"Visits": 0, "Unique_Buyers_Visited": 0})
    ae_perf["Coverage_Rate"] = (ae_perf["Unique_Buyers_Visited"] / ae_perf["Buyers_Assigned"].replace(0, pd.NA) * 100).fillna(0).round(1)
    ae_perf["Buy_per_Buyer"] = (ae_perf["Buy"] / ae_perf["Buyers_Assigned"].replace(0, pd.NA)).fillna(0).round(2)
    ae_perf["Bid_to_Buy_Rate"] = (ae_perf["Buy"] / ae_perf["Bid"].replace(0, pd.NA) * 100).fillna(0).round(1)

    section_title("AE Efficiency Quadrant", "X = Buyers Assigned, Y = Unique Buyers Visited %, Bubble = Visits, Color = Buy per Buyer พร้อม label AE")
    if chart_or_note(ae_perf):
        fig = px.scatter(ae_perf, x="Buyers_Assigned", y="Coverage_Rate", size="Visits", color="Buy_per_Buyer", text="AE", hover_name="AE", hover_data=["Buy", "Bid", "Units", "Unique_Buyers_Visited", "Bid_to_Buy_Rate"])
        fig.add_vline(x=ae_perf["Buyers_Assigned"].mean(), line_dash="dash", line_color="#94A3B8")
        fig.add_hline(y=ae_perf["Coverage_Rate"].mean(), line_dash="dash", line_color="#94A3B8")
        fig.update_traces(textposition="top center")
        fig.update_layout(yaxis_title="Unique Buyers Visited %", xaxis_title="Buyers Assigned", height=520)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(ae_perf.sort_values("Coverage_Rate", ascending=False), use_container_width=True)

    section_title("AE Funnel", "Login -> Bid -> Buy ตาม AE")
    st.plotly_chart(px.bar(ae_perf.melt(id_vars="AE", value_vars=["Login", "Bid", "Buy"], var_name="Stage", value_name="Value"), x="AE", y="Value", color="Stage", barmode="group"), use_container_width=True)

    section_title("AE Health Mix", "status ครบและสี consistent")
    ah = buyer_health.groupby(["AE", "Health_Status"]).size().reset_index(name="Count")
    ah = complete_status_grid(ah, "AE", "Health_Status")
    st.plotly_chart(px.bar(ah, x="AE", y="Count", color="Health_Status", color_discrete_map=STATUS_COLORS, category_orders={"Health_Status": HEALTH_ORDER}), use_container_width=True)

elif page.startswith("4 "):
    st.header("Buyer Health")
    section_title("Health Score Formula", "สูตรที่ lock ล่าสุด")
    st.code("""Login % = Total Login ล่าสุด 3 เดือน / 30
Login Status: HOT >=65%, WARM >=35% and <65%, COOL >0% and <35%, COLD =0%

Buy Units/Month = Total Period_Purchase_Units ล่าสุด 3 เดือน / 3
Buy Status: HIGH >=14, MODERATE >=5 and <14, LOW >0 and <5, COLD =0

Health Score = (Login Score x 50%) + (Buy Score x 50%)""")
    show_health_distribution(buyer_health, "Health Distribution")

    section_title("Login Status vs Buy Status", "แยก Engagement กับ Commercial Value")
    matrix = buyer_health.groupby(["Login_Status", "Buy_Status"]).size().reset_index(name="Buyers")
    grid = pd.MultiIndex.from_product([LOGIN_ORDER, BUY_ORDER], names=["Login_Status", "Buy_Status"]).to_frame(index=False)
    matrix = grid.merge(matrix, on=["Login_Status", "Buy_Status"], how="left").fillna({"Buyers": 0})
    st.plotly_chart(px.density_heatmap(matrix, x="Login_Status", y="Buy_Status", z="Buyers", text_auto=True, category_orders={"Login_Status": LOGIN_ORDER, "Buy_Status": BUY_ORDER}), use_container_width=True)

    section_title("Top Healthy Buyers", "เรียงตาม Health Score สูงสุด")
    cols = [customer_col, "Customer_Name", "Province", "AE", "Total_Login_3M", "Login_Pct", "Login_Status", "Total_Buy_Units_3M", "Buy_Units_Per_Month", "Buy_Status", "Health_Score", "Health_Status"]
    cols = [c for c in cols if c in buyer_health.columns]
    st.dataframe(buyer_health.sort_values("Health_Score", ascending=False)[cols].head(50), use_container_width=True)

    section_title("Cold / Cool Buyers", "กลุ่มที่ควร re-engage")
    st.dataframe(buyer_health[buyer_health["Health_Status"].isin(["COOL", "COLD"])].sort_values(["Health_Score", "Total_Login_3M"])[cols].head(100), use_container_width=True)

elif page.startswith("5 "):
    st.header("Opportunity")
    section_title("Opportunity Province Ranking", "จัดลำดับจาก Bid, Buyer Size และ Coverage Gap")
    st.dataframe(province_opp.sort_values("Opportunity_Score", ascending=False), use_container_width=True)
    section_title("High Potential / Low Coverage", "พื้นที่ที่ควร prioritize")
    st.plotly_chart(px.scatter(province_opp, x="Coverage_Rate", y="Total_Bid", size="Buyers", color="Opportunity_Level", hover_name="Province", color_discrete_map=STATUS_COLORS, category_orders={"Opportunity_Level": OPP_ORDER}), use_container_width=True)
    section_title("Opportunity Level Distribution", "แสดงครบทุก level")
    dist = province_opp.groupby("Opportunity_Level").size().reindex(OPP_ORDER, fill_value=0).reset_index(name="Provinces")
    st.plotly_chart(px.bar(dist, x="Provinces", y="Opportunity_Level", orientation="h", color="Opportunity_Level", color_discrete_map=STATUS_COLORS, category_orders={"Opportunity_Level": OPP_ORDER}, text="Provinces"), use_container_width=True)

elif page.startswith("6 "):
    st.header("Visit & Coverage")
    section_title("Visit Trend", "จำนวน visit ตามเดือนในไฟล์ visit")
    if visit_date_col and visit_filtered[visit_date_col].notna().any():
        vt = visit_filtered.copy()
        vt["Month"] = vt[visit_date_col].dt.to_period("M").astype(str)
        st.plotly_chart(px.line(vt.groupby("Month").size().reset_index(name="Visits"), x="Month", y="Visits", markers=True), use_container_width=True)
    else:
        st.info("ไม่พบ Visit Date")
    section_title("Coverage Gap by Province", "ใช้ Unique Registered Buyers Visited ไม่ใช่จำนวน visit rows")
    st.dataframe(province_opp[["Province", "Buyers", "Unique_Buyers_Visited", "Coverage_Rate", "Coverage_Gap_Score"]].sort_values("Coverage_Rate"), use_container_width=True)
    section_title("Visit Purpose Analysis", "ใช้ Visit_Objective_Detail")
    if visit_purpose_col:
        purpose = visit_filtered.groupby(visit_purpose_col).size().reset_index(name="Count").sort_values("Count", ascending=False)
        st.plotly_chart(px.bar(purpose.head(20), x="Count", y=visit_purpose_col, orientation="h"), use_container_width=True)
    else:
        st.info("ไม่พบคอลัมน์ Visit_Objective_Detail")

elif page.startswith("7 "):
    st.header("Demand Intelligence")
    if demand_filtered.empty:
        st.info("ไม่พบ Demand Log หรือไม่มี Demand หลัง filter")
    else:
        segment_col = find_col(demand_filtered, ["Vehicle_Segment", "Segment"])
        brand_col = find_col(demand_filtered, ["Brand", "Vehicle_Brand"])
        model_col = find_col(demand_filtered, ["Model", "Vehicle_Model"])
        year_col = find_col(demand_filtered, ["Year_From", "Year_To", "Year", "Vehicle_Year"])
        section_title("Vehicle Segment Demand", "จาก sheet 02_Visit_Car_Demand_Log")
        if segment_col:
            seg = demand_filtered.groupby(segment_col).size().reset_index(name="Demand").sort_values("Demand", ascending=False)
            st.plotly_chart(px.bar(seg, x="Demand", y=segment_col, orientation="h"), use_container_width=True)
        section_title("Brand Demand Ranking", "แบรนด์ที่ถูกถามหามากที่สุด")
        if brand_col:
            brand = demand_filtered.groupby(brand_col).size().reset_index(name="Demand").sort_values("Demand", ascending=False).head(20)
            st.plotly_chart(px.bar(brand, x="Demand", y=brand_col, orientation="h"), use_container_width=True)
        section_title("Model Demand Ranking", "รุ่นรถที่ถูกถามหามากที่สุด")
        if model_col:
            model = demand_filtered.groupby(model_col).size().reset_index(name="Demand").sort_values("Demand", ascending=False).head(20)
            st.plotly_chart(px.bar(model, x="Demand", y=model_col, orientation="h"), use_container_width=True)
        section_title("Year Demand Analysis", "ปีรถที่ลูกค้าสนใจ")
        if year_col:
            year = demand_filtered.groupby(year_col).size().reset_index(name="Demand").sort_values(year_col)
            st.plotly_chart(px.bar(year, x=year_col, y="Demand"), use_container_width=True)

elif page.startswith("8 "):
    st.header("Feedback Intelligence")
    if feedback_filtered.empty:
        st.info("ไม่พบ Feedback Log หรือไม่มี Feedback หลัง filter")
    else:
        fb_category_col = find_col(feedback_filtered, ["Feedback_Category", "Category"])
        fb_sentiment_col = find_col(feedback_filtered, ["Feedback_Sentiment", "Sentiment"])
        section_title("Feedback Category Distribution", "จาก sheet 03_Visit_Feedback_Log")
        if fb_category_col:
            fbc = feedback_filtered.groupby(fb_category_col).size().reset_index(name="Count").sort_values("Count", ascending=False)
            st.plotly_chart(px.bar(fbc, x="Count", y=fb_category_col, orientation="h"), use_container_width=True)
        section_title("Positive vs Negative Feedback", "ใช้ Feedback_Sentiment")
        if fb_sentiment_col:
            fs = feedback_filtered.groupby(fb_sentiment_col).size().reset_index(name="Count")
            st.plotly_chart(px.pie(fs, names=fb_sentiment_col, values="Count"), use_container_width=True)
        section_title("Feedback Detail Table", "Feedback_Action_Needed ไม่ถูกใช้เป็น source หลักสำหรับ follow-up เพราะในไฟล์ว่าง")
        st.dataframe(feedback_filtered, use_container_width=True)

elif page.startswith("9 "):
    st.header("Follow-up Command Center")
    follow_required_col = find_col(visit_filtered, ["Follow_Up_Required"])
    follow_action_col = find_col(visit_filtered, ["Follow_Up_Action"])
    follow_owner_col = find_col(visit_filtered, ["Follow_Up_Owner"])
    next_action_col = find_col(visit_filtered, ["Next_Action_Date"])
    if next_action_col:
        visit_filtered[next_action_col] = pd.to_datetime(visit_filtered[next_action_col], errors="coerce")
    if not follow_required_col:
        st.info("ไม่พบ Follow_Up_Required")
    else:
        follow_df = visit_filtered.copy()
        follow_df["Follow_Up_Flag"] = follow_df[follow_required_col].fillna("No").astype(str)
        section_title("Follow-up Required", "ใช้ Follow_Up_Required / Follow_Up_Action / Follow_Up_Owner ไม่ใช้ Feedback_Action_Needed เป็น source หลัก")
        fu = follow_df.groupby("Follow_Up_Flag").size().reset_index(name="Count")
        st.plotly_chart(px.bar(fu, x="Follow_Up_Flag", y="Count", text="Count"), use_container_width=True)
        if visit_ae_col:
            section_title("Follow-up by AE", "ภาระงาน follow-up ต่อ AE")
            fuae = follow_df.groupby([visit_ae_col, "Follow_Up_Flag"]).size().reset_index(name="Count")
            st.plotly_chart(px.bar(fuae, x=visit_ae_col, y="Count", color="Follow_Up_Flag", barmode="group"), use_container_width=True)
        section_title("Follow-up Detail Table", "เฉพาะรายการที่ต้อง follow-up")
        yes = follow_df[follow_df["Follow_Up_Flag"].str.lower().isin(["yes", "y", "true", "1"])]
        show_cols = ["Visit_ID", "Visit_Date", "AE_Lead", "Customer_No", "Customer_Name", "Province", "Visit_Objective_Detail", follow_required_col, follow_action_col, next_action_col, follow_owner_col]
        show_cols = [c for c in show_cols if c in yes.columns and c is not None]
        st.dataframe(yes[show_cols], use_container_width=True)

elif page.startswith("10 "):
    st.header("Recommendation / Next Best Action")
    section_title("Next Best Provinces", "จังหวัดที่ Opportunity Score สูงและ Coverage ยังต่ำ")
    st.dataframe(province_opp.sort_values(["Opportunity_Score", "Coverage_Rate"], ascending=[False, True]).head(20), use_container_width=True)

    section_title("Next Best Buyers", "Priority = Opportunity + Coverage Gap + Low Health เพื่อช่วย AE เลือก action")
    buyer_opp["Priority_Index"] = (buyer_opp["Opportunity_Score"] * 0.55 + (100 - buyer_opp["Health_Score"]) * 0.30 + buyer_opp["Coverage_Gap_Score"] * 0.15).round(1)
    buyer_opp["NBA"] = buyer_opp.apply(lambda r: "Visit This Week" if r["Visit_Count"] == 0 and r["Opportunity_Score"] >= 60 else ("Re-activate" if r["Churn_Risk"] in ["Inactive", "Churn Risk"] else ("Upsell / Maintain" if r["Health_Status"] in ["HOT", "WARM"] else "Call Follow-up")), axis=1)
    nb_cols = [customer_col, "Customer_Name", "Province", "AE", "Health_Status", "Churn_Risk", "Total_Login_3M", "Total_Buy_Units_3M", "Visit_Count", "Opportunity_Score", "Priority_Index", "NBA"]
    nb_cols = [c for c in nb_cols if c in buyer_opp.columns]
    st.dataframe(buyer_opp.sort_values("Priority_Index", ascending=False)[nb_cols].head(100), use_container_width=True)

    section_title("Churn Watch", "แยก Inactive vs Churn Risk")
    cw_cols = [customer_col, "Customer_Name", "Province", "AE", "Health_Status", "Inactive_Flag", "Churn_Risk", "Total_Login_3M", "Total_Buy_Units_3M", "Health_Score"]
    cw_cols = [c for c in cw_cols if c in buyer_health.columns]
    st.dataframe(buyer_health.sort_values(["Churn_Risk", "Health_Score"])[cw_cols].head(100), use_container_width=True)

    section_title("AE Daily Action List", "รายการ action รายวันสำหรับ AE")
    action = buyer_opp.copy()
    action["Recommended_Action"] = action.apply(lambda r: "Visit This Week" if r["Visit_Count"] == 0 and r["Priority_Index"] >= 55 else ("Call Follow-up" if r["Health_Status"] in ["COOL", "COLD"] else "Relationship Maintenance"), axis=1)
    action_cols = [customer_col, "Customer_Name", "Province", "AE", "Health_Status", "Opportunity_Level", "Visit_Count", "Priority_Index", "Recommended_Action"]
    action_cols = [c for c in action_cols if c in action.columns]
    st.dataframe(action.sort_values(["Priority_Index", "Opportunity_Score"], ascending=False)[action_cols].head(100), use_container_width=True)
