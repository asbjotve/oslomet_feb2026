# Updated Endpoint Definitions

from fastapi import APIRouter

router = APIRouter()

# Keeping this endpoint unchanged
@router.get("/alma_api/kursdata")
def get_kursdata():
    pass  # Define your logic here

# Keeping this endpoint unchanged
@router.get("/alma_api/hent_instructors")
def get_instructors():
    pass  # Define your logic here

# Removed /alma_api/enkelt_kurs endpoint
