import os
import csv
import boto3

from botocore.exceptions import ClientError

from app.config import (
    ROUTE_ID,
    STOP_ID,
    DIRECTION_ID,
    STOP_NAME,
    ROUTE_NAME,
    CSV_FILE,
    PLOT_FILE,
    OUTPUT_DIR,
    AWS_REGION,
    DYNAMODB_TABLE,
    S3_BUCKET,
)
from app.utils import utc_now_iso, classify_status


FIELDNAMES = [
    "route_id",
    "route_name",
    "stop_id",
    "stop_name",
    "direction_id",
    "timestamp",
    "scheduled_arrival",
    "predicted_arrival",
    "delay_minutes",
    "num_predictions",
    "status",
]


def build_record(prediction_data: dict) -> dict:
    delay_minutes = prediction_data.get("delay_minutes")

    return {
        "route_id": ROUTE_ID,
        "route_name": ROUTE_NAME,
        "stop_id": STOP_ID,
        "stop_name": STOP_NAME,
        "direction_id": DIRECTION_ID,
        "timestamp": utc_now_iso(),
        "scheduled_arrival": prediction_data.get("scheduled_arrival"),
        "predicted_arrival": prediction_data.get("predicted_arrival"),
        "delay_minutes": delay_minutes,
        "num_predictions": prediction_data.get("num_predictions", 0),
        "status": classify_status(delay_minutes),
    }


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def append_to_csv(record: dict, csv_path: str = CSV_FILE):
    ensure_output_dir()

    file_exists = os.path.exists(csv_path)
    file_has_data = file_exists and os.path.getsize(csv_path) > 0

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_has_data:
            writer.writeheader()
        writer.writerow(record)


def read_csv_data(csv_path: str = CSV_FILE):
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(DYNAMODB_TABLE)


def save_to_dynamodb(record: dict):
    table = get_dynamodb_table()

    item = dict(record)
    if item.get("delay_minutes") is not None:
        item["delay_minutes"] = str(item["delay_minutes"])

    table.put_item(Item=item)


def get_s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def download_csv_from_s3_if_exists(local_path: str = CSV_FILE, s3_key: str = "data.csv"):
    ensure_output_dir()
    s3 = get_s3_client()

    try:
        s3.download_file(S3_BUCKET, s3_key, local_path)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchKey"):
            return
        raise


def upload_file_to_s3(local_path: str, s3_key: str, content_type: str):
    s3 = get_s3_client()
    s3.upload_file(
        local_path,
        S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": content_type},
    )


def upload_outputs_to_s3():
    if os.path.exists(CSV_FILE):
        upload_file_to_s3(CSV_FILE, "data.csv", "text/csv")

    if os.path.exists(PLOT_FILE):
        upload_file_to_s3(PLOT_FILE, "plot.svg", "image/svg+xml")
