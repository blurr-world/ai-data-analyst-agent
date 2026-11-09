from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from io import BytesIO
from pathlib import Path

from app.services.duckdb_service import (
    create_connection,
    get_sample_rows,
    get_table_schema,
    format_schema_for_llm,
    build_table_context,
    validate_sql

)

from app.services.prompt_service import build_sql_prompt
from app.services.llm_service import generate_sql

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are allowed"
        )

    contents = await file.read(MAX_FILE_SIZE + 1)


    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File must not exceed 10 MB"
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    try:
        if extension == ".csv":
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the uploaded file"
        )

    if df.empty or len(df.columns) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploade dataset contains not data"
        )

    connection = create_connection(df=df, table_name="uploaded_data")

    query = """
        SELECT COUNT(*) AS total_row_count
        FROM uploaded_data;
    """

    result = connection.execute(query)
    rows = result.fetchone()

    context = build_table_context(connection, "uploaded_data")
    question = "What is the total revenue for each category?"
    prompt = build_sql_prompt(question, context)
    command = generate_sql(prompt)
    validate_sql(command)
    connection.close()


    return {
        "filename": file.filename,
        "rows": rows[0],
        "columns_count": len(df.columns),
        "columns": [
            {
                "name": str(column),
                "data_type": str(df[column].dtype)
            }
            for column in df.columns
        ],
        "preview": df.head(5).fillna("").to_dict(orient="records")
    }