# Distribution Service - LinkedIn Publisher
# src/distribution/platforms/linkedin_publisher.py

import logging
import asyncio
import os
import json
import time
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from urllib.parse import urlencode

class LinkedInPublisher:
    """
    LinkedIn content publishing service.
    Uses LinkedIn's API for posting content.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("distribution.linkedin")
        
        # Configuration
        self.api_base_url = "https://api.linkedin.com/v2"
        self.auth_base_url = "https://www.linkedin.com/oauth/v2"
        self.access_token = config.get("access_token", os.environ.get("LINKEDIN_ACCESS_TOKEN"))
        self.refresh_token = config.get("refresh_token", os.environ.get("LINKEDIN_REFRESH_TOKEN"))
        self.client_id = config.get("client_id", os.environ.get("LINKEDIN_CLIENT_ID"))
        self.client_secret = config.get("client_secret", os.environ.get("LINKEDIN_CLIENT_SECRET"))
        self.author_urn = config.get("author_urn", os.environ.get("LINKEDIN_AUTHOR_URN"))
        
        # For enterprise clients using organization pages
        self.organization_id = config.get("organization_id", os.environ.get("LINKEDIN_ORG_ID"))
        
        # Rate limiting parameters
        self.rate_limit = config.get("rate_limit", 3)  # Requests per minute
        self.last_request_time = 0
        
        # Validate required configuration
        if not self.client_id or not self.client_secret:
            self.logger.warning("LinkedIn client_id or client_secret not provided")
            
        if not self.author_urn:
            self.logger.warning("LinkedIn author_urn not provided, posts will be created for the authenticated user")
            
        # HTTP client with timeouts
        self.timeout = httpx.Timeout(10.0)
        
    async def publish_post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a text post to LinkedIn
        
        Args:
            content: Dictionary containing post data
            
        Returns:
            Dictionary with result information
        """
        if not self.access_token:
            await self._refresh_access_token()
            if not self.access_token:
                return {"success": False, "error": "No access token available"}
                
        # Get the post text
        post_text = content.get("linkedin_text", content.get("text", ""))
        if not post_text:
            return {"success": False, "error": "No content provided for LinkedIn post"}
            
        # Create the post
        return await self._create_text_post(post_text)
        
    async def publish_article(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish an article to LinkedIn
        This requires LinkedIn API partner access, not available to all developers
        
        Args:
            content: Dictionary containing article data
            
        Returns:
            Dictionary with result information
        """
        self.logger.warning("LinkedIn article publishing requires partner API access, not available to all developers")
        return {"success": False, "error": "LinkedIn article publishing not implemented"}
        
    async def _create_text_post(self, text: str) -> Dict[str, Any]:
        """
        Create a text post on LinkedIn
        
        Args:
            text: The text content to post
            
        Returns:
            Dictionary with result information
        """
        # Enforce rate limiting
        await self._rate_limit_delay()
        
        # Determine if posting as person or organization
        author = self.author_urn
        if not author and self.organization_id:
            author = f"urn:li:organization:{self.organization_id}"
        elif not author:
            # Get the current user's URN
            user_info = await self._get_current_user_info()
            if not user_info.get("success", False):
                return user_info
            author = user_info.get("user_urn")
            
        # Build the request payload
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/ugcPosts",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 201:
                    post_id = response.headers.get("x-restli-id", "unknown")
                    self.logger.info(f"Successfully published LinkedIn post with ID: {post_id}")
                    return {
                        "success": True,
                        "post_id": post_id,
                        "platform": "linkedin",
                        "published_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    error_message = f"LinkedIn API error: {response.status_code} - {response.text}"
                    self.logger.error(error_message)
                    
                    # Check for token expiration
                    if response.status_code == 401:
                        # Try to refresh the token and retry
                        refresh_result = await self._refresh_access_token()
                        if refresh_result.get("success", False):
                            self.logger.info("Access token refreshed, retrying post")
                            return await self._create_text_post(text)
                            
                    return {
                        "success": False,
                        "error": error_message,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            error_message = f"Error publishing LinkedIn post: {str(e)}"
            self.logger.error(error_message)
            return {"success": False, "error": error_message}
            
    async def _get_current_user_info(self) -> Dict[str, Any]:
        """
        Get information about the currently authenticated user
        
        Returns:
            Dictionary with user information
        """
        await self._rate_limit_delay()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base_url}/me",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    user_id = data.get("id")
                    if user_id:
                        user_urn = f"urn:li:person:{user_id}"
                        return {
                            "success": True,
                            "user_id": user_id,
                            "user_urn": user_urn
                        }
                    else:
                        return {
                            "success": False,
                            "error": "User ID not found in response"
                        }
                else:
                    error_message = f"LinkedIn API error: {response.status_code} - {response.text}"
                    self.logger.error(error_message)
                    return {
                        "success": False,
                        "error": error_message,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            error_message = f"Error getting LinkedIn user info: {str(e)}"
            self.logger.error(error_message)
            return {"success": False, "error": error_message}
            
    async def _refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the LinkedIn access token using the refresh token
        
        Returns:
            Dictionary with refresh result
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return {
                "success": False,
                "error": "Missing refresh token, client ID, or client secret"
            }
            
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_base_url}/accessToken",
                    data=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    new_refresh_token = data.get("refresh_token")
                    
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                        
                    self.logger.info("Successfully refreshed LinkedIn access token")
                    return {"success": True}
                else:
                    error_message = f"LinkedIn token refresh error: {response.status_code} - {response.text}"
                    self.logger.error(error_message)
                    return {
                        "success": False,
                        "error": error_message,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            error_message = f"Error refreshing LinkedIn token: {str(e)}"
            self.logger.error(error_message)
            return {"success": False, "error": error_message}
            
    async def _rate_limit_delay(self):
        """
        Enforce API rate limits by adding delays between requests
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # LinkedIn's rate limits are per-minute, so we'll pace ourselves
        min_interval = 60.0 / self.rate_limit  # seconds between requests
        
        if time_since_last < min_interval:
            delay = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: Waiting {delay:.2f} seconds before LinkedIn API request")
            await asyncio.sleep(delay)
            
        self.last_request_time = time.time()