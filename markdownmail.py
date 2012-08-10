#!/usr/bin/env python

'''Given an email message on stdin that consists of a single inline
message, this will look for an initial '<!-- markdown -->' in the
message body and, if found, will render the message body using
Markdown and generate an HTML attachment (which will be followed by the
original markdown contact as text/plain, which will be followed by a
signature, if any was found in the original message).

This filter uses the `markdown2` module and enables the `footnotes`
`code-friendly`, and `wiki-tables` extensions.

You can add the following flags to the '<!-- markdown -->' block:

- html-only -- create a single-part message with HTML content.
- strip-signature -- Do not include message signature in the rendered content.

For example:

    <!-- markdown html-only -->

'''

import os
import sys
import argparse
import email.parser
from email.mime.text import MIMEText
from email.generator import Generator
import re

import markdown2 as markdown

opts = None
re_marker = re.compile('<!-- markdown (?P<flags>.*) ?-->')

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--always', '-A', action='store_true')
    p.add_argument('--only-html', '-H', action='store_true')
    return p.parse_args()

def render_markdown(msg, flags=None):
    global opts

    if flags is None:
        flags = set()

    plaintext = msg.get_payload()

    # strip the first line (containing the <!-- markdown --> marker)
    marker, plaintext = plaintext.split('\n', 1)

    # make sure there was a marker and extract any
    # emedded flags.
    mo = re_marker.match(marker)
    if not mo and not opts.always:
        return msg
    elif not mo:
        # No marker but we're running with --always, so
        # we need to recover the original message body.
        plaintext = msg.get_payload()

    # flags are passed as a series of whitespace-separated
    # words. Split them into a set.
    if mo:
        flags = flags.union(
                set(mo.group('flags').strip().split()))

    # look for a signature marker ('-- \n') and strip
    # off the signature.
    try:
        mdtext, sigtext = plaintext.split('\n-- \n', 1)

        # Tack signature back in as a verbatim block.
        if not 'strip-signature' in flags:
            mdsig = '\n'.join(
                    ['    %s' % line for line in sigtext.split('\n')])
            mdtext = mdtext + '\n\n' + '<!-- signature -->\n\n    -- \n' + mdsig
    except ValueError:
        mdtext = plaintext
        sigtext = None

    # render the markdown content to HTML
    htmltext = markdown.markdown(mdtext, extras=[
        'footnotes', 'wiki-tables', 'code-friendly'])

    ## Assemble message
    htmlpart = MIMEText(htmltext, 'html')
    htmlpart.del_param('name')

    plainpart = MIMEText(plaintext, 'plain')
    plainpart.del_param('name')

    if 'only-html' in flags:
        msg.set_type('text/html')
        msg.set_payload(htmlpart.get_payload())
    else:
        msg.set_type('multipart/alternative')
        msg.set_payload(None)

        msg.attach(plainpart)
        msg.attach(htmlpart)

    return msg

def main():
    global opts
    opts = parse_args()
    flags = set()

    if opts.only_html:
        flags.add('only-html')

    parser = email.parser.Parser()
    msg = parser.parse(sys.stdin)

    if not msg.is_multipart() \
            and msg.get_content_type() == 'text/plain':

        msg = render_markdown(msg, flags=flags)

    g = Generator(sys.stdout, mangle_from_=False)
    g.flatten(msg)

if __name__ == '__main__':
    main()

