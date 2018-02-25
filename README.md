# URL Checker

`setup.py` is a work in progress; however, the script located in
`url_checker/url_checker.py` works well enough.

Script used to ensure that a file is accessible. If there is a problem
accessing the file, an email is sent to a configured list of recipients.
Configuration is stored in `~/.config/url_checker/config.yml`.
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
    timeout: 5

For the SMTP server and port, only a combination that supports STARTTLS is
supported. The timeout is given in seconds and is optional; 5 is the default.

When checking the URL, if a 3xx is received, the 'Location' in the response
will be checked. This will be done, at most, 5 times. If a 200 is not
eventually received, an email will be sent just like for any other failure.

Any issues with the configuration or with sending the email will be logged
and the script will terminate.

It probably isn't great to use this script just anywhere because it
requires the user's password be stored in plain text on disk and
additionally, the password will be floating around in plain text in memory
as well.

