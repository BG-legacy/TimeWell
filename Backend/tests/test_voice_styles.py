import pytest
from app.services.prompt_templates import PromptTemplateManager, VoiceStyle

class TestVoiceStyles:
    def test_prompt_template_manager_initialization(self):
        """Test that the PromptTemplateManager initializes with all expected voice styles"""
        manager = PromptTemplateManager()
        
        # Check that all voice styles are available in the templates
        for voice in VoiceStyle:
            assert voice in manager.templates
            
        # Check that each template has the required fields
        for template in manager.templates.values():
            assert "system_template" in template
            assert "tone_adjustments" in template
            
    def test_get_template(self):
        """Test the get_template method returns correct template"""
        manager = PromptTemplateManager()
        
        # Get template for each voice style
        for voice in VoiceStyle:
            template = manager.get_template(voice)
            assert template is not None
            assert template == manager.templates[voice]
            
        # Test default fallback when invalid style is provided
        invalid_style = "non_existent_style"
        template = manager.get_template(invalid_style)  # Should fallback to COOL_COUSIN
        assert template == manager.templates[VoiceStyle.COOL_COUSIN]
            
    def test_get_available_voices(self):
        """Test getting the list of available voice styles"""
        manager = PromptTemplateManager()
        voices = manager.get_available_voices()
        
        # Check that all enum values are represented in the list
        for voice in VoiceStyle:
            assert voice.value in voices
            
        # Check that the list has the right length
        assert len(voices) == len(VoiceStyle)
        
    def test_format_system_template(self):
        """Test formatting the system template with instructions"""
        manager = PromptTemplateManager()
        test_instructions = "TEST INSTRUCTIONS"
        
        for voice in VoiceStyle:
            formatted = manager.format_system_template(voice, test_instructions)
            assert test_instructions in formatted
            
            # Check that the template content is included
            template_content = manager.templates[voice]["system_template"]
            # Remove format placeholder from template for comparison
            template_content = template_content.replace("{format_instructions}", "")
            
            # The formatted string should contain the template content
            # (ignoring the format placeholder)
            assert all(line.strip() in formatted for line in template_content.split("\n") if line.strip()) 