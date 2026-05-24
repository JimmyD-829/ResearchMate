import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "noreply@researchmate.dev")
        
    async def send_password_reset_email(self, to_email: str, reset_link: str, user_nickname: str = "用户") -> dict:
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email send")
            return {"success": False, "message": "Email service not configured"}
        
        try:
            import resend
            
            resend.api_key = self.api_key
            
            params = {
                "from": f"ResearchMate <{self.from_email}>",
                "to": [to_email],
                "subject": "重置您的 ResearchMate 密码",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🔐 密码重置请求</h1>
                        </div>
                        <div class="content">
                            <p>您好 {user_nickname}，</p>
                            <p>我们收到了您重置 ResearchMate 账户密码的请求。请点击下方按钮重置密码：</p>
                            <a href="{reset_link}" class="button">重置密码</a>
                            <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
                            <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
                            <p><strong>⚠️ 此链接将在 1 小时后失效</strong></p>
                            <hr style="margin: 20px 0;">
                            <p>如果您没有发起此请求，请忽略此邮件，您的账户安全不受影响。</p>
                        </div>
                        <div class="footer">
                            <p>© 2024 ResearchMate. 智能财务分析平台</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Password reset email sent to {to_email}, ID: {response.get('id')}")
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "email_id": response.get('id')
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "message": str(e),
                "fallback": "reset_link_generated"
            }

email_service = EmailService()
