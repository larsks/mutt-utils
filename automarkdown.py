#!/usr/bin/python

import os
import sys
import argparse
import email.parser
from email.mime.text import MIMEText

import markdown

def parse_args():
    p = argparse.ArgumentParser()
    return p.parse_args()

def render_markdown(msg):
    plaintext = msg.get_payload()
    plainparts = plaintext.split('\n-- \n', 1)

    mdtext = plainparts.pop(0)
    htmltext = markdown.markdown(mdtext)

    if plainparts:
        signature = plainparts.pop(0)
    else:
        signature = None

    msg.set_type('multipart/mixed')
    msg.set_payload(None)
    msg.attach(MIMEText(htmltext, 'html'))
    msg.attach(MIMEText(mdtext, 'plain'))

    if signature:
        msg.attach(MIMEText('\n-- \n' + signature, 'plain'))

    return msg

def main():
    opts = parse_args()

    parser = email.parser.Parser()
    msg = parser.parse(sys.stdin)

    if not msg.is_multipart() \
            and msg.get_content_type() == 'text/plain' \
            and msg.get_payload().startswith('<!-- markdown -->'):

        msg = render_markdown(msg)

    print msg

if __name__ == '__main__':
    main()


