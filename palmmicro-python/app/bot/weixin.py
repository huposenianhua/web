"""WeChat Official Account implementation.

Translated from PHP weixin.php.
Handles WeChat message processing and stock queries.
"""

import hashlib
from typing import Optional

from app.services.stockbot import stock_bot_get_str


BOT_EOL = '\r\n'
MAX_BOT_MSG_LEN = 2048

WX_MSG_TYPE_EVENT = 'event'
WX_MSG_TYPE_FILE = 'file'
WX_MSG_TYPE_IMAGE = 'image'
WX_MSG_TYPE_LINK = 'link'
WX_MSG_TYPE_LOCATION = 'location'
WX_MSG_TYPE_SHORTVIDEO = 'shortvideo'
WX_MSG_TYPE_TEXT = 'text'
WX_MSG_TYPE_VOICE = 'voice'


class WeixinCallback:
    """Base WeChat callback handler."""
    
    def __init__(self, token: str):
        self.token = token
    
    def get_version(self) -> str:
        """Get bot version."""
        return '版本208'
    
    def run(self, signature: str, timestamp: str, nonce: str, echostr: str = None, body: str = None) -> str:
        """Main entry point."""
        if self.check_signature(signature, timestamp, nonce):
            if echostr:
                return echostr
            else:
                return self.response_msg(body)
        return ''
    
    def response_msg(self, post_str: str) -> str:
        """Handle incoming message."""
        if not post_str:
            return ''
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(post_str)
            
            from_username = root.find('FromUserName').text if root.find('FromUserName') is not None else ''
            to_username = root.find('ToUserName').text if root.find('ToUserName') is not None else ''
            msg_type = root.find('MsgType').text if root.find('MsgType') is not None else ''
            
            content_str = self.handle_message(root)
            
            return self._build_response_xml(from_username, to_username, content_str)
        
        except Exception:
            return ''
    
    def _build_response_xml(self, from_username: str, to_username: str, content: str) -> str:
        """Build XML response."""
        import time
        timestamp = str(int(time.time()))
        
        return f'''<xml>
<ToUserName><![CDATA[{from_username}]]></ToUserName>
<FromUserName><![CDATA[{to_username}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>'''
    
    def check_signature(self, signature: str, timestamp: str, nonce: str) -> bool:
        """Verify WeChat signature."""
        if not self.token:
            return False
        
        if not signature or not timestamp or not nonce:
            return False
        
        arr = [self.token, timestamp, nonce]
        arr.sort()
        str_sign = ''.join(arr)
        return hashlib.sha1(str_sign.encode()).hexdigest() == signature
    
    def handle_message(self, root) -> str:
        """Handle different message types."""
        from_username = root.find('FromUserName').text if root.find('FromUserName') is not None else ''
        msg_type = root.find('MsgType').text if root.find('MsgType') is not None else ''
        
        handlers = {
            WX_MSG_TYPE_TEXT: self._handle_text,
            WX_MSG_TYPE_VOICE: self._handle_voice,
            WX_MSG_TYPE_EVENT: self._handle_event,
            WX_MSG_TYPE_IMAGE: lambda r, u: self.get_unknown_text('未知图像', u),
            WX_MSG_TYPE_SHORTVIDEO: lambda r, u: self.get_unknown_text('未知小视频', u),
            WX_MSG_TYPE_LOCATION: lambda r, u: self.get_unknown_text('未知位置', u),
            WX_MSG_TYPE_LINK: lambda r, u: self.get_unknown_text('未知链接', u),
            WX_MSG_TYPE_FILE: lambda r, u: self.get_unknown_text('未知文件', u),
        }
        
        handler = handlers.get(msg_type, lambda r, u: self.get_unknown_text(f'未知信息类型{msg_type}', u))
        return handler(root, from_username) + self.get_version()
    
    def _handle_text(self, root, user_name: str) -> str:
        """Handle text message."""
        content = root.find('Content').text if root.find('Content') is not None else ''
        return self.on_text(content.strip(), user_name)
    
    def _handle_voice(self, root, user_name: str) -> str:
        """Handle voice message."""
        recognition = root.find('Recognition').text if root.find('Recognition') is not None else ''
        if recognition:
            return self.on_text(recognition.strip(), user_name)
        return self.get_unknown_text('未知语音', user_name)
    
    def _handle_event(self, root, user_name: str) -> str:
        """Handle event message."""
        event = root.find('Event').text if root.find('Event') is not None else ''
        if event == 'CLICK':
            return self.on_event_menu('', user_name)
        return self.on_event(event, user_name)
    
    def get_unknown_text(self, contents: str, user_name: str) -> str:
        """Get unknown message response."""
        return f'{contents}{BOT_EOL}没有匹配到信息.'
    
    def on_text(self, text: str, user_name: str) -> str:
        """Handle text message."""
        return f'{text}{BOT_EOL}'
    
    def on_voice(self, contents: str, user_name: str) -> str:
        """Handle voice message."""
        if contents:
            return self.on_text(contents, user_name)
        return self.get_unknown_text('未知语音', user_name)
    
    def on_event(self, contents: str, user_name: str) -> str:
        """Handle event."""
        if contents == 'subscribe':
            return f'欢迎订阅, 本账号为自动回复, 请用语音或者键盘输入要查找的内容.{BOT_EOL}'
        elif contents == 'unsubscribe':
            return '再见'
        elif contents == 'MASSSENDJOBFINISH':
            return '收到群发完毕'
        return f'未知{contents}'
    
    def on_event_menu(self, menu: str, user_name: str) -> str:
        """Handle menu event."""
        return self.get_unknown_text('未知自定义菜单点击事件', user_name)
    
    def on_image(self, url: str, user_name: str) -> str:
        """Handle image message."""
        return self.get_unknown_text('未知图像', user_name)
    
    def on_short_video(self, contents: str, user_name: str) -> str:
        """Handle short video message."""
        return self.get_unknown_text('未知小视频', user_name)
    
    def on_location(self, contents: str, user_name: str) -> str:
        """Handle location message."""
        return self.get_unknown_text('未知位置', user_name)
    
    def on_link(self, contents: str, user_name: str) -> str:
        """Handle link message."""
        return self.get_unknown_text('未知链接', user_name)
    
    def on_file(self, contents: str, user_name: str) -> str:
        """Handle file message."""
        return self.get_unknown_text('未知文件', user_name)
    
    def on_unknown_type(self, msg_type: str, user_name: str) -> str:
        """Handle unknown message type."""
        return self.get_unknown_text(f'未知信息类型{msg_type}', user_name)


class WeixinStock(WeixinCallback):
    """WeChat bot for stock queries."""
    
    def __init__(self, token: str):
        super().__init__(token)
    
    def on_text(self, text: str, user_name: str) -> str:
        """Handle stock query text."""
        if result := stock_bot_get_str(text):
            return result
        return self.get_unknown_text(text, user_name)