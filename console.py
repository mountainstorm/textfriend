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
from copy import copy


class Palette(object):
    def __init__(self):
        self.cache = {}
        self.colors = []
        #
        # This color generation code is taken from Pygments (oh the irony), 
        # so this code is BSD licensed: formatters/terminal256.py
        #

        # colors 0..15: 16 basic colors
        self.colors.append((0x00, 0x00, 0x00)) # 0
        self.colors.append((0xcd, 0x00, 0x00)) # 1
        self.colors.append((0x00, 0xcd, 0x00)) # 2
        self.colors.append((0xcd, 0xcd, 0x00)) # 3
        self.colors.append((0x00, 0x00, 0xee)) # 4
        self.colors.append((0xcd, 0x00, 0xcd)) # 5
        self.colors.append((0x00, 0xcd, 0xcd)) # 6
        self.colors.append((0xe5, 0xe5, 0xe5)) # 7
        self.colors.append((0x7f, 0x7f, 0x7f)) # 8
        self.colors.append((0xff, 0x00, 0x00)) # 9
        self.colors.append((0x00, 0xff, 0x00)) # 10
        self.colors.append((0xff, 0xff, 0x00)) # 11
        self.colors.append((0x5c, 0x5c, 0xff)) # 12
        self.colors.append((0xff, 0x00, 0xff)) # 13
        self.colors.append((0x00, 0xff, 0xff)) # 14
        self.colors.append((0xff, 0xff, 0xff)) # 15
        
        # colors 16..232: the 6x6x6 color cube
        valuerange = (0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff)
        for i in range(217):
            r = valuerange[(i // 36) % 6]
            g = valuerange[(i // 6) % 6]
            b = valuerange[i % 6]
            self.colors.append((r, g, b))

        # colors 233..253: grayscale
        for i in range(1, 22):
            v = 8 + i * 10
            self.colors.append((v, v, v))

    @classmethod
    def rgb(cls, r, g, b):
        global _palette
        distance = 257*257*3 # "infinity" (>distance from #000000 to #ffffff)
        match = 0
        for i in range(0, 254):
            values = _palette.colors[i]
            rd = r - values[0]
            gd = g - values[1]
            bd = b - values[2]
            d = rd*rd + gd*gd + bd*bd
            if d < distance:
                match = i
                distance = d
        return match

    @classmethod
    def lookup(cls, rrggbb):
        global _palette
        if rrggbb not in _palette.cache:
            r = int(rrggbb[1:3], 16)
            g = int(rrggbb[3:5], 16)
            b = int(rrggbb[5:7], 16)
            _palette.cache[rrggbb] = Palette.rgb(r, g, b)
        return _palette.cache[rrggbb]


_palette = Palette()


class Color(object):
    def __init__(self, rrggbb):
        self.rrggbb = rrggbb
        self.idx = Palette.lookup(rrggbb)

    def __cmp__(self, other):
        return cmp(self.idx, other.idx)


class Console(object):
    BOLD      = 0x01
    DIM       = 0x02
    UNDERLINE = 0x04
    BLINK     = 0x08
    INVERT    = 0x10
    HIDDEN    = 0x20

    DEFAULT   = 0x00

    def __init__(self, stream):
        self._stream = stream
        self._currentstate = [Console.DEFAULT, Console.DEFAULT, Console.DEFAULT]
        self._statestack = [] # stack of states, so you dont need to remember

    def set(self, attrs=None, fg=None, bg=None):
        if attrs is not None:
            self.attrs(attrs)
        if fg is not None:
            self.fg(fg)
        if bg is not None:
            self.bg(bg)
        return self

    def attrs(self, attrs):
        self.set_attrs(self._currentstate[0] | attrs)
        return self

    def set_attrs(self, attrs):
        oldstate = self._currentstate[0]
        self._currentstate[0] = attrs
        i = 1
        j = 0
        attributes = [[1, 22], [2, 22], [4, 24], [5, 25], [7, 27], [8, 28]]
        while i <= Console.HIDDEN:
            if i & self._currentstate[0]:
                #print "enable", i, attrs
                self._stream.write('\x1b[%um' % attributes[j][0]) # enable
            elif i & oldstate:
                #print "disable", i
                self._stream.write('\x1b[%um' % attributes[j][1]) # disable
            i <<= 1
            j += 1
        return self

    def clear_attrs(self):
        self._currentstate[0] = Console.DEFAULT
        self._stream.write('\x1b[0m')
        return self

    def fg(self, color):
        self._currentstate[1] = color
        if color is Console.DEFAULT:
            #print "fg clearing"
            self._stream.write('\x1b[39m')
        else:
            self._stream.write('\x1b[38;5;%dm' % (color.idx))
        return self

    def bg(self, color):
        self._currentstate[2] = color
        if color is Console.DEFAULT:
            #print "bg clearing"
            self._stream.write('\x1b[49m')
        else:
            self._stream.write('\x1b[48;5;%dm' % (color.idx))
        return self

    def pset(self, attrs=None, fg=None, bg=None):
        self.push()
        self.set(attrs, fg, bg)
        return self

    def clear_stack(self):
        self._statestack = []
        return self

    def push(self):
        self._statestack.append(copy(self._currentstate))
        return self

    def pop(self):
        if len(self._statestack) > 0:
            attrs, fg, bg = self._statestack.pop()
            self.set(None, fg, bg)
            self.set_attrs(attrs)
        return self

    def reset(self):
        self.clear_stack()
        self.set(Console.DEFAULT, Console.DEFAULT, Console.DEFAULT)
        return self

    def clear_line(self):
        self._stream.write('\x1b[K')
        return self

    def write(self, str):
        self._stream.write(str)
        return self


if __name__ == u'__main__':
    c = Console(sys.stdout)
    c.write(u'[').set(Console.BOLD).write(u'bold').clear_attrs().write(u']')
    
    for attr in [Console.DIM, Console.UNDERLINE, Console.BLINK, Console.INVERT, Console.HIDDEN]:
        sys.stdout.write(u'[')
        c.pset(attr)
        sys.stdout.write(u'12345')
        c.pop()
        sys.stdout.write(u']')
    
    col = Color(u'000000')
    for i in range(0, 256):
        if i % 8 == 0:
            sys.stdout.write(u'\n')
        col.idx = i 
        sys.stdout.write(u'[')
        c.fg(col)
        sys.stdout.write(u'█████')
        c.fg(Console.DEFAULT)
        sys.stdout.write(u']')
        sys.stdout.write(u'[')
        c.pset(bg=col)
        sys.stdout.write(u'     ')
        c.pop()
        sys.stdout.write(u']')
        c.reset()
    sys.stdout.write(u'\n')
