#!/usr/bin/env python3
"""
A script for ensuring that a file is available. This sends a HEAD request for
a provided list of URLs and sends and email to a configurable list of
recipients if any of the URLs return an error status code or if the script
encounters an exception while trying to send the request.
"""

import logging
import os
import smtplib
import sys
import traceback
from email.message import EmailMessage

import requests
import yaml

def load_config():
    """
    Load the user's configuration file and return it as a dictionary
    :return: the configuration as a dictionary
    """

    user_config_path = os.path.join(
        os.environ['HOME'], '.config', 'url_checker', 'config.yml'
    )
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

    expected_values = [
        'smtp_server', 'smtp_port', 'email_address', 'email_password',
        'recipients', 'downloads'
    ]
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

    if 'timeout' not in config:
        logging.info("No timeout specified. 5 seconds will be selected.")
        config['timeout'] = 5

    return errors == 0


def validate_url(url, timeout, user_agent):
    """
    Check a URL and get the status code from a HEAD request. Recursively
    check 3xx responses up to 5 times.

    :param url: The URL to check
    :param timeout: The timeout to use when sending the HEAD request
    :return the status code received
    """

    headers = {
        'User-Agent': user_agent
    }
    response = requests.head(url, timeout=timeout, headers=headers)
    max_3xx_checks = 5
    checks_for_3xx = 0

    while (
        response.status_code in range(300, 399)
        and checks_for_3xx <= max_3xx_checks
    ):
        if 'Location' in response.headers:
            response = requests.head(
                response.headers['Location'], timeout=timeout
            )
            checks_for_3xx += 1
        else:
            # If there is no 'Location' header, exit the loop which will
            # result in the 3xx status code being returned
            break

    if checks_for_3xx >= max_3xx_checks:
        logging.warning("Too many redirects for %s" % url)

    return response.status_code


def send_email(software, body, recipients, sender, server, port, password):
    """
    Send an email reporting that a software was not able to be retrieved
    successfully.

    :param software: The software that was not found
    :param body: The body of the message to send
    :param recipients: Who to send the email to
    :param sender: Who is sending the message
    :param server: The SMTP server
    :param port: The port on the SMTP server. An integer is expected
    :param password: The sender's password
    :returns: The email that was created and hopefully sent
    """

    # Prep the message
    msg = EmailMessage()
    msg.set_content(body)
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

    return msg


def main():
    logging.basicConfig(
        format="%(levelname)s: %(message)s", level=logging.INFO
    )

    try:
        config = load_config()
    except OSError as e:
        logging.error("Unable to open configuration file.", exc_info=e)
        sys.exit(1)

    if not validate_config(config):
        sys.exit(1)

    user_agent = config.get('user_agent',
                            "%s's URL availability checker"
                            % os.environ['USER']
                           )

    errors = 0
    msgs = []
    names = []
    for download in config['downloads']:
        url = download['url']
        name = download['name']
        try:
            status_code = validate_url(url, config['timeout'], user_agent)
            if status_code != 200:
                errors += 1
                names.append(name)
                msgs.append(
                    "%s may not be available. An HTTP %s status code"
                    " was received when sending a HEAD request."
                    "\nURL: %s" % (name, status_code, url)
                )
        # Many sorts of exceptions could theoretically occur while checking the
        # URL. This may not signify the file is inaccessible, but it's good to
        # notify just in case.
        except Exception as e:
            errors += 1
            names.append(name)
            msgs.append(
                "%s may not be available. An exception was raised"
                " while sending a HEAD request to the URL below."
                "\nURL: %s"
                "\nException: %s" % (name, url, traceback.format_exc())
            )

    # If the value is set, some error condition has occurred, so send
    # the email
    if msgs:
        msg_body = "\n\n".join(msgs)
        subject = ", ".join(names)
        try:
            msg = send_email(
                subject, msg_body, config['recipients'],
                config['email_address'], config['smtp_server'],
                config['smtp_port'], config['email_password']
            )
            logging.info("Sent message: \n\n%s", msg)
        except Exception as e:
            logging.error("Email failed to send for %s.", name, exc_info=e)
    else:
        logging.info("No failures.")

    sys.exit(errors)


if __name__ == '__main__':
    main()
