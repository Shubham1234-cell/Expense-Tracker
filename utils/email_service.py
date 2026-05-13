import random
from flask_mail import Message
from extensions import mail
from flask import render_template, current_app

def generate_otp():
    return str(random.randint(100000, 999999))

def send_verification_email(user_email, otp):
    msg = Message('Verify your FinTrack Account',
                  sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@fintrack.app'),
                  recipients=[user_email])
    
    # Simple HTML structure for the OTP email
    msg.html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 10px;">
        <h2 style="color: #0ea5e9; text-align: center;">FinTrack Authentication</h2>
        <p>Hello,</p>
        <p>Thank you for registering with FinTrack! To complete your registration, please enter the following One-Time Password (OTP) in the verification screen.</p>
        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <h1 style="letter-spacing: 5px; color: #1f2937; margin: 0;">{otp}</h1>
        </div>
        <p style="color: #6b7280; font-size: 0.875rem;">This OTP will expire in 10 minutes. If you did not request this, please ignore this email.</p>
        <p>Best regards,<br>The FinTrack Team</p>
    </div>
    """
    
    # Try sending, but gracefully handle if no SMTP server is configured
    try:
        mail.send(msg)
        print(f"DEBUG: Sent OTP {otp} to {user_email}")
    except Exception as e:
        print(f"DEBUG: Could not send email via SMTP. Mocking OTP: {otp} to {user_email}. Error: {e}")

def send_weekly_report(user, start_date, end_date, total_expense, total_income, highest_category, expense_data):
    msg = Message('Your Weekly FinTrack Report',
                  sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@fintrack.app'),
                  recipients=[user.email])
    
    msg.html = render_template('emails/weekly_report.html', 
                               user=user, 
                               start_date=start_date, 
                               end_date=end_date, 
                               total_expense=total_expense, 
                               total_income=total_income,
                               highest_category=highest_category,
                               expense_data=expense_data)
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"DEBUG: Mocked weekly report for {user.email}. Error: {e}")
