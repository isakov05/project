from pydantic import BaseModel
from typing import Optional

class FoodLogCreate(BaseModel):
    food_id: str                    # ID of food from DB
    servings: int = 1               # How many servings
    serving_size: Optional[str] = "100g"
    image_url: Optional[str] = None


class FoodLogResponse(BaseModel):
    id: str
    food_id: str
    food_name: str
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    serving_size: str
    image_url: Optional[str]
    created_at: str
