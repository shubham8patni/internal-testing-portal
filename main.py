"""Internal Testing Portal - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="Internal Testing Portal",
    description="Configuration-driven API sanity testing platform for insurance products",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint - returns index.html"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Internal Testing Portal"
    }


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print("Internal Testing Portal starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    print("Internal Testing Portal shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
