#!/usr/bin/python

import os
import sys
import argparse
import email.parser
from email.mime.text import MIMEText

import markdown2 as markdown

def parse_args():
    p = argparse.ArgumentParser()
    return p.parse_args()

def render_markdown(msg):
    plaintext = msg.get_payload()

    # remove '<!-- markdown -->\n' marker.
    plaintext = plaintext.split('\n', 1)[1]

    # split on the signature marker (if any)
    plainparts = plaintext.split('\n-- \n', 1)

    # extract the markdown payload and render it to html
    mdtext = plainparts.pop(0)
    htmltext = markdown.markdown(mdtext, extras=[
        'code-color', 'wiki-tables'])

    if plainparts:
        signature = plainparts.pop(0)
    else:
        signature = None

    msg.set_type('multipart/mixed')
    msg.set_payload(None)
    msg.attach(MIMEText(htmltext, 'html'))
    msg.attach(MIMEText(mdtext, 'plain'))

    # If there was a signature, append it as a text/plain
    # attachment.
    if signature:
        msg.attach(MIMEText('\n-- \n' + signature, 'plain'))

    return msg

def main():
    opts = parse_args()

    parser = email.parser.Parser()
    msg = parser.parse(sys.stdin)

    if not msg.is_multipart() \
            and msg.get_content_type() == 'text/plain' \
            and msg.get_payload().startswith('<!-- markdown -->\n'):

        msg = render_markdown(msg)

    print msg

if __name__ == '__main__':
    main()


