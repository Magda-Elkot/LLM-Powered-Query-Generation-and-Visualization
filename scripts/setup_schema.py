import os
import argparse
from src import SchemaManager

# -------------------------
# Command-line arguments
# -------------------------
parser = argparse.ArgumentParser(description="Setup schema: Excel → JSON → PostgreSQL")
parser.add_argument(
    "--excel", 
    default="data/raw/Telecom_Filled_Data_Model.xlsx", 
    help="Path to the Excel file containing the schema/data"
)
args = parser.parse_args()

# -------------------------
# Check if Excel file exists
# -------------------------
if not os.path.exists(args.excel):
    raise FileNotFoundError(f"Excel file not found: {args.excel}")

# -------------------------
# Check if JSON metadata exists
# -------------------------
json_path = "config/schema_metadata.json"
if os.path.exists(json_path):
    print(f"⚠ Schema metadata already exists at {json_path}. Running will overwrite it.")

# -------------------------
# Run SchemaManager
# -------------------------
try:
    sm = SchemaManager(args.excel)
    sm.build()  # Excel → JSON → PostgreSQL tables
    print("Schema setup complete!")
except Exception as e:
    print("Error during schema setup:", e)
