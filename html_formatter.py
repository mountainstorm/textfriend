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


import cgi
import StringIO


class HTMLFormatter(object):
    def __init__(self, stream, css_stream, theme, tab=8, showgutter=True):
        self._stream = stream
        self._css_stream = css_stream
        self._c = StringIO.StringIO()
        self._theme = theme
        self._tabstop = u' ' * tab
        self._showgutter = showgutter
        self._lineno = 1

        self._css = {}
        self._next_css = u'a'
        self._fixed_css = u''

        self._css_stream.write(u'.textfriend { border-spacing: 0; border-collapse: collapse; }\n')
        self._css_stream.write(u'.textfriend .gutter { padding: 0px; margin: 0px; vertical-align: top; }\n')
        self._css_stream.write(u'.textfriend .gutter pre { padding: 0px 1ch 0px 1ch; margin: 0px; display: inline-block; text-align: right; }\n')
        self._css_stream.write(u'.textfriend .code { padding: 0px 0px 0px 0px; margin: 0px; vertical-align: top; }\n')
        self._css_stream.write(u'.textfriend .code pre { padding: 0px 1ch 0px 1ch; margin: 0px; display: inline-block; }\n')
        self._css_stream.write(u'.textfriend > tr > td:last-child { width: 100%; }\n')
        self._css_stream.write(u'.textfriend .gutter { color: %s; background: %s; }\n' % (
                theme.gutter[u'foreground'], theme.gutter[u'background']
            )
        )

    def start_document(self, name):
        theme = self._theme.theme_for_scope(u'')
        self._css_stream.write(u'.textfriend .code { color: %s; background: %s }\n' % (theme[u'foreground'], theme[u'background']))
        self._stream.write(u'''<table class="textfriend"><tr>''')
        if self._showgutter == True:
            self._stream.write(u'<td class="gutter"><pre>')
            self.gutter()

    def end_document(self):
        if self._showgutter == True:
            self._stream.write(u'</pre></td>')
        self._stream.write(u'<td class="code"><pre>')
        self._stream.write(self._c.getvalue())
        self._stream.write(u'</pre></td>')
        self._stream.write(u'</tr></table>')

    def start_scope(self, name, off, line):
        theme = self._theme.theme_for_scope(name)
        t = u''
        if u'foreground' in theme:
            t += u'color: %s; ' % theme[u'foreground']
        if u'background' in theme:
            t += u'background: %s; ' % theme[u'background']
        if t in self._css:
            cls = self._css[t]
        else:
            cls = self._fixed_css + self._next_css
            if self._next_css == u'z':
                self._fixed_css += self._next_css
                self._next_css = u'a'
            else:  
                self._next_css = chr(ord(self._next_css) + 1)
            self._css[t] = cls
            self._css_stream.write(u'.textfriend .code pre .%s { %s}\n' % (cls, t))
        self._c.write(u'<span class="%s">' % (cls))

    def end_scope(self, off, line):
        self._c.write(u'</span>')

    def characters(self, str):
        last = 0
        str = str.replace(u'\t', self._tabstop)
        idx = str.find('\n', last)
        while idx != -1:
            self._c.write(cgi.escape(str[last:idx+1]))
            self.gutter()
            last = idx+1
            idx = str.find(u'\n', last)
        self._c.write(str[last:])

    def gutter(self):
        if self._showgutter == True:
            self._stream.write(u'%u\n' % self._lineno)
        self._lineno += 1
