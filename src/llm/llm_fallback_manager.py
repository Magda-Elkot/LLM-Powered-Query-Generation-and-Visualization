# src/llm/llm_fallback_manager.py

import logging
 
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
 
 
class LLMFallbackManager:

    """

    Ultra-lightweight fallback LLM.
 
    - Does NOT load any local model (no disk, no GPU, no transformers).

    - Just returns a small, safe SQL statement that the pipeline can execute.

    - The QueryOrchestrator will then treat it as a 'message' response and

      show a friendly text in the UI instead of crashing.

    """
 
    def __init__(self) -> None:

        # No heavy initialization needed

        pass
 
    def generate_sql(self, prompt: str) -> str:

        """

        Return a simple SQL that your pipeline can execute safely.
 
        We use the 'message' column on purpose, because your QueryOrchestrator

        already has a special case for:

          SELECT '...' AS message;

        """

        truncated_prompt = prompt[:120].replace("\n", " ")

        logger.warning(

            "Using fallback SQL generator (remote LLM unavailable). "

            "Prompt (truncated): %s",

            truncated_prompt,

        )
 
        return (

            "SELECT "

            "'LLM offline – cannot generate SQL for this question right now. "

            "Please try again later or contact the admin.' AS message;"

        )

 