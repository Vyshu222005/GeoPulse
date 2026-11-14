"""Run a SQL file on Snowflake and print the results.

Usage:  python snowflake/run_sql.py snowflake/02_create_tables.sql
Uses the login values from the .env file.
"""
import os
import sys

import snowflake.connector
from dotenv import load_dotenv


def main():
    if len(sys.argv) != 2:
        print("Usage: python snowflake/run_sql.py <file.sql>")
        return 1

    with open(sys.argv[1], encoding="utf-8") as f:
        sql = f.read()

    load_dotenv()
    missing = [k for k in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD")
               if not os.getenv(k) or os.getenv(k).startswith("your_")]
    if missing:
        print("Missing Snowflake login:", ", ".join(missing))
        print("Copy .env.example to .env and fill in your account, user and password.")
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
        # execute_string runs every statement in the file, one after another
        for cur in conn.execute_string(sql):
            rows = cur.fetchall()
            if rows:
                cols = [c[0] for c in cur.description]
                print(" | ".join(cols))
                for row in rows:
                    print(" | ".join(str(v) for v in row))
                print()
    finally:
        conn.close()
    print("Finished", sys.argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
