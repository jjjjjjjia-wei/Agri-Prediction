from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import markets 
from routers import predict
from routers import quary_history_price

app = FastAPI(title="菜價預測 API 系統", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 把部門分機掛載到大門口
app.include_router(markets.router)
app.include_router(predict.router)
app.include_router(quary_history_price.router)

@app.get("/")
def read_root():
    return {"message": "系統運作正常"}