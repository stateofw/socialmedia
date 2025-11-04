import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.core.config import settings


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL or settings.SMTP_USER

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address or list of addresses
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body (fallback)

        Returns:
            bool: True if sent successfully
        """

        if not self.smtp_host or not self.smtp_user:
            print("⚠️ Email not configured. Skipping email send.")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email

            # Handle multiple recipients
            if isinstance(to_email, list):
                msg["To"] = ", ".join(to_email)
                recipients = to_email
            else:
                msg["To"] = to_email
                recipients = [to_email]

            # Add text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, "plain")
                msg.attach(part1)

            part2 = MIMEText(body_html, "html")
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, recipients, msg.as_string())

            print(f"✅ Email sent to {recipients}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    async def notify_content_ready_for_review(
        self,
        team_email: str,
        client_name: str,
        content_id: int,
        topic: str,
        caption_preview: str,
    ) -> bool:
        """Notify team that content is ready for approval with Accept/Reject buttons."""

        subject = f"Content Ready for Review: {client_name}"

        # Create action URLs
        base_url = settings.FRONTEND_URL or "http://localhost:8000"
        review_url = f"{base_url}/admin/content/{content_id}"
        approve_url = f"{base_url}/api/v1/content/{content_id}/approve"
        reject_url = f"{base_url}/admin/content/{content_id}/reject"

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Content Ready for Review</h2>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
              <p><strong>Client:</strong> {client_name}</p>
              <p><strong>Topic:</strong> {topic}</p>
            </div>

            <div style="margin: 20px 0;">
              <p><strong>Caption Preview:</strong></p>
              <p style="font-style: italic; color: #555; background-color: #fafafa; padding: 15px; border-left: 3px solid #4CAF50;">
                {caption_preview[:200]}{"..." if len(caption_preview) > 200 else ""}
              </p>
            </div>

            <div style="margin: 30px 0; text-align: center;">
              <a href="{review_url}"
                 style="display: inline-block; background-color: #2196F3; color: white;
                        padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px;">
                📝 View Full Content
              </a>
            </div>

            <div style="margin: 30px 0; text-align: center; padding: 20px; background-color: #f9f9f9; border-radius: 5px;">
              <p style="margin-bottom: 15px;"><strong>Quick Actions:</strong></p>
              <a href="{approve_url}"
                 style="display: inline-block; background-color: #4CAF50; color: white;
                        padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 5px; font-weight: bold;">
                ✓ Approve & Publish
              </a>
              <a href="{reject_url}"
                 style="display: inline-block; background-color: #f44336; color: white;
                        padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 5px; font-weight: bold;">
                ✗ Reject & Provide Feedback
              </a>
            </div>

            <p style="color: #666; font-size: 14px; margin-top: 30px;">
              <strong>Note:</strong> Clicking "Approve" will automatically publish the content to all configured platforms.
              Clicking "Reject" will allow you to provide feedback for AI to regenerate improved content.
            </p>

            <p style="color: #888; font-size: 12px; margin-top: 40px;">
              This is an automated notification from Social Automation SaaS
            </p>
          </body>
        </html>
        """

        body_text = f"""
        Content Ready for Review

        Client: {client_name}
        Topic: {topic}

        Caption Preview:
        {caption_preview[:200]}{"..." if len(caption_preview) > 200 else ""}

        Actions:
        - Approve & Publish: {approve_url}
        - Reject & Provide Feedback: {reject_url}
        - View Full Content: {review_url}

        Note: Approving will automatically publish to all configured platforms.
        Rejecting will allow you to provide feedback for content regeneration.
        """

        return await self.send_email(team_email, subject, body_html, body_text)

    async def notify_content_published(
        self,
        client_email: str,
        client_name: str,
        topic: str,
        platforms: List[str],
        post_urls: dict,
    ) -> bool:
        """Notify client that their content has been published."""

        subject = f"Your Post is Live: {topic}"

        # Build platform links
        platform_links_html = ""
        for platform, url in post_urls.items():
            platform_links_html += f'<li><a href="{url}">{platform.title()}</a></li>'

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Your Post is Now Live! 🎉</h2>

            <p>Hi {client_name},</p>

            <p>Great news! We've published your post about "{topic}" to your social media platforms.</p>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
              <p><strong>Published to:</strong></p>
              <ul>
                {platform_links_html}
              </ul>
            </div>

            <p>Check out your posts using the links above. We're here if you need anything!</p>

            <p style="margin-top: 40px;">
              Best regards,<br>
              Your Social Media Team
            </p>

            <p style="color: #888; font-size: 12px; margin-top: 40px;">
              This is an automated notification from Social Automation SaaS
            </p>
          </body>
        </html>
        """

        platform_links_text = "\n".join([f"- {platform.title()}: {url}" for platform, url in post_urls.items()])

        body_text = f"""
        Your Post is Now Live!

        Hi {client_name},

        Great news! We've published your post about "{topic}" to your social media platforms.

        Published to:
        {platform_links_text}

        Check out your posts using the links above. We're here if you need anything!

        Best regards,
        Your Social Media Team
        """

        return await self.send_email(client_email, subject, body_html, body_text)

    async def send_monthly_report(
        self,
        client_email: str,
        client_name: str,
        month: str,
        total_posts: int,
        top_post_url: Optional[str] = None,
        engagement_stats: Optional[dict] = None,
    ) -> bool:
        """Send monthly report to client."""

        subject = f"Your {month} Social Media Report"

        stats_html = ""
        if engagement_stats:
            stats_html = f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
              <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; text-align: center;">
                <h3 style="margin: 0; color: #1976d2;">{engagement_stats.get('total_likes', 0)}</h3>
                <p style="margin: 5px 0 0 0; color: #555;">Total Likes</p>
              </div>
              <div style="background-color: #f3e5f5; padding: 15px; border-radius: 5px; text-align: center;">
                <h3 style="margin: 0; color: #7b1fa2;">{engagement_stats.get('total_comments', 0)}</h3>
                <p style="margin: 5px 0 0 0; color: #555;">Total Comments</p>
              </div>
            </div>
            """

        top_post_html = ""
        if top_post_url:
            top_post_html = f"""
            <div style="background-color: #fff3e0; padding: 20px; border-radius: 5px; margin: 20px 0;">
              <p><strong>🏆 Top Performing Post:</strong></p>
              <a href="{top_post_url}" style="color: #f57c00;">View Post →</a>
            </div>
            """

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Your {month} Social Media Report</h2>

            <p>Hi {client_name},</p>

            <p>Here's a summary of your social media activity this month:</p>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
              <h1 style="margin: 0; color: #4CAF50;">{total_posts}</h1>
              <p style="margin: 10px 0 0 0;">Posts Published</p>
            </div>

            {stats_html}

            {top_post_html}

            <p>We're committed to helping your business grow online. Let us know if you have any questions!</p>

            <p style="margin-top: 40px;">
              Best regards,<br>
              Your Social Media Team
            </p>

            <p style="color: #888; font-size: 12px; margin-top: 40px;">
              This is an automated monthly report from Social Automation SaaS
            </p>
          </body>
        </html>
        """

        body_text = f"""
        Your {month} Social Media Report

        Hi {client_name},

        Here's a summary of your social media activity this month:

        Posts Published: {total_posts}

        We're committed to helping your business grow online. Let us know if you have any questions!

        Best regards,
        Your Social Media Team
        """

        return await self.send_email(client_email, subject, body_html, body_text)

    async def notify_monthly_limit_reached(
        self,
        client_email: str,
        client_name: str,
        monthly_limit: int,
    ) -> bool:
        """Notify client they've reached their monthly post limit."""

        subject = "Monthly Post Limit Reached"

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Monthly Post Limit Reached</h2>

            <p>Hi {client_name},</p>

            <p>You've reached your monthly limit of {monthly_limit} posts.</p>

            <p>To continue posting, consider upgrading your plan for more posts per month!</p>

            <a href="{settings.FRONTEND_URL}/upgrade"
               style="display: inline-block; background-color: #4CAF50; color: white;
                      padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">
              Upgrade Plan →
            </a>

            <p>Questions? Just reply to this email and we'll help!</p>

            <p style="margin-top: 40px;">
              Best regards,<br>
              Your Social Media Team
            </p>
          </body>
        </html>
        """

        body_text = f"""
        Monthly Post Limit Reached

        Hi {client_name},

        You've reached your monthly limit of {monthly_limit} posts.

        To continue posting, consider upgrading your plan for more posts per month!

        Questions? Just reply to this email and we'll help!

        Best regards,
        Your Social Media Team
        """

        return await self.send_email(client_email, subject, body_html, body_text)

    async def notify_retry_limit_reached(
        self,
        team_email: str,
        client_name: str,
        content_id: int,
        platform: str,
        error_message: str,
        retry_count: int,
    ) -> bool:
        """Notify team that retry limit has been reached for a post."""

        subject = f"⚠️ Posting Failed After {retry_count} Retries: {client_name}"

        # Create admin URL
        base_url = settings.FRONTEND_URL or "http://localhost:8000"
        admin_url = f"{base_url}/admin/content/{content_id}"

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #d32f2f;">⚠️ Posting Failed After {retry_count} Retries</h2>

            <div style="background-color: #ffebee; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #d32f2f;">
              <p><strong>Client:</strong> {client_name}</p>
              <p><strong>Content ID:</strong> {content_id}</p>
              <p><strong>Platform:</strong> {platform.title()}</p>
              <p><strong>Retries Attempted:</strong> {retry_count}</p>
            </div>

            <div style="margin: 20px 0;">
              <p><strong>Error Message:</strong></p>
              <p style="font-family: monospace; background-color: #f5f5f5; padding: 15px; border-radius: 5px; color: #d32f2f;">
                {error_message}
              </p>
            </div>

            <p>Please review the content and try one of the following:</p>
            <ul>
              <li>Check platform credentials and permissions</li>
              <li>Verify the content meets platform requirements</li>
              <li>Review the error message for specific issues</li>
              <li>Manually retry or edit the content</li>
            </ul>

            <a href="{admin_url}"
               style="display: inline-block; background-color: #d32f2f; color: white;
                      padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0;">
              Review Content →
            </a>

            <p style="color: #888; font-size: 12px; margin-top: 40px;">
              This is an automated notification from Social Automation SaaS
            </p>
          </body>
        </html>
        """

        body_text = f"""
        ⚠️ Posting Failed After {retry_count} Retries

        Client: {client_name}
        Content ID: {content_id}
        Platform: {platform.title()}
        Retries Attempted: {retry_count}

        Error Message:
        {error_message}

        Please review the content and try one of the following:
        - Check platform credentials and permissions
        - Verify the content meets platform requirements
        - Review the error message for specific issues
        - Manually retry or edit the content

        Review at: {admin_url}
        """

        return await self.send_email(team_email, subject, body_html, body_text)


# Singleton instance
email_service = EmailService()
