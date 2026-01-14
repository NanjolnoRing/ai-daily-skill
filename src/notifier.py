"""
邮件通知模块
发送任务执行结果的邮件通知
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from src.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    NOTIFICATION_TO,
    GITHUB_PAGES_URL
)


class EmailNotifier:
    """邮件通知器"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        to_email: str = None
    ):
        """
        初始化邮件通知器

        Args:
            host: SMTP 服务器地址
            port: SMTP 端口
            user: 发件邮箱
            password: 邮箱密码/授权码
            to_email: 收件邮箱
        """
        self.host = host or SMTP_HOST
        self.port = port or SMTP_PORT
        self.user = user or SMTP_USER
        self.password = password or SMTP_PASSWORD
        self.to_email = to_email or NOTIFICATION_TO

        # GitHub Actions 环境变量（用于生成日志链接）
        self.github_repository = os.getenv("GITHUB_REPOSITORY")
        self.github_run_id = os.getenv("GITHUB_RUN_ID")
        self.github_server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")

    def _get_actions_url(self) -> Optional[str]:
        """获取 GitHub Actions 运行日志链接"""
        if self.github_repository and self.github_run_id:
            return f"{self.github_server_url}/{self.github_repository}/actions/runs/{self.github_run_id}"
        return None

    def _get_page_url(self, date: str) -> str:
        """获取生成的页面 URL"""
        base_url = GITHUB_PAGES_URL or os.getenv("GITHUB_PAGES_URL", "")
        if base_url:
            return f"{base_url.rstrip('/')}/{date}.html"
        return f"{date}.html"

    def send_success(self, date: str, summary_count: int) -> bool:
        """
        发送成功通知

        Args:
            date: 日期
            summary_count: 资讯条数

        Returns:
            是否发送成功
        """
        page_url = self._get_page_url(date)
        subject = f"✅ AI Daily 生成成功 - {date}"

        body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
    <div style="max-width: 600px; margin: 40px auto; padding: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08);">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #42A5F5, #1A3A52); padding: 30px; text-align: center;">
            <span style="font-size: 48px;">✅</span>
            <h1 style="color: white; margin: 16px 0 0; font-size: 24px;">AI Daily 生成成功</h1>
        </div>

        <!-- 内容 -->
        <div style="padding: 30px;">
            <div style="background: #E3F2FD; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <p style="margin: 5px 0; color: #1565C0;"><strong>📅 日期:</strong> {date}</p>
                <p style="margin: 5px 0; color: #1565C0;"><strong>📊 资讯条数:</strong> {summary_count} 条</p>
            </div>

            <p style="color: #555; margin-bottom: 16px;"><strong>🔗 访问链接:</strong></p>
            <a href="{page_url}" style="display: block; padding: 14px 24px; background: #42A5F5; color: white; text-decoration: none; border-radius: 8px; text-align: center; font-weight: 500;">查看 AI Daily 页面</a>

            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

            <p style="color: #999; font-size: 12px; margin: 0;">
                此邮件由 GitHub Actions 自动发送<br>
                时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
            </p>
        </div>
    </div>
</body>
</html>
"""

        return self._send(subject, body)

    def send_empty(self, date: str, reason: str = "RSS中未找到对应日期的资讯") -> bool:
        """
        发送空数据通知

        Args:
            date: 日期
            reason: 原因

        Returns:
            是否发送成功
        """
        subject = f"📭 AI Daily 无数据 - {date}"
        actions_url = self._get_actions_url()

        actions_button = ""
        if actions_url:
            actions_button = f'<a href="{actions_url}" style="display: inline-block; padding: 10px 20px; background: #FFA726; color: white; text-decoration: none; border-radius: 6px;">查看 Actions 日志</a>'

        body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5;">
    <div style="max-width: 600px; margin: 40px auto; padding: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08);">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #FFA726, #3D2415); padding: 30px; text-align: center;">
            <span style="font-size: 48px;">📭</span>
            <h1 style="color: white; margin: 16px 0 0; font-size: 24px;">今日暂无资讯</h1>
        </div>

        <!-- 内容 -->
        <div style="padding: 30px;">
            <div style="background: #FFF3E0; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <p style="margin: 5px 0; color: #E65100;"><strong>📅 目标日期:</strong> {date}</p>
                <p style="margin: 5px 0; color: #E65100;"><strong>📝 原因:</strong> {reason}</p>
            </div>

            <div style="text-align: center;">
                {actions_button}
            </div>

            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

            <p style="color: #999; font-size: 12px; margin: 0; text-align: center;">
                此邮件由 GitHub Actions 自动发送
            </p>
        </div>
    </div>
</body>
</html>
"""

        return self._send(subject, body)

    def send_error(self, date: str, error: str) -> bool:
        """
        发送错误通知（带 GitHub Actions 日志链接）

        Args:
            date: 日期
            error: 错误信息

        Returns:
            是否发送成功
        """
        subject = f"❌ AI Daily 生成失败 - {date}"
        actions_url = self._get_actions_url()

        actions_section = ""
        if actions_url:
            actions_section = f'''
                <div style="text-align: center; margin-top: 24px;">
                    <a href="{actions_url}" style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #F06292, #E91E63); color: white; text-decoration: none; border-radius: 8px; font-weight: 500;">🔍 查看 GitHub Actions 日志</a>
                </div>
            '''

        body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #fafafa;">
    <div style="max-width: 600px; margin: 40px auto; padding: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08);">
        <!-- 头部 -->
        <div style="background: linear-gradient(135deg, #F06292, #C62828); padding: 30px; text-align: center;">
            <span style="font-size: 48px;">❌</span>
            <h1 style="color: white; margin: 16px 0 0; font-size: 24px;">生成过程出错</h1>
        </div>

        <!-- 内容 -->
        <div style="padding: 30px;">
            <div style="background: #FFEBEE; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                <p style="margin: 5px 0; color: #C62828;"><strong>📅 目标日期:</strong> {date}</p>
                <p style="margin: 5px 0; color: #C62828;"><strong>⏰ 时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>

            <p style="color: #555; margin-bottom: 12px;"><strong>错误信息:</strong></p>
            <pre style="background: #263238; color: #ECEFF1; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5; margin-bottom: 20px;">{self._escape_html(error)}</pre>

            {actions_section}

            <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

            <p style="color: #999; font-size: 12px; margin: 0; text-align: center;">
                请检查 GitHub Actions 日志获取详细信息
            </p>
        </div>
    </div>
</body>
</html>
"""

        return self._send(subject, body)

    def _send(self, subject: str, html_body: str) -> bool:
        """
        发送邮件的底层方法

        Args:
            subject: 邮件主题
            html_body: HTML 邮件正文

        Returns:
            是否发送成功
        """
        # 检查配置
        if not all([self.host, self.user, self.password, self.to_email]):
            print("⚠️ 邮件配置不完整，跳过发送")
            print(f"   Host: {bool(self.host)}")
            print(f"   User: {bool(self.user)}")
            print(f"   Password: {bool(self.password)}")
            print(f"   To: {bool(self.to_email)}")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = self.to_email

            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            print(f"✅ 邮件已发送: {subject}")
            return True

        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False

    def _escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))


def send_success_email(date: str, summary_count: int) -> bool:
    """便捷函数：发送成功通知"""
    notifier = EmailNotifier()
    return notifier.send_success(date, summary_count)


def send_empty_email(date: str, reason: str = "") -> bool:
    """便捷函数：发送空数据通知"""
    notifier = EmailNotifier()
    return notifier.send_empty(date, reason)


def send_error_email(date: str, error: str) -> bool:
    """便捷函数：发送错误通知"""
    notifier = EmailNotifier()
    return notifier.send_error(date, error)
