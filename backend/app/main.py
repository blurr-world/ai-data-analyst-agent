from fastapi import FastAPI
from app.api.upload import router as upload_router


app = FastAPI(
    title="AI Data Analyst Agent"
)

@app.get("/")
def home():
    return {
        "message": "AI Data Analyst Agent is running!"
    }


app.include_router(
    upload_router,
    prefix="/api",
    tags=["Dataset Upload"]
)