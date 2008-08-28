# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.datatypes import XMLContent
from itools.handlers import TextFile, register_handler_class
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, COMMENT, TEXT



doctype = (
    '<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN"\n'
    '  "http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">\n')


class Note(object):

    def __init__(self, attributes):
        self.text = None
        self.attributes = attributes


    def to_str(self):
        s = []
        if self.attributes != {}:
            att = ['%s="%s"' % (k, self.attributes[k])
                  for k in self.attributes.keys() if k != 'lang']
            s.append('<note %s ' % ' '.join(att))
            if 'lang' in self.attributes.keys():
                s.append('xml:lang="%s"' % self.attributes['lang'])
            s.append('>')
        else:
            s.append('<note>')

        s.append(self.text)
        s.append('</note>\n')
        return ''.join(s)



class Translation(object):

    def __init__(self, attributes):
        self.source = None
        self.target = None
        self.attributes = attributes
        self.notes = []


    def to_str(self):
        s = []
        if self.attributes != {}:
            att = ['%s="%s"' % (k, self.attributes[k])
                  for k in self.attributes.keys() if k != 'space']
            s.append('<trans-unit %s ' % '\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append('>\n')
        else:
            s.append('<trans-unit>\n')

        if self.source:
            source = XMLContent.encode(self.source)
            s.append(' <source>%s</source>\n' % source)

        if self.target:
            target = XMLContent.encode(self.target)
            s.append(' <target>%s</target>\n' % target)

        for l in self.notes:
            s.append(l.to_str())

        s.append('</trans-unit>\n')
        return ''.join(s)



class File(object):

    def __init__(self, attributes):
        self.body = {}
        self.attributes = attributes
        self.header = []


    def to_str(self):
        s = []

        # Opent tag
        if self.attributes != {}:
            att = [' %s="%s"' % (k, self.attributes[k])
                  for k in self.attributes.keys() if k != 'space']
            s.append('<file %s' % '\n'.join(att))
            if 'space' in self.attributes.keys():
                s.append('xml:space="%s"' % self.attributes['space'])
            s.append('>\n')
        else:
            s.append('<file>\n')
        # The header
        if self.header:
            s.append('<header>\n')
            for l in self.header:
                s.append(l.to_str())
            s.append('</header>\n')
        # The body
        s.append('<body>\n')
        if self.body:
            mkeys = self.body.keys()
            mkeys.sort()
            msgs = '\n'.join([ self.body[m].to_str() for m in mkeys ])
            s.append(msgs)
        s.append('</body>\n')
        # Close tag
        s.append('</file>\n')

        return ''.join(s)



class XLIFF(TextFile):

    class_mimetypes = ['application/x-xliff']
    class_extension = 'xlf'

    def new(self):
        self.version = '1.0'
        self.lang = None
        self.files = []


    #######################################################################
    # Load
    def _load_state_from_file(self, file):
        self.files = []
        for event, value, line_number in XMLParser(file.read()):
            if event == START_ELEMENT:
                namespace, local_name, attributes = value
                # Attributes, get rid of the namespace uri (XXX bad)
                aux = {}
                for attr_key in attributes:
                    attr_name = attr_key[1]
                    aux[attr_name] = attributes[attr_key]
                attributes = aux

                if local_name == 'xliff':
                    self.version = attributes['version']
                    self.lang = attributes.get('lang', None)
                elif local_name == 'file':
                    file = File(attributes)
                elif local_name == 'header':
                    notes = []
                elif local_name == 'trans-unit':
                    translation = Translation(attributes)
                    notes = []
                elif local_name == 'note':
                    note = Note(attributes)
            elif event == END_ELEMENT:
                namespace, local_name = value

                if local_name == 'file':
                    self.files.append(file)
                elif local_name == 'header':
                    file.header = notes
                elif local_name == 'trans-unit':
                    translation.notes = notes
                    file.body[translation.source] = translation
                elif local_name == 'source':
                    translation.source = text
                elif local_name == 'target':
                    translation.target = text
                elif local_name == 'note':
                    note.text = text
                    notes.append(note)
            elif event == COMMENT:
                pass
            elif event == TEXT:
                text = unicode(value, 'UTF-8')


    #######################################################################
    # Save
    #######################################################################
    def to_str(self, encoding=None):
        output = []
        # The XML declaration
        output.append('<?xml version="1.0" encoding="%s"?>\n' % encoding)
        # The Doctype
        output.append(doctype)
        # <xliff>
        if self.lang:
            template = '<xliff version="%s">\n'
            output.append(template % self.version)
        else:
            template = '<xliff version="%s" xml:lang="%s">\n'
            output.append(template % (self.version, self.lang))
        # The files
        for file in self.files:
            output.append(file.to_str())
        # </xliff>
        output.append('</xliff>\n')
        # Ok
        return ''.join(output)


    #######################################################################
    # API
    #######################################################################
    def build(self, version, files):
        self.version = version
        self.files = files


    def get_languages(self):
        files_id, sources, targets = [], [], []
        for file in self.files:
            file_id = file.attributes['original']
            source = file.attributes['source-language']
            target = file.attributes.get('target-language', '')

            if file_id not in files_id:
                files_id.append(file_id)
            if source not in sources:
                sources.append(source)
            if target not in targets:
                targets.append(target)

        return ((files_id, sources, targets))



register_handler_class(XLIFF)
