# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Taverne Sylvain <taverne.sylvain@gmail.com>
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

# Import from the Standard Library

# Local imports
from dispatcher import URIDispatcher
from router import BaseRouter

class DispatchRouter(BaseRouter):

    dispatcher = URIDispatcher()

    def add_route(self, pattern, view):
        self.dispatcher.add(pattern, view)


    def handle_request(self, method_name, context):
        # TODO: Write code
        response = self.dispatcher.select(str(context.path))
        if response:
            view, query = response
            entity = view.GET(query)
            status = 200
        else:
            status = 404
            entity = 'error'
        context.status = status
        context.entity = entity
        context.soup_message.set_status(status)
        context.soup_message.set_response('text/plain', entity)
        context.set_content_type('text/plain', charset='UTF-8')
        return context