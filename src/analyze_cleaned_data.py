import pandas as pd
from pathlib import Path
import re


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEANED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_tickets.csv"
)


# ============================================================
# LOAD CLEANED DATA
# ============================================================

print("=" * 70)
print("IT SUPPORT TICKET - AI READINESS ANALYSIS")
print("=" * 70)

print("\nLoading cleaned dataset:")
print(CLEANED_DATA_PATH)

if not CLEANED_DATA_PATH.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found:\n{CLEANED_DATA_PATH}"
    )

df = pd.read_csv(CLEANED_DATA_PATH)

print(f"\nRows loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns)}")


# ============================================================
# BASIC VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("1. BASIC VALIDATION")
print("=" * 70)

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
        f"Missing required columns: {missing_columns}"
    )

print("Required columns:")
for column in required_columns:
    print(f"  ✓ {column}")


# ============================================================
# TEXT LENGTH ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("2. TEXT LENGTH ANALYSIS")
print("=" * 70)

df["document"] = df["document"].fillna("").astype(str)

df["character_count"] = df["document"].str.len()

df["word_count"] = (
    df["document"]
    .str.split()
    .str.len()
)

print("\nCharacter count:")
print(f"  Minimum : {df['character_count'].min():,}")
print(f"  Maximum : {df['character_count'].max():,}")
print(f"  Mean    : {df['character_count'].mean():.2f}")
print(f"  Median  : {df['character_count'].median():.2f}")

print("\nWord count:")
print(f"  Minimum : {df['word_count'].min():,}")
print(f"  Maximum : {df['word_count'].max():,}")
print(f"  Mean    : {df['word_count'].mean():.2f}")
print(f"  Median  : {df['word_count'].median():.2f}")


# ============================================================
# SHORT TICKET ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("3. SHORT TICKET ANALYSIS")
print("=" * 70)

thresholds = [10, 20, 50, 100]

for threshold in thresholds:

    count = (
        df["character_count"] < threshold
    ).sum()

    percentage = (
        count / len(df)
    ) * 100

    print(
        f"Tickets under {threshold:3} characters: "
        f"{count:6,} ({percentage:6.2f}%)"
    )


# ============================================================
# LONG TICKET ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("4. LONG TICKET ANALYSIS")
print("=" * 70)

thresholds = [500, 1000, 2000, 5000]

for threshold in thresholds:

    count = (
        df["character_count"] > threshold
    ).sum()

    percentage = (
        count / len(df)
    ) * 100

    print(
        f"Tickets over {threshold:4} characters: "
        f"{count:6,} ({percentage:6.2f}%)"
    )


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("5. CATEGORY ANALYSIS")
print("=" * 70)

category_summary = (
    df.groupby("topic_group")
    .agg(
        ticket_count=("ticket_id", "count"),
        avg_characters=("character_count", "mean"),
        median_characters=("character_count", "median"),
        avg_words=("word_count", "mean"),
        median_words=("word_count", "median")
    )
    .sort_values(
        "ticket_count",
        ascending=False
    )
)

print(
    category_summary.to_string(
        float_format=lambda x: f"{x:.2f}"
    )
)


# ============================================================
# CATEGORY TEXT LENGTH EXTREMES
# ============================================================

print("\n" + "=" * 70)
print("6. CATEGORY TEXT LENGTH EXTREMES")
print("=" * 70)

for category in sorted(df["topic_group"].unique()):

    category_data = df[
        df["topic_group"] == category
    ]

    print(f"\n{category}")

    print(
        f"  Tickets : {len(category_data):,}"
    )

    print(
        f"  Avg chars : "
        f"{category_data['character_count'].mean():.2f}"
    )

    print(
        f"  Max chars : "
        f"{category_data['character_count'].max():,}"
    )


# ============================================================
# REPETITION ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("7. REPETITION / TEXT QUALITY ANALYSIS")
print("=" * 70)

# Count repeated consecutive words such as:
# "icon icon"
# "user user"
# "please please"

def count_repeated_words(text):

    words = text.lower().split()

    if len(words) < 2:
        return 0

    repeated = 0

    for i in range(1, len(words)):

        if words[i] == words[i - 1]:
            repeated += 1

    return repeated


df["repeated_word_count"] = (
    df["document"]
    .apply(count_repeated_words)
)

repeated_ticket_count = (
    df["repeated_word_count"] > 0
).sum()

repeated_ticket_percentage = (
    repeated_ticket_count / len(df)
) * 100

print(
    f"Tickets containing consecutive repeated words: "
    f"{repeated_ticket_count:,} "
    f"({repeated_ticket_percentage:.2f}%)"
)


# ============================================================
# TOP REPEATED WORD PATTERNS
# ============================================================

print("\n" + "=" * 70)
print("8. COMMON CONSECUTIVE WORD REPETITIONS")
print("=" * 70)

repeated_patterns = {}

for text in df["document"]:

    words = text.lower().split()

    for i in range(1, len(words)):

        if words[i] == words[i - 1]:

            word = words[i]

            repeated_patterns[word] = (
                repeated_patterns.get(word, 0) + 1
            )

if repeated_patterns:

    sorted_patterns = sorted(
        repeated_patterns.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for word, count in sorted_patterns[:20]:

        print(
            f"  '{word} {word}' : {count:,}"
        )

else:

    print("No consecutive repeated-word patterns found.")


# ============================================================
# SAMPLE TICKETS
# ============================================================

print("\n" + "=" * 70)
print("9. SAMPLE TICKETS FOR AI REVIEW")
print("=" * 70)

sample_size = min(10, len(df))

sample = df.sample(
    n=sample_size,
    random_state=42
)

for _, row in sample.iterrows():

    print("\n" + "-" * 70)

    print(
        f"Ticket ID : {row['ticket_id']}"
    )

    print(
        f"Category  : {row['topic_group']}"
    )

    print(
        f"Characters: {row['character_count']}"
    )

    print(
        f"Words     : {row['word_count']}"
    )

    print(
        f"Document  : {row['document'][:500]}"
    )


# ============================================================
# AI TOKEN / BATCH PLANNING
# ============================================================

print("\n" + "=" * 70)
print("10. AI PROCESSING PLANNING")
print("=" * 70)

# Rough token estimate.
# English text is often approximately 1 token per
# 3-5 characters. We use 4 characters/token only
# as a rough planning estimate.

estimated_tokens = (
    df["character_count"].sum() / 4
)

print(
    f"Total characters: "
    f"{df['character_count'].sum():,}"
)

print(
    f"Estimated input tokens: "
    f"{estimated_tokens:,.0f}"
)

print(
    "\nNOTE:"
)

print(
    "The token estimate is approximate and will depend "
    "on the model/tokenizer we eventually choose."
)


# ============================================================
# DATASET SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("11. FINAL AI READINESS SUMMARY")
print("=" * 70)

print(
    f"Total tickets           : {len(df):,}"
)

print(
    f"Unique categories       : "
    f"{df['topic_group'].nunique():,}"
)

print(
    f"Average ticket length   : "
    f"{df['character_count'].mean():.2f} characters"
)

print(
    f"Median ticket length    : "
    f"{df['character_count'].median():.2f} characters"
)

print(
    f"Tickets with repetition : "
    f"{repeated_ticket_count:,}"
)

print(
    f"Estimated input tokens  : "
    f"{estimated_tokens:,.0f}"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("AI READINESS ANALYSIS COMPLETE")
print("=" * 70)