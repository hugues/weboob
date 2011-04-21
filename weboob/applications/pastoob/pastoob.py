# -*- coding: utf-8 -*-

# Copyright(C) 2011 Laurent Bachelier
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import sys

from weboob.capabilities.paste import ICapPaste, PasteNotFound
from weboob.tools.application.repl import ReplApplication


__all__ = ['Pastoob']


class Pastoob(ReplApplication):
    APPNAME = 'pastoob'
    VERSION = '0.8'
    COPYRIGHT = 'Copyright(C) 2011 Laurent Bachelier'
    DESCRIPTION = 'Console application allowing to post and get pastes from pastebins.'
    CAPS = ICapPaste

    def main(self, argv):
        self.load_config()
        return ReplApplication.main(self, argv)

    def do_show(self, _id):
        """
        show ID

        Get a paste contents.
        """
        if not _id:
            print >>sys.stderr, 'This command takes an argument: %s' % self.get_command_help('show', short=True)
            return 1

        try:
            paste = self.get_object(_id, 'get_paste', ['title'])
        except PasteNotFound:
            print >>sys.stderr, 'Paste not found: %s' %  _id
            return 2
        if not paste:
            print >>sys.stderr, 'Unable to handle paste: %s' %  _id
            return 3
        print paste.contents