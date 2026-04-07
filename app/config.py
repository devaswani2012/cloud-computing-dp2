import os
from dotenv import load_dotenv

load_dotenv()

# MBTA API settings
MBTA_API_KEY = os.getenv("MBTA_API_KEY", "")
MBTA_BASE_URL = "https://api-v3.mbta.com"

# Project-specific transit settings
ROUTE_ID = "Red"
STOP_ID = "70071"          # Kendall/MIT southbound
DIRECTION_ID = 0           # southbound toward Ashmont/Braintree
STOP_NAME = "Kendall/MIT"
ROUTE_NAME = "Red Line"

# AWS settings
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "mbta_kendall_redline")
S3_BUCKET = os.getenv("S3_BUCKET", "your-s3-bucket-name")

# Output files
OUTPUT_DIR = "output"
CSV_FILE = f"{OUTPUT_DIR}/data.csv"
PLOT_FILE = f"{OUTPUT_DIR}/plot.svg"

# Collection settings
TIMEOUT = 30
STATUS_ON_TIME_THRESHOLD = 2
