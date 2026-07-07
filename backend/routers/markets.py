from fastapi import APIRouter

router = APIRouter()

@router.get("/markets", tags=["市場資訊"])
def get_marketcode():
    market_data = [
            {"name": "台北一", "code": "109"},
            {"name": "台北二", "code": "104"},
            {"name": "板橋區", "code": "220"},
            {"name": "三重區", "code": "241"},
            {"name": "宜蘭市", "code": "260"},
            {"name": "桃農", "code": "338"},
            {"name": "台中市", "code": "400"},
            {"name": "豐原區", "code": "420"},
            {"name": "永靖區", "code": "512"},
            {"name": "西湖鎮", "code": "514"},
            {"name": "南投市", "code": "540"},
            {"name": "西螺鎮", "code": "648"},
            {"name": "高雄市", "code": "800"},
            {"name": "鳳山區", "code": "830"},
            {"name": "屏東市", "code": "900"},
            {"name": "台東市", "code": "930"},
            {"name": "花蓮市", "code": "950"}
        ]
    return {"markets": market_data}