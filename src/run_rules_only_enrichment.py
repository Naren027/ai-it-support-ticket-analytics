import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

from rule_classifier import classify_ticket_rules_only


# ============================================================
# RULES-ONLY TICKET ENRICHMENT PIPELINE
# ============================================================
#
# Purpose:
#   Enrich the complete cleaned ticket dataset using ONLY the
#   deterministic rule classifier.
#
# IMPORTANT:
#   - No Ollama
#   - No LLM
#   - No ai_classifier import
#   - No modification to the existing hybrid AI pipeline
#
# This script is intentionally separate from:
#
#   run_ai_enrichment.py
#   ai_classifier.py
#
# The existing AI/hybrid pipeline remains untouched.
#
# ============================================================


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_tickets.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rules_only_enriched_tickets.csv"
)

LOG_DIR = PROJECT_ROOT / "logs"

LOG_FILE = (
    LOG_DIR
    / "rules_only_enrichment.log"
)


# ============================================================
# PIPELINE CONFIGURATION
# ============================================================

PROGRESS_UPDATE_EVERY = 2000


# ============================================================
# LOGGING
# ============================================================

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
    handlers=[
        logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# RESULT COLUMNS
# ============================================================

RESULT_FIELDS = [
    "priority",
    "urgency_score",
    "urgency_reason",
    "work_blocked",
    "deadline_present",
    "explicit_urgency",
    "service_unavailable",
    "security_issue",
    "multiple_users",
    "business_critical",
    "limited_functionality"
]


CLASSIFICATION_COLUMNS = RESULT_FIELDS + [
    "classification_status",
    "classified_at",
    "classification_method"
]


# ============================================================
# LOAD INPUT DATA
# ============================================================

def load_input_data():

    logger.info(
        "Loading cleaned dataset: %s",
        INPUT_FILE
    )

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input dataset not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [
        "ticket_id",
        "document",
        "topic_group"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    logger.info(
        "Rows loaded: %s",
        f"{len(df):,}"
    )

    return df


# ============================================================
# PROCESS TICKETS
# ============================================================

def process_tickets(df):

    total_tickets = len(df)

    # --------------------------------------------------------
    # Create classification columns if they don't exist.
    # --------------------------------------------------------

    for column in CLASSIFICATION_COLUMNS:

        if column not in df.columns:

            df[column] = None

    successful = 0
    failed = 0

    run_start = datetime.now()

    # --------------------------------------------------------
    # Process every ticket.
    # --------------------------------------------------------

    for index in df.index:

        row = df.loc[index]

        ticket_id = row["ticket_id"]

        document = str(
            row["document"]
        ).strip()

        # ----------------------------------------------------
        # Empty ticket protection
        # ----------------------------------------------------

        if not document:

            df.at[
                index,
                "classification_status"
            ] = "FAILED_EMPTY_TEXT"

            df.at[
                index,
                "classification_method"
            ] = "rule_only"

            df.at[
                index,
                "classified_at"
            ] = datetime.now().isoformat(
                timespec="seconds"
            )

            failed += 1

            continue

        # ----------------------------------------------------
        # Rule-based classification
        # ----------------------------------------------------

        try:

            result = classify_ticket_rules_only(
                document
            )

            # ------------------------------------------------
            # Store classification result
            # ------------------------------------------------

            for column in RESULT_FIELDS:

                df.at[
                    index,
                    column
                ] = result[column]

            # ------------------------------------------------
            # Processing metadata
            # ------------------------------------------------

            df.at[
                index,
                "classification_status"
            ] = "SUCCESS"

            df.at[
                index,
                "classified_at"
            ] = datetime.now().isoformat(
                timespec="seconds"
            )

            df.at[
                index,
                "classification_method"
            ] = "rule_only"

            successful += 1

        except Exception as error:

            failed += 1

            df.at[
                index,
                "classification_status"
            ] = "FAILED"

            df.at[
                index,
                "classified_at"
            ] = datetime.now().isoformat(
                timespec="seconds"
            )

            df.at[
                index,
                "classification_method"
            ] = "rule_only"

            logger.error(
                "Ticket %s failed: %s",
                ticket_id,
                error
            )

        # ----------------------------------------------------
        # Progress logging
        # ----------------------------------------------------

        processed_so_far = (
            successful + failed
        )

        if (
            processed_so_far
            % PROGRESS_UPDATE_EVERY
            == 0
        ):

            percentage = (
                processed_so_far
                / total_tickets
            ) * 100

            logger.info(
                "Progress: %s/%s (%.1f%%)",
                f"{processed_so_far:,}",
                f"{total_tickets:,}",
                percentage
            )

    # ========================================================
    # SAVE FINAL DATASET
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        "Output saved successfully: %s",
        OUTPUT_FILE
    )

    run_end = datetime.now()

    duration = (
        run_end - run_start
    )

    return {
        "total_tickets": total_tickets,
        "successful": successful,
        "failed": failed,
        "run_start": run_start,
        "run_end": run_end,
        "duration": duration,
        "dataframe": df
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_output(df, summary):

    print("\n")
    print("=" * 70)
    print("FINAL OUTPUT VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    print(
        f"Input rows              : "
        f"{summary['total_tickets']:,}"
    )

    print(
        f"Output rows             : "
        f"{len(df):,}"
    )

    if (
        len(df)
        == summary["total_tickets"]
    ):

        print(
            "✓ Row count validation passed"
        )

    else:

        print(
            "✗ Row count validation FAILED"
        )

    # --------------------------------------------------------
    # Required output columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in CLASSIFICATION_COLUMNS
        if column not in df.columns
    ]

    if not missing_columns:

        print(
            "✓ Classification columns present"
        )

    else:

        print(
            "✗ Missing classification columns:"
        )

        for column in missing_columns:

            print(
                f"  - {column}"
            )

    # --------------------------------------------------------
    # Classification status
    # --------------------------------------------------------

    if "classification_status" in df.columns:

        print(
            "\nClassification status:"
        )

        print(
            df["classification_status"]
            .value_counts(dropna=False)
            .to_string()
        )

    # --------------------------------------------------------
    # Classification method
    # --------------------------------------------------------

    if "classification_method" in df.columns:

        print(
            "\nClassification method:"
        )

        print(
            df["classification_method"]
            .value_counts(dropna=False)
            .to_string()
        )

    # --------------------------------------------------------
    # Priority distribution
    # --------------------------------------------------------

    if "priority" in df.columns:

        print(
            "\nPriority distribution:"
        )

        priority_counts = (
            df["priority"]
            .value_counts(dropna=False)
        )

        for priority, count in priority_counts.items():

            percentage = (
                count
                / len(df)
            ) * 100

            print(
                f"  {str(priority):10s} : "
                f"{count:6,} "
                f"({percentage:5.2f}%)"
            )

    # --------------------------------------------------------
    # Urgency statistics
    # --------------------------------------------------------

    if "urgency_score" in df.columns:

        urgency = pd.to_numeric(
            df["urgency_score"],
            errors="coerce"
        )

        print(
            "\nUrgency score:"
        )

        print(
            f"  Minimum : "
            f"{urgency.min():.2f}"
        )

        print(
            f"  Maximum : "
            f"{urgency.max():.2f}"
        )

        print(
            f"  Mean    : "
            f"{urgency.mean():.2f}"
        )

        print(
            f"  Median  : "
            f"{urgency.median():.2f}"
        )

    # --------------------------------------------------------
    # Critical tickets
    # --------------------------------------------------------

    if "priority" in df.columns:

        critical_count = (
            df["priority"]
            .astype(str)
            .str.lower()
            .eq("critical")
            .sum()
        )

        print(
            "\nCritical tickets:"
        )

        print(
            f"  {critical_count:,}"
        )

    # --------------------------------------------------------
    # Security tickets
    # --------------------------------------------------------

    if "security_issue" in df.columns:

        security_count = (
            df["security_issue"]
            .fillna(False)
            .astype(str)
            .str.lower()
            .isin(["true", "1"])
            .sum()
        )

        print(
            "\nSecurity-related tickets:"
        )

        print(
            f"  {security_count:,}"
        )

    # --------------------------------------------------------
    # Failed tickets
    # --------------------------------------------------------

    print(
        "\nProcessing failures:"
    )

    print(
        f"  {summary['failed']:,}"
    )

    print("=" * 70)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(summary):

    print("\n")
    print("=" * 70)
    print(
        "RULES-ONLY ENRICHMENT PIPELINE COMPLETED"
    )
    print("=" * 70)

    print(
        f"Total tickets          : "
        f"{summary['total_tickets']:,}"
    )

    print(
        f"Successful             : "
        f"{summary['successful']:,}"
    )

    print(
        f"Failed                 : "
        f"{summary['failed']:,}"
    )

    print(
        f"Run started            : "
        f"{summary['run_start']}"
    )

    print(
        f"Run finished           : "
        f"{summary['run_end']}"
    )

    print(
        f"Duration               : "
        f"{summary['duration']}"
    )

    print(
        "\nOutput file:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nLog file:"
    )

    print(
        LOG_FILE
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "AI IT SUPPORT TICKET - "
        "RULES-ONLY ENRICHMENT PIPELINE"
    )
    print("=" * 70)

    print(
        "\nIMPORTANT:"
    )

    print(
        "This pipeline does NOT use Ollama or an LLM."
    )

    print(
        "Every ticket is classified using deterministic rules only."
    )

    print(
        "\nInput:"
    )

    print(
        INPUT_FILE
    )

    print(
        "\nOutput:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nStarting processing..."
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_input_data()

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    summary = process_tickets(
        df
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_output(
        summary["dataframe"],
        summary
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print_summary(
        summary
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()