"""
Executor module for handling tool invocations and LLM calls.
Manages error handling, retries, and logging.
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import time

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from config import settings

logger = logging.getLogger(__name__)


class ExecutorError(Exception):
    """Base exception for executor errors."""
    pass


class ToolExecutor:
    """Handles execution of tools with error handling and retries."""
    
    def __init__(self):
        """Initialize the tool executor."""
        self.tools: Dict[str, Callable] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_tool(self, name: str, tool_function: Callable):
        """
        Register a tool for execution.
        
        Args:
            name: Name of the tool
            tool_function: The callable tool function
        """
        self.tools[name] = tool_function
        logger.info(f"Registered tool: {name}")
    
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        Execute a tool with retry logic.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result from the tool execution
            
        Raises:
            ExecutorError: If tool execution fails
        """
        if tool_name not in self.tools:
            raise ExecutorError(f"Unknown tool: {tool_name}")
        
        start_time = time.time()
        
        try:
            logger.info(f"Executing tool: {tool_name} with args: {list(kwargs.keys())}")
            result = self.tools[tool_name](**kwargs)
            
            execution_time = time.time() - start_time
            
            # Log execution
            self.execution_history.append({
                "tool": tool_name,
                "timestamp": datetime.now(),
                "duration": execution_time,
                "status": "success",
                "args": kwargs
            })
            
            logger.info(f"Tool {tool_name} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log failure
            self.execution_history.append({
                "tool": tool_name,
                "timestamp": datetime.now(),
                "duration": execution_time,
                "status": "error",
                "error": str(e),
                "args": kwargs
            })
            
            logger.error(f"Tool {tool_name} failed after {execution_time:.2f}s: {e}")
            raise ExecutorError(f"Tool execution failed: {e}") from e
    
    def get_execution_history(self, tool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Args:
            tool_name: Optional filter by tool name
            
        Returns:
            List of execution records
        """
        if tool_name:
            return [h for h in self.execution_history if h["tool"] == tool_name]
        return self.execution_history


class LLMExecutor:
    """Handles LLM calls via Gemini API with error handling."""
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the LLM executor.
        
        Args:
            model: Gemini model to use (defaults to config setting)
        """
        self.model_name = model or settings.gemini_model
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=settings.gemini_api_key,
            temperature=1.0,
            max_tokens=65536,
        )
        self.call_history: List[Dict[str, Any]] = []
        logger.info(f"LLM Executor initialized with model: {self.model_name}")
    
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    def invoke(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> str:
        """
        Invoke the LLM with retry logic.
        
        Args:
            messages: List of messages to send to LLM
            **kwargs: Additional arguments for LLM
            
        Returns:
            LLM response content
            
        Raises:
            ExecutorError: If LLM call fails
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Invoking LLM with {len(messages)} messages")
            response = self.llm.invoke(messages, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Log call
            self.call_history.append({
                "timestamp": datetime.now(),
                "duration": execution_time,
                "status": "success",
                "message_count": len(messages),
                "response_length": len(response.content) if hasattr(response, 'content') else 0
            })
            
            logger.info(f"LLM call completed in {execution_time:.2f}s")
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log failure
            self.call_history.append({
                "timestamp": datetime.now(),
                "duration": execution_time,
                "status": "error",
                "error": str(e),
                "message_count": len(messages)
            })
            
            logger.error(f"LLM call failed after {execution_time:.2f}s: {e}")
            raise ExecutorError(f"LLM invocation failed: {e}") from e
    
    def invoke_with_system_prompt(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> str:
        """
        Convenience method to invoke LLM with system prompt and user message.
        
        Args:
            system_prompt: System prompt (agent instructions)
            user_message: User message/query
            **kwargs: Additional arguments for LLM
            
        Returns:
            LLM response content
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        return self.invoke(messages, **kwargs)
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get LLM call history."""
        return self.call_history
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about LLM usage.
        
        Returns:
            Dictionary with statistics
        """
        total_calls = len(self.call_history)
        successful_calls = len([h for h in self.call_history if h["status"] == "success"])
        failed_calls = total_calls - successful_calls
        
        avg_duration = 0
        if total_calls > 0:
            avg_duration = sum(h["duration"] for h in self.call_history) / total_calls
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "average_duration": avg_duration,
            "model": self.model_name
        }


class AgentExecutor:
    """Combined executor for agents - handles both tools and LLM calls."""
    
    def __init__(self, agent_name: str, system_prompt: str):
        """
        Initialize agent executor.
        
        Args:
            agent_name: Name of the agent
            system_prompt: System prompt for the agent
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tool_executor = ToolExecutor()
        self.llm_executor = LLMExecutor()
        
        logger.info(f"Agent executor initialized for: {agent_name}")
    
    def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent logic: LLM call potentially followed by tool calls.
        
        Args:
            user_input: User input/query
            context: Optional context dictionary
            
        Returns:
            Dictionary with response and any tool results
        """
        try:
            # Invoke LLM with system prompt and user input
            llm_response = self.llm_executor.invoke_with_system_prompt(
                system_prompt=self.system_prompt,
                user_message=user_input
            )
            
            result = {
                "agent": self.agent_name,
                "response": llm_response,
                "timestamp": datetime.now(),
                "tool_calls": []
            }
            
            # Parse response for any tool calls (simplified)
            # In a full implementation, this would use structured output
            # or tool calling features of the LLM
            
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed for {self.agent_name}: {e}")
            raise ExecutorError(f"Agent execution failed: {e}") from e
    
    def register_tool(self, tool_name: str, tool_function: Callable):
        """Register a tool for this agent."""
        self.tool_executor.register_tool(tool_name, tool_function)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "agent": self.agent_name,
            "llm_stats": self.llm_executor.get_stats(),
            "tool_executions": len(self.tool_executor.execution_history)
        }

