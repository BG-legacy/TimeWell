import pytest
from langchain.chains import LLMChain
from langchain.output_parsers import ResponseSchema
from app.services.prompt_templates import VoiceStyle
from app.services.chain_factory import chain_factory

class TestChainFactory:
    """Test suite for the ChainFactory service"""
    
    def test_chain_factory_initialization(self):
        """Test that the ChainFactory initializes properly"""
        # Verify the factory has been created as a singleton
        assert chain_factory is not None
        
        # Check that the factory has initialized the prompt manager
        assert chain_factory.prompt_manager is not None
        
        # Check that the factory has initialized the models dictionary
        assert "gpt-4" in chain_factory.models
        assert "gpt-3.5-turbo" in chain_factory.models
    
    def test_create_chain(self):
        """Test creating a basic chain with system and human templates"""
        # Create a test chain
        system_template = "You are a helpful assistant."
        human_template = "Answer this question: {question}"
        
        chain = chain_factory.create_chain(
            system_template=system_template,
            human_template=human_template
        )
        
        # Verify the chain was created successfully
        assert isinstance(chain, LLMChain)
        assert chain.prompt.messages[0].prompt.template == system_template
        assert chain.prompt.messages[1].prompt.template == human_template
    
    def test_create_chain_with_voice(self):
        """Test creating a chain with a voice style"""
        # Create a test chain with each voice style
        human_template = "Answer this question: {question}"
        
        for voice in VoiceStyle:
            chain = chain_factory.create_chain_with_voice(
                human_template=human_template,
                voice_style=voice
            )
            
            # Verify the chain was created successfully
            assert isinstance(chain, LLMChain)
            assert chain.prompt.messages[1].prompt.template == human_template
            
            # Verify that the system template is not empty and contains key phrases from the voice style
            system_template = chain.prompt.messages[0].prompt.template
            assert len(system_template) > 0
            
            # Get some expected content for this voice style
            if voice == VoiceStyle.COOL_COUSIN:
                assert "Cool Cousin" in system_template
            elif voice == VoiceStyle.OG_BIG_BRO:
                assert "OG Big Bro" in system_template
            elif voice == VoiceStyle.ORACLE:
                assert "Oracle" in system_template
            elif voice == VoiceStyle.MOTIVATOR:
                assert "Motivator" in system_template
            elif voice == VoiceStyle.WISE_ELDER:
                assert "Wise Elder" in system_template
    
    def test_create_parser_chain(self):
        """Test creating a chain with a structured output parser"""
        # Define test schemas
        response_schemas = [
            ResponseSchema(
                name="answer",
                description="The answer to the question.",
                type="string"
            ),
            ResponseSchema(
                name="confidence",
                description="Confidence level from 1-10.",
                type="integer"
            )
        ]
        
        # Create a test chain with the parser
        human_template = "Answer this question: {question}"
        result = chain_factory.create_parser_chain(
            human_template=human_template,
            response_schemas=response_schemas
        )
        
        # Verify the result contains both chain and parser
        assert "chain" in result
        assert "parser" in result
        
        # Verify the chain was created successfully
        chain = result["chain"]
        assert isinstance(chain, LLMChain)
        assert chain.prompt.messages[1].prompt.template == human_template
        
        # Verify the parser was created successfully
        parser = result["parser"]
        assert parser.response_schemas == response_schemas 