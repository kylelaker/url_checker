import logging
import os
import smtplib
import sys
from email.message import EmailMessage

import requests
import yaml

"""
    Script used to ensure that a file is accessible. If there is a problem
    accessing the file, an email is sent a configured list of recipients.
    Configuration is stored in ~/.config/url_checker/config.yml.
    An example config looks like:

    smtp_server: server.com
    smtp_port: 587
    email_address: user@server.com
    email_password: hunter2
    recipients:
        - user@email.com
    downloads:
        - name: Software
          url: https://google.com

    For the SMTP server and port, only a combination that supports STARTTLS is
    supported.

    When checking the URL, if a 3xx is received, the 'Location' in the response
    will be checked. This will be done, at most, 5 times. If a 200 is not
    eventually received, an email will be sent just like for any other failure.

    If there is any sort of exception while trying to get the status code, then
    an email will be sent reporting that status code 999 was received.
    Additional information will be logged.

    Any issues with the configuration or with sending the email will be logged
    and the script will terminate.

    It probably isn't great to use this script just anywhere because it
    requires the user's password be stored in plain text on disk and
    additionally, the password will be floating around in plain text in memory
    as well.
"""


def load_config():
    """
    Load the user's configuration file and return it as a dictionary
    :return: the configuration as a dictionary
    """

    user_config_path = os.path.join(os.environ['HOME'], '.config',
                                    'url_checker', 'config.yml')
    with open(user_config_path, 'r') as config_file:
        config = yaml.load(config_file)
        return config


def validate_config(config):
    """
    Validate the user's config. Any errors get logged. If there are 1 or more
    errors, False is returned.

    :param config: The configuration dictionary to validate
    :return: Whether or not the number of errors in the config was 0
    """

    expected_values = ['smtp_server', 'smtp_port', 'email_address',
                       'email_password', 'recipients', 'downloads']
    errors = 0
    if config is None:
        logging.error("Configuration file is empty or does not exist.")
        return False

    for value in expected_values:
        if value not in config:
            logging.error("Invalid config: %s is not present." % value)
            errors += 1
    if 'downloads' in config:
        for download in config['downloads']:
            if 'url' not in download:
                logging.error("Invalid config. Download missing URL")
                errors += 1
            if 'name' not in download:
                logging.error("Invalid config. Download missing name")
                errors += 1
    if 'recipients' in config:
        if len(config['recipients']) < 1:
            logging.error("At least one recipient is required")
            errors += 1

    return errors == 0


def validate_url(url):
    """
    Check a URL and get the status code from a HEAD request. Recursively
    check 3xx responses up to 5 times.

    :param url: The URL to check
    :return the status code received
    """

    response = requests.head(url)
    max_3xx_checks = 5
    checks_for_3xx = 0
    while response.status_code in range(300, 399) \
            and checks_for_3xx <= max_3xx_checks:
        if 'Location' in response.headers:
            response = requests.head(response.headers['Location'])
            checks_for_3xx += 1
        else:
            # If there is no 'Location' header, exit the loop which will
            # result in the 3xx status code being returned
            break
    if checks_for_3xx >= max_3xx_checks:
        logging.warning("Too many redirects for %s" % url)
    return response.status_code


def send_email(software, url, status_code, recipients, sender, server, port,
               password):
    """
    Send an email reporting that a software was not able to be retrieved
    successfully.

    :param software: The software that was not found
    :param url: The URL that did not result in a 200 status code
    :param status_code: The status code returned
    :param recipients: Who to send the email to
    :param sender: Who is sending the message
    :param server: The SMTP server
    :param port: The port on the SMTP server. An integer is expected
    :param password: The sender's password
    """

    # Prep the message
    msg = EmailMessage()
    msg_body = ("It does not seem like %s is available. Received a %d response"
                " when sending a HEAD request."
                "\n\nURL: %s" % (software, status_code, url))
    msg.set_content(msg_body)
    msg['Subject'] = "%s unavailable" % software
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    # Connect to the server and send the message
    server = smtplib.SMTP("%s:%d" % (server, port))
    server.ehlo()
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()


def main():
    try:
        config = load_config()
    except OSError as e:
        logging.error("Unable to open configuration file.", exc_info=e)
        sys.exit(1)
    if not validate_config(config):
        sys.exit(1)

    errors = 0
    for download in config['downloads']:
        url = download['url']
        name = download['name']
        try:
            status_code = validate_url(url)
        except Exception as e:
            default_status_code = 999
            logging.warning("Unable to get the url for %s. Proceeding and"
                            "reporting status code as %d."
                            % (name, default_status_code), exc_info=e)
            status_code = 999

        if status_code != 200:
            errors += 1
            try:
                send_email(name, url, status_code, config['recipients'],
                           config['email_address'], config['smtp_server'],
                           config['smtp_port'], config['email_password'])
            except Exception as e:
                logging.error("Email failed to send for %s" % name, exc_info=e)

    sys.exit(errors)


if __name__ == '__main__':
    main()
