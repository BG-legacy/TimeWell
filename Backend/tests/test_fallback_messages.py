import pytest
from app.services.prompt_templates import VoiceStyle
from app.services.fallback_messages import fallback_service

class TestFallbackMessages:
    """Test suite for the FallbackMessageService"""
    
    def test_fallback_service_initialization(self):
        """Test that the fallback service initializes correctly"""
        # Verify that the service has been created as a singleton
        assert fallback_service is not None
        
        # Check that the fallback messages dictionary is populated
        for voice_style in VoiceStyle:
            assert voice_style in fallback_service.fallback_messages
            
            # Check that each voice style has all message types
            voice_messages = fallback_service.fallback_messages[voice_style]
            for message_type in ["general", "analysis", "suggestion", "weekly_review", "action_plan"]:
                assert message_type in voice_messages
                assert isinstance(voice_messages[message_type], list)
                assert len(voice_messages[message_type]) > 0
    
    def test_get_fallback_message(self):
        """Test getting fallback messages with different voice styles and message types"""
        # Check each voice style
        for voice_style in VoiceStyle:
            # Check each message type
            for message_type in ["general", "analysis", "suggestion", "weekly_review", "action_plan"]:
                message = fallback_service.get_fallback_message(voice_style, message_type)
                
                # Verify we get a non-empty string
                assert isinstance(message, str)
                assert len(message) > 0
                
                # Verify we get the same message type when using string voice style
                string_message = fallback_service.get_fallback_message(voice_style.value, message_type)
                assert isinstance(string_message, str)
                assert len(string_message) > 0
        
        # Test fallback to default voice style with invalid voice style
        message = fallback_service.get_fallback_message("invalid_voice", "general")
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Test fallback to general message type with invalid message type
        message = fallback_service.get_fallback_message(VoiceStyle.COOL_COUSIN, "invalid_type")
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_get_fallback_analysis(self):
        """Test generating a fallback analysis response"""
        # Test with minimal data
        analysis = fallback_service.get_fallback_analysis(VoiceStyle.COOL_COUSIN)
        
        # Verify the structure
        assert "error" in analysis
        assert analysis["error"] is False
        assert "fallback" in analysis
        assert analysis["fallback"] is True
        assert "analysis" in analysis
        assert "voice_style" in analysis
        assert "model_used" in analysis
        assert analysis["model_used"] == "fallback"
        
        # Test with event data
        event_data = {
            "_id": "test_id",
            "title": "Test Event",
            "description": "Test description"
        }
        
        analysis = fallback_service.get_fallback_analysis(VoiceStyle.OG_BIG_BRO, event_data)
        
        # Verify event data was incorporated
        assert "event_id" in analysis
        assert analysis["event_id"] == "test_id"
        assert "Test Event" in analysis["analysis"]["analysis"]
    
    def test_get_fallback_weekly_review(self):
        """Test generating a fallback weekly review"""
        # Test with minimal data
        review = fallback_service.get_fallback_weekly_review(VoiceStyle.WISE_ELDER)
        
        # Verify the structure
        assert "text" in review
        assert "voice_style" in review
        assert "model" in review
        assert "fallback" in review
        assert review["fallback"] is True
        assert review["model"] == "fallback"
        
        # Test with user data
        user_data = {
            "user_name": "TestUser"
        }
        
        review = fallback_service.get_fallback_weekly_review(VoiceStyle.MOTIVATOR, user_data)
        
        # Verify user data was incorporated
        assert "TestUser" in review["text"]
    
    def test_get_fallback_action_plan(self):
        """Test generating a fallback action plan"""
        # Test with different voice styles
        for voice_style in VoiceStyle:
            plan = fallback_service.get_fallback_action_plan(voice_style)
            
            # Verify the structure
            assert "actions" in plan
            assert "priorities" in plan
            assert "insights" in plan
            assert "fallback" in plan
            assert plan["fallback"] is True
            
            # Check arrays
            assert isinstance(plan["actions"], list)
            assert len(plan["actions"]) > 0
            assert isinstance(plan["priorities"], list)
            assert len(plan["priorities"]) > 0
            assert isinstance(plan["insights"], list)
            assert len(plan["insights"]) > 0 