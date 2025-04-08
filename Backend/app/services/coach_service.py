"""
TimeWell Coach service that provides AI coaching using direct OpenAI API calls.
This service complements the LangChain approach with a simpler, more direct integration.
"""

import os
import json
import openai
import logging
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv
from app.services.prompt_templates import PromptTemplateManager, VoiceStyle
from app.services.fallback_messages import fallback_service
from contextlib import asynccontextmanager

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = openai.AsyncOpenAI(api_key=openai_api_key)

class CoachService:
    """
    Provides AI coaching functionality using direct OpenAI API calls.
    Can be used as an alternative to LangChain when more direct control is needed.
    """
    
    def __init__(self):
        self.prompt_manager = PromptTemplateManager()
        
    async def get_coaching_message(
        self, 
        user_prompt: str, 
        voice_style: Union[VoiceStyle, str] = VoiceStyle.COOL_COUSIN,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500,
        use_fallback_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Get a coaching message directly from OpenAI API
        
        Args:
            user_prompt: The user's question or prompt
            voice_style: The voice style to use
            model: The OpenAI model to use
            temperature: The temperature setting (0-1)
            max_tokens: Maximum tokens in the response
            use_fallback_on_error: Whether to use fallback messages if API fails
            
        Returns:
            Dictionary with the response and metadata
        """
        try:
            # Convert string voice_style to enum if needed
            if isinstance(voice_style, str):
                try:
                    voice_style = VoiceStyle(voice_style)
                except ValueError:
                    voice_style = VoiceStyle.COOL_COUSIN
            
            # Get the system prompt for this voice style
            system_prompt = self.prompt_manager.get_template(voice_style)["system_template"]
            system_prompt = system_prompt.format(format_instructions="")
            
            # Create the messages array
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Make the API call using the new client syntax
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Process and return the response
            content = response.choices[0].message.content
            
            return {
                "text": content,
                "voice_style": voice_style.value,
                "model": model,
                "token_usage": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error getting coaching message: {str(e)}")
            
            if not use_fallback_on_error:
                return {
                    "error": True,
                    "message": f"Error getting coaching message: {str(e)}"
                }
            
            # Use fallback message if API call fails
            logger.info(f"Using fallback message for voice style {voice_style}")
            
            # Get message type based on user prompt (simple heuristic)
            message_type = "general"
            if "analyze" in user_prompt.lower() or "assessment" in user_prompt.lower():
                message_type = "analysis"
            elif "suggest" in user_prompt.lower() or "advice" in user_prompt.lower():
                message_type = "suggestion"
            elif "plan" in user_prompt.lower() or "action" in user_prompt.lower():
                message_type = "action_plan"
            elif "review" in user_prompt.lower() or "week" in user_prompt.lower():
                message_type = "weekly_review"
                
            fallback_message = fallback_service.get_fallback_message(
                voice_style=voice_style,
                message_type=message_type
            )
            
            # Add a bit of context by including part of the user's question
            question_preview = user_prompt[:50] + "..." if len(user_prompt) > 50 else user_prompt
            response_text = f"Regarding '{question_preview}': {fallback_message}"
            
            return {
                "text": response_text,
                "voice_style": voice_style.value,
                "model": "fallback",
                "fallback": True
            }
    
    async def weekly_review(
        self,
        user_data: Dict[str, Any],
        voice_style: Union[VoiceStyle, str] = VoiceStyle.WISE_ELDER,
        use_fallback_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a weekly review of the user's progress
        
        Args:
            user_data: Dictionary containing user data for the week
            voice_style: The voice style to use
            use_fallback_on_error: Whether to use fallback messages if API fails
            
        Returns:
            Dictionary with the review and metadata
        """
        try:
            # Prepare the user data
            events_summary = "\n".join([f"- {e['title']}: {e['description']}" for e in user_data.get("events", [])])
            goals_summary = "\n".join([f"- {g['title']}: {g['description']}" for g in user_data.get("goals", [])])
            
            # Create the user prompt
            user_prompt = f"""
            Please provide a weekly review for this user based on their activity:
            
            EVENTS THIS WEEK:
            {events_summary if events_summary else "No events recorded this week."}
            
            ACTIVE GOALS:
            {goals_summary if goals_summary else "No active goals."}
            
            Please include:
            1. A summary of their week
            2. Patterns or insights from their time use
            3. How their activities align with their goals
            4. Encouragement and suggestions for the coming week
            """
            
            # Get the coaching message
            return await self.get_coaching_message(
                user_prompt=user_prompt,
                voice_style=voice_style,
                max_tokens=1000,  # Longer for weekly reviews
                use_fallback_on_error=use_fallback_on_error
            )
            
        except Exception as e:
            logger.error(f"Error generating weekly review: {str(e)}")
            
            if not use_fallback_on_error:
                return {
                    "error": True,
                    "message": f"Error generating weekly review: {str(e)}"
                }
            
            # Use fallback weekly review
            logger.info(f"Using fallback weekly review for voice style {voice_style}")
            return fallback_service.get_fallback_weekly_review(
                voice_style=voice_style,
                user_data=user_data
            )
            
    @asynccontextmanager
    async def structured_coach(
        self,
        voice_style: Union[VoiceStyle, str] = VoiceStyle.COOL_COUSIN,
        model: str = "gpt-3.5-turbo-1106",
        use_fallback_on_error: bool = True
    ):
        """
        Context manager for interacting with OpenAI's JSON mode
        for highly structured responses
        
        Args:
            voice_style: The voice style to use
            model: The OpenAI model to use (must support JSON mode)
            use_fallback_on_error: Whether to use fallback output if API fails
            
        Yields:
            Coach function that can be called with prompts
        """
        # Convert string voice_style to enum if needed
        if isinstance(voice_style, str):
            try:
                voice_style = VoiceStyle(voice_style)
            except ValueError:
                voice_style = VoiceStyle.COOL_COUSIN
        
        # Get the voice style adjustments
        tone_adjustments = self.prompt_manager.get_template(voice_style)["tone_adjustments"]
        
        # Get the base system prompt
        system_prompt = self.prompt_manager.get_template(voice_style)["system_template"]
        system_prompt = system_prompt.format(format_instructions="")
        
        async def coach_function(
            prompt: str, 
            response_format: Dict[str, Any]
        ) -> Dict[str, Any]:
            try:
                # Create the messages array with JSON instructions
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                
                # Make the API call with JSON mode
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object", "schema": response_format},
                    temperature=0.7
                )
                
                # Parse the JSON response
                content = response.choices[0].message.content
                return {
                    "data": json.loads(content),
                    "voice_style": voice_style.value,
                    "model": model,
                    "token_usage": response.usage.total_tokens
                }
                
            except Exception as e:
                logger.error(f"Error with structured coaching: {str(e)}")
                
                if not use_fallback_on_error:
                    return {
                        "error": True,
                        "message": f"Error with structured coaching: {str(e)}"
                    }
                    
                # Determine what kind of structured output was expected
                response_type = "action_plan"  # Default fallback type
                required_props = response_format.get("properties", {}).keys()
                
                if "actions" in required_props and "priorities" in required_props:
                    response_type = "action_plan"
                
                # Get appropriate fallback
                if response_type == "action_plan":
                    logger.info(f"Using fallback action plan for voice style {voice_style}")
                    return {
                        "data": fallback_service.get_fallback_action_plan(voice_style),
                        "voice_style": voice_style.value,
                        "model": "fallback",
                        "fallback": True
                    }
                else:
                    # Generic fallback for unknown structured formats
                    logger.info(f"Using generic fallback for voice style {voice_style}")
                    return {
                        "data": {
                            "message": fallback_service.get_fallback_message(voice_style, "general"),
                            "fallback": True
                        },
                        "voice_style": voice_style.value,
                        "model": "fallback",
                        "fallback": True
                    }
        
        try:
            yield coach_function
        finally:
            # Cleanup if needed
            pass
            
# Create a singleton instance
coach_service = CoachService() 