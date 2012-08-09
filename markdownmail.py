#!/usr/bin/python

'''Given an email message on stdin that consists of a single inline
message, this will look for an initial '<!-- markdown -->' in the
message body and, if found, will render the message body using
Markdown and generate an HTML attachment (which will be followed by the
original markdown contact as text/plain, which will be followed by a
signature, if any was found in the original message).

This filter uses the `markdown2` module and enables the `footnotes`
`code-friendly`, and `wiki-tables` extensions.
'''

import os
import sys
import argparse
import email.parser
from email.mime.text import MIMEText

import markdown2 as markdown

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--marker', '-m', default='<!-- markdown -->')
    return p.parse_args()

def render_markdown(msg):
    plaintext = msg.get_payload()

    # remove the first line (which we expect to 
    # be the '<!-- markdown -->\n' marker).
    plaintext = plaintext.split('\n', 1)[1]

    # split on the signature marker (if any)
    plainparts = plaintext.split('\n-- \n', 1)

    # extract the markdown payload and render it to html
    mdtext = plainparts.pop(0)
    htmltext = markdown.markdown(mdtext, extras=[
        'footnotes', 'wiki-tables', 'code-friendly'])

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
            and msg.get_payload().startswith('%s\n' % opts.marker):

        msg = render_markdown(msg)

    print msg

if __name__ == '__main__':
    main()

