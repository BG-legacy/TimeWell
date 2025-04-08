"""
Factory for creating and managing LangChain chains with different configurations and voice styles.
This centralizes chain creation logic for reuse across the application.
"""

import os
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.chains import LLMChain
from langchain_core.runnables import RunnableSequence
from app.services.prompt_templates import PromptTemplateManager, VoiceStyle

load_dotenv()

class ChainFactory:
    """Factory for creating and configuring LangChain chains with different models and voice styles"""
    
    def __init__(self):
        self.prompt_manager = PromptTemplateManager()
        self.models = {
            "gpt-4": ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-3.5-turbo",
                temperature=0.7
            ),
            "gpt-3.5-turbo": ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-3.5-turbo",
                temperature=0.7
            )
        }
        
    def create_chain(
        self, 
        system_template: str, 
        human_template: str, 
        model_name: str = "gpt-4"
    ) -> RunnableSequence:
        """
        Create a basic LangChain with system and human templates
        
        Args:
            system_template: The system message template
            human_template: The human message template
            model_name: The model to use (default: gpt-4)
            
        Returns:
            Configured RunnableSequence
        """
        # Get the appropriate model
        llm = self._get_model(model_name)
        
        # Create message templates
        system_message = SystemMessagePromptTemplate.from_template(system_template)
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        # Create chat prompt
        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        
        # Return the runnable sequence
        return chat_prompt | llm
    
    def create_chain_with_voice(
        self, 
        human_template: str,
        voice_style: Union[VoiceStyle, str] = VoiceStyle.COOL_COUSIN,
        format_instructions: Optional[str] = None,
        model_name: str = "gpt-4"
    ) -> RunnableSequence:
        """
        Create a LangChain with the specified voice style
        
        Args:
            human_template: The human message template
            voice_style: The voice style to use (default: COOL_COUSIN)
            format_instructions: Optional formatting instructions
            model_name: The model to use (default: gpt-4)
            
        Returns:
            Configured RunnableSequence with voice styling
        """
        # Convert string voice_style to enum if needed
        if isinstance(voice_style, str):
            try:
                voice_style = VoiceStyle(voice_style)
            except ValueError:
                voice_style = VoiceStyle.COOL_COUSIN
        
        # Get the appropriate model
        llm = self._get_model(model_name)
        
        # Get the system template with voice styling
        system_template = self.prompt_manager.get_template(voice_style)["system_template"]
        
        # Include format instructions if provided
        if format_instructions:
            system_template = system_template.format(format_instructions=format_instructions)
        
        # Create message templates
        system_message = SystemMessagePromptTemplate.from_template(system_template)
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        # Create chat prompt
        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        
        # Return the runnable sequence
        return chat_prompt | llm
    
    def create_parser_chain(
        self,
        human_template: str,
        response_schemas: List[ResponseSchema],
        voice_style: Union[VoiceStyle, str] = VoiceStyle.COOL_COUSIN,
        model_name: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Create a chain with a structured output parser
        
        Args:
            human_template: The human message template
            response_schemas: List of ResponseSchema objects defining the output structure
            voice_style: The voice style to use (default: COOL_COUSIN)
            model_name: The model to use (default: gpt-4)
            
        Returns:
            Dictionary containing the chain and parser
        """
        # Create the output parser
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        
        # Create the chain with voice styling and format instructions
        runnable = self.create_chain_with_voice(
            human_template=human_template,
            voice_style=voice_style,
            format_instructions=format_instructions,
            model_name=model_name
        )
        
        # Create a wrapper to maintain compatibility with the old LLMChain interface
        chain = LLMChainWrapper(runnable)
        
        return {
            "chain": chain,
            "parser": output_parser
        }
    
    def _get_model(self, model_name: str) -> ChatOpenAI:
        """
        Get the appropriate LLM model
        
        Args:
            model_name: The name of the model to use
            
        Returns:
            ChatOpenAI model instance
        """
        if model_name in self.models:
            return self.models[model_name]
        
        # Default to GPT-4 if model not found
        return self.models["gpt-4"]

class LLMChainWrapper:
    """Wrapper to provide LLMChain-like interface for RunnableSequence"""
    
    def __init__(self, runnable: RunnableSequence):
        self.runnable = runnable
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async invoke method to match LLMChain interface"""
        result = await self.runnable.ainvoke(inputs)
        # Convert to dict format compatible with LLMChain output
        return {"text": result.content}

# Create a singleton instance
chain_factory = ChainFactory() 