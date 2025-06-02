# Telegram Bot for Monitoring
# src/monitoring/modules/telegram_bot.py

import logging
import asyncio
import os
import json
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
import telegram
from telegram import Update, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)

class MonitoringBot:
    """Telegram bot for system monitoring and status updates"""
    
    def __init__(self, config: Dict[str, Any], service_callbacks: Dict[str, Callable] = None):
        self.logger = logging.getLogger("monitoring.telegram")
        
        # Configuration
        self.token = config.get("telegram_token", os.environ.get("TELEGRAM_BOT_TOKEN"))
        if not self.token:
            raise ValueError("Telegram bot token not provided")
            
        self.allowed_user_ids = config.get("allowed_user_ids", [])
        self.allowed_chat_ids = config.get("allowed_chat_ids", [])
        
        # Convert string IDs to integers if needed
        self.allowed_user_ids = [int(uid) if isinstance(uid, str) else uid for uid in self.allowed_user_ids]
        self.allowed_chat_ids = [int(cid) if isinstance(cid, str) else cid for cid in self.allowed_chat_ids]
        
        # Status information
        self.system_status = {
            "status": "initializing",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "services": {},
            "metrics": {}
        }
        
        # Service callbacks for dynamic status information
        self.service_callbacks = service_callbacks or {}
        
        # Initialize the bot application
        self.application = None
        
    async def start(self):
        """Start the Telegram bot"""
        try:
            # Create the application
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("metrics", self.cmd_metrics))
            self.application.add_handler(CommandHandler("services", self.cmd_services))
            
            # Start the bot
            self.logger.info("Starting Telegram bot")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.system_status["status"] = "running"
            self.system_status["last_update"] = datetime.now(timezone.utc).isoformat()
            self.logger.info("Telegram bot started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot: {e}")
            raise
            
    async def stop(self):
        """Stop the Telegram bot"""
        if self.application:
            self.logger.info("Stopping Telegram bot")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("Telegram bot stopped")
            
    async def send_message(self, message: str, chat_id: int = None, parse_mode: str = ParseMode.HTML) -> bool:
        """
        Send a message to a specific chat or all allowed chats
        
        Args:
            message: The message to send
            chat_id: Optional specific chat ID to send to
            parse_mode: Parse mode for message formatting
            
        Returns:
            True if message was sent, False otherwise
        """
        if chat_id is not None:
            # Send to specific chat
            if chat_id not in self.allowed_chat_ids:
                self.logger.warning(f"Attempted to send message to unauthorized chat ID: {chat_id}")
                return False
                
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to send message to chat {chat_id}: {e}")
                return False
                
        else:
            # Send to all allowed chats
            success = False
            for allowed_chat in self.allowed_chat_ids:
                try:
                    await self.application.bot.send_message(
                        chat_id=allowed_chat,
                        text=message,
                        parse_mode=parse_mode
                    )
                    success = True
                    
                except Exception as e:
                    self.logger.error(f"Failed to send message to chat {allowed_chat}: {e}")
                    
            return success
            
    async def broadcast_status_update(self, status: Dict[str, Any]) -> bool:
        """
        Broadcast a status update to all allowed chats
        
        Args:
            status: Status information to broadcast
            
        Returns:
            True if message was broadcast to at least one chat, False otherwise
        """
        # Update internal status
        self.system_status.update(status)
        self.system_status["last_update"] = datetime.now(timezone.utc).isoformat()
        
        # Format status message
        status_type = status.get("type", "info")
        status_message = status.get("message", "Status update")
        details = status.get("details", {})
        
        if status_type == "alert":
            emoji = "🚨"
        elif status_type == "warning":
            emoji = "⚠️"
        elif status_type == "success":
            emoji = "✅"
        else:
            emoji = "ℹ️"
            
        message = f"{emoji} <b>{status_message}</b>\n\n"
        
        if details:
            for key, value in details.items():
                if isinstance(value, dict) or isinstance(value, list):
                    value_str = json.dumps(value, indent=2)
                    message += f"<b>{key}:</b>\n<pre>{value_str}</pre>\n"
                else:
                    message += f"<b>{key}:</b> {value}\n"
                    
        message += f"\n<i>Updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        # Send to all chats
        return await self.send_message(message)
        
    async def update_service_status(self, service_name: str, status: Dict[str, Any]):
        """
        Update the status of a specific service
        
        Args:
            service_name: Name of the service
            status: Status information for the service
        """
        # Update service status
        self.system_status["services"][service_name] = {
            **status,
            "last_update": datetime.now(timezone.utc).isoformat()
        }
        
        # Update overall system status
        all_services = self.system_status["services"].values()
        
        # Check for service errors
        service_errors = [
            s for s in all_services 
            if s.get("status") == "error" or s.get("status") == "critical"
        ]
        
        if service_errors:
            self.system_status["status"] = "degraded"
        else:
            self.system_status["status"] = "running"
            
        self.system_status["last_update"] = datetime.now(timezone.utc).isoformat()
        
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Update system metrics
        
        Args:
            metrics: Metrics data to update
        """
        self.system_status["metrics"] = {
            **self.system_status.get("metrics", {}),
            **metrics,
            "last_update": datetime.now(timezone.utc).isoformat()
        }
        
    async def is_authorized(self, update: Update) -> bool:
        """
        Check if a user is authorized to use the bot
        
        Args:
            update: Telegram update object
            
        Returns:
            True if user is authorized, False otherwise
        """
        if not update.effective_user:
            return False
            
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # If we have no allowed users/chats specified, default to secure (deny all)
        if not self.allowed_user_ids and not self.allowed_chat_ids:
            self.logger.warning("No allowed user IDs or chat IDs configured, denying access")
            return False
            
        # Check if user or chat is allowed
        is_allowed = (
            user_id in self.allowed_user_ids or
            chat_id in self.allowed_chat_ids
        )
        
        if not is_allowed:
            self.logger.warning(
                f"Unauthorized access attempt - User ID: {user_id}, Chat ID: {chat_id}, "
                f"Username: {update.effective_user.username}"
            )
            
        return is_allowed
        
    # Command handlers
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
        if not await self.is_authorized(update):
            return
            
        await update.message.reply_html(
            f"👋 <b>Welcome to the Niche Content Syndication Monitor</b>\n\n"
            f"This bot helps you monitor the status of your content syndication system.\n\n"
            f"Use /help to see available commands."
        )
        
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help command"""
        if not await self.is_authorized(update):
            return
            
        await update.message.reply_html(
            f"<b>Available Commands</b>\n\n"
            f"/status - Show current system status\n"
            f"/services - List all services and their status\n"
            f"/metrics - Show system performance metrics\n"
            f"/help - Show this help message"
        )
        
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /status command"""
        if not await self.is_authorized(update):
            return
            
        # Get fresh service status if available
        for service_name, callback in self.service_callbacks.items():
            try:
                service_status = await callback()
                self.system_status["services"][service_name] = service_status
            except Exception as e:
                self.logger.error(f"Error getting status for {service_name}: {e}")
                
        # Format status message
        status = self.system_status.get("status", "unknown")
        last_update = self.system_status.get("last_update", "never")
        
        if status == "running":
            emoji = "✅"
        elif status == "degraded":
            emoji = "⚠️"
        elif status == "error":
            emoji = "🚨"
        else:
            emoji = "❓"
            
        # Format timestamp for display
        if isinstance(last_update, str):
            try:
                last_update_dt = datetime.fromisoformat(last_update)
                last_update = last_update_dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
                
        message = f"{emoji} <b>System Status: {status.upper()}</b>\n\n"
        
        # Add service summary
        services = self.system_status.get("services", {})
        if services:
            message += "<b>Services:</b>\n"
            for service_name, service_data in services.items():
                service_status = service_data.get("status", "unknown")
                
                if service_status == "running":
                    service_emoji = "✅"
                elif service_status == "degraded":
                    service_emoji = "⚠️"
                elif service_status in ("error", "critical"):
                    service_emoji = "🚨"
                else:
                    service_emoji = "❓"
                    
                message += f"{service_emoji} {service_name}: {service_status}\n"
        else:
            message += "No services configured.\n"
            
        message += f"\n<i>Last updated: {last_update}</i>"
        
        await update.message.reply_html(message)
        
    async def cmd_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /services command"""
        if not await self.is_authorized(update):
            return
            
        # Get fresh service status if available
        for service_name, callback in self.service_callbacks.items():
            try:
                service_status = await callback()
                self.system_status["services"][service_name] = service_status
            except Exception as e:
                self.logger.error(f"Error getting status for {service_name}: {e}")
                
        # Format services message
        services = self.system_status.get("services", {})
        if not services:
            await update.message.reply_html("No services configured.")
            return
            
        message = "<b>Service Status Details</b>\n\n"
        
        for service_name, service_data in services.items():
            service_status = service_data.get("status", "unknown")
            
            if service_status == "running":
                service_emoji = "✅"
            elif service_status == "degraded":
                service_emoji = "⚠️"
            elif service_status in ("error", "critical"):
                service_emoji = "🚨"
            else:
                service_emoji = "❓"
                
            message += f"{service_emoji} <b>{service_name}</b>: {service_status}\n"
            
            # Add details if available
            if "details" in service_data and service_data["details"]:
                details = service_data["details"]
                if isinstance(details, dict):
                    for key, value in details.items():
                        message += f"  - {key}: {value}\n"
                elif isinstance(details, str):
                    message += f"  - {details}\n"
                    
            # Add last update time
            service_update = service_data.get("last_update")
            if service_update:
                try:
                    if isinstance(service_update, str):
                        service_update_dt = datetime.fromisoformat(service_update)
                        service_update = service_update_dt.strftime("%Y-%m-%d %H:%M:%S")
                    message += f"  <i>Updated: {service_update}</i>\n"
                except ValueError:
                    message += f"  <i>Updated: {service_update}</i>\n"
                    
            message += "\n"
            
        await update.message.reply_html(message)
        
    async def cmd_metrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /metrics command"""
        if not await self.is_authorized(update):
            return
            
        # Format metrics message
        metrics = self.system_status.get("metrics", {})
        if not metrics:
            await update.message.reply_html("No metrics available.")
            return
            
        message = "<b>System Metrics</b>\n\n"
        
        # Remove last_update from display
        metrics_copy = metrics.copy()
        metrics_copy.pop("last_update", None)
        
        # Format metrics data
        for category, values in metrics_copy.items():
            message += f"<b>{category}</b>\n"
            
            if isinstance(values, dict):
                for key, value in values.items():
                    message += f"  - {key}: {value}\n"
            else:
                message += f"  {values}\n"
                
            message += "\n"
            
        # Add last update time
        last_update = metrics.get("last_update")
        if last_update:
            try:
                if isinstance(last_update, str):
                    last_update_dt = datetime.fromisoformat(last_update)
                    last_update = last_update_dt.strftime("%Y-%m-%d %H:%M:%S")
                message += f"<i>Last updated: {last_update}</i>"
            except ValueError:
                message += f"<i>Last updated: {last_update}</i>"
                
        await update.message.reply_html(message)