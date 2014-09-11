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


import os
import sys
import StringIO
from theme import ThemeStore
from grammar import GrammarStore
from html_formatter import HTMLFormatter


if __name__ == u'__main__':
    ts = ThemeStore()
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        print(u'Usage: %s [theme] <input> <html> <css>' % os.path.basename(__file__))
        print(u'Themes:')
        for t in ts.themes.keys():
            print(u'    %s' % t)

    else:
        ts = ThemeStore()
        gs = GrammarStore()

        theme = ts.themes.values()[0]
        if len(sys.argv) == 5:
            theme = ts.get_theme(sys.argv[1])
            infn = sys.argv[2]
            htmlfn = sys.argv[3]
            cssfn = sys.argv[4]
        else:
            infn = sys.argv[1]
            htmlfn = sys.argv[2]
            cssfn = sys.argv[3]

        with open(infn, u'rt') as f:
            html = open(htmlfn, u'wt+')
            html.write(u'''<!DOCTYPE html>

<!--
Copyright (c) 2014 Mountainstorm
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
-->

<html lang="en">
    <head>
        <link rel="stylesheet" type="text/css" href="%s">
    </head>
    <body>
''' % cssfn)

            css = open(cssfn, u'wt+')
            fmt = HTMLFormatter(html, css, theme, tab=4)
            gs.parse_document(infn, f, fmt)
            css.close()

            html.write(u'''
    </body>
</html>
''')
            html.close()

