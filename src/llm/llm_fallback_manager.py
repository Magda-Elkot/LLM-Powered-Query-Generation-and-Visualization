# src/llm/llm_fallback_manager.py
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("Transformers not installed. Offline LLM will use placeholder output.")


class LLMFallbackManager:
    """
    Offline-only manager: wraps a local Hugging Face model.
    """
    def __init__(self, model_path: str):
        self.model = None
        self.tokenizer = None

        if not os.path.exists(model_path):
            logger.error(f"Offline model path does not exist: {model_path}")
            return

        if HF_AVAILABLE:
            try:
                logger.info(f"Loading offline model from {model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="cpu")
            except Exception as e:
                logger.error(f"Failed to load offline model: {e}")
        else:
            logger.warning("Transformers not available. Offline LLM cannot run.")

    async def generate_sql(self, prompt: str) -> str:
        if self.model is not None:
            import asyncio
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = await asyncio.to_thread(
                lambda: self.model.generate(**inputs, max_new_tokens=256, pad_token_id=self.tokenizer.eos_token_id)
            )
            sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return sql
        else:
            return "-- Offline placeholder SQL.\nSELECT 1;"
