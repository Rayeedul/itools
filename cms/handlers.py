# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from datetime import datetime
import mimetypes
from random import random
from time import time

# Import from itools
from itools.datatypes import DateTime, QName, String, Unicode, XML
from itools import schemas
from itools.handlers.File import File
from itools.handlers.Text import Text
from itools.handlers.registry import register_handler_class
from itools.xml import namespaces, parser
from itools.web import get_context
from Handler import Node
from metadata import Record



class ListOfUsers(File):

    def get_skeleton(self, users=[]):
        return '\n'.join(users)


    def _load_state(self, resource):
        state = self.state

        state.usernames = set()
        for username in resource.readlines():
            username = username.strip()
            if username:
                state.usernames.add(username)


    def to_str(self):
        return '\n'.join(self.state.usernames)


    def get_usernames(self):
        return self.state.usernames


    def add(self, username):
        self.set_changed()
        self.state.usernames.add(username)


    def remove(self, username):
        self.set_changed()
        self.state.usernames.remove(username)



class Lock(Text):

    def get_skeleton(self, username=None, **kw):
        key = '%s-%s-00105A989226:%.03f' % (random(), random(), time())
        timestamp = DateTime.encode(datetime.now())
        return '%s\n%s\n%s' % (username, timestamp, key)


    def _load_state(self, resource):
        state = self.state
        username, timestamp, key = resource.read().strip().split('\n')
        state.username = username
        # XXX backwards compatibility: remove microseconds first
        timestamp = timestamp.split('.')[0]
        state.timestamp = DateTime.decode(timestamp)
        state.key = key


    def to_str(self):
        state = self.state
        timestamp = DateTime.encode(state.timestamp)
        return '%s\n%s\n%s' % (state.username, timestamp, state.key)



class Metadata(Node, File):

    class_title = u'Metadata'
    class_icon48 = 'images/File48.png'


    def get_skeleton(self, handler_class=None, **kw):
        # Initialize the properties to add
        properties = {'format': handler_class.class_id,
                      'version': handler_class.class_version}
        # Update properties with the keyword parameters
        properties.update(kw)

        needed_namespaces = {}
        # Build the XML
        skeleton = ['<?xml version="1.0" encoding="UTF-8"?>']
        for name, value in properties.items():
            if value is not None:
                prefix, local_name = QName.decode(name)
                if prefix is None:
                    datatype = String
                else:
                    schema = schemas.get_schema(prefix)
                    needed_namespaces[schema.class_uri] = prefix
                    datatype = schema.get_datatype(local_name)

                if isinstance(value, dict):
                    for lang, value in value.items():
                        value = datatype.encode(value)
                        value = XML.encode(value)
                        skeleton.append('  <%s xml:lang="%s">%s</%s>'
                                        % (name, lang, value, name))
                else:
                    value = datatype.encode(value)
                    value = XML.encode(value)
                    skeleton.append('  <%s>%s</%s>' % (name, value, name))

        # Insert open root element with the required namespace declarations
        if needed_namespaces:
            needed_namespaces = [ 'xmlns:%s="%s"' % (y, x)
                                  for x, y in needed_namespaces.items() ]
            head = '<metadata %s>' % '\n          '.join(needed_namespaces)
        else:
            head = '<metadata>'
        skeleton.insert(1, head)

        skeleton.append('</metadata>')
        return '\n'.join(skeleton)


    def _load_state(self, resource):
        state = self.state
        # Keep the namespace prefixes
        state.prefixes = set()

        p_key = None
        datatype = None
        p_language = None
        p_value = ''
        stack = []
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.START_ELEMENT:
                namespace_uri, local_name, attributes = value
                if local_name == 'metadata':
                    stack.append({})
                else:
                    # Get the property type
                    schema = schemas.get_schema_by_uri(namespace_uri)
                    datatype = schema.get_datatype(local_name)
                    # Build the property key
                    p_key = (schema.class_prefix, local_name)

                    if datatype is Record:
                        stack.append({})
                    else:
                        p_value = ''

                    # xml:lang
                    attr_key = (namespaces.XMLNamespace.class_uri, 'lang')
                    p_language = attributes.get(attr_key)
            elif event == parser.END_ELEMENT:
                namespace_uri, local_name = value
                # Get the property type
                schema = schemas.get_schema_by_uri(namespace_uri)
                datatype = schema.get_datatype(local_name)
                p_default = datatype.default
                # Build the property key
                p_key = (schema.class_prefix, local_name)

                if local_name == 'metadata':
                    state.properties = stack.pop()
                else:
                    # Decode value
                    if datatype is Record:
                        p_value = stack.pop()
                    elif datatype is Unicode:
                        p_value = datatype.decode(p_value, 'UTF-8')
                    else:
                        p_value = datatype.decode(p_value)
                    # Set property
                    if isinstance(p_default, list):
                        stack[-1].setdefault(p_key, []).append(p_value)
                    elif p_language is None:
                        stack[-1][p_key] = p_value
                    else:
                        stack[-1].setdefault(p_key, {})
                        stack[-1][p_key][p_language] = p_value
                    # Reset variables
                    datatype = None
                    p_language = None
                    p_value = ''
            elif event == parser.TEXT:
                if p_key is not None:
                    p_value += value
            elif event == parser.NAMESPACE:
                # Update prefixes
                schema = schemas.get_schema_by_uri(value)
                prefix = schema.class_prefix
                if prefix is not None:
                    state.prefixes.add(prefix)


    def to_str(self):
        state = self.state

        lines = ['<?xml version="1.0" encoding="UTF-8"?>']

        # Insert open root element with the required namespace declarations
        if state.prefixes:
            aux = [ (x, schemas.get_schema(x).class_uri)
                    for x in state.prefixes ]
            aux = '\n          '.join([ 'xmlns:%s="%s"' % x for x in aux ])
            lines.append('<metadata %s>' % aux)
        else:
            lines.append('<metadata>')

        for key, value in state.properties.items():
            prefix, local_name = key

            # Get the type
            datatype = schemas.get_datatype(key)
            # Get the qualified name
            if prefix is None:
                qname = local_name
            else:
                qname = '%s:%s' % key

            if isinstance(value, dict):
                for language, value in value.items():
                    value = datatype.encode(value)
                    value = XML.encode(value)
                    lines.append('  <%s xml:lang="%s">%s</%s>'
                                 % (qname, language, value, qname))
            elif isinstance(value, list):
                for value in value:
                    value = datatype.encode(value)
                    if datatype is not Record:
                        value = XML.encode(value)
                    lines.append('  <%s>%s</%s>' % (qname, value, qname))
            else:
                value = datatype.encode(value)
                value = XML.encode(value)
                lines.append('  <%s>%s</%s>' % (qname, value, qname))

        lines.append('</metadata>')
        return '\n'.join(lines)


    ########################################################################
    # API
    ########################################################################
    def get_property(self, name, language=None):
        key = QName.decode(name)

        # Default value
        datatype = schemas.get_datatype(key)
        default_value = datatype.default

        state = self.state
        if key in state.properties:
            value = state.properties[key]
        else:
            return default_value

        if isinstance(value, dict):
            # LocaleAware
            if language is None:
                # Language negotiation
                context = get_context()
                if context is None:
                    language = None
                else:
                    languages = [ k for k, v in value.items() if v.strip() ]
                    accept = context.request.accept_language
                    language = accept.select_language(languages)
                # Default (XXX pick one at random)
                if language is None:
                    language = value.keys()[0]
                return value[language]
            return value.get(language, default_value)
        return value


    def has_property(self, name, language=None):
        key = QName.decode(name)

        state = self.state
        if key not in state.properties:
            return False

        if language is not None:
            return language in state.properties[key]

        return True


    def set_property(self, name, value, language=None):
        self.set_changed()

        key = QName.decode(name)

        state = self.state
        # Set the value
        if language is None:
            datatype = schemas.get_datatype(key)

            default = datatype.default
            if isinstance(default, list):
                if isinstance(value, list):
                    state.properties[key] = value
                else:
                    values = state.properties.setdefault(key, [])
                    values.append(value)
            else:
                state.properties[key] = value
        else:
            values = state.properties.setdefault(key, {})
            values[language] = value

        # Update prefixes
        if key[0] is not None:
            state.prefixes.add(key[0])
        if isinstance(value, dict):
            for prefix, local_name in value:
                if prefix is not None:
                    state.prefixes.add(prefix)


    def del_property(self, name, language=None):
        key = QName.decode(name)

        state = self.state
        if key in state.properties:
            if language is None:
                self.set_changed()
                del state.properties[key]
            else:
                values = state.properties[key]
                if language in values:
                    self.set_changed()
                    del values[language]



# Register handler classes, and mimetypes
for handler_class in [ListOfUsers, Lock, Metadata]:
    register_handler_class(handler_class)
    for mimetype in handler_class.class_mimetypes:
        mimetypes.add_type(mimetype, '.%s' % handler_class.class_extension)

mimetypes.add_type('application/x-catalog', '.catalog')
