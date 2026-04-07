from app.mbta_api import get_next_prediction
from app.storage import (
    build_record,
    append_to_csv,
    save_to_dynamodb,
    upload_outputs_to_s3,
)
from app.plotting import make_plot


def main():
    prediction = get_next_prediction()
    print("prediction:", prediction)

    record = build_record(prediction)
    print("record:", record)

    append_to_csv(record)
    print("saved record to CSV")

    save_to_dynamodb(record)
    print("saved record to DynamoDB")

    make_plot()
    print("updated plot")

    upload_outputs_to_s3()
    print("uploaded outputs to S3")


if __name__ == "__main__":
    main()
