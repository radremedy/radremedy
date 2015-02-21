"""
email_utils.py

Contains functionality for sending emails.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from flask import current_app, request, render_template, url_for
from flask.ext.login import current_user

def assert_defined(name, val):
    """
    Checks to see that the provided string value is defined
    (i.e. not None, an empty string, or whitespace),
    and raises an error if it does not.

    Args:
        name: The name of the value, which will be
            included in the error message.
        val: The string value to check.
    """
    if val is None or \
        not isinstance(val, basestring) or \
        len(val) == 0 or \
        val.isspace():
        raise RuntimeError(name + ' is not configured.')


def send_email(toaddr, subject, message_text, message_html):
    """
    Sends an email.

    Args:
        toaddr: The recipient of the email.
        subject: The subject line to include.
        message_text: The text version of the email.
        message_html: The HTML version of the email.
    """
    # Get our config options and throw an error
    # if we don't have any of them configured.
    username = current_app.config.get('EMAIL_USERNAME')
    password = current_app.config.get('EMAIL_PASSWORD')
    fromaddr = current_app.config.get('EMAIL_ADDRESS')
    server = current_app.config.get('EMAIL_SERVER')

    assert_defined('EMAIL_USERNAME', username)
    assert_defined('EMAIL_PASSWORD', password)
    assert_defined('EMAIL_ADDRESS', fromaddr)
    assert_defined('EMAIL_SERVER', server)

    # If we have a display name to include in our From line,
    # add that in.
    displayname = current_app.config.get('EMAIL_DISPLAY_NAME')
    if displayname and not displayname.isspace():
        fromaddr = formataddr((displayname, fromaddr))

    # Create the email container
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddr

    # Build the plain-text and HTML versions.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(MIMEText(message_text, 'plain'))
    msg.attach(MIMEText(message_html, 'html'))

    # Send the email.
    server = smtplib.SMTP(server)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()


def send_resource_error(resource, comments):
    """
    Notifies administrators of an error in a resource.

    Args:
        resource: The resource in question.
        comments: The comments on the resource.
    """
    # Get our target email address and throw an error
    # if it's not defined.
    toaddr = current_app.config.get('EMAIL_ADDRESS')
    assert_defined('EMAIL_ADDRESS', toaddr)

    # Default the name to a public user, but if the requesting
    # user's authenticated, use that instead.
    from_name = "Public User"
    if current_user.is_authenticated():
        from_name = current_user.username

    # Append the IP
    from_name = from_name + " (" + str(request.remote_addr) + ")"

    # Get the subject
    subject =  "Resource Correction - " + resource.name

    # Get the URL to the resource
    resource_url = current_app.config.get('BASE_URL') + \
        url_for('remedy.resource', resource_id=resource.id)

    # Build the text of the message
    message_text = render_template('email/resource-error.txt',
        subject = subject,
        from_name = from_name,
        resource = resource,
        resource_url = resource_url,
        comments = comments)

    # Now build the HTML version
    message_html = render_template('email/resource-error.html',
        subject = subject,
        from_name = from_name,
        resource = resource,
        resource_url = resource_url,
        comments = comments)

    send_email(toaddr, subject, message_text, message_html)


def send_confirm_account(user):
    """
    Sends an email to the specified user to confirm their account.

    Args:
        user: The user to email.
    """
    # Generate the user's email address
    toaddr = formataddr((user.display_name, user.email))

    # Build the subject
    subject = 'RAD Remedy - Confirm Account'

    # Build the confirmation URL
    confirm_url = current_app.config.get('BASE_URL') + \
        url_for('auth.confirm_account', code=user.email_code)

    # Build the text of the message
    message_text = render_template('email/confirm-account.txt',
        subject = subject,
        user = user,
        confirm_url = confirm_url)

    # Now build the HTML version
    message_html = render_template('email/confirm-account.html',
        subject = subject,
        user = user,
        confirm_url = confirm_url)

    send_email(toaddr, subject, message_text, message_html)


def send_password_reset(user):
    """
    Sends an email to the specified user to reset their password.

    Args:
        user: The user to email.
    """
    # Generate the user's email address
    toaddr = formataddr((user.display_name, user.email))

    # Build the subject
    subject = 'RAD Remedy - Password Reset Request'

    # Build the reset URL
    reset_url = current_app.config.get('BASE_URL') + \
        url_for('auth.reset_password', code=user.email_code)

    # Get the IP of the person requesting the reset
    request_ip = str(request.remote_addr)

    # Build the text of the message
    message_text = render_template('email/reset-password.txt',
        subject = subject,
        user = user,
        reset_url = reset_url,
        request_ip = request_ip)

    # Now build the HTML version
    message_html = render_template('email/reset-password.html',
        subject = subject,
        user = user,
        reset_url = reset_url,
        request_ip = request_ip)

    send_email(toaddr, subject, message_text, message_html)    
