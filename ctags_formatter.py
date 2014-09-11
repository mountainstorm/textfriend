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


class Scope(object):
    def __init__(self, depth):
        self.depth = depth
        self.content = u''


class FunctionScope(Scope):
    def __init__(self, depth, line):
        Scope.__init__(self, depth)
        self.line = line
        self.name = None

class FunctionNameScope(Scope):
    def __init__(self, depth):
        Scope.__init__(self, depth)
        self.depth = depth


class CallScope(Scope):
    def __init__(self, depth, line):
        Scope.__init__(self, depth)
        self.depth = depth
        self.line = line


class CTagsFormatter(object):
    def __init__(self, filename, ctags, call_tags=None):
        self._filename = filename
        self._ctags = ctags
        self._call_tags = call_tags
        self._depth = 0
        self._scopes = []

    def start_document(self, name):
        self._ctags.write(u'!_TAG_FILE_FORMAT\t2\n')
        self._ctags.write(u'!_TAG_FILE_SORTED\t1\n')
        self._ctags.write(u'!_TAG_PROGRAM_AUTHOR\tMountainstorm\n')
        self._ctags.write(u'!_TAG_PROGRAM_NAME\ttextfriend\n')
        self._ctags.write(u'!_TAG_PROGRAM_URL\thttps://github.com/mountainstorm\n')
        if self._call_tags is not None:
            self._call_tags.write(u'!_TAG_FILE_FORMAT\t2\n')
            self._call_tags.write(u'!_TAG_FILE_SORTED\t1\n')
            self._call_tags.write(u'!_TAG_PROGRAM_AUTHOR\tMountainstorm\n')
            self._call_tags.write(u'!_TAG_PROGRAM_NAME\ttextfriend\n')
            self._call_tags.write(u'!_TAG_PROGRAM_URL\thttps://github.com/mountainstorm\n')

    def end_document(self):
        pass

    def start_scope(self, name, off, line):
        if name.startswith(u'meta.function'):
            self._scopes.append(FunctionScope(self._depth, line))

        elif name.startswith(u'entity.name.function'):
            # XXX: different languages seem to name differently - particually for calls
            self._scopes.append(FunctionNameScope(self._depth))

        elif name.startswith(u'support.function'):
            self._scopes.append(CallScope(self._depth, line))
        self._depth += 1

    def end_scope(self, off, line):
        self._depth -= 1
        if len(self._scopes) > 0 and self._scopes[-1].depth == self._depth:
            # we've finished the top scope
            top = self._scopes.pop()

            if isinstance(top, FunctionNameScope):
                # finished function name - associate it with the function we're in
                self._scopes[-1].name = top.content

            elif isinstance(top, CallScope):
                # print to call tags if we're doing that
                if self._call_tags:
                    self._call_tags.write(u'%s\t%s\t%u\t;\tby\t%s\n' % (
                        top.content, self._filename, top.line, self._scopes[-1].name
                    ))
            elif isinstance(top, FunctionScope):
                self._ctags.write(u'%s\t%s\t%u\n' % (top.name, self._filename, top.line))

    def characters(self, str):
        if len(self._scopes) > 0:
            self._scopes[-1].content += str
