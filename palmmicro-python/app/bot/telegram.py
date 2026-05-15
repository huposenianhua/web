"""Telegram Bot implementation.

Translated from PHP telegram.php.
Handles Telegram bot message processing and stock queries.
"""

import json
import urllib.parse

from app.services.stockbot import stock_bot_get_str


BOT_EOL = '\r\n'
MAX_BOT_MSG_LEN = 2048


class TelegramCallback:
    """Base Telegram callback handler."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_url = f'https://api.telegram.org/bot{token}/'
    
    def get_version(self) -> str:
        """Get bot version."""
        return '版本041'
    
    def set_webhook(self, url: str):
        """Set webhook URL."""
        webhook_url = f'{self.api_url}setWebhook?url={urllib.parse.quote(url)}'
        pass
    
    def direct_reply(self, method: str, parameters: dict = None):
        """Direct reply with JSON payload."""
        if not isinstance(method, str):
            return False
        
        if parameters is None:
            parameters = {}
        elif not isinstance(parameters, dict):
            return False
        
        parameters['method'] = method
        payload = json.dumps(parameters)
        return payload
    
    def reply_text(self, text: str, message_id: str, chat_id: str) -> str:
        """Reply to a message with text."""
        return self.direct_reply('sendMessage', {
            'chat_id': chat_id,
            'reply_to_message_id': message_id,
            'text': text
        })
    
    def _send_text(self, text: str, chat_id: str):
        """Send text message to chat."""
        url = f'{self.api_url}sendMessage?text={urllib.parse.quote(text)}&chat_id={chat_id}'
        pass
    
    def debug(self, text: str, admin_chat_id: str = '992671436'):
        """Send debug message to admin."""
        self._send_text(text, admin_chat_id)
    
    def on_text(self, text: str, message_id: str, chat_id: str):
        """Handle incoming text message."""
        self._send_text(text, chat_id)
    
    def _process_message(self, message: dict):
        """Process incoming message."""
        if 'message_id' not in message:
            return
        
        message_id = message['message_id']
        
        if 'chat' not in message:
            return
        
        chat_id = message['chat']['id']
        
        if 'text' in message:
            text = message['text']
            
            if text.startswith('/'):
                command = text[1:].strip()
                if command == 'start':
                    return
                elif command == 'stop':
                    return
            
            self.on_text(text, message_id, chat_id)
    
    def run(self, body: dict):
        """Main entry point for processing updates."""
        if 'message' in body:
            self._process_message(body['message'])


class TelegramStock(TelegramCallback):
    """Telegram bot for stock queries."""
    
    def __init__(self, token: str):
        super().__init__(token)
    
    def on_text(self, text: str, message_id: str, chat_id: str) -> str:
        """Handle stock query text."""
        version = self.get_version()
        
        if result := stock_bot_get_str(text):
            result += version
            return self.reply_text(result, message_id, chat_id)
        else:
            self.debug(f'未知查询：{text}')
            return None