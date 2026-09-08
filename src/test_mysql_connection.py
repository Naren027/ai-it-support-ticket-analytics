from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os


# Load environment variables from .env
load_dotenv()


# Read database configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME")


# Check that required variables exist
required_variables = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_NAME": DB_NAME,
}

missing_variables = [
    name for name, value in required_variables.items()
    if not value
]

if missing_variables:
    raise ValueError(
        f"Missing environment variables: {', '.join(missing_variables)}"
    )


# Build MySQL connection URL safely
connection_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)


# Create SQLAlchemy engine
engine = create_engine(connection_url)


# Test the connection
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT VERSION();"))
        version = result.fetchone()[0]

        print("Successfully connected to MySQL!")
        print(f"MySQL version: {version}")
        print(f"Database: {DB_NAME}")

except Exception as e:
    print("MySQL connection failed.")
    print(f"Error: {e}")