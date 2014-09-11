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


import plistlib
import regex
import os
from copy import copy
import sys
import xml


class ParserScope(object):
    def __init__(self, match=None, off=0, node=None):
        self.node = node
        self.match = match
        if self.match is not None:
            self.node = match.node
        self.off = off


class Parser(object):
    u'''A parser object, stores parsing state'''
    def __init__(self, node, formatter):
        self._formatter = formatter
        self._stack = [ParserScope(node=node)]
        self._formatter.start_document(node.scope)

    def parse_line(self, line, off, lno):
        # XXX: sort out $1 etc into in names
        loff = 0
        end = 0
        llen = len(line)
        #print "[%s]" % line, len(line)
        while end < llen:
            top = self._stack[-1]
            match = top.node.next_match(top.match, line, loff)
            if match is None:
                #print "left over: ", loff, len(line)
                if loff < len(line):
                    # add leftovers at the end of the line
                    self._formatter.characters(line[loff:])
                #print self._formatter._str
                #sys.exit(1)
                break # nothing else to find on this line
            
            # output all the characters before the match
            if loff < match.start:
                self._formatter.characters(line[loff:match.start])

            if match.type == GrammarNode.SCOPE_MATCH:
                # basic match of a range
                if match.node.name is not None:
                    self._formatter.start_scope(match.node.name, off + match.start, lno)
                self.process_captures(match, u'captures', line, off, lno)
                if match.node.name is not None:
                    self._formatter.end_scope(off + match.end, lno)

            elif match.type == GrammarNode.SCOPE_BEGIN:
                # we're into a new nested match - push this node
                if match.node.name is not None:
                    self._formatter.start_scope(match.node.name, off + match.start, lno)
                self.process_captures(match, u'begin_captures', line, off, lno)
                if match.node.content_name is not None:
                    self._formatter.start_scope(match.node.content_name, off + match.end, lno)
                self._stack.append(ParserScope(match, off))

            else:
                # finished that scope - pop it
                prev = self._stack.pop()
                if prev.node.content_name is not None:
                    self._formatter.end_scope(off + match.start, lno)
                self.process_captures(match, u'end_captures', line, off, lno)
                if match.node.name is not None:
                    self._formatter.end_scope(off + match.end, lno)
            loff = match.end # next time search from the end of this match

    def process_captures(self, match, which, line, off, lno):
        captures = getattr(match.node, which)
        loff = match.start
        for r in match.ranges:
            if r.key in captures.keys() and captures[r.key] is not None:
                if r.type == MatchRange.CAPTURE_BEGIN:
                    if r.pos > loff:
                        self._formatter.characters(line[loff:r.pos])
                    self._formatter.start_scope(captures[r.key], off + r.pos, lno)
                    loff = r.pos

                else: # MatchRange.CAPTURE_END
                    if r.pos > loff:
                        self._formatter.characters(line[loff:r.pos])
                    self._formatter.end_scope(off + r.pos, lno)
                    loff = r.pos

        # print chars in this match we're not already printed
        if match.end > loff:
            self._formatter.characters(line[loff:match.end])

    def complete(self):
        self._formatter.end_document()


class MatchRange(object):
    CAPTURE_BEGIN = 0
    CAPTURE_END = 1

    def __init__(self, type, key, sort):
        self.type = type
        self.key = key
        self.pos = int(sort)
        self.sort = sort


class Match(object):
    def __init__(self, re=None, node=None, type=None):
        self.node = node
        self.type = type
        self.ranges = []
        self.start = sys.maxint
        self.end = sys.maxint

        if re is not None:
            # Note: re.start()/re.end() can be wrong; as we need to sort them anyway 
            # we'll do it here.  We dont have a total length to use to normalize - so 
            # we will use twice the re returned length or 4096 whichever is bigger
            total_len = max(4096, (re.end()-re.start())*2)

            # captures can be nested, you get this with C preprocessor ones
            # one capture matches the whole of the #ifdef <DEFINE>, the nested
            # one just the ifdef.  We need to sort all these matches in order such 
            # that we get the nesting right.
            #
            # To do this we are going to create a number, the integer component will
            # be the start position and the decimal places will represent the length
            #  
            # For start positions we'll use the inverted normalised length of the 
            # match, for ends we'll use the normalized length - sounds crazy but 
            # just might work.  This way, when we sort by this number we'll end up 
            # with the first matches first, and the longest ones before the shorter 
            # ones - and vica versa at the end.  Genius?

            # add numbered groups and named groups
            locs = []
            for k in list(range(1, len(re.groups())+1)) + re.groupdict().keys():
                start = re.start(k)
                end = re.end(k)
                length = end-start
                if length > 0:
                    dec = float(length) / total_len # normalized
                    locs.append(MatchRange(MatchRange.CAPTURE_BEGIN, k, float(start) + (1.0 - dec)))
                    locs.append(MatchRange(MatchRange.CAPTURE_END, k, float(end) + dec))
            self.ranges = sorted(locs, key=lambda span: span.sort)

            # XXX: now add capture zero - this must enclose everything and be (at least) as big
            # this is because start/end with 0 on the regex can (for some reason) return a range 
            # smaller than the sum of the captures
            self.start = re.start()
            self.end = re.end()
            if len(self.ranges) > 0:
                self.start = min(self.start, self.ranges[0].pos)
                self.end = max(self.end, self.ranges[-1].pos)
            self.ranges.insert(0, MatchRange(MatchRange.CAPTURE_BEGIN, 0, self.start))
            self.ranges.append(MatchRange(MatchRange.CAPTURE_END, 0, self.end))

    def __cmp__(self, other):
        return cmp(self.start, other.start)


class IncludeNode(object):
    def __init__(self, textmate, grammar, node):
        self._textmate = textmate
        self._grammar = grammar
        self._include = node[u'include']
        if len(self._include) <= 2:
            # do the check now so we don't have to whilst parsing
            raise ValueError(u'include value is too small: "%s"' % (self._include))

    def __getattr__(self, name):
        target = None
        if self._include[0] == u'#':
            target = self._grammar.get_node(self._include[1:]) # it's in this repo
        elif self._include == u'$self' or self._include == u'$base':
            target = self._grammar # the whoel of this grammar
        else:
            target = self._textmate.get_grammar(self._include) # another grammar    
        return getattr(target, name)


class GrammarNode(object):
    u'''A node in the grammar tree'''
    SCOPE_MATCH = 0
    SCOPE_BEGIN  = 1
    SCOPE_END   = -1

    @classmethod
    def create(cls, textmate, grammar, node):
        retval = None
        if u'include' in node:
            retval = IncludeNode(textmate, grammar, node)
        else:
            retval = GrammarNode(textmate, grammar, node)
        return retval

    def __init__(self, textmate, grammar, node):
        self.name = None if u'name' not in node else node[u'name']
        self.comment = None if u'comment' not in node else node[u'comment']
        # XXX: add support for folding
        #self._folding_start = None if u'foldingStartMarker' not in node else node[u'foldingStartMarker']
        #self._folding_end = None if u'foldingStopMarker' not in node else node[u'foldingStopMarker']
        self._match = None if u'match' not in node else regex.compile(node[u'match'])
        self._begin = None if u'begin' not in node else regex.compile(node[u'begin'])
        self._end = None if u'end' not in node else node[u'end']
        self.content_name = None if u'contentName' not in node else node[u'contentName']
        self.begin_captures = self._load_captures(node, u'beginCaptures')
        self.end_captures = self._load_captures(node, u'endCaptures')
        self.captures = self._load_captures(node, u'captures')
        if len(self.captures) > 0 and (len(self.begin_captures) == 0 and len(self.end_captures) == 0):
            # shorthand for begin/end
            for k, v in self.captures.items():
                self.begin_captures[k] = v
                self.end_captures[k] = v
        # parse and compile all regex
        self._children = []
        if u'patterns' in node:
            for el in node[u'patterns']:
                self._children.append(GrammarNode.create(textmate, grammar, el))

    def _load_captures(self, node, name):
        retval = {}
        if name in node:
            for k, v in node[name].items():
                key = k
                try:
                    key = int(k)
                except ValueError:
                    pass
                #print v
                # XXX: why do some C++ v not have name?
                if u'name' in v:
                    retval[key] = v[u'name']
                else:
                    print v
        return retval

    def next_match(self, enclosing_match, line, off):
        u'''find the next grammar match; in line, starting from off.  This 
        checks its 'end' (if present) and all of its children'''
        retval = self.next_child_match(line, off)
        if self._end is not None:
            # we can use groupings from our begin' match i.e. the enclosing_match
            # in the end - so we need to re-compile every time; after replacing the 
            # groups in end with the matches from begin
            # XXX: fix end matching - rarely used, need to find an example to test
            retval = min(
                retval, 
                Match(regex.compile(self._end).search(line, off), self, GrammarNode.SCOPE_END)
            )
        return retval if retval.node is not None else None

    def next_child_match(self, line, off):
        u'''finds the earliest match of all the child nodes'''
        retval = Match()
        for child in self._children:
            #print child.name
            if child._match is not None:
                retval = min(
                    retval, 
                    Match(child._match.search(line, off), child, GrammarNode.SCOPE_MATCH)
                )
            elif child._begin is not None:
                retval = min(
                    retval, 
                    Match(child._begin.search(line, off), child, GrammarNode.SCOPE_BEGIN)
                )
            else:
                retval = min(retval, child.next_child_match(line, off))
        return retval


class Grammar(GrammarNode):
    u'''A top level grammar object'''
    def __init__(self, textmate, node):
        GrammarNode.__init__(self, textmate, self, node) # the grammar for this is us
        self.scope = None if u'scopeName' not in node else node[u'scopeName']
        self.uuid = None if u'uuid' not in node else node[u'uuid']
        self.key_equiv = None if u'keyEquivalent' not in node else node[u'keyEquivalent']

        self._file_extensions = []
        if u'fileTypes' in node:
            self._file_extensions = node[u'fileTypes']
        self._firstline = None
        if u'firstLineMatch' in node:
            self._firstline = regex.compile(node[u'firstLineMatch'])
        self._repository = {}
        if u'repository' in node:
            self._repository = {}
            for name, el in node[u'repository'].items():
                self._repository[name] = GrammarNode.create(textmate, self, el)

    def get_node(self, name):
        return self._repository[name]

    def check_document(self, filename, firstline):
        retval = 0
        if self._firstline is not None:
            if self._firstline.match(firstline) is not None:
                retval += 2 # first line is more important than file ext

        fn, x = os.path.splitext(filename)
        if len(x) > 1:
            x = x[1:]
            for ext in self._file_extensions:
                if x == ext:
                    retval += 1
                    break
        return retval


class GrammarStore(object):
    u'''Top level storage of grammars.'''
    def __init__(self, autoload=True):
        self._grammars = {}
        if autoload == True:
            self.load_grammars()

    @property
    def grammars(self):
        return copy(self._grammars)

    def add_grammar(self, fp):
        grammar = Grammar(self, plistlib.readPlist(fp))
        self._grammars[grammar.scope] = grammar
        return grammar

    def get_grammar(self, scope):
        return self._grammars[scope]

    def parse_document(self, filename, fp, fmt, grammar=None):
        # read first line & find grammar tree
        retval = None

        line = fp.readline().decode(u'utf-8')
        if grammar is None:
            grammar = self._find_grammar(filename, line)
        if grammar is not None:
            parser = Parser(grammar, fmt)
            off = 0
            lno = 1
            parser.parse_line(line, off, lno)
            off += len(line)
            while line is not None and len(line) > 0: # we always get a trailing \n
                line = fp.readline().decode(u'utf-8')
                if line is not None and len(line) > 0:
                    lno += 1
                    ret = parser.parse_line(line, off, lno)
                    off += len(line)
            retval = parser.complete()
        return retval

    def load_grammars(self):
        file_exts = [u'.plist', u'.tmLanguage']
        dirname = os.path.join(os.path.dirname(os.path.realpath(__file__)), u'Grammars')
        for name in os.listdir(dirname):
            fn = os.path.join(dirname, name)
            if os.path.isfile(fn) and os.path.splitext(fn)[1] in file_exts:
                with open(fn, u'rt') as f:
                    self.add_grammar(f)

    def _find_grammar(self, filename, firstline):
        retval = None
        maxrank = 0
        for grammar in self._grammars.values():
            rank = grammar.check_document(filename, firstline)
            if rank > maxrank:
                retval = grammar
                maxrank = rank
        return retval

