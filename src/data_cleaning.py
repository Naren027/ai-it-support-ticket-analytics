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

PROCESSED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_tickets.csv"
)


# ============================================================
# EXPECTED DATASET STRUCTURE
# ============================================================

REQUIRED_COLUMNS = [
    "Document",
    "Topic_group"
]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    print("=" * 70)
    print("STEP 1 - LOADING RAW DATA")
    print("=" * 70)

    print(f"Source file: {RAW_DATA_PATH}")

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Raw dataset not found:\n{RAW_DATA_PATH}"
        )

    df = pd.read_csv(RAW_DATA_PATH)

    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    return df


# ============================================================
# VALIDATE STRUCTURE
# ============================================================

def validate_columns(df):
    print("\n" + "=" * 70)
    print("STEP 2 - VALIDATING DATASET STRUCTURE")
    print("=" * 70)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns are missing: {missing_columns}"
        )

    print("Required columns found:")
    for column in REQUIRED_COLUMNS:
        print(f"  ✓ {column}")


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean_column_names(df):
    print("\n" + "=" * 70)
    print("STEP 3 - STANDARDIZING COLUMN NAMES")
    print("=" * 70)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # Rename columns to our project naming convention
    df = df.rename(
        columns={
            "document": "document",
            "topic_group": "topic_group"
        }
    )

    print("Final columns:")
    for column in df.columns:
        print(f"  ✓ {column}")

    return df


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

def handle_missing_values(df):
    print("\n" + "=" * 70)
    print("STEP 4 - CHECKING MISSING VALUES")
    print("=" * 70)

    document_missing = df["document"].isna().sum()
    category_missing = df["topic_group"].isna().sum()

    print(f"Missing documents : {document_missing:,}")
    print(f"Missing categories: {category_missing:,}")

    # Remove records where the ticket text is missing
    if document_missing > 0:
        df = df.dropna(subset=["document"])

    # Remove records where the category is missing
    if category_missing > 0:
        df = df.dropna(subset=["topic_group"])

    print(f"Rows after missing-value handling: {len(df):,}")

    return df


# ============================================================
# CLEAN TICKET TEXT
# ============================================================

def clean_ticket_text(df):
    print("\n" + "=" * 70)
    print("STEP 5 - CLEANING TICKET TEXT")
    print("=" * 70)

    # Convert to string
    df["document"] = df["document"].astype(str)

    # Remove leading/trailing whitespace
    df["document"] = df["document"].str.strip()

    # Replace multiple whitespace characters with a single space
    df["document"] = (
        df["document"]
        .str.replace(r"\s+", " ", regex=True)
    )

    # Remove completely empty documents
    before = len(df)

    df = df[
        df["document"].str.strip() != ""
    ].copy()

    removed = before - len(df)

    print(f"Empty documents removed: {removed:,}")

    return df


# ============================================================
# STANDARDIZE CATEGORY VALUES
# ============================================================

def standardize_categories(df):
    print("\n" + "=" * 70)
    print("STEP 6 - STANDARDIZING CATEGORIES")
    print("=" * 70)

    # Remove unnecessary whitespace
    df["topic_group"] = (
        df["topic_group"]
        .astype(str)
        .str.strip()
    )

    print("Categories found:")

    for category in sorted(df["topic_group"].unique()):
        print(f"  ✓ {category}")

    return df


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):
    print("\n" + "=" * 70)
    print("STEP 7 - CHECKING DUPLICATES")
    print("=" * 70)

    duplicate_count = df.duplicated(
        subset=["document", "topic_group"]
    ).sum()

    print(f"Duplicate records found: {duplicate_count:,}")

    if duplicate_count > 0:
        df = df.drop_duplicates(
            subset=["document", "topic_group"]
        ).copy()

    print(f"Rows after duplicate handling: {len(df):,}")

    return df


# ============================================================
# CREATE TICKET ID
# ============================================================

def create_ticket_id(df):
    print("\n" + "=" * 70)
    print("STEP 8 - CREATING TICKET ID")
    print("=" * 70)

    # Generate a stable sequential ID for the cleaned dataset
    df.insert(
        0,
        "ticket_id",
        range(1, len(df) + 1)
    )

    print("Ticket IDs created.")
    print(f"ID range: {df['ticket_id'].min()} - {df['ticket_id'].max()}")

    return df


# ============================================================
# FINAL VALIDATION
# ============================================================

def final_validation(df):
    print("\n" + "=" * 70)
    print("STEP 9 - FINAL DATA VALIDATION")
    print("=" * 70)

    print(f"Final rows    : {len(df):,}")
    print(f"Final columns : {len(df.columns)}")

    print("\nMissing values:")

    missing = df.isna().sum()

    for column, count in missing.items():
        print(f"  {column}: {count:,}")

    print("\nDuplicate records:")

    duplicates = df.duplicated().sum()

    print(f"  {duplicates:,}")

    print("\nCategory distribution:")

    category_counts = df["topic_group"].value_counts()

    for category, count in category_counts.items():
        percentage = (count / len(df)) * 100

        print(
            f"  {category}: "
            f"{count:,} ({percentage:.2f}%)"
        )

    # Final quality checks
    if df["document"].isna().any():
        raise ValueError("Validation failed: missing documents found.")

    if df["topic_group"].isna().any():
        raise ValueError("Validation failed: missing categories found.")

    if df["document"].str.strip().eq("").any():
        raise ValueError("Validation failed: empty documents found.")

    if df.duplicated().any():
        raise ValueError("Validation failed: duplicate rows found.")

    print("\n✓ All validation checks passed.")


# ============================================================
# SAVE CLEANED DATA
# ============================================================

def save_data(df):
    print("\n" + "=" * 70)
    print("STEP 10 - SAVING CLEANED DATA")
    print("=" * 70)

    PROCESSED_DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        PROCESSED_DATA_PATH,
        index=False
    )

    print(f"Cleaned dataset saved to:")
    print(PROCESSED_DATA_PATH)

    print(f"\nRows saved: {len(df):,}")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("IT SUPPORT TICKET - DATA CLEANING PIPELINE")
    print("=" * 70)

    # 1. Load
    df = load_data()

    # 2. Validate source structure
    validate_columns(df)

    # 3. Standardize column names
    df = clean_column_names(df)

    # 4. Handle missing values
    df = handle_missing_values(df)

    # 5. Clean ticket text
    df = clean_ticket_text(df)

    # 6. Standardize categories
    df = standardize_categories(df)

    # 7. Remove duplicates
    df = remove_duplicates(df)

    # 8. Create ticket ID
    df = create_ticket_id(df)

    # 9. Final validation
    final_validation(df)

    # 10. Save
    save_data(df)

    print("\n" + "=" * 70)
    print("DATA CLEANING PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\n")


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()