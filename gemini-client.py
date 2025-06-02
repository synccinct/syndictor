# Content Processing with Gemini Pro
# src/content-processor/modules/gemini_client.py

import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiProClient:
    """Client for interacting with Google's Gemini Pro API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("processor.gemini")
        
        # Configuration
        self.api_key = config.get("api_key", os.environ.get("GEMINI_API_KEY"))
        if not self.api_key:
            raise ValueError("Gemini API key not provided in config or environment variables")
            
        self.model_name = config.get("model_name", "gemini-pro")
        self.max_tokens = config.get("max_tokens", 8192)
        self.temperature = config.get("temperature", 0.7)
        self.top_p = config.get("top_p", 0.9)
        self.top_k = config.get("top_k", 40)
        self.rate_limit_pause = config.get("rate_limit_pause", 2.0)  # seconds to pause on rate limit
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 5.0)  # seconds between retries
        
        # Configure safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Initialize the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Create the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "max_output_tokens": self.max_tokens,
            },
            safety_settings=self.safety_settings
        )
        
    async def analyze_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze content and extract key information
        
        Args:
            content: Dictionary containing content data (title, text, etc.)
            
        Returns:
            Dictionary with analysis results
        """
        prompt = self._create_analysis_prompt(content)
        
        try:
            result = await self._generate_with_retry(prompt)
            analysis = self._parse_analysis_result(result)
            
            self.logger.info(f"Successfully analyzed content: {content.get('title', 'Untitled')}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def enhance_content(self, content: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance content based on analysis results
        
        Args:
            content: Original content dictionary
            analysis: Analysis results from analyze_content
            
        Returns:
            Dictionary with enhanced content
        """
        prompt = self._create_enhancement_prompt(content, analysis)
        
        try:
            result = await self._generate_with_retry(prompt)
            enhanced = self._parse_enhancement_result(result)
            
            # Combine with original content
            enhanced["original_title"] = content.get("title", "")
            enhanced["original_content"] = content.get("content", "")
            enhanced["original_url"] = content.get("url", "")
            enhanced["source_name"] = content.get("source_name", "")
            enhanced["enhanced_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(f"Successfully enhanced content: {content.get('title', 'Untitled')}")
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Error enhancing content: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def generate_social_posts(self, content: Dict[str, Any], platforms: List[str]) -> Dict[str, Any]:
        """
        Generate social media posts for different platforms
        
        Args:
            content: Content dictionary (enhanced or original)
            platforms: List of platforms to generate posts for (e.g., ["linkedin", "twitter"])
            
        Returns:
            Dictionary with posts for each platform
        """
        prompt = self._create_social_prompt(content, platforms)
        
        try:
            result = await self._generate_with_retry(prompt)
            posts = self._parse_social_result(result, platforms)
            
            self.logger.info(f"Generated social posts for {len(platforms)} platforms")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error generating social posts: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def _generate_with_retry(self, prompt: str) -> str:
        """
        Generate content with retry logic for handling rate limits and errors
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            The generated text result
        """
        for attempt in range(self.retry_attempts):
            try:
                # Call the Gemini API (needs to be async compatible)
                return await asyncio.to_thread(
                    self._call_gemini_api,
                    prompt
                )
                
            except Exception as e:
                if "rate limit" in str(e).lower() and attempt < self.retry_attempts - 1:
                    # Rate limit hit, pause and retry
                    self.logger.warning(f"Rate limit hit, pausing for {self.rate_limit_pause} seconds")
                    await asyncio.sleep(self.rate_limit_pause)
                    continue
                    
                if attempt < self.retry_attempts - 1:
                    # Other error, retry after delay
                    self.logger.warning(f"API error: {e}, retrying in {self.retry_delay} seconds")
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
                # All retries failed, raise the exception
                raise
                
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Make a synchronous call to the Gemini API
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            The generated text result
        """
        response = self.model.generate_content(prompt)
        return response.text
        
    def _create_analysis_prompt(self, content: Dict[str, Any]) -> str:
        """Create a prompt for content analysis"""
        title = content.get("title", "")
        text = content.get("content", "")
        source = content.get("source_name", "")
        
        return f"""
        You are an expert content analyst for a niche industry news syndication service.
        Analyze the following content from {source} and extract key information.
        
        TITLE: {title}
        
        CONTENT:
        {text}
        
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "summary": "Brief 2-3 sentence summary of the content",
            "key_points": ["List of 3-5 key points from the article"],
            "entities": ["Important people, companies, products, etc. mentioned"],
            "industry_relevance": "Assessment of how relevant this is to the industry (High/Medium/Low)",
            "sentiment": "Overall sentiment of the article (Positive/Negative/Neutral)",
            "categories": ["List of relevant categories/tags"],
            "action_items": ["Potential action items for industry professionals"]
        }}
        
        Return ONLY the JSON without any additional text or explanation.
        """
        
    def _create_enhancement_prompt(self, content: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Create a prompt for content enhancement"""
        title = content.get("title", "")
        text = content.get("content", "")
        
        # Extract key elements from analysis
        summary = analysis.get("summary", "")
        key_points = analysis.get("key_points", [])
        key_points_text = "\n".join([f"- {point}" for point in key_points])
        
        return f"""
        You are an expert content editor for a niche industry news syndication service.
        Enhance the following content based on the provided analysis.
        
        ORIGINAL TITLE: {title}
        
        ORIGINAL CONTENT:
        {text}
        
        ANALYSIS SUMMARY: {summary}
        
        KEY POINTS:
        {key_points_text}
        
        Enhance this content by:
        1. Creating an improved, attention-grabbing title
        2. Writing a concise, engaging introduction (1-2 paragraphs)
        3. Restructuring and enhancing the main content while preserving all factual information
        4. Adding a conclusion with industry implications
        5. Adding section headings where appropriate
        
        Provide the enhanced content in JSON format with this structure:
        {{
            "enhanced_title": "Improved title",
            "introduction": "Engaging introduction paragraphs",
            "enhanced_content": "Full enhanced content with HTML formatting",
            "conclusion": "Added conclusion with industry implications",
            "suggested_hashtags": ["5-7 relevant hashtags"]
        }}
        
        Return ONLY the JSON without any additional text or explanation.
        """
        
    def _create_social_prompt(self, content: Dict[str, Any], platforms: List[str]) -> str:
        """Create a prompt for social media post generation"""
        title = content.get("enhanced_title", content.get("title", ""))
        intro = content.get("introduction", "")
        url = content.get("original_url", "")
        
        platforms_text = ", ".join(platforms)
        
        return f"""
        You are a social media expert for a niche industry news syndication service.
        Create platform-specific posts for the following content.
        
        TITLE: {title}
        
        INTRODUCTION:
        {intro}
        
        URL: {url}
        
        Create engaging social media posts for these platforms: {platforms_text}
        
        For each platform, follow these guidelines:
        - LinkedIn: Professional tone, 1-2 paragraphs, 3-5 hashtags, include URL
        - Twitter: Concise, engaging, under 280 characters, 1-2 hashtags, include URL
        - Telegram: Informative summary with key points, include URL
        
        Provide the posts in JSON format with this structure:
        {{
            "linkedin": "LinkedIn post content",
            "twitter": "Twitter post content",
            "telegram": "Telegram post content"
        }}
        
        Only include the platforms requested. Return ONLY the JSON without any additional text.
        """
        
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """Parse the analysis result from Gemini"""
        try:
            # Extract JSON from the result
            json_text = self._extract_json(result)
            return json.loads(json_text)
        except Exception as e:
            self.logger.error(f"Error parsing analysis result: {e}")
            return {"error": "Failed to parse analysis result"}
            
    def _parse_enhancement_result(self, result: str) -> Dict[str, Any]:
        """Parse the enhancement result from Gemini"""
        try:
            # Extract JSON from the result
            json_text = self._extract_json(result)
            return json.loads(json_text)
        except Exception as e:
            self.logger.error(f"Error parsing enhancement result: {e}")
            return {"error": "Failed to parse enhancement result"}
            
    def _parse_social_result(self, result: str, platforms: List[str]) -> Dict[str, Any]:
        """Parse the social media post generation result"""
        try:
            # Extract JSON from the result
            json_text = self._extract_json(result)
            parsed = json.loads(json_text)
            
            # Ensure we only have the requested platforms
            return {platform: parsed.get(platform, "") for platform in platforms if platform in parsed}
        except Exception as e:
            self.logger.error(f"Error parsing social result: {e}")
            return {"error": "Failed to parse social media post results"}
            
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain additional content"""
        try:
            # Check if the text is already valid JSON
            json.loads(text)
            return text
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            # Look for start and end braces
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = text[start_idx:end_idx+1]
                try:
                    # Validate that this is valid JSON
                    json.loads(json_text)
                    return json_text
                except json.JSONDecodeError:
                    pass
                    
            # If we get here, we couldn't extract valid JSON
            raise ValueError("Could not extract valid JSON from response")