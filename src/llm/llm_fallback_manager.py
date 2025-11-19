# src/llm/llm_fallback_manager.py
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LLMFallbackManager:
    """Ultra-lightweight fallback LLM.
    - Does NOT load any local model (no disk, no GPU, no transformers).
    - Returns a small, safe SQL statement the pipeline can execute.
    - QueryOrchestrator treats this as a 'message' for the UI instead of crashing.
    """

    def __init__(self) -> None:
        # No heavy initialization needed
        pass

    def generate_sql(self, prompt: str) -> str:
        """Return a simple SQL that your pipeline can execute safely.
        Uses the 'message' column intentionally, because QueryOrchestrator
        handles this special case:
            SELECT '...' AS message;
        """
        truncated_prompt = prompt[:120].replace("\n", " ")
        logger.warning(
            "Using fallback SQL generator (remote LLM unavailable). Prompt (truncated): %s",
            truncated_prompt,
        )
        return (
            "SELECT "
            "'LLM offline – cannot generate SQL for this question right now. "
            "Please try again later or contact the admin.' AS message;"
        )
