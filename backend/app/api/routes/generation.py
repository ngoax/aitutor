from fastapi import APIRouter

from app.schemas.generation import WizardOptions, wizard_options

router = APIRouter(prefix="/generation", tags=["generation"])


@router.get("/options", response_model=WizardOptions)
def get_wizard_options() -> WizardOptions:
    return wizard_options()
