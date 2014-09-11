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


from console import Console, Color


class ConsoleFormatter(object):
    def __init__(self, stream, theme, tab=8, showgutter=True):
        self._c = Console(stream)
        self._theme = theme
        self._tabstop = u' ' * tab
        self._lineno = 1

        self._showgutter = showgutter
        self._gutter = (
            Color(theme.gutter[u'foreground']), 
            Color(theme.gutter[u'background']), 
            Color(theme.gutter[u'divider'])
        )

    def start_document(self, name):
        theme = self._theme.theme_for_scope(u'')
        fg = Color(theme[u'foreground'])
        bg = Color(theme[u'background'])
        self._c.pset(fg=fg, bg=bg).clear_line()
        self.gutter()

    def end_document(self):
        self._c.pop()
        self._c.reset().write(u'\n')

    def start_scope(self, name, off, line):
        theme = self._theme.theme_for_scope(name)
        fg = None
        if u'foreground' in theme:
            fg = Color(theme[u'foreground'])
        bg = None
        if u'background' in theme:
            bg = Color(theme[u'background'])
        self._c.pset(fg=fg, bg=bg)

    def end_scope(self, off, line):
        self._c.pop()

    def characters(self, str):
        last = 0
        str = str.replace(u'\t', self._tabstop)
        idx = str.find('\n', last)
        while idx != -1:
            self._c.write(str[last:idx+1])
            self._c.clear_line()
            self.gutter()
            last = idx+1
            idx = str.find(u'\n', last)
        self._c.write(str[last:])

    def gutter(self):
        if self._showgutter == True:
            self._c.pset(fg=self._gutter[0], bg=self._gutter[1])
            self._c.write(u'%4u' % self._lineno).set(fg=self._gutter[2]).write(u'│')
            self._c.pop().write(u' ')
        self._lineno += 1


