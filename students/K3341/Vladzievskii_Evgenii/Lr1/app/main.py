from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routers import auth, categories, transactions, budgets, tags


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Personal Finance Management API",
    description="API for managing personal finances with authentication and budgeting",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(tags.router)


@app.get("/")
def root():
    return {"message": "Personal Finance Management API is running. Visit /docs for documentation."}
