#!/usr/bin/python
# coding: utf-8

# Copyright (c) 2014 Mountainstorm
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
import os
from StringIO import StringIO

from grammar import GrammarStore
from theme import ThemeStore
from debug_formatter import DebugFormatter


def validate_testcases(dirname):
    print(u'Testcase validation\n')
    gs = GrammarStore()

    print(u'\nRunning Testcases')
    testcases = os.path.join(dirname, u'Testcases')
    for name in os.listdir(testcases):
        if name != u'.DS_Store' and os.path.splitext(name)[1] != u'.xml':
            testfile = os.path.join(testcases, name)
            checkfile = os.path.splitext(testfile)[0] + u'.xml'
            if os.path.isfile(testfile):
                if os.path.isfile(checkfile):
                    with open(checkfile, u'rt') as f:
                        check = f.read()
                    try:
                        with open(testfile, u'rt') as f:
                            debug_stream = StringIO()
                            fmt = DebugFormatter(debug_stream)
                            gs.parse_document(testfile, f, fmt)
                        if check == debug_stream.getvalue():
                            print(u'✓ success: %s' % name)
                        else:
                            print(u'✗ failure, output has changed: %s' % name)
                    except:
                        print(u'✗ failure, exception: %s' % name)
                else:
                    print(u'✗ failure, no check file for: %s' % name)


def usage(name):
    print(u'''%s -h|test|create <testcase>|debug <testcase>''' % name)


if __name__ == u'__main__':
    if len(sys.argv) > 1:
        if len(sys.argv) == 2 and sys.argv[1] == u'test':
            dirname = os.path.dirname(os.path.realpath(sys.argv[0]))
            validate_testcases(dirname)

        elif len(sys.argv) == 3 and sys.argv[1] == u'debug' or sys.argv[1] == u'create':
            testfile = sys.argv[2]
            checkfile = os.path.splitext(testfile)[0] + u'.xml'

            gs = GrammarStore()
            ts = ThemeStore()
            debug_stream = StringIO()
            fmt = DebugFormatter(debug_stream, theme=ts.themes.values()[0])
            with open(testfile, u'rt') as f:
                gs.parse_document(testfile, f, fmt)

            # validate all content against original document
            original = u''
            with open(testfile, u'rt') as f:
                original = f.read()
            if fmt.content == original:
                print(u'✓ content is identical')
            else:
                print(u'✗ content is not identical to original')

            if sys.argv[1] == u'create':
                with open(checkfile, u'wb') as f:
                    f.write(debug_stream.getvalue())
        else:
            usage(sys.argv[0])
    else:
        usage(sys.argv[0])
