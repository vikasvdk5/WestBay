"""
Gemini API wrapper with support for structured outputs, tool calling, and streaming.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import BaseTool

from config import settings

logger = logging.getLogger(__name__)


class GeminiLLM:
    """
    Wrapper for Google Gemini API with enhanced features.
    Supports structured outputs, tool calling, and streaming.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize Gemini LLM wrapper.
        
        Args:
            model: Gemini model name (defaults to config setting)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.model_name = model or settings.gemini_model
        self.temperature = temperature
        self.max_tokens = max_tokens or 65536
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=settings.gemini_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        logger.info(f"Gemini LLM initialized: {self.model_name}")
    
    def invoke(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> str:
        """
        Invoke the LLM with messages.
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments
            
        Returns:
            Response content as string
        """
        try:
            response = self.llm.invoke(messages, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Error invoking Gemini: {e}")
            raise
    
    def invoke_with_system(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> str:
        """
        Convenience method to invoke with system prompt and user message.
        
        Args:
            system_prompt: System prompt
            user_message: User message
            **kwargs: Additional arguments
            
        Returns:
            Response content as string
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        return self.invoke(messages, **kwargs)
    
    def with_structured_output(
        self,
        schema: Type[BaseModel]
    ) -> 'StructuredGeminiLLM':
        """
        Create a version of the LLM that returns structured output.
        
        Args:
            schema: Pydantic model for structured output
            
        Returns:
            StructuredGeminiLLM instance
        """
        return StructuredGeminiLLM(
            llm=self.llm,
            schema=schema,
            model_name=self.model_name
        )
    
    def bind_tools(
        self,
        tools: List[BaseTool]
    ) -> 'ToolCallingGeminiLLM':
        """
        Bind tools for tool calling.
        
        Args:
            tools: List of LangChain tools
            
        Returns:
            ToolCallingGeminiLLM instance
        """
        return ToolCallingGeminiLLM(
            llm=self.llm.bind_tools(tools),
            tools=tools,
            model_name=self.model_name
        )
    
    async def astream(
        self,
        messages: List[BaseMessage],
        **kwargs
    ):
        """
        Stream responses asynchronously.
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments
            
        Yields:
            Response chunks
        """
        try:
            async for chunk in self.llm.astream(messages, **kwargs):
                yield chunk.content if hasattr(chunk, 'content') else str(chunk)
        except Exception as e:
            logger.error(f"Error streaming from Gemini: {e}")
            raise


class StructuredGeminiLLM:
    """Gemini LLM configured for structured output."""
    
    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        schema: Type[BaseModel],
        model_name: str
    ):
        """
        Initialize structured output LLM.
        
        Args:
            llm: Base LLM instance
            schema: Pydantic model for output structure
            model_name: Model name for logging
        """
        self.llm = llm.with_structured_output(schema)
        self.schema = schema
        self.model_name = model_name
        logger.info(f"Structured Gemini LLM initialized with schema: {schema.__name__}")
    
    def invoke(
        self,
        messages: List[BaseMessage] | str,
        **kwargs
    ) -> BaseModel:
        """
        Invoke LLM and return structured output.
        
        Args:
            messages: Messages or single prompt string
            **kwargs: Additional arguments
            
        Returns:
            Instance of the schema model
        """
        try:
            if isinstance(messages, str):
                messages = [HumanMessage(content=messages)]
            
            result = self.llm.invoke(messages, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error getting structured output from Gemini: {e}")
            raise


class ToolCallingGeminiLLM:
    """Gemini LLM configured with tool calling capabilities."""
    
    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        tools: List[BaseTool],
        model_name: str
    ):
        """
        Initialize tool calling LLM.
        
        Args:
            llm: Base LLM with tools bound
            tools: List of available tools
            model_name: Model name for logging
        """
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.model_name = model_name
        logger.info(f"Tool-calling Gemini LLM initialized with {len(tools)} tools")
    
    def invoke(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke LLM with tool calling support.
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with response and tool calls
        """
        try:
            response = self.llm.invoke(messages, **kwargs)
            
            result = {
                "content": response.content if hasattr(response, 'content') else str(response),
                "tool_calls": []
            }
            
            # Extract tool calls if present
            if hasattr(response, 'tool_calls'):
                result["tool_calls"] = response.tool_calls
            
            return result
        except Exception as e:
            logger.error(f"Error in tool-calling LLM: {e}")
            raise
    
    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute tool calls and return results.
        
        Args:
            tool_calls: List of tool call specifications
            
        Returns:
            List of tool results
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            
            if tool_name in self.tools:
                try:
                    tool = self.tools[tool_name]
                    result = tool.invoke(tool_args)
                    results.append({
                        "tool": tool_name,
                        "result": result,
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    results.append({
                        "tool": tool_name,
                        "error": str(e),
                        "status": "error"
                    })
            else:
                logger.warning(f"Unknown tool requested: {tool_name}")
                results.append({
                    "tool": tool_name,
                    "error": f"Unknown tool: {tool_name}",
                    "status": "error"
                })
        
        return results


def create_gemini_llm(
    temperature: float = 1.0,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None
) -> GeminiLLM:
    """
    Factory function to create a Gemini LLM instance.
    
    Args:
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        model: Model name
        
    Returns:
        GeminiLLM instance
    """
    return GeminiLLM(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

