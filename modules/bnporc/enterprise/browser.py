# -*- coding: utf-8 -*-

# Copyright(C) 2013      Laurent Bachelier
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


from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword

from .pages import LoginPage, AccountsPage, UnknownPage

__all__ = ['BNPEnterprise']


class BNPEnterprise(BaseBrowser):
    DOMAIN = 'entreprisesplus.bnpparibas.net'
    PROTOCOL = 'https'
    CERTHASH = '423f68a8162d1328bacb48269675d8b8577ebcc9d222860de8421792c4d222c1'

    PAGES = {'%s://%s/NSAccess.*' % (PROTOCOL, DOMAIN): LoginPage,
             '%s://%s/UNE\?.*' % (PROTOCOL, DOMAIN): AccountsPage,
             '%s://%s/NSFR' % (PROTOCOL, DOMAIN): UnknownPage}

    def home(self):
        self.location('%s://%s/NSAccess' % (self.PROTOCOL, self.DOMAIN))

    def is_logged(self):
        if self.page:
            if self.page.get_error() is not None:
                return False
        return not self.is_on_page(LoginPage)

    def login(self):
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)
        assert self.password.isdigit()

        if not self.is_on_page(LoginPage):
            self.home()

        self.page.login(self.username, self.password)
        self.location('/UNE?ch6=0&ch8=2000&chA=1&chh=O', no_login=True)

        if not self.is_logged():
            raise BrowserIncorrectPassword()

    def get_accounts_list(self):
        # options shows accounts in their original currency
        # it's the "en capitaux" mode, not sure if it's the best
        # the "en valeur" mode is ch8=1000
        self.location('/UNE?ch6=0&ch8=2000&chA=1&chh=O')
        for account in self.page.get_list():
            yield account
