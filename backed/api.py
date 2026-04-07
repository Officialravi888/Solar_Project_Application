from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Solar API Running"}

@app.get("/calculate")
def calculate(length: float, width: float):
    area = length * width
    kw = area / 100
    cost = kw * 60000

    return {
        "area_sqft": area,
        "estimated_kw": round(kw, 2),
        "system_type": "Small" if kw < 1 else "Large",
        "estimated_cost": round(cost),
        "components": [
            "Solar Panel",
            "Inverter",
            "Battery",
            "Wiring"
        ]
    }