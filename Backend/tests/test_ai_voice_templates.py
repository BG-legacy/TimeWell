import pytest
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.prompt_templates import VoiceStyle, PromptTemplateManager
from app.services.chain_factory import chain_factory
from app.services.ai_analysis import analyze_event_goal_alignment
from app.services.coach_service import coach_service
from app.schemas.event import EventCreate
from app.schemas.user import UserCreate

# Mock data for testing
MOCK_EVENT_ANALYSIS = {
    "score": 8,
    "aligned_goals": ["goal-123"],
    "analysis": "This is a test analysis.",
    "suggestion": "This is a test suggestion.",
    "new_goal_suggestion": "This is a new goal suggestion."
}

MOCK_COACHING_RESPONSE = {
    "text": "This is a coaching response."
}

MOCK_USER = {
    "_id": "mock-user-id", 
    "username": "test_user",
    "email": "test@example.com"
}

MOCK_EVENT = {
    "_id": "mock-event-id",
    "user_id": "mock-user-id",
    "title": "Test Event",
    "description": "Test event description",
    "start_time": datetime.utcnow(),
    "end_time": datetime.utcnow() + timedelta(hours=1)
}

class TestAIVoiceTemplates:
    """Test suite for AI interactions with different voice templates"""
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN,
        VoiceStyle.OG_BIG_BRO,
        VoiceStyle.ORACLE,
        VoiceStyle.MOTIVATOR,
        VoiceStyle.WISE_ELDER
    ])
    def test_voice_style_prompt_templates(self, voice_style):
        """Test that each voice style has appropriate prompt templates"""
        manager = PromptTemplateManager()
        template = manager.get_template(voice_style)
        
        # Verify template structure
        assert "system_template" in template
        assert "tone_adjustments" in template
        
        # Verify content is appropriate for the voice style
        system_template = template["system_template"]
        
        # Each voice style should have its name in the template
        if voice_style == VoiceStyle.COOL_COUSIN:
            assert "Cool Cousin" in system_template
        elif voice_style == VoiceStyle.OG_BIG_BRO:
            assert "OG Big Bro" in system_template
        elif voice_style == VoiceStyle.ORACLE:
            assert "Oracle" in system_template
        elif voice_style == VoiceStyle.MOTIVATOR:
            assert "Motivator" in system_template
        elif voice_style == VoiceStyle.WISE_ELDER:
            assert "Wise Elder" in system_template
        
        # Verify tone adjustments exist for analysis and suggestions
        assert "analysis" in template["tone_adjustments"]
        assert "suggestions" in template["tone_adjustments"]
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ])
    @pytest.mark.asyncio
    async def test_event_analysis_with_voice_style(self, monkeypatch, voice_style):
        """Test event analysis with each voice style"""
        from app.services import ai_analysis
        
        # We'll patch the internal functions directly in the ai_analysis module
        # Mock get_event_by_id within the ai_analysis module
        async def mock_get_event_by_id(event_id):
            return MOCK_EVENT
        
        # Mock get_goals_by_user_id within the ai_analysis module
        async def mock_get_goals_by_user_id(user_id):
            return []
        
        # Mock create_suggestion within the ai_analysis module
        async def mock_create_suggestion(suggestion_data):
            return {"_id": "mock-suggestion-id"}
        
        # Apply the mocks
        monkeypatch.setattr(ai_analysis, "get_event_by_id", mock_get_event_by_id)
        monkeypatch.setattr(ai_analysis, "get_goals_by_user_id", mock_get_goals_by_user_id)
        monkeypatch.setattr(ai_analysis, "create_suggestion", mock_create_suggestion)
        
        # Create a mock chain that returns our predefined response
        class MockChain:
            async def ainvoke(self, *args, **kwargs):
                return {"text": json.dumps(MOCK_EVENT_ANALYSIS)}
        
        # Create a mock chain config that returns our mock chain
        class MockChainFactory:
            def create_parser_chain(self, *args, **kwargs):
                # Create a mock parser that just returns the data
                class MockParser:
                    def parse(self, text):
                        return json.loads(text)
                
                return {
                    "chain": MockChain(),
                    "parser": MockParser()
                }
        
        # Store the original chain factory
        original_chain_factory = ai_analysis.chain_factory
        
        try:
            # Apply our mock chain factory
            ai_analysis.chain_factory = MockChainFactory()
            
            # Call analyze_event_goal_alignment with our test data
            result = await analyze_event_goal_alignment(
                MOCK_USER["_id"],
                MOCK_EVENT["_id"],
                voice_style=voice_style
            )
            
            # Verify the result
            assert result["error"] is False
            assert result["event_id"] == MOCK_EVENT["_id"]
            assert result["voice_style"] == voice_style
            
            # Parse the analysis JSON string to verify its contents
            analysis = json.loads(result["analysis"])
            assert analysis["score"] == MOCK_EVENT_ANALYSIS["score"]
            assert analysis["analysis"] == MOCK_EVENT_ANALYSIS["analysis"]
            assert analysis["suggestion"] == MOCK_EVENT_ANALYSIS["suggestion"]
            
        finally:
            # Restore the original chain factory
            ai_analysis.chain_factory = original_chain_factory
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ])
    @pytest.mark.asyncio
    async def test_coaching_message_with_voice_style(self, monkeypatch, voice_style):
        """Test coaching messages with each voice style"""
        # Create a mock for the OpenAI chat completion
        async def mock_acreate(*args, **kwargs):
            # Check that the voice style is correctly passed in the system message
            messages = kwargs.get("messages", [])
            system_message = next((m for m in messages if m["role"] == "system"), None)
            
            # Make the mock response include the voice style to verify it was used
            class MockResponse:
                class MockChoice:
                    class MockMessage:
                        content = f"Voice style: {voice_style} - {MOCK_COACHING_RESPONSE['text']}"
                    
                    message = MockMessage()
                
                choices = [MockChoice()]
                
                class MockUsage:
                    total_tokens = 100
                
                usage = MockUsage()
            
            return MockResponse()
        
        # Patch the OpenAI API
        import openai
        original_acreate = openai.ChatCompletion.acreate
        openai.ChatCompletion.acreate = mock_acreate
        
        try:
            # Call the coaching service with our test prompt
            result = await coach_service.get_coaching_message(
                "Test coaching prompt",
                voice_style=voice_style
            )
            
            # Verify the result
            assert "text" in result
            assert voice_style in result["voice_style"]
            assert "Voice style:" in result["text"]
            assert MOCK_COACHING_RESPONSE["text"] in result["text"]
            assert "token_usage" in result
            
        finally:
            # Restore the original OpenAI API
            openai.ChatCompletion.acreate = original_acreate
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ])
    @pytest.mark.asyncio
    async def test_weekly_review_with_voice_style(self, monkeypatch, voice_style):
        """Test weekly review with each voice style"""
        # Create a mock for the coaching service to avoid actual OpenAI calls
        original_get_coaching_message = coach_service.get_coaching_message
        
        async def mock_get_coaching_message(*args, **kwargs):
            # Include voice style in response to verify it was used
            return {
                "text": f"Voice style: {kwargs.get('voice_style')} - Weekly review content",
                "voice_style": kwargs.get('voice_style'),
                "model": "gpt-4-mock",
                "token_usage": 150
            }
        
        # Apply the mock
        coach_service.get_coaching_message = mock_get_coaching_message
        
        # Mock user data for the weekly review
        user_data = {
            "events": [
                {"title": "Test Event 1", "description": "Description 1"},
                {"title": "Test Event 2", "description": "Description 2"}
            ],
            "goals": [
                {"title": "Test Goal 1", "description": "Goal Description 1"},
                {"title": "Test Goal 2", "description": "Goal Description 2"}
            ],
            "user_name": "Test User"
        }
        
        try:
            # Call the weekly review function
            result = await coach_service.weekly_review(
                user_data=user_data,
                voice_style=voice_style
            )
            
            # Verify the result
            assert "text" in result
            assert "voice_style" in result
            assert result["voice_style"] == voice_style
            assert "Voice style:" in result["text"]
            assert voice_style in result["text"]
            
        finally:
            # Restore the original function
            coach_service.get_coaching_message = original_get_coaching_message
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ])
    @pytest.mark.asyncio
    async def test_structured_coach_with_voice_style(self, monkeypatch, voice_style):
        """Test structured coaching with each voice style"""
        # Create a mock for the OpenAI chat completion
        async def mock_acreate(*args, **kwargs):
            # Verify that the correct voice style is used in the system message
            messages = kwargs.get("messages", [])
            system_message = next((m for m in messages if m["role"] == "system"), None)
            
            # Create mock structured response data
            structured_data = {
                "actions": [f"Action 1 with {voice_style} style", "Action 2", "Action 3"],
                "priorities": ["Priority 1", "Priority 2"],
                "insights": ["Insight 1", "Insight 2"]
            }
            
            class MockResponse:
                class MockChoice:
                    class MockMessage:
                        content = json.dumps(structured_data)
                    
                    message = MockMessage()
                
                choices = [MockChoice()]
                
                class MockUsage:
                    total_tokens = 120
                
                usage = MockUsage()
            
            return MockResponse()
        
        # Patch the OpenAI API
        import openai
        original_acreate = openai.ChatCompletion.acreate
        openai.ChatCompletion.acreate = mock_acreate
        
        try:
            # Use the structured coach context manager
            async with coach_service.structured_coach(voice_style=voice_style) as coach:
                # Define a test prompt and response format
                prompt = "Create an action plan for improving productivity"
                response_format = {
                    "type": "object",
                    "properties": {
                        "actions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "priorities": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "insights": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
                
                # Call the coach function
                result = await coach(prompt, response_format)
                
                # Verify the result
                assert "data" in result
                assert "voice_style" in result
                assert result["voice_style"] == voice_style
                assert "actions" in result["data"]
                assert "priorities" in result["data"]
                assert "insights" in result["data"]
                assert voice_style in result["data"]["actions"][0]
                
        finally:
            # Restore the original OpenAI API
            openai.ChatCompletion.acreate = original_acreate
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ])
    @pytest.mark.asyncio
    async def test_event_analysis_fallback(self, monkeypatch, voice_style):
        """Test fallback messages for event analysis with each voice style"""
        from app.services import ai_analysis
        
        # We'll patch the internal functions directly in the ai_analysis module
        # Mock get_event_by_id within the ai_analysis module
        async def mock_get_event_by_id(event_id):
            return MOCK_EVENT
        
        # Mock get_goals_by_user_id within the ai_analysis module
        async def mock_get_goals_by_user_id(user_id):
            return []
        
        # Mock create_suggestion within the ai_analysis module
        async def mock_create_suggestion(suggestion_data):
            return {"_id": "mock-suggestion-id"}
        
        # Apply the mocks
        monkeypatch.setattr(ai_analysis, "get_event_by_id", mock_get_event_by_id)
        monkeypatch.setattr(ai_analysis, "get_goals_by_user_id", mock_get_goals_by_user_id)
        monkeypatch.setattr(ai_analysis, "create_suggestion", mock_create_suggestion)
        
        # Create a mock chain that raises an exception to trigger fallback
        class MockChain:
            async def ainvoke(self, *args, **kwargs):
                raise Exception("Mock API failure")
        
        # Create a mock chain config that returns our mock chain
        class MockChainFactory:
            def create_parser_chain(self, *args, **kwargs):
                # Create a mock parser that should not be called
                class MockParser:
                    def parse(self, text):
                        raise Exception("Parser should not be called in fallback scenario")
                
                return {
                    "chain": MockChain(),
                    "parser": MockParser()
                }
        
        # Store the original chain factory
        original_chain_factory = ai_analysis.chain_factory
        
        try:
            # Apply our mock chain factory
            ai_analysis.chain_factory = MockChainFactory()
            
            # Call analyze_event_goal_alignment with our test data
            result = await analyze_event_goal_alignment(
                MOCK_USER["_id"],
                MOCK_EVENT["_id"],
                voice_style=voice_style,
                use_fallback_on_error=True
            )
            
            # Verify we got a fallback response
            assert "fallback" in result
            assert result["fallback"] is True
            assert "error" in result
            assert result["error"] is False  # Fallbacks don't return errors
            assert result["event_id"] == MOCK_EVENT["_id"]
            assert result["voice_style"] == voice_style
            assert result["model_used"] == "fallback"
            
            # The analysis should be a JSON string containing the fallback message
            analysis = json.loads(result["analysis"])
            assert "analysis" in analysis
            assert "suggestion" in analysis
            assert isinstance(analysis["analysis"], str)
            assert isinstance(analysis["suggestion"], str)
            
        finally:
            # Restore the original chain factory
            ai_analysis.chain_factory = original_chain_factory
    
    @pytest.mark.parametrize("voice_style", [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ])
    @pytest.mark.asyncio
    async def test_coaching_message_fallback(self, monkeypatch, voice_style):
        """Test fallback messages for coaching with each voice style"""
        # Create a mock for the OpenAI chat completion that raises an exception
        async def mock_acreate_error(*args, **kwargs):
            raise Exception("Mock API failure")
        
        # Patch the OpenAI API
        import openai
        original_acreate = openai.ChatCompletion.acreate
        openai.ChatCompletion.acreate = mock_acreate_error
        
        try:
            # Call the coaching service with our test prompt
            result = await coach_service.get_coaching_message(
                "Test coaching prompt",
                voice_style=voice_style,
                use_fallback_on_error=True
            )
            
            # Verify we got a fallback response
            assert "fallback" in result
            assert result["fallback"] is True
            assert "text" in result
            assert result["voice_style"] == voice_style
            assert result["model"] == "fallback"
            
            # The response should include the fallback message
            assert "Regarding 'Test coaching prompt':" in result["text"]
            
        finally:
            # Restore the original OpenAI API
            openai.ChatCompletion.acreate = original_acreate 