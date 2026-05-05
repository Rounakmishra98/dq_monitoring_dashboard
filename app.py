# ============================================================
# DATA QUALITY MONITORING DASHBOARD
# Author: Rounak Mishra
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from dq_analysis import run_full_dq_assessment

# Page config
st.set_page_config(
    page_title="Data Quality Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem; font-weight: 800;
        color: #1F4E79; margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1rem; color: #555;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def get_score_color(score):
    if score >= 85: return "#28a745"
    elif score >= 70: return "#ffc107"
    else: return "#dc3545"


def get_score_label(score):
    if score >= 85: return "✅ Excellent"
    elif score >= 70: return "⚠️ Needs Attention"
    else: return "❌ Critical Issue"


# ── SIDEBAR ──────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DQ Dashboard")
    st.markdown("**Built by Rounak Mishra**")
    st.markdown("Data Quality Analyst | CSIR-IITR")
    st.divider()
    uploaded_file = st.file_uploader(
        "📁 Upload CSV dataset",
        type=['csv']
    )
    st.markdown("---")
    st.markdown("### DQ Dimensions")
    for d in ["✅ Completeness", "✅ Uniqueness",
              "✅ Consistency", "✅ Validity",
              "✅ Accuracy", "✅ Timeliness"]:
        st.markdown(d)


# ── HEADER ───────────────────────────────────────
st.markdown(
    '<div class="main-title">📊 Data Quality Monitoring Dashboard</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">End-to-end DQ assessment across 6 dimensions | Rounak Mishra | CSIR-IITR</div>',
    unsafe_allow_html=True
)

# Load data
if uploaded_file:
    df_temp = pd.read_csv(uploaded_file)
    df_temp.to_csv('dataset.csv', index=False)

try:
    results = run_full_dq_assessment('dataset.csv')
    df = results['dataframe']
except FileNotFoundError:
    st.error("⚠️ dataset.csv not found.")
    st.stop()


# ── SECTION 1: OVERVIEW METRICS ──────────────────
st.subheader("📋 Dataset Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rows",
    f"{results['dataset_info']['rows']:,}")
col2.metric("Total Columns",
    results['dataset_info']['columns'])
col3.metric("Missing Cells",
    f"{results['completeness']['null_cells']:,}",
    delta=f"-{results['completeness']['missing_pct']}%",
    delta_color="inverse")
col4.metric("Duplicate Rows",
    f"{results['uniqueness']['duplicate_rows']:,}",
    delta=f"-{results['uniqueness']['duplicate_pct']}%",
    delta_color="inverse")

st.divider()


# ── SECTION 2: OVERALL SCORECARD ─────────────────
st.subheader("🎯 Overall Data Quality Scorecard")

overall = results['overall_score']
overall_color = get_score_color(overall)

dim_names = ['Completeness', 'Uniqueness', 'Consistency',
             'Validity', 'Accuracy', 'Timeliness']
dim_scores = [
    results['completeness']['score'],
    results['uniqueness']['score'],
    results['consistency']['score'],
    results['validity']['score'],
    results['accuracy']['score'],
    results['timeliness']['score']
]

# Gauge chart
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=overall,
    title={'text': "Overall DQ Score", 'font': {'size': 20}},
    number={'suffix': "%", 'font': {'size': 40}},
    delta={'reference': 80, 'valueformat': '.1f'},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': overall_color},
        'steps': [
            {'range': [0, 70], 'color': '#ffe0e0'},
            {'range': [70, 85], 'color': '#fff8e0'},
            {'range': [85, 100], 'color': '#e0ffe8'}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75, 'value': 80
        }
    }
))
fig_gauge.update_layout(height=280,
    margin=dict(t=40, b=20))

# Radar chart
fig_radar = go.Figure(go.Scatterpolar(
    r=dim_scores + [dim_scores[0]],
    theta=dim_names + [dim_names[0]],
    fill='toself',
    fillcolor='rgba(31,78,121,0.2)',
    line=dict(color='#1F4E79', width=2),
    marker=dict(size=8, color='#1F4E79')
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(
        visible=True, range=[0, 100])),
    showlegend=False, height=320,
    title="DQ Dimensions Radar"
)

g1, g2 = st.columns([1, 1])
with g1:
    st.plotly_chart(fig_gauge,
        use_container_width=True)
with g2:
    st.plotly_chart(fig_radar,
        use_container_width=True)

st.divider()


# ── SECTION 3: DIMENSION BAR CHART ───────────────
st.subheader("📐 DQ Dimension Breakdown")

fig_bar = px.bar(
    x=dim_names, y=dim_scores,
    color=dim_scores,
    color_continuous_scale=[
        '#dc3545', '#ffc107', '#28a745'],
    range_color=[0, 100],
    labels={'x': 'DQ Dimension', 'y': 'Score (%)'},
    title="Score by DQ Dimension",
    text=[f"{s}%" for s in dim_scores]
)
fig_bar.update_traces(textposition='outside')
fig_bar.update_layout(
    yaxis_range=[0, 110],
    showlegend=False, height=380)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()


# ── SECTION 4: MISSING VALUE HEATMAP ─────────────
st.subheader("🗺️ Completeness — Missing Values by Column")

missing_df = pd.DataFrame({
    'Column': df.columns,
    'Missing %': [round(df[c].isnull().mean()*100, 2)
                  for c in df.columns],
}).sort_values('Missing %', ascending=False)

fig_miss = px.bar(
    missing_df, x='Column', y='Missing %',
    color='Missing %',
    color_continuous_scale=['#e8f5e9', '#ff5252'],
    title="Missing Value % per Column",
    text='Missing %'
)
fig_miss.update_traces(
    texttemplate='%{text}%',
    textposition='outside')
fig_miss.update_layout(
    height=380, xaxis_tickangle=-45)
st.plotly_chart(fig_miss, use_container_width=True)

st.divider()


# ── SECTION 5: CORRELATION HEATMAP ───────────────
st.subheader("🔗 Correlation Heatmap")

numeric_df = df.select_dtypes(include=[np.number])
if not numeric_df.empty and len(numeric_df.columns) > 1:
    fig_corr, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        numeric_df.corr(), annot=True, fmt='.2f',
        cmap='Blues', ax=ax,
        linewidths=0.5, square=True
    )
    ax.set_title('Feature Correlation Matrix',
        fontsize=14, fontweight='bold')
    st.pyplot(fig_corr)
else:
    st.info("No numeric columns for correlation.")

st.divider()


# ── SECTION 6: ISSUES TABLE ───────────────────────
st.subheader("🚨 Data Quality Issues Summary")

issues = []
for col, pct in results['completeness']['col_breakdown'].items():
    if pct < 100:
        issues.append({
            'Column': col,
            'Issue Type': 'Missing Values',
            'Severity': 'High' if pct < 70 else 'Medium',
            'Details': f"{100-pct:.1f}% missing"
        })

for col in results['consistency']['inconsistent_cols']:
    issues.append({
        'Column': col,
        'Issue Type': 'Consistency',
        'Severity': 'Medium',
        'Details': 'Mixed data types or casing'
    })

for col, cnt in results['validity']['invalid_counts'].items():
    if cnt > 0:
        issues.append({
            'Column': col,
            'Issue Type': 'Outliers',
            'Severity': 'Low',
            'Details': f"{cnt} outliers detected"
        })

if issues:
    st.dataframe(
        pd.DataFrame(issues),
        use_container_width=True)
else:
    st.success("🎉 No critical DQ issues found!")

st.divider()

# ── FOOTER ────────────────────────────────────────
st.markdown("""
<div style='text-align:center;color:#888;
font-size:13px;padding:20px'>
Built by <strong>Rounak Mishra</strong> |
Data Quality Analyst Portfolio |
<a href='https://github.com/Rounakmishra98'>
GitHub</a>
</div>
""", unsafe_allow_html=True)