# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2006 Juan David Ib��ez Palomar <jdavid@itaapy.com>
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


class AccessControl(object):
    """
    Base class to control access. Provides default implementation; maybe
    overriden.
    """

    def is_access_allowed(self, user, object, method_name):
        """
        Returns True if the given user is allowed to access the given method
        of the given object. False otherwise.
        """
        # Get the access control definition (default to False)
        access = getattr(object, '%s__access__' % method_name, False)

        # Private (False) or Public (True)
        if isinstance(access, bool):
            return access

        # Access Control through a method
        if isinstance(access, str):
            method = getattr(self, access, None)
            if method is None:
                raise ValueError, 'access control "%s" not defined' % access

            return method(user, object)

        # Only booleans and strings are allowed
        raise TypeError, 'unexpected value "%s"' % access


    def get_method(self, user, object, method):
        """
        If the given user is allowed to access the given method in the given
        object, return the method. Otherwise return None.
        """
        if self.is_access_allowed(user, object, method):
            # We assume the method is defined
            return getattr(object, method)

        return None


    #########################################################################
    # Basic Controls
    def is_authenticated(self, user, object):
        return user is not None
