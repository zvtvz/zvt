# -*- coding: utf-8 -*-
import json
import os


def get_subscriber_emails():
    emails_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'subscriber_emails.json'))
    with open(emails_file) as f:
        return json.load(f)


if __name__ == '__main__':
    print(get_subscriber_emails())
