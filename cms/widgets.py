# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from operator import attrgetter
from string import Template

# Import from itools
from itools.uri import Path
from itools.handlers.Folder import Folder
from itools.web import get_context

# Import from itools.cms
from utils import get_parameters
from Handler import Handler



def sortcontrol(column, sortby, sortorder):
    """
    Returns an html snippet with a link that lets to order a column
    in a table.
    """
    # Process column
    if isinstance(column, (str, unicode)):
        column = [column]

    # Calculate the href
    data = {}
    data['sortby'] = column

    if sortby == column:
        value = sortorder
        if sortorder == 'up':
            data['sortorder'] = 'down'
        else:
            data['sortorder'] = 'up'
    else:
        value = 'none'
        data['sortorder'] = 'up'

    href = get_context().uri.replace(**data)
    return href, value


class Breadcrumb(object):
    """
    Instances of this class will be used as namespaces for STL templates.
    The built namespace contains the breadcrumb, that is to say, the path
    from the tree root to another tree node, and the content of that node.
    """

    def __init__(self, filter_type=Handler, root=None, start=None):
        """
        The 'start' must be a handler, 'filter_type' must be a handler class.
        """
        context = get_context()
        request, response = context.request, context.response

        if root is None:
            root = context.root
        if start is None:
            start = root

        here = context.handler

        # Get the query parameters
        parameters = get_parameters('bc', id=None, target=None)
        id = parameters['id']
        # Get the target folder
        target_path = parameters['target']
        if target_path is None:
            if isinstance(start, Folder):
                target = start
            else:
                target = start.parent
        else:
            target = root.get_handler(target_path)

        # XXX Obsolete code
        self.style = 'style'
##        self.style = '../' * len(start.get_abspath().split('/')) + 'style'

        # Object to link
        object = request.form.get('object')
        if object == '':
            object = '.'
        self.object = object

        # The breadcrumb
        breadcrumb = []
        node = target
        while node is not root.parent:
            url = context.uri.replace(bc_target=str(root.get_pathto(node)))
            breadcrumb.insert(0, {'name': node.name, 'url': url})
            node = node.parent
        self.path = breadcrumb

        # Content
        objects = []
        self.is_submit = False
        user = context.user
        filter = (Folder, filter_type)
        for handler in target.search_handlers(handler_class=filter):
            ac = handler.get_access_control()
            if not ac.is_allowed_to_view(user, handler):
                continue

            path = here.get_pathto(handler)
            bc_target = str(root.get_pathto(handler))
            url = context.uri.replace(bc_target=bc_target)

            self.is_submit = True
            # Calculate path
            path_to_icon = handler.get_path_to_icon(16)
            if path:
                path_to_handler = Path(str(path) + '/')
                path_to_icon = path_to_handler.resolve(path_to_icon)
            objects.append({'name': handler.name,
                            'is_folder': isinstance(handler, Folder),
                            'is_selectable': True,
                            'path': path,
                            'url': url,
                            'icon': path_to_icon,
                            'object_type': handler.get_mimetype()})

        self.objects = objects

        # Avoid general template
        response.set_header('Content-Type', 'text/html; charset=UTF-8')



pattern1 = Template(
    '<dt><a href="${href}" class="${class}"><img src="${src}" alt=""'
    ' width="16" height="16" /> ${title}</a></dt>\n'
    '<dd>\n'
    '  <dl>\n'
    '  ${children}\n'
    '  </dl>\n'
    '</dd>\n')

pattern2 = Template(
    '<dt><span class="${class}"><img src="${src}" alt="" width="16"'
    ' height="16" /> ${title}</span></dt>\n'
    '<dd>\n'
    '  <dl>\n'
    '  ${children}\n'
    '  </dl>\n'
    '</dd>\n')


def _tree(context, handler, depth):
    from Folder import Folder

    # Define local variables
    here = context.handler
    here_path = str(context.path)
    handler_path = handler.abspath
    in_path = here_path.startswith(handler_path)

    # Choose the pattern to use
    firstview = handler.get_firstview()
    if firstview is None:
        pattern = pattern2
    else:
        pattern = pattern1

    # Build the namespace
    namespace = {}
    namespace['src'] = handler.get_path_to_icon(size=16, from_handler=here)
    namespace['title'] = handler.get_title_or_name()
    if firstview is not None:
        if handler_path == '/':
            namespace['href'] = '/;%s' % firstview
        else:
            namespace['href'] = '%s/;%s' % (handler_path, firstview)

    # The CSS style
    namespace['class'] = ''
    if here_path == handler_path:
        namespace['class'] = 'nav_active'

    # The children
    namespace['children'] = ''
    if in_path:
        if depth > 0:
            depth = depth - 1
            user = context.user
            children = []
            for child in handler.search_handlers(handler_class=Folder):
                ac = child.get_access_control()
                if ac.is_allowed_to_view(user, child):
                    children.append(_tree(context, child, depth))
            namespace['children'] = '\n'.join(children)
 
    return pattern.substitute(namespace)



def tree(context, root=None, depth=6):
    if root is None:
        root = context.root

    return '<dl>\n' + _tree(context, root, depth) + '</dl>\n'

