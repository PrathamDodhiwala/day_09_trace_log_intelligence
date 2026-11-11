
# TRACE — Log Intelligence & Incident Monitor

Day 9 of the 60-Day End-of-Year Project Marathon.

TRACE is a Python-based log analytics and system observability
application. It transforms application logs into searchable event
streams, service health summaries, error trends and potential
incident candidates.

## Features

- Built-in synthetic application logs.
- CSV log upload.
- Plain-text log upload with supported format.
- Severity and service filtering.
- Date and time filtering.
- Searchable event stream.
- Event volume visualisation.
- Severity distribution.
- Error spike screening.
- Incident grouping by service and five-minute interval.
- Service-level error analysis.
- Frequent source IP analysis.
- CSV export for logs, services and incident candidates.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly

## CSV Input Format

Required columns:

| timestamp | level | service | message |
|---|---|---|---|
| 2026-11-09 12:30:00 | ERROR | payment-api | Database timeout |
| 2026-11-09 12:31:00 | INFO | auth-service | Session created |

Optional columns:

- source_ip
- event_id

## TXT Input Format

Each line should follow this structure:

    2026-11-09 12:30:00 ERROR payment-api 10.0.0.4 Database timeout

The source IP is optional:

    2026-11-09 12:31:00 INFO auth-service User session created

Supported levels:

DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL, FATAL

## Installation — Windows / PowerShell

Open the project folder in VS Code.

Create a virtual environment:

    py -3.10 -m venv .venv

Activate it:

    .\.venv\Scripts\Activate.ps1

If PowerShell blocks activation:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install --upgrade pip --timeout 600 --retries 10

    python -m pip install -r requirements.txt --no-cache-dir --timeout 600 --retries 10

Run the application:

    streamlit run app.py

## Getting Started

1. Launch TRACE.
2. Select Synthetic demo.
3. Explore the Command Center.
4. Investigate individual events in Event Stream.
5. Review correlated incident candidates.
6. Compare service-level error patterns.
7. Export the analysis.

## Analytical Methods

- Time-based event aggregation.
- Severity classification.
- Median absolute deviation based error-spike screening.
- Service and time-window incident grouping.
- Error-rate comparison.
- Source-IP frequency analysis.

## Important Limitations

TRACE uses rule-based log analysis and statistical heuristics.
It does not use a trained AI model, prove malicious activity,
or establish the root cause of an incident.

Incident candidates require manual investigation.
Source IP frequency alone is not evidence of an attack.
