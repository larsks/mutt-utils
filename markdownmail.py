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
import re

import markdown2 as markdown

re_marker = re.compile('<!-- markdown (?P<options>.*) ?-->')

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--always', '-A', action='store_true')
    p.add_argument('--only-html', '-H', action='store_true')
    return p.parse_args()

def render_markdown(msg, options=None):
    if options is None:
        options = set()

    plaintext = msg.get_payload()

    # remove the first line (which we expect to 
    # be the '<!-- markdown -->\n' marker).
    marker, plaintext = plaintext.split('\n', 1)

    # Extract options from the markdown flag
    mo = re_marker.match(marker)
    if mo:
        options = set(mo.group('options').strip().split())

    # split on the signature marker (if any)
    try:
        mdtext, sigtext = plaintext.split('\n-- \n', 1)
        if not 'strip-signature' in options:
            mdsig = '\n'.join([ '    %s' % line for line in
                sigtext.split('\n')])
            mdtext = mdtext + '\n\n    -- \n' + mdsig
    except ValueError:
        mdtext = plaintext
        sigtext = None

    # render the markdown content to HTML
    htmltext = markdown.markdown(mdtext, extras=[
        'footnotes', 'wiki-tables', 'code-friendly'])

    ## Assemble message

    htmlpart = MIMEText(htmltext, 'html')
    htmlpart.set_param('name', 'message.html')

    plainpart = MIMEText(plaintext, 'plain')
    plainpart.set_param('name', 'message.txt')

    if 'only-html' in options:
        msg.set_type('text/html')
        msg.set_payload(htmlpart.get_payload())
    else:
        msg.set_type('multipart/alternative')
        msg.set_payload(None)

        msg.attach(plainpart)
        msg.attach(htmlpart)

    return msg

def main():
    opts = parse_args()

    parser = email.parser.Parser()
    msg = parser.parse(sys.stdin)

    if not msg.is_multipart() \
            and msg.get_content_type() == 'text/plain' \
            and (opts.always or msg.get_payload().startswith('<!-- markdown ')):

        msg = render_markdown(msg)

    print msg

if __name__ == '__main__':
    main()

