# MBTA Red Line Delay Tracker

A containerized data pipeline that tracks prediction delay on the **MBTA Red Line at Kendall/MIT (southbound)** every 30 minutes. Built for DS 5220 Data Project 2.

## Data Source

This project uses the **MBTA V3 API**, the official REST API for the Massachusetts Bay Transportation Authority. The pipeline queries MBTA prediction and schedule data for the Red Line at **Kendall/MIT** (`70071`), **direction 0**, and computes the delay for the next upcoming train as:

`predicted_arrival - scheduled_arrival`

I chose this data source because it is:
- directly relevant to a real public transit system
- updated continuously during service hours
- easy to query in JSON format
- well-suited for an automated time-based pipeline

## Scheduled Process

A Kubernetes CronJob runs a containerized Python application every 30 minutes. On each run, the application:

1. Fetches upcoming MBTA prediction and schedule data
2. Selects the next relevant train at Kendall/MIT
3. Computes delay in minutes
4. Builds a structured record
5. Writes the record to DynamoDB
6. Appends the record to `data.csv`
7. Regenerates `plot.svg`
8. Uploads the updated outputs to S3

The pipeline runs on a **single-node K3s cluster** hosted on an AWS EC2 instance.

## Output Data and Plot

`data.csv` stores one row per pipeline run. Columns include:
- `timestamp`
- `route_id`
- `route_name`
- `stop_id`
- `stop_name`
- `direction_id`
- `scheduled_arrival`
- `predicted_arrival`
- `delay_minutes`
- `num_predictions`
- `status`

`plot.svg` is a time-series visualization of delay over time.

- Website URL: `http://mbta-kendall-tracker-2026.s3-website-us-east-1.amazonaws.com`
- Data URL: `https://mbta-kendall-tracker-2026.s3.amazonaws.com/data.csv`
- Plot URL: `https://mbta-kendall-tracker-2026.s3.amazonaws.com/plot.svg`

## Repository Structure

    .
    ├── README.md
    ├── Dockerfile
    ├── requirements.txt
    ├── .gitignore
    ├── index.html
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── mbta_api.py
    │   ├── storage.py
    │   ├── plotting.py
    │   └── utils.py
    ├── kubernetes/
    │   ├── configmap.yaml
    │   └── cronjob.yaml

## Canvas Quiz

### 1. Which data source you chose and why.

I chose the **MBTA V3 API** because it provides live prediction and schedule data for Boston transit in a format that is easy to query and automate. I wanted a data source with real operational variation over time, and MBTA arrival predictions are a good fit for a recurring pipeline because they update frequently and produce meaningful delay measurements. This project focuses on the **Red Line at Kendall/MIT**, which makes the dataset narrow, interpretable, and easy to visualize.

### 2. What you observe in the data — any patterns, spikes, or surprises over the 72-hour window.

Over the collection window, the main pattern is that delay is **not constant**. Most readings are positive, meaning the next train is arriving later than scheduled, but the size of the delay changes noticeably from run to run. The larger spikes tend to stand out more than the lower-delay periods, which suggests that service conditions can shift meaningfully even within a single day. A second pattern is that the dataset naturally reflects service timing: overnight gaps or lower-activity periods are expected because train service is not uniform across all hours. The most useful takeaway is that even a simple stop-level metric reveals real variation in transit reliability over time.

### 3. How Kubernetes Secrets differ from plain environment variables and why that distinction matters.

Plain environment variables are often written directly into a manifest or shell session in clear text. Kubernetes Secrets are a separate Kubernetes object designed for sensitive values such as API keys or credentials. In a manifest, the pod references the Secret by name, so the secret value itself does not need to be hardcoded into the CronJob definition. That matters because it reduces the chance of accidentally exposing sensitive values in source code, screenshots, or version control. It is not perfect security by itself, but it is better practice than placing secrets directly in ordinary environment variable declarations.

### 4. How your CronJob pods gain permission to read/write to AWS services without credentials appearing in any file.

In the current version of **my** project, the pod gets AWS access through values injected from a **Kubernetes Secret**, so the credentials are not baked into the Python code or Docker image. However, to be fully accurate, the credentials do still exist in my local `kubernetes/secret.yaml`, which is why that file is gitignored and never committed. If I were answering this as a production-grade design, the better solution would be to use an **IAM role attached to the compute environment** so the AWS SDK could obtain temporary credentials automatically and no long-lived credentials would appear in a file at all.

### 5. One thing you would do differently if you were building this pipeline for a real production system.

The biggest change I would make is to replace manually managed AWS credentials with **role-based authentication** and use a proper image registry plus CI/CD. Right now the pipeline works, but production infrastructure should avoid long-lived credentials, manual image transfer, and manual redeploy steps. A more production-ready version would build and publish the container automatically, deploy through a repeatable workflow, and use stronger monitoring so failures are caught immediately.

## Notes

A notable implementation choice in this project is that it uses:
- built-in `csv` instead of pandas
- a pure-Python SVG generator instead of matplotlib

This was done to avoid dependency issues encountered during local development while keeping the pipeline lightweight and stable.
