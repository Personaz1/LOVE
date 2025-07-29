"""
Image Analysis Module
Handles image processing with dedicated vision model and prompt
"""

import os
import logging
import google.generativeai as genai
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self):
        self.vision_model = None
        self.vision_prompt = """
You are an expert image analyzer. Your role is to:

1. **DESCRIBE VISUAL CONTENT** - Provide detailed, accurate descriptions of what you see
2. **IDENTIFY KEY ELEMENTS** - Note important objects, people, text, interfaces, colors, layout
3. **ANALYZE CONTEXT** - Understand the purpose and meaning of the image
4. **BE PRECISE** - Use specific details rather than vague descriptions
5. **STRUCTURE OUTPUT** - Organize your analysis clearly:
   - Main content/objects
   - Text and interface elements (for screenshots)
   - Visual style and mood
   - Technical details (resolution, quality, etc.)

**FOR SCREENSHOTS:**
- Describe the interface, buttons, text, layout
- Note any errors, warnings, or status messages
- Identify the application/website being shown

**FOR PHOTOS:**
- Describe people, objects, setting, lighting
- Note emotions, activities, relationships
- Mention composition, colors, mood

**FOR DOCUMENTS:**
- Transcribe readable text
- Note formatting, structure, key information
- Identify document type and purpose

Always be helpful and thorough in your analysis.
"""
        
        self._initialize_vision_model()
    
    def _initialize_vision_model(self):
        """Initialize the vision-capable model"""
        try:
            # Use the same initialization logic as AIClient
            from ai_client import AIClient
            ai_client = AIClient()
            
            # Find a vision-capable model from the available models
            for model_config in ai_client.models:
                if model_config.get('vision', False) or 'pro' in model_config['name'].lower():
                    try:
                        if model_config['model'] is None:
                            model_config['model'] = genai.GenerativeModel(model_config['name'])
                        self.vision_model = model_config['model']
                        logger.info(f"🔍 Using vision model: {model_config['name']}")
                        break
                    except Exception as e:
                        logger.warning(f"⚠️ Model {model_config['name']} not available: {e}")
                        continue
            
            if self.vision_model:
                logger.info(f"✅ Vision model initialized: {self.vision_model.model_name}")
            else:
                logger.error("❌ No vision-capable model available")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize vision model: {e}")
    
    def analyze_image(self, image_path: str, user_context: str = "") -> str:
        """
        Analyze an image using the dedicated vision model
        
        Args:
            image_path: Path to the image file
            user_context: Additional context from user (optional)
        
        Returns:
            Detailed analysis of the image
        """
        try:
            if not self.vision_model:
                return "❌ Vision model not available"
            
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"
            
            # Read image file
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Create image part for Gemini
            image_part = {
                "mime_type": self._get_mime_type(image_path),
                "data": image_data
            }
            
            # Build prompt with user context
            full_prompt = self.vision_prompt
            if user_context:
                full_prompt += f"\n\n**USER CONTEXT:** {user_context}\n\nPlease consider this context in your analysis."
            
            # Generate analysis
            response = self.vision_model.generate_content([full_prompt, image_part])
            
            if response.text:
                logger.info(f"✅ Image analysis completed using {self.vision_model.model_name}")
                return response.text
            else:
                return "❌ No response from vision model"
                
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {str(e)}")
            return f"❌ Image analysis failed: {str(e)}"
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            "vision_model": self.vision_model.model_name if self.vision_model else None,
            "api_key_set": bool(os.getenv('GEMINI_API_KEY')),
            "available": self.vision_model is not None
        }

# Global instance
image_analyzer = ImageAnalyzer() 