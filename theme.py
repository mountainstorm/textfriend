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


from copy import copy
import plistlib
import os


class Theme(object):
    def __init__(self, theme):
        self._uuid = None if u'uuid' not in theme else theme[u'uuid']
        self._name = None if u'name' not in theme else theme[u'name']
        self._semantic_class = None if u'semanticClass' not in theme else theme[u'semanticClass']
        self._author = None if u'author' not in theme else theme[u'author']
        self._comment = None if u'comment' not in theme else theme[u'comment']
        self._cache = {} # speef lookup of previously found selectors
        self._settings = {}
        # right; more detailed specifiers override less detailed ones
        # to allow this to be done simply we're going to duplicate and sort all
        # scope selectors, we put the more specific ones at the end and let them 
        # overwrite the less specific ones - we'll also save the defaults on the way
        for setting in theme[u'settings']:
            if u'scope' not in setting:
                self._settings[u''] = setting[u'settings']
            else:
                # extract out all the bits of the scope
                s = setting[u'settings']
                for scope in setting[u'scope'].split(u','):
                    scope = scope.strip()
                    if scope not in self._settings:
                        self._settings[scope] = {}
                    for k, v in s.items():
                        self._settings[scope][k] = v
        self._settings_keys = sorted(self._settings.keys())
        # load gutter settings - default to 'defaults'
        self._gutter = self.theme_for_scope(u'')
        if u'gutterSettings' in theme:
            self._gutter = theme[u'gutterSettings']

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def semantic_class(self):
        return self._semantic_class

    @property
    def author(self):
        return self._author

    @property
    def comment(self):
        return self._comment

    @property
    def gutter(self):
        return self._gutter

    def theme_for_scope(self, scope):
        retval = {}
        if scope in self._cache:
            retval = self._cache[scope]

        else:
            for key in self._settings_keys:
                if len(scope) >= len(key) and scope[:len(key)] == key:
                    # this rule applies
                    for k, v in self._settings[key].items():
                        retval[k] = v
            self._cache[scope] = retval
        return retval


class ThemeStore(object):
    u'''Top level storage of themes.'''
    def __init__(self, autoload=True):
        self._themes = {}
        if autoload == True:
            self.load_themes()

    @property
    def themes(self):
        return copy(self._themes)

    def add_theme(self, fp):
        theme = Theme(plistlib.readPlist(fp))
        self._themes[theme.semantic_class] = theme
        return theme

    def get_theme(self, semantic_class):
        return self._themes[semantic_class]

    def load_themes(self):
        file_exts = [u'.plist', u'.tmTheme']
        dirname = os.path.join(os.path.dirname(os.path.realpath(__file__)), u'Themes')
        for name in os.listdir(dirname):
            fn = os.path.join(dirname, name)
            if os.path.isfile(fn) and os.path.splitext(fn)[1] in file_exts:
                with open(fn, u'rt') as f:
                    self.add_theme(f)

