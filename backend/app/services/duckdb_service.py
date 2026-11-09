from pandas import DataFrame
import duckdb
from duckdb import DuckDBPyConnection
import re
import json
from fastapi import HTTPException
import sqlglot
from sqlglot import exp


def create_connection(df: DataFrame, table_name: str):

    connection = duckdb.connect(database=":memory:")
    connection.register("uploaded_data", df)

    if not table_name or not is_name_valid(table_name):
        raise ValueError("Invalid table name")

    connection.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM uploaded_data
        """)
    
    return connection

def is_name_valid(name: str):
    pattern = r'[a-zA-Z][a-zA-Z0-9_]*'
    return bool(re.fullmatch(pattern=pattern, string=name))


def get_table_schema(connection: DuckDBPyConnection, table_name: str):

    if not table_name or not is_name_valid(table_name):
        raise ValueError("Invalid table name")

    described = connection.execute(f"DESCRIBE {table_name}").fetchall()

    schema: list[dict] = []

    for table in described:
        schema.append({
            "column_name": table[0],
            "data_type": table[1]
        })

    return schema

def format_schema_for_llm(schema: list[dict], table_name: str) -> str:
    lines = []

    for column in schema:
        column_name = column["column_name"]
        data_type = column["data_type"]

        lines.append(f"- {column_name} ({data_type})")

    formatted_schema = (
        f"Table: {table_name}\n\n"
        "Columns:\n"
        + "\n".join(lines)
    )

    return formatted_schema

def get_sample_rows(connection: DuckDBPyConnection, table_name: str):

    if not table_name or not is_name_valid(table_name):
        raise ValueError("Invalid table name")
    
    result = connection.execute(
        query=f"SELECT * FROM {table_name} LIMIT 3"
    ).fetchdf().to_dict(orient="records")

    return result

def build_table_context(connection: DuckDBPyConnection, table_name: str):

    if not table_name or not is_name_valid(table_name):
        raise ValueError("Invalid table name")

    schema = get_table_schema(connection, table_name)
    sample_row = get_sample_rows(connection, table_name)

    formatted_schema = format_schema_for_llm(schema, table_name)
    formatted_rows = json.dumps(sample_row, indent=2)

    context = (
        f"Table information:\n\n"
        f"{formatted_schema}\n\n"
        f"Sample rows:\n{formatted_rows}"
    )

    return context

def validate_sql(sql: str) -> bool:

    if not sql or not sql.strip():
        raise HTTPException(
            status_code=400,
            detail="SQL command is empty"
        )

    try:
        parsed = sqlglot.parse(sql, read="duckdb")

        if len(parsed) != 1 or parsed[0] is None:
            raise HTTPException(
                status_code=400,
                detail="Only one SQL statement is allowed"
            )

        if not isinstance(parsed[0], exp.Select):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries are allowed"
            )

        return True

    except sqlglot.errors.ParseError:
        raise HTTPException(
            status_code=400,
            detail="Invalid SQL syntax"
        )





    

    

    



