import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CRM Intelligence Dashboard", layout="wide")


def find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def score_login(total_login):
    login_pct = total_login / 30
    if login_pct >= 0.65:
        return 100, "HOT"
    if login_pct >= 0.35:
        return 70, "WARM"
    if login_pct > 0:
        return 40, "COOL"
    return 0, "COLD"


def score_sold(avg_sold):
    if avg_sold >= 14:
        return 100, "HIGH"
    if avg_sold >= 5:
        return 70, "MODERATE"
    if avg_sold > 0:
        return 40, "LOW"
    return 0, "COLD"


def final_health_status(score):
    if score >= 80:
        return "HOT"
    if score >= 50:
        return "WARM"
    if score >= 20:
        return "COOL"
    return "COLD"


def bid_score(bid_count):
    if bid_count >= 10:
        return 100
    if bid_count >= 5:
        return 75
    if bid_count >= 2:
        return 50
    if bid_count == 1:
        return 25
    return 0


def buyer_size_score(buyer_count):
    if buyer_count >= 50:
        return 100
    if buyer_count >= 30:
        return 75
    if buyer_count >= 10:
        return 50
    if buyer_count >= 1:
        return 25
    return 0


def coverage_gap_score(visit_count):
    if visit_count == 0:
        return 100
    if visit_count <= 2:
        return 75
    if visit_count <= 5:
        return 50
    return 25


def opportunity_level(score):
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    if score >= 40:
        return "LOW"
    return "VERY LOW"


def section_title(title, description):
    st.subheader(title)
    st.caption(description)


def chart_or_note(df, note="ไม่มีข้อมูลเพียงพอสำหรับกราฟนี้"):
    if df is None or df.empty:
        st.info(note)
        return False
    return True


st.title("CRM Intelligence Dashboard")
st.sidebar.header("Upload Excel Files")
buyer_file = st.sidebar.file_uploader("Upload Buyer Master File", type=["xlsx"])
visit_file = st.sidebar.file_uploader("Upload Visit Activity File", type=["xlsx"])

if not buyer_file or not visit_file:
    st.info("Upload both Excel files to start dashboard")
    st.stop()

buyer_xls = pd.ExcelFile(buyer_file)
buyer_frames = []
for sheet in buyer_xls.sheet_names:
    if "Buyer_Master_" in sheet:
        temp = pd.read_excel(buyer_file, sheet_name=sheet)
        temp["Period"] = sheet.replace("Buyer_Master_", "")
        buyer_frames.append(temp)

if not buyer_frames:
    st.error("ไม่พบ sheet ที่ขึ้นต้นด้วย Buyer_Master_ ใน Buyer Master File")
    st.stop()

buyer_df = pd.concat(buyer_frames, ignore_index=True)
visit_df = pd.read_excel(visit_file, sheet_name="01_Visit_Activity_Log")
try:
    demand_df = pd.read_excel(visit_file, sheet_name="02_Visit_Car_Demand_Log")
except Exception:
    demand_df = pd.DataFrame()
try:
    feedback_df = pd.read_excel(visit_file, sheet_name="03_Visit_Feedback_Log")
except Exception:
    feedback_df = pd.DataFrame()

customer_col = find_col(buyer_df, ["Customer_No", "Customer No", "Customer_ID", "Buyer_ID"])
province_col = find_col(buyer_df, ["Province", "จังหวัด"])
ae_col = find_col(buyer_df, ["AE_Name", "AE Name", "AE_Lead", "AE"])
login_col = find_col(buyer_df, ["Login_Count", "Login Count", "Login"])
bid_col = find_col(buyer_df, ["Bid_Count", "Bid Count", "Bid"])
buy_col = find_col(buyer_df, ["Buy_Count", "Sold_Count", "Sold", "Buy Count"])

visit_customer_col = find_col(visit_df, ["Customer_No", "Customer No", "Customer_ID", "Buyer_ID"])
visit_province_col = find_col(visit_df, ["Province", "จังหวัด"])
visit_ae_col = find_col(visit_df, ["AE_Lead", "AE_Name", "AE Name", "AE"])
visit_date_col = find_col(visit_df, ["Visit_Date", "Visit Date", "Date", "วันที่"])
visit_purpose_col = find_col(visit_df, ["Visit_Purpose", "Purpose", "Visit Objective"])
follow_col = find_col(visit_df, ["Need_Follow_Up", "Follow_Up_Status", "Follow-up Status", "Followup_Status"])

if not all([customer_col, province_col, ae_col, login_col, bid_col, buy_col]):
    st.error("ไฟล์ Buyer Master ขาดคอลัมน์หลักที่ต้องใช้ เช่น Customer_No, Province, AE_Name, Login_Count, Bid_Count, Buy_Count")
    st.stop()

for c in [login_col, bid_col, buy_col]:
    buyer_df[c] = to_num(buyer_df[c])

if visit_date_col:
    visit_df[visit_date_col] = pd.to_datetime(visit_df[visit_date_col], errors="coerce")

st.sidebar.header("Global Filters")
periods = sorted(buyer_df["Period"].dropna().unique().tolist())
period_filter = st.sidebar.multiselect("Period", periods, default=periods)
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

filtered = buyer_df.copy()
if period_filter:
    filtered = filtered[filtered["Period"].isin(period_filter)]
if province_filter:
    filtered = filtered[filtered[province_col].astype(str).isin(province_filter)]
if ae_filter:
    filtered = filtered[filtered[ae_col].astype(str).isin(ae_filter)]

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

demand_filtered = demand_df.copy()
feedback_filtered = feedback_df.copy()

period_count = max(1, filtered["Period"].nunique())
buyer_health = filtered.groupby(customer_col).agg(
    Province=(province_col, "last"),
    AE=(ae_col, "last"),
    Total_Login=(login_col, "sum"),
    Total_Bid=(bid_col, "sum"),
    Total_Sold=(buy_col, "sum")
).reset_index()
buyer_health["Sold_Avg_Month"] = buyer_health["Total_Sold"] / period_count
buyer_health["Login_Pct"] = buyer_health["Total_Login"] / 30
login_scores = buyer_health["Total_Login"].apply(score_login)
buyer_health["Login_Score"] = [x[0] for x in login_scores]
buyer_health["Login_Status"] = [x[1] for x in login_scores]
sold_scores = buyer_health["Sold_Avg_Month"].apply(score_sold)
buyer_health["Sold_Score"] = [x[0] for x in sold_scores]
buyer_health["Sold_Status"] = [x[1] for x in sold_scores]
buyer_health["Health_Score"] = (buyer_health["Login_Score"] * 0.50 + buyer_health["Sold_Score"] * 0.50).round(1)
buyer_health["Health_Status"] = buyer_health["Health_Score"].apply(final_health_status)

province_summary = filtered.groupby(province_col).agg(
    Buyers=(customer_col, "nunique"),
    Total_Bid=(bid_col, "sum"),
    Total_Login=(login_col, "sum"),
    Total_Sold=(buy_col, "sum")
).reset_index().rename(columns={province_col: "Province"})
if visit_province_col and not visit_filtered.empty:
    visit_summary = visit_filtered.groupby(visit_province_col).size().reset_index(name="Visits").rename(columns={visit_province_col: "Province"})
else:
    visit_summary = pd.DataFrame(columns=["Province", "Visits"])
province_opp = province_summary.merge(visit_summary, on="Province", how="left")
province_opp["Visits"] = province_opp["Visits"].fillna(0).astype(int)
province_opp["Bid_Score"] = province_opp["Total_Bid"].apply(bid_score)
province_opp["Buyer_Size_Score"] = province_opp["Buyers"].apply(buyer_size_score)
province_opp["Coverage_Gap_Score"] = province_opp["Visits"].apply(coverage_gap_score)
province_opp["Opportunity_Score"] = (province_opp["Bid_Score"] * 0.50 + province_opp["Buyer_Size_Score"] * 0.30 + province_opp["Coverage_Gap_Score"] * 0.20).round(1)
province_opp["Opportunity_Level"] = province_opp["Opportunity_Score"].apply(opportunity_level)

buyer_visit_count = pd.DataFrame(columns=[customer_col, "Visits"])
if visit_customer_col and visit_customer_col in visit_filtered.columns:
    buyer_visit_count = visit_filtered.groupby(visit_customer_col).size().reset_index(name="Visits").rename(columns={visit_customer_col: customer_col})
buyer_opp = buyer_health.merge(buyer_visit_count, on=customer_col, how="left")
buyer_opp["Visits"] = buyer_opp["Visits"].fillna(0).astype(int)
buyer_opp["Bid_Score"] = buyer_opp["Total_Bid"].apply(bid_score)
buyer_opp["Coverage_Gap_Score"] = buyer_opp["Visits"].apply(coverage_gap_score)
buyer_opp["Buyer_Size_Score"] = 25
buyer_opp["Opportunity_Score"] = (buyer_opp["Bid_Score"] * 0.50 + buyer_opp["Buyer_Size_Score"] * 0.30 + buyer_opp["Coverage_Gap_Score"] * 0.20).round(1)
buyer_opp["Opportunity_Level"] = buyer_opp["Opportunity_Score"].apply(opportunity_level)

with st.sidebar.expander("Score Definitions"):
    st.write("Health Score")
    st.code("""Login % = Total Login ล่าสุด 6 เดือน / 30

Login Status:
HOT  >= 65%
WARM >= 35% and < 65%
COOL > 0% and < 35%
COLD = 0%

Sold Avg./Month = Total Sold ล่าสุด 6 เดือน / 6

Sold Status:
HIGH     >= 14 units/month
MODERATE >= 5 and < 14
LOW      > 0 and < 5
COLD     = 0

Health Score =
(Login Score x 50%)
+ (Sold Score x 50%)""")
    st.write("Opportunity Score")
    st.code("""Opportunity Score =
(Bid Score x 50%)
+ (Buyer Size Score x 30%)
+ (Coverage Gap Score x 20%)""")

if page.startswith("1 "):
    st.header("Executive Command Center")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Buyers", f"{filtered[customer_col].nunique():,.0f}")
    c2.metric("Total Login", f"{int(filtered[login_col].sum()):,.0f}")
    c3.metric("Total Bid", f"{int(filtered[bid_col].sum()):,.0f}")
    c4.metric("Total Sold", f"{int(filtered[buy_col].sum()):,.0f}")
    c5.metric("Total Visits", f"{len(visit_filtered):,.0f}")
    section_title("CRM Trend", "ดูแนวโน้ม Login, Bid และ Sold ตาม Period ที่เลือก")
    trend = filtered.groupby("Period").agg(Login=(login_col, "sum"), Bid=(bid_col, "sum"), Sold=(buy_col, "sum")).reset_index()
    if chart_or_note(trend):
        st.plotly_chart(px.line(trend.melt(id_vars="Period", var_name="Metric", value_name="Value"), x="Period", y="Value", color="Metric", markers=True), use_container_width=True)
    section_title("Buyer Health Distribution", "ดูสัดส่วนลูกค้า HOT / WARM / COOL / COLD จากนิยาม Login และ Sold ใหม่")
    heat = buyer_health.groupby("Health_Status").size().reset_index(name="Count")
    if chart_or_note(heat):
        st.plotly_chart(px.pie(heat, names="Health_Status", values="Count"), use_container_width=True)
    section_title("Top Provinces by Sold", "ดูจังหวัดที่สร้าง Sold สูงสุดในช่วงที่เลือก")
    top_province = province_summary.sort_values("Total_Sold", ascending=False).head(15)
    if chart_or_note(top_province):
        st.plotly_chart(px.bar(top_province, x="Total_Sold", y="Province", orientation="h"), use_container_width=True)
    section_title("AE Snapshot", "ดูภาพรวม Buyer, Login, Bid และ Sold แยกตาม AE")
    ae_snapshot = filtered.groupby(ae_col).agg(Buyers=(customer_col, "nunique"), Login=(login_col, "sum"), Bid=(bid_col, "sum"), Sold=(buy_col, "sum")).reset_index().sort_values("Sold", ascending=False)
    st.dataframe(ae_snapshot, use_container_width=True)

elif page.startswith("2 "):
    st.header("Geography & Territory Intelligence")
    section_title("Buyers by Province", "ดูการกระจายฐานลูกค้าตามจังหวัด")
    st.plotly_chart(px.bar(province_summary.sort_values("Buyers", ascending=False).head(25), x="Province", y="Buyers"), use_container_width=True)
    section_title("Province Opportunity Matrix", "เทียบ Visit, Sold, Buyer Size และ Opportunity Score เพื่อหาพื้นที่ที่ควร prioritize")
    st.plotly_chart(px.scatter(province_opp, x="Visits", y="Total_Sold", size="Buyers", color="Opportunity_Score", hover_name="Province"), use_container_width=True)
    section_title("White Space Analysis", "หาจังหวัดที่ Buyer เยอะแต่ Visit ต่ำ ซึ่งอาจเป็นพื้นที่ under coverage")
    st.dataframe(province_opp.sort_values(["Coverage_Gap_Score", "Buyers"], ascending=[False, False]).head(20), use_container_width=True)
    section_title("Province Health Mix", "ดูว่าแต่ละจังหวัดมีลูกค้า HOT / WARM / COOL / COLD มากน้อยแค่ไหน")
    health_province = buyer_health.groupby(["Province", "Health_Status"]).size().reset_index(name="Count")
    if chart_or_note(health_province):
        st.plotly_chart(px.bar(health_province, x="Province", y="Count", color="Health_Status"), use_container_width=True)

elif page.startswith("3 "):
    st.header("AE Performance & Conversion")
    section_title("Visits by AE", "ดูจำนวนการเข้าพบลูกค้าของ AE ตามข้อมูล Visit Log")
    if visit_ae_col:
        visits_ae = visit_filtered.groupby(visit_ae_col).size().reset_index(name="Visits")
        if chart_or_note(visits_ae):
            st.plotly_chart(px.bar(visits_ae.sort_values("Visits", ascending=False), x=visit_ae_col, y="Visits"), use_container_width=True)
    section_title("Sold by AE", "ดู Sold ที่เกิดจากลูกค้าในความรับผิดชอบของ AE")
    ae_perf = filtered.groupby(ae_col).agg(Buyers=(customer_col, "nunique"), Login=(login_col, "sum"), Bid=(bid_col, "sum"), Sold=(buy_col, "sum")).reset_index()
    st.plotly_chart(px.bar(ae_perf.sort_values("Sold", ascending=False), x=ae_col, y="Sold", color="Buyers"), use_container_width=True)
    section_title("AE Conversion Funnel", "ดู flow จาก Login -> Bid -> Sold เพื่อหา drop-off ของแต่ละ AE")
    st.plotly_chart(px.bar(ae_perf.melt(id_vars=ae_col, value_vars=["Login", "Bid", "Sold"], var_name="Stage", value_name="Value"), x=ae_col, y="Value", color="Stage", barmode="group"), use_container_width=True)
    section_title("AE Efficiency Matrix", "เทียบจำนวน Buyer กับ Sold เพื่อดู productivity ของ AE")
    st.plotly_chart(px.scatter(ae_perf, x="Buyers", y="Sold", size="Bid", color="Login", hover_name=ae_col), use_container_width=True)
    section_title("AE Health Mix", "ดูคุณภาพฐานลูกค้าของแต่ละ AE ตาม Health Status")
    ae_health = buyer_health.groupby(["AE", "Health_Status"]).size().reset_index(name="Count")
    st.plotly_chart(px.bar(ae_health, x="AE", y="Count", color="Health_Status"), use_container_width=True)

elif page.startswith("4 "):
    st.header("Buyer Health")
    section_title("Health Score Formula", "สูตรนี้ใช้ Login Status และ Sold Status อย่างละครึ่ง เพื่อให้เข้าใจง่ายและอธิบายได้")
    st.code("""Login % = Total Login ล่าสุด 6 เดือน / 30
Sold Avg./Month = Total Sold ล่าสุด 6 เดือน / 6

Health Score =
(Login Score x 50%)
+ (Sold Score x 50%)""")
    section_title("Health Distribution", "ดูจำนวนลูกค้าแต่ละ Health Status")
    heat = buyer_health.groupby("Health_Status").size().reset_index(name="Count")
    st.plotly_chart(px.pie(heat, names="Health_Status", values="Count"), use_container_width=True)
    section_title("Login Status vs Sold Status", "แยกลูกค้าตาม Engagement และ Commercial Value เพื่อดู pattern ที่ต้อง action")
    matrix = buyer_health.groupby(["Login_Status", "Sold_Status"]).size().reset_index(name="Buyers")
    st.plotly_chart(px.density_heatmap(matrix, x="Login_Status", y="Sold_Status", z="Buyers", text_auto=True), use_container_width=True)
    section_title("Top Healthy Buyers", "รายชื่อลูกค้าที่ Health Score สูงสุดในช่วงที่เลือก")
    st.dataframe(buyer_health.sort_values("Health_Score", ascending=False).head(50), use_container_width=True)
    section_title("Cold / Cool Buyers", "รายชื่อลูกค้าที่ควรพิจารณา re-engage หรือ reactivate")
    st.dataframe(buyer_health[buyer_health["Health_Status"].isin(["COOL", "COLD"])].sort_values("Health_Score").head(50), use_container_width=True)

elif page.startswith("5 "):
    st.header("Opportunity")
    section_title("Opportunity Score Formula", "ใช้ buying intent, market size และ coverage gap โดยไม่ปน Demand Log ที่อาจเป็นลูกค้าใหม่คนละฐาน")
    st.code("""Opportunity Score =
(Bid Score x 50%)
+ (Buyer Size Score x 30%)
+ (Coverage Gap Score x 20%)

Bid Score source: Bid_Count
Buyer Size source: COUNT DISTINCT Customer_No
Coverage Gap source: Visit Count by Province""")
    section_title("Opportunity Province Ranking", "จัดลำดับจังหวัดที่ควร prioritize ให้ AE เข้าไปดูแล")
    st.dataframe(province_opp.sort_values("Opportunity_Score", ascending=False), use_container_width=True)
    section_title("High Potential / Low Coverage", "ดูพื้นที่ที่ Bid หรือ Buyer Size สูง แต่ Visit ยังต่ำ")
    st.plotly_chart(px.scatter(province_opp, x="Visits", y="Total_Bid", size="Buyers", color="Opportunity_Level", hover_name="Province"), use_container_width=True)
    section_title("Opportunity Level Distribution", "ดูสัดส่วนจังหวัด HIGH / MEDIUM / LOW / VERY LOW")
    level = province_opp.groupby("Opportunity_Level").size().reset_index(name="Count")
    st.plotly_chart(px.pie(level, names="Opportunity_Level", values="Count"), use_container_width=True)

elif page.startswith("6 "):
    st.header("Visit & Coverage")
    section_title("Visit Trend", "ดูจำนวน Visit ตามช่วงเวลาเพื่อวัด activity ของทีม AE")
    if visit_date_col and visit_filtered[visit_date_col].notna().any():
        vt = visit_filtered.copy()
        vt["Month"] = vt[visit_date_col].dt.to_period("M").astype(str)
        visit_trend = vt.groupby("Month").size().reset_index(name="Visits")
        st.plotly_chart(px.line(visit_trend, x="Month", y="Visits", markers=True), use_container_width=True)
    else:
        st.info("ไม่พบ Visit Date สำหรับทำกราฟแนวโน้ม")
    section_title("Visits by Province", "ดูว่าทีม AE เข้าไปจังหวัดไหนมากน้อยแค่ไหน")
    if visit_province_col:
        vp = visit_filtered.groupby(visit_province_col).size().reset_index(name="Visits")
        st.plotly_chart(px.bar(vp.sort_values("Visits", ascending=False).head(25), x=visit_province_col, y="Visits"), use_container_width=True)
    section_title("Coverage Gap by Province", "ดูจังหวัดที่มี Buyer แต่ Visit ยังต่ำ")
    st.dataframe(province_opp.sort_values("Coverage_Gap_Score", ascending=False)[["Province", "Buyers", "Visits", "Coverage_Gap_Score"]], use_container_width=True)
    section_title("Visit Purpose Analysis", "ดูว่าการเข้าพบลูกค้าส่วนใหญ่เป็นเรื่องอะไร")
    if visit_purpose_col:
        purpose = visit_filtered.groupby(visit_purpose_col).size().reset_index(name="Count")
        st.plotly_chart(px.pie(purpose, names=visit_purpose_col, values="Count"), use_container_width=True)
    else:
        st.info("ไม่พบคอลัมน์ Visit Purpose")

elif page.startswith("7 "):
    st.header("Demand Intelligence")
    if demand_filtered.empty:
        st.info("ไม่พบ Demand Log")
    else:
        segment_col = find_col(demand_filtered, ["Vehicle_Segment", "Segment"])
        brand_col = find_col(demand_filtered, ["Brand", "Vehicle_Brand"])
        model_col = find_col(demand_filtered, ["Model", "Vehicle_Model"])
        year_col = find_col(demand_filtered, ["Year", "Vehicle_Year"])
        demand_province_col = find_col(demand_filtered, ["Province", "จังหวัด"])
        section_title("Vehicle Segment Demand", "ดูประเภทรถที่ลูกค้าถามหามากที่สุด")
        if segment_col:
            seg = demand_filtered.groupby(segment_col).size().reset_index(name="Demand")
            st.plotly_chart(px.pie(seg, names=segment_col, values="Demand"), use_container_width=True)
        section_title("Brand Demand Ranking", "ดูแบรนด์ที่ถูกถามหามากที่สุด")
        if brand_col:
            brand = demand_filtered.groupby(brand_col).size().reset_index(name="Demand").sort_values("Demand", ascending=False).head(20)
            st.plotly_chart(px.bar(brand, x="Demand", y=brand_col, orientation="h"), use_container_width=True)
        section_title("Model Demand Ranking", "ดูรุ่นรถที่ถูกถามหามากที่สุด")
        if model_col:
            model = demand_filtered.groupby(model_col).size().reset_index(name="Demand").sort_values("Demand", ascending=False).head(20)
            st.plotly_chart(px.treemap(model, path=[model_col], values="Demand"), use_container_width=True)
        section_title("Year Demand Analysis", "ดูปีรถที่ลูกค้าสนใจ")
        if year_col:
            year = demand_filtered.groupby(year_col).size().reset_index(name="Demand")
            st.plotly_chart(px.bar(year, x=year_col, y="Demand"), use_container_width=True)
        section_title("Demand by Province", "ดู Demand ตามพื้นที่จาก Demand Log")
        if demand_province_col:
            dp = demand_filtered.groupby(demand_province_col).size().reset_index(name="Demand").sort_values("Demand", ascending=False).head(25)
            st.plotly_chart(px.bar(dp, x=demand_province_col, y="Demand"), use_container_width=True)

elif page.startswith("8 "):
    st.header("Feedback Intelligence")
    if feedback_filtered.empty:
        st.info("ไม่พบ Feedback Log")
    else:
        fb_category_col = find_col(feedback_filtered, ["Feedback_Category", "Category"])
        fb_sentiment_col = find_col(feedback_filtered, ["Sentiment", "Feedback_Sentiment"])
        fb_ae_col = find_col(feedback_filtered, ["AE_Lead", "AE_Name", "AE"])
        fb_date_col = find_col(feedback_filtered, ["Feedback_Date", "Date"])
        fb_province_col = find_col(feedback_filtered, ["Province", "จังหวัด"])
        if fb_date_col:
            feedback_filtered[fb_date_col] = pd.to_datetime(feedback_filtered[fb_date_col], errors="coerce")
        section_title("Feedback Category Distribution", "ดูประเภท feedback หรือ complaint ที่พบมากที่สุด")
        if fb_category_col:
            fbc = feedback_filtered.groupby(fb_category_col).size().reset_index(name="Count")
            st.plotly_chart(px.pie(fbc, names=fb_category_col, values="Count"), use_container_width=True)
        section_title("Feedback Trend", "ดูแนวโน้ม feedback ตามเวลา")
        if fb_date_col and feedback_filtered[fb_date_col].notna().any():
            ft = feedback_filtered.copy()
            ft["Month"] = ft[fb_date_col].dt.to_period("M").astype(str)
            ftrend = ft.groupby("Month").size().reset_index(name="Feedback")
            st.plotly_chart(px.line(ftrend, x="Month", y="Feedback", markers=True), use_container_width=True)
        section_title("Feedback by AE", "ดู feedback ที่เกี่ยวข้องกับแต่ละ AE")
        if fb_ae_col and fb_category_col:
            fae = feedback_filtered.groupby([fb_ae_col, fb_category_col]).size().reset_index(name="Count")
            st.plotly_chart(px.bar(fae, x=fb_ae_col, y="Count", color=fb_category_col), use_container_width=True)
        section_title("Feedback by Province", "ดูพื้นที่ที่มี feedback สูง")
        if fb_province_col:
            fp = feedback_filtered.groupby(fb_province_col).size().reset_index(name="Feedback").sort_values("Feedback", ascending=False).head(25)
            st.plotly_chart(px.bar(fp, x=fb_province_col, y="Feedback"), use_container_width=True)
        section_title("Positive vs Negative Feedback", "ดูภาพรวม sentiment ถ้ามีข้อมูล sentiment ในไฟล์")
        if fb_sentiment_col:
            fs = feedback_filtered.groupby(fb_sentiment_col).size().reset_index(name="Count")
            st.plotly_chart(px.pie(fs, names=fb_sentiment_col, values="Count"), use_container_width=True)

elif page.startswith("9 "):
    st.header("Follow-up Command Center")
    if not follow_col:
        st.info("ไม่พบคอลัมน์ Follow-up ใน Visit Log")
    else:
        section_title("Follow-up Status", "ดูจำนวนงาน follow-up แยกตามสถานะหรือ flag ที่บันทึกไว้")
        fu = visit_filtered.groupby(follow_col).size().reset_index(name="Count")
        st.plotly_chart(px.bar(fu, x=follow_col, y="Count"), use_container_width=True)
        section_title("Follow-up by AE", "ดูภาระงาน follow-up ของแต่ละ AE")
        if visit_ae_col:
            fuae = visit_filtered.groupby([visit_ae_col, follow_col]).size().reset_index(name="Count")
            st.plotly_chart(px.bar(fuae, x=visit_ae_col, y="Count", color=follow_col), use_container_width=True)
        section_title("Follow-up by Province", "ดูพื้นที่ที่มี follow-up มาก")
        if visit_province_col:
            fup = visit_filtered.groupby([visit_province_col, follow_col]).size().reset_index(name="Count")
            st.plotly_chart(px.bar(fup, x=visit_province_col, y="Count", color=follow_col), use_container_width=True)
        section_title("Follow-up Detail Table", "ใช้ติดตามรายการที่ต้องดำเนินการต่อ")
        st.dataframe(visit_filtered, use_container_width=True)

elif page.startswith("10 "):
    st.header("Recommendation / Next Best Action")
    section_title("Next Best Provinces", "จังหวัดที่ Opportunity Score สูงและควรให้ AE prioritize")
    st.dataframe(province_opp.sort_values("Opportunity_Score", ascending=False).head(20), use_container_width=True)
    section_title("Next Best Buyers", "ลูกค้าที่มี Opportunity สูงจาก Bid และ Coverage Gap")
    st.dataframe(buyer_opp.sort_values("Opportunity_Score", ascending=False).head(50), use_container_width=True)
    section_title("Churn Watch Buyers", "ลูกค้า Health ต่ำที่ควรพิจารณา re-engage")
    churn_watch = buyer_health[buyer_health["Health_Status"].isin(["COOL", "COLD"])].sort_values(["Health_Score", "Total_Sold"], ascending=[True, False])
    st.dataframe(churn_watch.head(50), use_container_width=True)
    section_title("AE Daily Action List", "รายการ action เบื้องต้นสำหรับ AE จาก Health และ Opportunity")
    action = buyer_opp.copy()
    action["Recommended_Action"] = action.apply(lambda r: "Priority Visit" if r["Opportunity_Level"] == "HIGH" else ("Re-engage" if r["Health_Status"] in ["COOL", "COLD"] else "Monitor"), axis=1)
    st.dataframe(action[[customer_col, "Province", "AE", "Health_Status", "Opportunity_Level", "Opportunity_Score", "Recommended_Action"]].sort_values("Opportunity_Score", ascending=False).head(100), use_container_width=True)
