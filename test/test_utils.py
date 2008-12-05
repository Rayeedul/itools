# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.utils import freeze, frozenlist


a_frozen_list = freeze([1, 2, 3])


class FrozenlistTestCase(TestCase):

    def test_freeze(self):
        alist = [1, 2, 3]
        self.assertEqual(freeze(alist), alist)


    #######################################################################
    # Mutable operations must raise 'TypeError'
    #######################################################################
    def test_append(self):
        self.assertRaises(TypeError, a_frozen_list.append, 5)


    def test_extend(self):
        self.assertRaises(TypeError, a_frozen_list.extend, [1,2,3])


    def test_del_item(self):
        try:
            del a_frozen_list[0]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_del_slice(self):
        try:
            del a_frozen_list[0:2]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_incremental_add(self):
        a_frozen_list = freeze([1, 2, 3])
        try:
            a_frozen_list += [4, 5]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_incremental_mul(self):
        a_frozen_list = freeze([1, 2, 3])
        try:
            a_frozen_list *= 2
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_setitem(self):
        try:
            a_frozen_list[1] = 5
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_setslice(self):
        try:
            a_frozen_list[0:2] = [5]
        except TypeError:
            pass
        else:
            self.assert_(False)


    def test_insert(self):
        self.assertRaises(TypeError, a_frozen_list.insert, 0, 1)


    def test_pop(self):
        self.assertRaises(TypeError, a_frozen_list.pop)


    def test_remove(self):
        self.assertRaises(TypeError, a_frozen_list.remove, 1)


    def test_reverse(self):
        self.assertRaises(TypeError, a_frozen_list.reverse)


    def test_sort(self):
        self.assertRaises(TypeError, a_frozen_list.sort)


    #######################################################################
    # Test semantics of non-mutable operations
    #######################################################################
    def test_concatenation(self):
        """Like set objects, the concatenation of a frozenlist and a list
        must preserve the type of the left argument.
        """
        # frozenlist + frozenlist
        alist = freeze([]) + freeze([])
        self.assert_(isinstance(alist, frozenlist))
        # frozenlist + list
        alist = freeze([]) + []
        self.assert_(isinstance(alist, frozenlist))
        # list + frozenlist
        alist = [] + freeze([])
        self.assert_(not isinstance(alist, frozenlist))


    def test_equality(self):
        self.assertEqual(freeze([1, 2, 3]), [1, 2, 3])


    def test_multiplication(self):
        # frozenlist * n
        alist = freeze([1, 2]) * 2
        self.assert_(isinstance(alist, frozenlist))
        self.assertEqual(alist, [1, 2, 1, 2])
        # n * frozenlist
        alist = 2 * freeze([1, 2])
        self.assert_(isinstance(alist, frozenlist))
        self.assertEqual(alist, [1, 2, 1, 2])


    def test_representation(self):
        self.assertEqual(repr(a_frozen_list), 'frozenlist([1, 2, 3])')



if __name__ == '__main__':
    unittest.main()