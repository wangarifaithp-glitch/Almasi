
from fastapi import FastAPI

app = FastAPI(
    title="ALMASI Learning Platform API",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to the ALMASI backend",
        "status": "running",
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "database": "not connected yet",
    }
