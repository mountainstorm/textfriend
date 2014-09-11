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
from console import Console, Color


class DebugFormatter(object):
    def __init__(self, stream, tab=8, theme=None):
        self._stream = stream
        self._c = None
        self._tabstop = u' ' * tab
        self._content = u''
        if theme is not None:
            self._c = Console(sys.stdout)
            self._theme = theme
            self._lineno = 1

            self._gutter = (
                Color(theme.gutter[u'foreground']), 
                Color(theme.gutter[u'background']), 
                Color(theme.gutter[u'divider'])
            )

    @property
    def content(self):
        return self._content

    def start_document(self, name):
        if self._c is not None:
            theme = self._theme.theme_for_scope(u'')
            fg = Color(theme[u'foreground'])
            bg = Color(theme[u'background'])
            self._c.pset(fg=fg, bg=bg)
            self._c.clear_line()
            self.gutter()
            self._c.write(u'@%s{' % name)
        self._stream.write(u'@%s{' % name)

    def end_document(self):
        if self._c is not None:
            self._c.write(u'}')
            self._c.pop()
            self._c.reset()
            self._c.write(u'\n')
        self._stream.write(u'}')

    def start_scope(self, name, off, line):
        if self._c is not None:
            theme = self._theme.theme_for_scope(name)
            fg = None
            if u'foreground' in theme:
                fg = Color(theme[u'foreground'])
            bg = None
            if u'background' in theme:
                bg = Color(theme[u'background'])
            self._c.pset(fg=fg, bg=bg)
            self._c.write(u'@%s(%u,%u){' % (name, off, line))
        self._stream.write(u'@%s(%u,%u){' % (name, off, line))

    def end_scope(self, off, line):
        if self._c is not None:
            self._c.write(u'}(%u,%u)' % (off, line))
            self._c.pop()
        self._stream.write(u'}(%u,%u)' % (off, line))

    def characters(self, str):
        self._content += str
        last = 0
        str = str.replace(u'\t', self._tabstop)
        idx = str.find('\n', last)
        while idx != -1:
            self._stream.write(str[last:idx+1])
            if self._c is not None:
                self._c.write(str[last:idx+1])
                self._c.clear_line()
                self.gutter()
            last = idx+1
            idx = str.find(u'\n', last)
        self._stream.write(str[last:])
        if self._c is not None:
            self._c.write(str[last:])

    def gutter(self):
        self._c.pset(fg=self._gutter[0], bg=self._gutter[1])
        self._c.write(u'%4u' % self._lineno).set(fg=self._gutter[2]).write(u'│')
        self._c.pop().write(u' ')
        self._lineno += 1




