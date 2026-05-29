import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

# =========================
# CONFIG
# =========================

load_dotenv(override=True)

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(proxy_var, None)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="Operational Resilience Intelligence Platform",
    page_icon="🏦",
    layout="wide"
)

RISK_COLORS = {
    "LOW": "#2ECC71",
    "MEDIUM": "#F1C40F",
    "HIGH": "#E67E22",
    "CRITICAL": "#E74C3C"
}

# =========================
# HELPERS
# =========================

@st.cache_data(ttl=60)
def load_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)


def safe_load(table_name):
    try:
        return load_table(table_name)
    except Exception:
        return pd.DataFrame()


def metric_card(label, value):
    st.metric(label, value)


def get_risk_level(score):
    if score >= 85:
        return "CRITICAL"
    elif score >= 65:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    return "LOW"


def show_risk_message(risk_level):
    if risk_level == "CRITICAL":
        st.error(f"Risk Level: {risk_level}")
    elif risk_level == "HIGH":
        st.warning(f"Risk Level: {risk_level}")
    elif risk_level == "MEDIUM":
        st.info(f"Risk Level: {risk_level}")
    else:
        st.success(f"Risk Level: {risk_level}")


def sort_by_time(df):
    if "detected_at" in df.columns:
        return df.sort_values("detected_at", ascending=False)
    if "created_at" in df.columns:
        return df.sort_values("created_at", ascending=False)
    return df


# =========================
# LOAD DATA
# =========================

services = safe_load("services")
incidents = safe_load("incidents")
business_impact = safe_load("business_impact")
propagation = safe_load("incident_propagation")
criticality = safe_load("service_criticality_ranking")
root_causes = safe_load("root_cause_analysis")
resilience_score = safe_load("resilience_score")

recommendations = safe_load("resilience_recommendations")
scenarios = safe_load("scenario_simulations")
vendors = safe_load("vendors")
vendor_dependencies = safe_load("vendor_dependencies")
advanced_kpis = safe_load("advanced_resilience_kpis")

# =========================
# SIDEBAR
# =========================

st.sidebar.title("🏦 Operational Resilience")

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Incident Center",
        "Business Impact",
        "Propagation Analysis",
        "Critical Services",
        "Recommendations",
        "Scenario Simulations",
        "What-if Simulation",
        "Vendor & Cloud Risk",
        "Advanced KPIs",
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Financial Operational Resilience Dashboard")

# =========================
# EXECUTIVE OVERVIEW
# =========================

if page == "Executive Overview":
    st.title("🏦 Operational Resilience Intelligence Platform")
    st.subheader("Executive Overview")

    if not resilience_score.empty:
        latest_score = resilience_score.sort_values("created_at").iloc[-1]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Resilience Score", f"{latest_score['resilience_score']} / 100")
        col2.metric("Risk Level", latest_score["risk_level"])
        col3.metric("Total Incidents", int(latest_score["total_incidents"]))
        col4.metric("Estimated Loss", f"${latest_score['total_estimated_loss_usd']:,.0f}")
    else:
        st.warning("No resilience score found.")

    st.markdown("---")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Incident Severity Distribution")
        if not incidents.empty:
            fig = px.histogram(
                incidents,
                x="severity",
                color="severity",
                color_discrete_map=RISK_COLORS,
                title="Incidents by Severity"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incidents found.")

    with colB:
        st.markdown("### Top Critical Services")
        if not criticality.empty:
            top_services = criticality.sort_values("criticality_score", ascending=False).head(10)

            fig = px.bar(
                top_services,
                x="service_name",
                y="criticality_score",
                color="risk_level",
                color_discrete_map=RISK_COLORS,
                title="Top Critical Services"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No criticality data found.")

# =========================
# INCIDENT CENTER
# =========================

elif page == "Incident Center":
    st.title("🚨 Incident Center")

    if not incidents.empty:
        col1, col2, col3 = st.columns(3)

        col1.metric("Open Incidents", len(incidents[incidents["status"] == "OPEN"]))
        col2.metric("Resolved Incidents", len(incidents[incidents["status"] == "RESOLVED"]))
        col3.metric("Critical Incidents", len(incidents[incidents["severity"] == "CRITICAL"]))

        severity_filter = st.multiselect(
            "Filter by severity",
            options=sorted(incidents["severity"].dropna().unique()),
            default=sorted(incidents["severity"].dropna().unique())
        )

        filtered_incidents = incidents[incidents["severity"].isin(severity_filter)]

        st.dataframe(
            sort_by_time(filtered_incidents),
            use_container_width=True
        )
    else:
        st.info("No incidents found.")

    st.markdown("### Root Cause Analysis")

    if not root_causes.empty:
        st.dataframe(root_causes, use_container_width=True)
    else:
        st.info("No root cause analysis found.")

# =========================
# BUSINESS IMPACT
# =========================

elif page == "Business Impact":
    st.title("💰 Business Impact Analysis")

    if not business_impact.empty:
        total_loss = business_impact["estimated_loss_usd"].sum()
        total_customers = business_impact["affected_customers"].sum()
        total_lost_tx = business_impact["lost_transactions"].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Estimated Loss", f"${total_loss:,.0f}")
        col2.metric("Affected Customers", f"{total_customers:,.0f}")
        col3.metric("Lost Transactions", f"{total_lost_tx:,.0f}")

        fig = px.bar(
            business_impact.sort_values("estimated_loss_usd", ascending=False),
            x="incident_id",
            y="estimated_loss_usd",
            title="Estimated Loss by Incident"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(business_impact, use_container_width=True)
    else:
        st.info("No business impact data found.")

# =========================
# PROPAGATION
# =========================

elif page == "Propagation Analysis":
    st.title("🕸️ Incident Propagation Analysis")

    if not propagation.empty:
        col1, col2 = st.columns(2)

        col1.metric("Propagation Links", len(propagation))
        col2.metric("Average Risk Score", round(propagation["risk_score"].mean(), 2))

        fig = px.histogram(
            propagation,
            x="propagation_level",
            title="Propagation Depth Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.scatter(
            propagation,
            x="propagation_level",
            y="risk_score",
            color="risk_score",
            size="risk_score",
            title="Propagation Risk by Level"
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(propagation, use_container_width=True)
    else:
        st.info("No propagation data found.")

# =========================
# CRITICAL SERVICES
# =========================

elif page == "Critical Services":
    st.title("🔥 Critical Service Ranking")

    if not criticality.empty:
        criticality_sorted = criticality.sort_values("criticality_score", ascending=False)

        fig = px.bar(
            criticality_sorted,
            x="service_name",
            y="criticality_score",
            color="risk_level",
            color_discrete_map=RISK_COLORS,
            title="Service Criticality Ranking"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(criticality_sorted, use_container_width=True)
    else:
        st.info("No critical service ranking found.")

# =========================
# RECOMMENDATIONS
# =========================

elif page == "Recommendations":
    st.title("🧠 Operational Recommendations")

    if not recommendations.empty:
        col1, col2 = st.columns(2)

        col1.metric("Total Recommendations", len(recommendations))
        col2.metric(
            "Critical Recommendations",
            len(recommendations[recommendations["priority"] == "CRITICAL"])
        )

        priority_filter = st.multiselect(
            "Filter by priority",
            options=sorted(recommendations["priority"].dropna().unique()),
            default=sorted(recommendations["priority"].dropna().unique())
        )

        filtered = recommendations[recommendations["priority"].isin(priority_filter)]

        st.dataframe(
            filtered.sort_values("created_at", ascending=False),
            use_container_width=True
        )
    else:
        st.info("No recommendations found.")

# =========================
# SCENARIO SIMULATIONS
# =========================

elif page == "Scenario Simulations":
    st.title("🧪 Scenario Simulations")

    if not scenarios.empty:
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Simulations", len(scenarios))
        col2.metric("Max Estimated Loss", f"${scenarios['estimated_loss_usd'].max():,.0f}")
        col3.metric("Max Risk Score", round(scenarios["risk_score"].max(), 2))

        fig = px.bar(
            scenarios,
            x="scenario_name",
            y="estimated_loss_usd",
            color="risk_score",
            title="Scenario Estimated Loss"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(scenarios, use_container_width=True)
    else:
        st.info("No scenario simulations found.")

# =========================
# WHAT-IF SIMULATION
# =========================

elif page == "What-if Simulation":
    st.title("🧪 What-if Scenario Simulator")

    if services.empty or propagation.empty:
        st.info("Services or propagation data not found.")
    else:
        service_options = dict(zip(services["service_name"], services["service_id"]))

        selected_service = st.selectbox(
            "Select a service failure scenario",
            options=list(service_options.keys())
        )

        source_service_id = service_options[selected_service]

        if st.button("Run Simulation"):
            impacted = propagation[propagation["source_service_id"] == source_service_id]

            impacted_count = impacted["impacted_service_id"].nunique()
            risk_score = impacted["risk_score"].mean() if not impacted.empty else 0

            estimated_customers = impacted_count * 8500
            estimated_lost_transactions = impacted_count * 2200
            estimated_loss = estimated_lost_transactions * 15

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Selected Service", selected_service)
            col2.metric("Impacted Services", impacted_count)
            col3.metric("Estimated Customers", f"{estimated_customers:,.0f}")
            col4.metric("Estimated Loss", f"${estimated_loss:,.0f}")

            st.markdown("---")

            risk_level = get_risk_level(risk_score)

            st.metric("Average Propagation Risk", f"{round(risk_score, 2)} / 100")
            show_risk_message(risk_level)

            st.subheader("Impacted Services")

            if impacted.empty:
                st.warning(
                    "No impacted services detected for this scenario. "
                    "Try Cloud Provider, Payment API, or Core Banking System."
                )
            else:
                impacted_details = impacted.merge(
                    services,
                    left_on="impacted_service_id",
                    right_on="service_id",
                    how="left"
                )

                st.dataframe(
                    impacted_details[
                        [
                            "source_service_id",
                            "impacted_service_id",
                            "service_name",
                            "propagation_level",
                            "risk_score"
                        ]
                    ],
                    use_container_width=True
                )

# =========================
# VENDOR & CLOUD RISK
# =========================

elif page == "Vendor & Cloud Risk":
    st.title("☁️ Vendor & Cloud Risk")

    if not vendors.empty:
        fig = px.bar(
            vendors,
            x="vendor_name",
            y="criticality_score",
            color="risk_level",
            color_discrete_map=RISK_COLORS,
            title="Vendor Risk Score"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(vendors, use_container_width=True)
    else:
        st.info("No vendor data found.")

    st.markdown("### Vendor Dependencies")

    if not vendor_dependencies.empty:
        st.dataframe(vendor_dependencies, use_container_width=True)
    else:
        st.info("No vendor dependencies found.")

# =========================
# ADVANCED KPIS
# =========================

elif page == "Advanced KPIs":
    st.title("📊 Advanced Resilience KPIs")

    if not advanced_kpis.empty:
        latest_kpis = advanced_kpis.sort_values("created_at").iloc[-1]

        col1, col2, col3 = st.columns(3)

        col1.metric("MTTR", f"{latest_kpis['mttr_minutes']} min")
        col2.metric("MTTD", f"{latest_kpis['mttd_minutes']} min")
        col3.metric("MTBF", f"{latest_kpis['mtbf_minutes']} min")

        col4, col5, col6 = st.columns(3)

        col4.metric("SLA Compliance", f"{latest_kpis['sla_compliance_rate']}%")
        col5.metric("Open Incident Rate", f"{latest_kpis['open_incident_rate']}%")
        col6.metric("Critical Incident Rate", f"{latest_kpis['critical_incident_rate']}%")

        st.dataframe(advanced_kpis, use_container_width=True)
    else:
        st.info("No advanced KPIs found.")
