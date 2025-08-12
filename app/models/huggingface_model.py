# app/models/huggingface_model.py
import logging
from typing import Dict, Any, Optional
from .base_model import BaseLLMModel

logger = logging.getLogger(__name__)

class HuggingFaceModel(BaseLLMModel):
    """Hugging Face Transformers model implementation"""
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.device = model_config.get('device', 'cpu')
        self.max_length = model_config.get('max_length', 512)
        self.temperature = model_config.get('temperature', 0.7)
        self.do_sample = model_config.get('do_sample', True)
        self.top_p = model_config.get('top_p', 0.9)
        
        # Model components
        self.tokenizer = None
        self.model = None
        
        logger.info(f"Initialized HuggingFace model: {self.model_name} on {self.device}")
    
    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Hugging Face transformers"""
        if not self.validate_input(prompt, system_prompt):
            raise ValueError("Invalid input provided")
        
        if not self.is_available():
            raise RuntimeError(f"HuggingFace model {self.model_name} is not loaded")
        
        try:
            # Combine system prompt and user prompt
            full_prompt = self._format_prompt(system_prompt, prompt)
            
            # Tokenize input
            inputs = self.tokenizer.encode(
                full_prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=self.context_length
            )
            
            if self.device != 'cpu':
                inputs = inputs.to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=self.max_length,
                    temperature=self.temperature,
                    do_sample=self.do_sample,
                    top_p=self.top_p,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.shape[1]:], 
                skip_special_tokens=True
            ).strip()
            
            logger.debug(f"Generated response length: {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")
    
    def _format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format prompts according to model's expected format"""
        # Different models may require different formatting
        if "llama" in self.model_name.lower():
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_prompt} [/INST]"
        elif "mistral" in self.model_name.lower():
            return f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"
        else:
            # Generic format
            return f"System: {system_prompt}\n\nUser: {user_prompt}\nAssistant:"
    
    def is_available(self) -> bool:
        """Check if model and tokenizer are loaded"""
        return (self.tokenizer is not None and 
                self.model is not None and 
                self._is_loaded)
    
    def load_model(self) -> bool:
        """Load HuggingFace model and tokenizer"""
        try:
            # Import here to avoid dependency issues if transformers not installed
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            logger.info(f"Loading HuggingFace model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device != 'cpu' else torch.float32,
                device_map=self.device if self.device != 'cpu' else None,
                trust_remote_code=True
            )
            
            if self.device != 'cpu':
                self.model = self.model.to(self.device)
            
            self.model.eval()  # Set to evaluation mode
            self._is_loaded = True
            
            logger.info(f"Successfully loaded HuggingFace model: {self.model_name}")
            return True
            
        except ImportError as e:
            logger.error(f"Required dependencies not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model {self.model_name}: {e}")
            return False
    
    def unload_model(self) -> bool:
        """Unload model to free memory"""
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None
            
            # Clear GPU cache if using CUDA
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            self._is_loaded = False
            logger.info(f"Unloaded HuggingFace model: {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload HuggingFace model: {e}")
            return False
