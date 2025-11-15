from fastapi import FastAPI
from .predict import predict_router
from .auth import auth_router
from .users import user_router
from .dashboard_routes import dashboard_router

app = FastAPI(
    title="Food Classification Backend",
    docs_url="/docs",      # back to default
    redoc_url="/redoc"     # back to default
)

# Register routers
app.include_router(predict_router, prefix="/predict", tags=["Prediction"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])


@app.on_event("startup")
async def show_routes():
    print("\n📌 LOADED ROUTES:")
    for route in app.routes:
        print(route.path, " → ", route.name)
    print("\n")


@app.get("/")
def root():
    return {"message": "Food Recognition API Running!"}
