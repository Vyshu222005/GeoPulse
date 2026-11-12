"""Test the connection to Snowflake using the values in the .env file."""
import os
import sys

import snowflake.connector
from dotenv import load_dotenv

REQUIRED = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
]


def main():
    load_dotenv()
    missing = [k for k in REQUIRED if not os.getenv(k) or os.getenv(k).startswith("your_")]
    if missing:
        print("Please fill these values in your .env file:", ", ".join(missing))
        return 1

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT CURRENT_VERSION(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), "
            "CURRENT_DATABASE(), CURRENT_SCHEMA()"
        )
        version, role, wh, db, schema = cur.fetchone()
        print("Connected to Snowflake")
        print(f"  version:   {version}")
        print(f"  role:      {role}")
        print(f"  warehouse: {wh}")
        print(f"  database:  {db}")
        print(f"  schema:    {schema}")

        cur.execute("SHOW SCHEMAS IN DATABASE GEOPULSE")
        names = sorted(row[1] for row in cur.fetchall())
        print("  schemas:  ", ", ".join(names))
        for needed in ("RAW", "STAGING", "MARTS"):
            if needed not in names:
                print(f"Missing schema {needed}. Run snowflake/01_setup.sql first.")
                return 1
    finally:
        conn.close()
    print("Setup OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
