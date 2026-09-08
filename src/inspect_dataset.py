import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "all_tickets_processed_improved_v3.csv"
)


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("IT SUPPORT TICKET DATASET - INITIAL DATA PROFILE")
print("=" * 70)

print(f"\nLoading file:")
print(RAW_DATA_PATH)

try:
    df = pd.read_csv(RAW_DATA_PATH)

except FileNotFoundError:
    print("\nERROR: Dataset file was not found.")
    print("Make sure the CSV exists at:")
    print(RAW_DATA_PATH)
    raise

except Exception as e:
    print("\nERROR: Could not read the CSV file.")
    print(f"Error: {e}")
    raise


# ============================================================
# BASIC DATASET INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("1. DATASET SIZE")
print("=" * 70)

print(f"Rows    : {df.shape[0]:,}")
print(f"Columns : {df.shape[1]:,}")


# ============================================================
# COLUMN INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("2. COLUMN INFORMATION")
print("=" * 70)

for column in df.columns:
    print(f"- {column} | Data type: {df[column].dtype}")


# ============================================================
# FIRST 5 RECORDS
# ============================================================

print("\n" + "=" * 70)
print("3. FIRST 5 RECORDS")
print("=" * 70)

print(df.head().to_string())


# ============================================================
# MISSING VALUES
# ============================================================

print("\n" + "=" * 70)
print("4. MISSING VALUES")
print("=" * 70)

missing_values = df.isnull().sum()

for column, count in missing_values.items():
    percentage = (count / len(df)) * 100
    print(f"{column}: {count:,} ({percentage:.2f}%)")


# ============================================================
# DUPLICATE RECORDS
# ============================================================

print("\n" + "=" * 70)
print("5. DUPLICATE RECORDS")
print("=" * 70)

duplicate_count = df.duplicated().sum()

print(f"Duplicate rows: {duplicate_count:,}")


# ============================================================
# UNIQUE VALUES
# ============================================================

print("\n" + "=" * 70)
print("6. UNIQUE VALUES PER COLUMN")
print("=" * 70)

for column in df.columns:
    print(f"{column}: {df[column].nunique(dropna=True):,} unique values")


# ============================================================
# TOPIC GROUP ANALYSIS
# ============================================================

if "Topic_group" in df.columns:

    print("\n" + "=" * 70)
    print("7. TOPIC GROUP DISTRIBUTION")
    print("=" * 70)

    category_counts = df["Topic_group"].value_counts(dropna=False)

    for category, count in category_counts.items():
        percentage = (count / len(df)) * 100
        print(f"{str(category):30} {count:8,} ({percentage:6.2f}%)")

else:
    print("\nWARNING: 'Topic_group' column was not found.")


# ============================================================
# DOCUMENT / TICKET TEXT ANALYSIS
# ============================================================

if "Document" in df.columns:

    print("\n" + "=" * 70)
    print("8. DOCUMENT / TICKET TEXT ANALYSIS")
    print("=" * 70)

    document_series = df["Document"].fillna("").astype(str)

    text_lengths = document_series.str.len()

    print(f"Empty documents      : {(document_series.str.strip() == '').sum():,}")
    print(f"Minimum text length  : {text_lengths.min():,}")
    print(f"Maximum text length  : {text_lengths.max():,}")
    print(f"Average text length  : {text_lengths.mean():.2f}")
    print(f"Median text length   : {text_lengths.median():.2f}")

else:
    print("\nWARNING: 'Document' column was not found.")


# ============================================================
# DATA TYPES SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("9. DATA TYPES")
print("=" * 70)

print(df.dtypes)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("DATASET INSPECTION COMPLETE")
print("=" * 70)