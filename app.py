
import re
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from datetime import datetime, timedelta

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="TRACE | Log Intelligence",
    page_icon="⌁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# DESIGN SYSTEM
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #0B0F10;
    --panel: #111819;
    --panel2: #172020;
    --line: #263332;
    --text: #E7EFEB;
    --muted: #899994;
    --green: #B8F36B;
    --amber: #FFBD59;
    --red: #FF646E;
    --cyan: #67DCE0;
}
.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
}
[data-testid="stSidebar"] {
    background: #101718;
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] * {
    color: var(--text);
}
.block-container {
    max-width: 1550px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}
h1, h2, h3, p, label {
    color: var(--text);
}
.eyebrow {
    color: var(--green);
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 2.2px;
    text-transform: uppercase;
}
.hero {
    font-size: clamp(38px, 5vw, 62px);
    font-weight: 700;
    letter-spacing: -3.5px;
    line-height: 1.02;
    margin-top: 8px;
}
.subtitle {
    color: var(--muted);
    max-width: 760px;
    font-size: 14px;
    line-height: 1.8;
    margin-top: 12px;
}
.metric {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 17px;
    min-height: 105px;
}
.metric-label {
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}
.metric-value {
    color: var(--green);
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -1.5px;
    margin-top: 8px;
}
.metric-note {
    color: var(--muted);
    font-size: 11px;
    margin-top: 2px;
}
.section-heading {
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.8px;
    margin-top: 17px;
    margin-bottom: 6px;
}
.panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 13px;
    padding: 18px;
}
.mono {
    font-family: 'DM Mono', monospace;
    color: var(--muted);
    font-size: 10px;
}
.status-line {
    font-family: 'DM Mono', monospace;
    color: var(--green);
    font-size: 11px;
    letter-spacing: 1px;
}
.stButton > button, .stDownloadButton > button {
    background: var(--green);
    color: #101718;
    border: 0;
    border-radius: 7px;
    font-weight: 700;
    min-height: 40px;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: #D0FF91;
    color: #101718;
    border: 0;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 9px;
}
div[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--line);
    padding: 12px;
    border-radius: 10px;
}
hr {
    border-color: var(--line);
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTS
# =========================================================
BG = "#111819"
GRID = "#263332"
GREEN = "#B8F36B"
AMBER = "#FFBD59"
RED = "#FF646E"
CYAN = "#67DCE0"
TEXT = "#E7EFEB"
MUTED = "#899994"

LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LEVEL_RANK = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4
}

# =========================================================
# DEMO DATA GENERATOR
# =========================================================
def generate_demo_logs():
    rng = np.random.default_rng(91)

    services = [
        "auth-service",
        "payment-api",
        "user-service",
        "inventory-worker",
        "notification-service",
        "gateway"
    ]

    messages = {
        "DEBUG": [
            "Cache lookup completed",
            "Request payload validated",
            "Connection pool checked",
            "Background task scheduled"
        ],
        "INFO": [
            "Request processed successfully",
            "User session created",
            "Database query completed",
            "Worker task completed",
            "Health check passed"
        ],
        "WARNING": [
            "Response time above expected range",
            "Retry attempt initiated",
            "Connection pool nearing capacity",
            "Rate limit approaching threshold"
        ],
        "ERROR": [
            "Database connection timeout",
            "Request processing failed",
            "Dependency returned server error",
            "Queue delivery failed",
            "Authentication token rejected"
        ],
        "CRITICAL": [
            "Service health check failed",
            "Database connection unavailable",
            "Repeated request failures detected",
            "Worker process terminated unexpectedly"
        ]
    }

    start = datetime.now() - timedelta(hours=24)
    rows = []

    for i in range(1800):
        timestamp = start + timedelta(
            seconds=int(rng.integers(0, 86400))
        )
        service = rng.choice(services)

        # Normal baseline severity distribution.
        level = rng.choice(
            LEVELS,
            p=[0.12, 0.69, 0.12, 0.06, 0.01]
        )

        # Create a concentrated error burst for the demo.
        if (
            timestamp.hour == (start + timedelta(hours=12)).hour
            and timestamp.minute in range(10, 18)
            and service in ["payment-api", "gateway"]
        ):
            level = rng.choice(
                ["ERROR", "CRITICAL"],
                p=[0.82, 0.18]
            )

        message = rng.choice(messages[level])
        source_ip = (
            f"10.0.{int(rng.integers(1, 9))}."
            f"{int(rng.integers(2, 250))}"
        )

        rows.append({
            "timestamp": timestamp,
            "level": level,
            "service": service,
            "source_ip": source_ip,
            "message": message,
            "event_id": f"EVT-{i + 1:06d}"
        })

    return pd.DataFrame(rows)


# =========================================================
# LOG PARSING
# =========================================================
def normalise_level(value):
    text = str(value).strip().upper()

    aliases = {
        "WARN": "WARNING",
        "FATAL": "CRITICAL",
        "SEVERE": "ERROR"
    }

    text = aliases.get(text, text)
    return text if text in LEVELS else "INFO"


def parse_text_logs(text):
    """
    Supports lines similar to:
    2026-11-09 12:30:00 ERROR payment-api 10.0.0.4 Database timeout
    """
    pattern = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})"
        r"\s+(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)"
        r"\s+(?P<service>\S+)"
        r"(?:\s+(?P<source_ip>\d{1,3}(?:\.\d{1,3}){3}))?"
        r"\s+(?P<message>.*)$",
        re.IGNORECASE
    )

    rows = []
    skipped = 0

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if not match:
            skipped += 1
            continue

        item = match.groupdict()
        rows.append({
            "timestamp": item["timestamp"],
            "level": normalise_level(item["level"]),
            "service": item["service"],
            "source_ip": item["source_ip"] or "Unknown",
            "message": item["message"],
            "event_id": f"TXT-{len(rows) + 1:06d}"
        })

    return pd.DataFrame(rows), skipped


def prepare_logs(df):
    required = ["timestamp", "level", "service", "message"]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    clean = df.copy()

    clean["timestamp"] = pd.to_datetime(
        clean["timestamp"], errors="coerce"
    )
    clean["level"] = clean["level"].apply(normalise_level)
    clean["service"] = clean["service"].fillna("unknown").astype(str)
    clean["message"] = clean["message"].fillna("").astype(str)

    if "source_ip" not in clean.columns:
        clean["source_ip"] = "Unknown"
    else:
        clean["source_ip"] = (
            clean["source_ip"].fillna("Unknown").astype(str)
        )

    if "event_id" not in clean.columns:
        clean["event_id"] = [
            f"EVT-{i + 1:06d}" for i in range(len(clean))
        ]

    clean = clean.dropna(subset=["timestamp"])
    clean = clean[clean["service"].str.strip() != ""]
    clean = clean.sort_values("timestamp").reset_index(drop=True)

    if clean.empty:
        raise ValueError(
            "No valid log records remain after parsing timestamps."
        )

    clean["severity_rank"] = clean["level"].map(LEVEL_RANK)
    clean["is_error"] = clean["level"].isin(
        ["ERROR", "CRITICAL"]
    )
    clean["minute"] = clean["timestamp"].dt.floor("min")
    clean["five_minute"] = clean["timestamp"].dt.floor("5min")

    return clean


# =========================================================
# ANALYTICS
# =========================================================
def detect_error_spikes(logs, multiplier=3.0):
    per_minute = (
        logs[logs["is_error"]]
        .groupby("minute")
        .size()
        .rename("error_count")
        .reset_index()
    )

    if per_minute.empty:
        return per_minute, 0.0

    # Fill missing minutes so the timeline is continuous.
    full_range = pd.date_range(
        per_minute["minute"].min(),
        per_minute["minute"].max(),
        freq="1min"
    )

    per_minute = (
        per_minute.set_index("minute")
        .reindex(full_range, fill_value=0)
        .rename_axis("minute")
        .reset_index()
    )

    median = float(per_minute["error_count"].median())
    mad = float(
        np.median(
            np.abs(per_minute["error_count"] - median)
        )
    )

    threshold = median + multiplier * 1.4826 * mad

    # Avoid flagging zero-count periods when the baseline is zero.
    if threshold == 0:
        threshold = 1.0

    per_minute["is_spike"] = (
        per_minute["error_count"] > threshold
    )

    return per_minute, threshold


def build_incidents(logs, min_events=3):
    serious = logs[
        logs["level"].isin(["ERROR", "CRITICAL"])
    ].copy()

    if serious.empty:
        return pd.DataFrame()

    incidents = (
        serious.groupby(["service", "five_minute"])
        .agg(
            event_count=("event_id", "count"),
            critical_count=(
                "level",
                lambda x: int((x == "CRITICAL").sum())
            ),
            first_seen=("timestamp", "min"),
            last_seen=("timestamp", "max"),
            sample_message=("message", "first")
        )
        .reset_index()
    )

    incidents = incidents[
        incidents["event_count"] >= min_events
    ].copy()

    if incidents.empty:
        return incidents

    incidents["priority"] = np.where(
        incidents["critical_count"] > 0,
        "CRITICAL",
        "HIGH"
    )

    incidents["incident_id"] = [
        f"INC-{i + 1:04d}" for i in range(len(incidents))
    ]

    return incidents.sort_values(
        ["critical_count", "event_count"],
        ascending=False
    ).reset_index(drop=True)


# =========================================================
# CHART THEME
# =========================================================
def theme_chart(fig, height=330):
    fig.update_layout(
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Space Grotesk"),
        margin=dict(l=15, r=15, t=45, b=15),
        xaxis=dict(
            gridcolor=GRID,
            zerolinecolor=GRID
        ),
        yaxis=dict(
            gridcolor=GRID,
            zerolinecolor=GRID
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT)
        )
    )
    return fig


def page_header(kicker, title, description):
    st.markdown(
        f"<div class='eyebrow'>{kicker}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='hero'>{title}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='subtitle'>{description}</div>",
        unsafe_allow_html=True
    )
    st.write("")


def metric_card(label, value, note):
    st.markdown(
        f"""
        <div class="metric">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SIDEBAR — DATA SOURCE
# =========================================================
st.sidebar.markdown("## ⌁ TRACE")
st.sidebar.markdown(
    "<div class='mono'>LOG INTELLIGENCE / DAY 09</div>",
    unsafe_allow_html=True
)
st.sidebar.divider()

source_mode = st.sidebar.radio(
    "LOG SOURCE",
    ["Synthetic demo", "Upload CSV", "Upload TXT"]
)

skipped_lines = 0

if source_mode == "Synthetic demo":
    raw_logs = generate_demo_logs()
    source_name = "trace_demo_logs"
elif source_mode == "Upload CSV":
    file = st.sidebar.file_uploader(
        "Upload log CSV",
        type=["csv"]
    )

    if file is None:
        page_header(
            "INPUT REQUIRED / 001",
            "Waiting for log data.",
            "Upload a CSV file containing timestamp, level, service "
            "and message columns to begin the investigation."
        )
        st.info("Or switch to Synthetic demo to explore TRACE immediately.")
        st.stop()

    try:
        raw_logs = pd.read_csv(file)
        source_name = file.name
    except Exception as error:
        st.error(f"Could not read CSV: {error}")
        st.stop()

elif source_mode == "Upload TXT":
    file = st.sidebar.file_uploader(
        "Upload plain-text logs",
        type=["txt", "log"]
    )

    if file is None:
        page_header(
            "INPUT REQUIRED / 001",
            "Waiting for log data.",
            "Upload text logs in the supported timestamp, severity, "
            "service, optional IP and message format."
        )
        st.info("Or switch to Synthetic demo to explore TRACE immediately.")
        st.stop()

    text_content = file.getvalue().decode(
        "utf-8", errors="replace"
    )
    raw_logs, skipped_lines = parse_text_logs(text_content)
    source_name = file.name

    if raw_logs.empty:
        st.error(
            "No supported log lines were found. Check the TXT format "
            "described in the README."
        )
        st.stop()

try:
    logs = prepare_logs(raw_logs)
except Exception as error:
    st.error(f"Could not prepare the logs: {error}")
    st.stop()

# =========================================================
# FILTER CONTROLS
# =========================================================
st.sidebar.divider()
st.sidebar.markdown("### INVESTIGATION FILTERS")

available_levels = [
    level for level in LEVELS
    if level in logs["level"].unique()
]

selected_levels = st.sidebar.multiselect(
    "Severity",
    available_levels,
    default=available_levels
)

available_services = sorted(logs["service"].unique())

selected_services = st.sidebar.multiselect(
    "Services",
    available_services,
    default=available_services
)

time_min = logs["timestamp"].min().to_pydatetime()
time_max = logs["timestamp"].max().to_pydatetime()

if time_min == time_max:
    selected_start, selected_end = time_min, time_max
else:
    selected_start, selected_end = st.sidebar.slider(
        "Time range",
        min_value=time_min,
        max_value=time_max,
        value=(time_min, time_max),
        format="DD/MM HH:mm"
    )

min_incident_events = st.sidebar.slider(
    "Minimum events per incident",
    min_value=2,
    max_value=15,
    value=3
)

filtered = logs[
    logs["level"].isin(selected_levels)
    & logs["service"].isin(selected_services)
    & (logs["timestamp"] >= selected_start)
    & (logs["timestamp"] <= selected_end)
].copy()

if filtered.empty:
    st.warning("No events match your current filters.")
    st.stop()

# =========================================================
# GLOBAL ANALYSIS
# =========================================================
error_logs = filtered[filtered["is_error"]]
critical_count = int((filtered["level"] == "CRITICAL").sum())
warning_count = int((filtered["level"] == "WARNING").sum())

spike_data, spike_threshold = detect_error_spikes(filtered)
incidents = build_incidents(
    filtered,
    min_events=min_incident_events
)

# =========================================================
# NAVIGATION
# =========================================================
st.sidebar.divider()
page = st.sidebar.radio(
    "OPERATIONS CONSOLE",
    [
        "Command Center",
        "Event Stream",
        "Incident Correlation",
        "Service Health",
        "Export & Reports"
    ]
)

st.sidebar.divider()
st.sidebar.markdown(
    "<div class='mono'>TRACE ENGINE / 0.9<br>DAY 09 OF 60</div>",
    unsafe_allow_html=True
)

# =========================================================
# PAGE 1 — COMMAND CENTER
# =========================================================
if page == "Command Center":
    page_header(
        "SYSTEM OBSERVABILITY / 001",
        "Know what is happening.",
        "A unified view of application events, severity patterns, "
        "and potential incidents. Investigate the signals before "
        "they become bigger operational problems."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total events", f"{len(filtered):,}", "After selected filters")
    with c2:
        metric_card("Errors", f"{len(error_logs):,}", "ERROR + CRITICAL")
    with c3:
        metric_card("Critical", f"{critical_count:,}", "Highest severity")
    with c4:
        metric_card("Potential incidents", f"{len(incidents):,}", "Correlated event groups")

    st.write("")

    left, right = st.columns([1.6, 1])

    with left:
        st.markdown(
            "<div class='section-heading'>Event activity</div>",
            unsafe_allow_html=True
        )

        activity = (
            filtered.set_index("timestamp")
            .resample("15min")
            .size()
            .rename("events")
            .reset_index()
        )

        fig = px.area(
            activity,
            x="timestamp",
            y="events",
            color_discrete_sequence=[GREEN]
        )
        fig.update_traces(
            line=dict(width=2),
            fillcolor="rgba(184,243,107,0.12)"
        )
        theme_chart(fig, 340)
        fig.update_layout(
            title="EVENT VOLUME · 15 MINUTE INTERVALS",
            xaxis_title="Time",
            yaxis_title="Events"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown(
            "<div class='section-heading'>Severity distribution</div>",
            unsafe_allow_html=True
        )

        severity = (
            filtered["level"].value_counts()
            .reindex(LEVELS, fill_value=0)
            .reset_index()
        )
        severity.columns = ["Severity", "Events"]

        colors = {
            "DEBUG": "#697B76",
            "INFO": CYAN,
            "WARNING": AMBER,
            "ERROR": "#FF8B65",
            "CRITICAL": RED
        }

        fig = px.pie(
            severity[severity["Events"] > 0],
            names="Severity",
            values="Events",
            hole=0.68,
            color="Severity",
            color_discrete_map=colors
        )
        fig.update_traces(
            textposition="outside",
            textfont=dict(color=TEXT)
        )
        theme_chart(fig, 340)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "<div class='section-heading'>Latest high-severity events</div>",
        unsafe_allow_html=True
    )

    latest = filtered[
        filtered["level"].isin(["ERROR", "CRITICAL"])
    ].sort_values("timestamp", ascending=False).head(8)

    if latest.empty:
        st.success("No ERROR or CRITICAL events in this filtered view.")
    else:
        st.dataframe(
            latest[
                ["timestamp", "level", "service", "source_ip", "message"]
            ],
            hide_index=True,
            use_container_width=True
        )

# =========================================================
# PAGE 2 — EVENT STREAM
# =========================================================
elif page == "Event Stream":
    page_header(
        "RAW EVENT INVESTIGATION / 002",
        "Read the event stream.",
        "Search through individual log records, narrow the view "
        "by service and severity, and inspect the messages behind "
        "your operational signals."
    )

    search_text = st.text_input(
        "Search log messages",
        placeholder="Search for timeout, failed, database..."
    )

    stream = filtered.copy()

    if search_text.strip():
        mask = (
            stream["message"].str.contains(
                search_text,
                case=False,
                na=False,
                regex=False
            )
            | stream["source_ip"].str.contains(
                search_text,
                case=False,
                na=False,
                regex=False
            )
            | stream["service"].str.contains(
                search_text,
                case=False,
                na=False,
                regex=False
            )
        )
        stream = stream[mask]

    st.markdown(
        f"<div class='status-line'>"
        f"QUERY RESULT: {len(stream):,} EVENTS"
        f"</div>",
        unsafe_allow_html=True
    )

    st.dataframe(
        stream[
            [
                "timestamp",
                "level",
                "service",
                "source_ip",
                "message",
                "event_id"
            ]
        ].sort_values("timestamp", ascending=False),
        hide_index=True,
        use_container_width=True,
        height=560
    )

    st.caption(
        "Search is literal text matching across the message, source IP "
        "and service fields."
    )

# =========================================================
# PAGE 3 — INCIDENT CORRELATION
# =========================================================
elif page == "Incident Correlation":
    page_header(
        "EVENT CORRELATION / 003",
        "Connect the signals.",
        "Group serious events by service and five-minute time window "
        "to create potential incident candidates for investigation."
    )

    if incidents.empty:
        st.success(
            "No event groups meet the current incident threshold. "
            "Try lowering the minimum event count in the sidebar."
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Incident candidates", len(incidents), "Correlated groups")
        with c2:
            metric_card(
                "Critical groups",
                int((incidents["priority"] == "CRITICAL").sum()),
                "Contain at least one CRITICAL event"
            )
        with c3:
            metric_card(
                "Events in groups",
                int(incidents["event_count"].sum()),
                "ERROR + CRITICAL events"
            )

        st.markdown(
            "<div class='section-heading'>Incident candidates</div>",
            unsafe_allow_html=True
        )

        st.dataframe(
            incidents[
                [
                    "incident_id",
                    "priority",
                    "service",
                    "five_minute",
                    "event_count",
                    "critical_count",
                    "first_seen",
                    "last_seen",
                    "sample_message"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

        incident_id = st.selectbox(
            "Investigate an incident",
            incidents["incident_id"].tolist()
        )

        selected_incident = incidents[
            incidents["incident_id"] == incident_id
        ].iloc[0]

        related = filtered[
            (filtered["service"] == selected_incident["service"])
            & (
                filtered["five_minute"]
                == selected_incident["five_minute"]
            )
            & filtered["is_error"]
        ]

        st.markdown(
            "<div class='section-heading'>Related event records</div>",
            unsafe_allow_html=True
        )

        st.write(
            f"Service: **{selected_incident['service']}** · "
            f"Window: **{selected_incident['five_minute']}**"
        )

        st.dataframe(
            related[
                [
                    "timestamp",
                    "level",
                    "source_ip",
                    "message",
                    "event_id"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

        st.warning(
            "These are potential incidents based on time and service "
            "grouping. They are not proof that events share one root cause."
        )

    st.markdown(
        "<div class='section-heading'>Error spike detection</div>",
        unsafe_allow_html=True
    )

    if spike_data.empty:
        st.info("No error events are available for spike analysis.")
    else:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=spike_data["minute"],
            y=spike_data["error_count"],
            marker_color=[
                RED if value else GREEN
                for value in spike_data["is_spike"]
            ],
            name="Errors per minute"
        ))

        fig.add_hline(
            y=spike_threshold,
            line_dash="dash",
            line_color=AMBER,
            annotation_text="Spike threshold"
        )

        theme_chart(fig, 320)
        fig.update_layout(
            title="ERROR EVENTS PER MINUTE",
            xaxis_title="Time",
            yaxis_title="Error count"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Spike threshold is based on the median and median absolute "
            "deviation of minute-level error counts."
        )

# =========================================================
# PAGE 4 — SERVICE HEALTH
# =========================================================
elif page == "Service Health":
    page_header(
        "SERVICE OBSERVABILITY / 004",
        "Find the noisy services.",
        "Compare services by event volume, error rate and severity "
        "to identify where investigation may be most useful."
    )

    service_stats = (
        filtered.groupby("service")
        .agg(
            total_events=("event_id", "count"),
            errors=("is_error", "sum"),
            critical=("level", lambda x: int((x == "CRITICAL").sum())),
            warnings=("level", lambda x: int((x == "WARNING").sum()))
        )
        .reset_index()
    )

    service_stats["error_rate_pct"] = (
        service_stats["errors"]
        / service_stats["total_events"].clip(lower=1)
        * 100
    )

    service_stats = service_stats.sort_values(
        ["errors", "total_events"],
        ascending=False
    )

    st.markdown(
        "<div class='section-heading'>Service comparison</div>",
        unsafe_allow_html=True
    )

    fig = px.bar(
        service_stats,
        x="service",
        y="errors",
        color="errors",
        color_continuous_scale=["#40534B", GREEN]
    )
    theme_chart(fig, 360)
    fig.update_layout(
        title="ERROR EVENTS BY SERVICE",
        xaxis_title="Service",
        yaxis_title="Error count",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        service_stats.round(2),
        hide_index=True,
        use_container_width=True
    )

    st.markdown(
        "<div class='section-heading'>Frequent source IPs</div>",
        unsafe_allow_html=True
    )

    ip_stats = (
        error_logs.groupby("source_ip")
        .size()
        .rename("error_events")
        .reset_index()
        .sort_values("error_events", ascending=False)
        .head(12)
    )

    if ip_stats.empty:
        st.info("No error source IPs found in the current filtered view.")
    else:
        fig = px.bar(
            ip_stats,
            x="error_events",
            y="source_ip",
            orientation="h",
            color_discrete_sequence=[CYAN]
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        theme_chart(fig, 360)
        fig.update_layout(
            title="TOP SOURCE IPS BY ERROR COUNT",
            xaxis_title="Error events",
            yaxis_title="Source IP"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "An IP with many errors is an investigation lead, not evidence "
        "of malicious activity."
    )

# =========================================================
# PAGE 5 — EXPORT
# =========================================================
elif page == "Export & Reports":
    page_header(
        "REPORTING / 005",
        "Package the findings.",
        "Export filtered event records, service-level statistics "
        "and potential incident candidates for further investigation."
    )

    st.markdown(
        "<div class='section-heading'>Export preview</div>",
        unsafe_allow_html=True
    )

    st.dataframe(
        filtered.head(15),
        hide_index=True,
        use_container_width=True
    )

    logs_csv = filtered.to_csv(index=False).encode("utf-8")
    service_csv = (
        filtered.groupby("service")
        .agg(
            total_events=("event_id", "count"),
            errors=("is_error", "sum"),
            critical=("level", lambda x: int((x == "CRITICAL").sum()))
        )
        .reset_index()
        .to_csv(index=False)
        .encode("utf-8")
    )

    incident_csv = incidents.to_csv(index=False).encode("utf-8")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            "Download filtered logs",
            logs_csv,
            "trace_filtered_logs.csv",
            "text/csv",
            use_container_width=True
        )

    with c2:
        st.download_button(
            "Download service report",
            service_csv,
            "trace_service_report.csv",
            "text/csv",
            use_container_width=True
        )

    with c3:
        st.download_button(
            "Download incident report",
            incident_csv,
            "trace_incident_candidates.csv",
            "text/csv",
            use_container_width=True
        )

    st.info(
        "Incident exports contain heuristic groupings. "
        "Review the original event records before drawing conclusions."
    )

# =========================================================
# FOOTER
# =========================================================
st.divider()

if skipped_lines:
    st.caption(
        f"TXT parser skipped {skipped_lines} unsupported line(s)."
    )

st.markdown(
    "<div class='mono'>TRACE LOG INTELLIGENCE ENGINE · "
    "DAY 09 OF 60 · BUILT WITH PYTHON</div>",
    unsafe_allow_html=True
)
