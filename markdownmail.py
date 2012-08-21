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
- include-src -- include markdown as a text/x-markdown alternative

For example:

    <!-- markdown html-only -->

'''

import os
import sys
import argparse
import copy
import email.parser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.generator import Generator
import re

import markdown2 as markdown

opts = None
re_marker = re.compile('<!-- markdown (?P<flags>.*) ?-->')

class MarkdownError (Exception):
    pass

class InvalidInputMessage (Exception):
    pass

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--always', '-A', action='store_true')
    p.add_argument('--force', '-F', action='store_true')
    p.add_argument('--only-html', '-H', action='store_true')
    return p.parse_args()

def make_multipart(msg):
    '''Takes a flat message and turns it into a message with 
    a single text/plain attachment.'''

    plaintext = msg.get_payload()
    msg.set_payload(None)
    msg.set_type('multipart/alternative')
    plainpart = MIMEText(plaintext, 'plain')
    plainpart.del_param('name')
    msg.attach(plainpart)

def get_markdown_content(text):
    global opts

    flags = None
    signature = None

    # strip the first line (containing the <!-- markdown --> marker)
    marker, plaintext = text.split('\n', 1)

    # make sure there was a marker and extract any
    # emedded flags.
    mo = re_marker.match(marker)
    if mo:
        flags = set(mo.group('flags').split())
    else:
        # No marker -- recover original text
        plaintext = text

    try:
        content, signature = plaintext.split('\n-- \n', 1)
    except ValueError:
        content = plaintext

    return (flags, plaintext, content, signature)

def process_message(origmsg, flags=None):
    global opts

    msg = copy.deepcopy(origmsg)

    if flags is None:
        flags = set()

    if not msg.is_multipart():
        if msg.get_content_type() != 'text/plain':
            # We don't know what to do with this message.
            raise InvalidInputMessage('Main body is not text/plain')
        make_multipart(msg)

    # Make sure there is only one text/plain part and that it is
    # the first part.
    if msg.get_payload()[0].get_content_type() != 'text/plain':
        raise InvalidInputMessage('first part is not text/plain')

    found_text_part = False
    for p in msg.get_payload():
        if p.get_content_type() == 'text/plain':
            if found_text_part:
                raise InvalidInputMessage('More than one text/plain part')
            found_text_part = True

    plainpart = msg.get_payload()[0]
    auxparts = msg.get_payload()[1:]
    rootpart = MIMEMultipart('related')

    msg.set_payload(None)
    msg.set_type('multipart/alternative')

    plaintext = plainpart.get_payload()
    msgflags, plaintext, content, signature = get_markdown_content(plaintext)
    if msgflags is None and not opts.always:
        raise InvalidInputMessage('No markdown marker.')
    elif msgflags is not None:
        flags.update(msgflags)

    # Append the signature as a `<pre>` block to the markdown
    # content.
    if not 'strip-signature' in flags:
        content = content + '\n<pre>-- \n%s\n</pre>' % signature

    # render the markdown content to HTML
    htmltext = markdown.markdown(content, extras=[
        'footnotes', 'wiki-tables', 'code-friendly'])
    htmlpart = MIMEText(htmltext, 'html')
    htmlpart.del_param('name')

    if not 'only-html' in flags:
        plainpart = MIMEText(plaintext)
        msg.attach(plainpart)

        if 'include-src' in flags:
            mdpart = MIMEText(content, 'x-markdown')
            msg.attach(mdpart)

    rootpart.attach(htmlpart)
    for part in auxparts:
        if part.get_filename():
            part.add_header('Content-ID', '<%s>' % part.get_filename())
        rootpart.attach(part)

    msg.attach(rootpart)
    return msg

def main():
    global opts
    opts = parse_args()
    flags = set()

    if opts.only_html:
        flags.add('only-html')

    parser = email.parser.Parser()
    msg = parser.parse(sys.stdin)
    
    try:
        msg = process_message(msg, flags=flags)
    except InvalidInputMessage:
        pass
    except Exception, detail:
        if not opts.force:
            raise
        else:
            print >>sys.stderr, 'ERROR: %s' % detail

    g = Generator(sys.stdout, mangle_from_=False)
    g.flatten(msg)

if __name__ == '__main__':
    main()

