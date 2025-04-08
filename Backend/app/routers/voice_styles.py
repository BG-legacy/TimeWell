from fastapi import APIRouter, Depends
from typing import List
from app.services.prompt_templates import PromptTemplateManager, VoiceStyle
from app.core.auth import get_current_user

router = APIRouter(
    prefix="/voice-styles",
    tags=["voice-styles"],
    responses={404: {"description": "Not found"}},
)

prompt_template_manager = PromptTemplateManager()

@router.get("", response_model=List[str])
async def get_available_voice_styles(
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of available voice styles for AI analysis.
    
    Returns the names of all available voice styles that can be used
    when analyzing events and generating suggestions.
    
    Available voices include:
    - cool_cousin: Young, hip mentor who keeps it real
    - og_big_bro: Experienced, protective guide with street wisdom
    - oracle: Wise, spiritual advisor connected to ancestral knowledge
    - motivator: Energetic, passionate coach focused on empowerment
    - wise_elder: Patient, nuanced mentor with deep historical perspective
    """
    return prompt_template_manager.get_available_voices() 