"""
Utility module for loading agent prompts from the prompts/ directory.
Provides caching and validation for prompt files.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

from config import get_prompts_dir

logger = logging.getLogger(__name__)


class PromptLoader:
    """Handles loading and caching of agent prompt files."""
    
    def __init__(self, prompts_directory: Optional[Path] = None):
        """
        Initialize the PromptLoader.
        
        Args:
            prompts_directory: Path to prompts directory. Defaults to project prompts/ dir.
        """
        self.prompts_dir = prompts_directory or get_prompts_dir()
        self._cache: Dict[str, str] = {}
        
    def load_prompt(self, prompt_file: str) -> str:
        """
        Load a prompt from file with caching.
        
        Args:
            prompt_file: Name of the prompt file (e.g., 'lead_agent.txt')
            
        Returns:
            The prompt content as a string
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            ValueError: If the prompt file is empty
        """
        # Check cache first
        if prompt_file in self._cache:
            logger.debug(f"Loading prompt from cache: {prompt_file}")
            return self._cache[prompt_file]
        
        # Load from file
        prompt_path = self.prompts_dir / prompt_file
        
        if not prompt_path.exists():
            error_msg = f"Prompt file not found: {prompt_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read().strip()
            
            if not prompt_content:
                error_msg = f"Prompt file is empty: {prompt_path}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Cache the loaded prompt
            self._cache[prompt_file] = prompt_content
            logger.info(f"Loaded prompt: {prompt_file} ({len(prompt_content)} characters)")
            
            return prompt_content
            
        except Exception as e:
            logger.error(f"Error loading prompt file {prompt_path}: {e}")
            raise
    
    def validate_prompt(self, prompt_content: str) -> bool:
        """
        Validate that a prompt has minimum required structure.
        
        Args:
            prompt_content: The prompt content to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = [
            "<role_definition>",
            "<workflow>",
        ]
        
        for section in required_sections:
            if section not in prompt_content:
                logger.warning(f"Prompt missing required section: {section}")
                return False
        
        return True
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
        logger.info("Prompt cache cleared")
    
    def list_available_prompts(self) -> list:
        """
        List all available prompt files in the prompts directory.
        
        Returns:
            List of prompt filenames
        """
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory does not exist: {self.prompts_dir}")
            return []
        
        prompt_files = list(self.prompts_dir.glob("*.txt"))
        return [f.name for f in prompt_files]


# Global prompt loader instance
_prompt_loader = PromptLoader()


@lru_cache(maxsize=32)
def load_agent_prompt(agent_name: str) -> str:
    """
    Convenience function to load an agent's prompt file.
    
    Agent name to file mapping:
    - 'lead_researcher' -> 'lead_agent.txt'
    - 'data_collector' -> 'researcher.txt'
    - 'writer' -> 'report_writer.txt'
    - 'api_researcher' -> 'api_researcher.txt'
    - 'analyst' -> 'analyst.txt'
    - 'cost_calculator' -> 'cost_calculator.txt'
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        The prompt content as a string
    """
    # Mapping of agent names to prompt files
    prompt_map = {
        'lead_researcher': 'lead_agent.txt',
        'data_collector': 'researcher.txt',
        'writer': 'synthesizer.txt',  # Writer now uses synthesizer prompt (merged)
        'synthesizer': 'synthesizer.txt',  # Synthesizer agent prompt
        'api_researcher': 'api_researcher.txt',
        'analyst': 'analyst.txt',
        'cost_calculator': 'cost_calculator.txt',
        'straight_through_llm': 'straight-through-llm.txt',  # Straight-through-LLM agent
    }
    
    prompt_file = prompt_map.get(agent_name)
    
    if not prompt_file:
        raise ValueError(f"Unknown agent name: {agent_name}. Available: {list(prompt_map.keys())}")
    
    return _prompt_loader.load_prompt(prompt_file)


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    return _prompt_loader

