# -*- coding: utf-8 -*-

# Copyright(C) 2012 Johann Broudin
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


from weboob.capabilities.bank import ICapBank, AccountNotFound
from weboob.capabilities.bank import Account, Operation
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import ValueBackendPassword
from weboob.capabilities.base import NotAvailable
from weboob.tools.browser import BrowserIncorrectPassword, BrokenPageError

from re import match
from httplib import HTTPSConnection
from urllib import urlencode

from lxml import etree
from datetime import date
from StringIO import StringIO

__all__ = ['CmbBackend']

class WrongLoginOrPassword(Exception):
     def __init__(self):
        return

class CmbBackend(BaseBackend, ICapBank):
    NAME = 'cmb'
    MAINTAINER = 'Johann Broudin'
    EMAIL = 'Johann.Broudin@6-8.fr'
    VERSION = '0.a'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = 'Credit Mutuel de Bretagne'
    CONFIG = BackendConfig(
            ValueBackendPassword('login', label='Account ID', masked=False),
            ValueBackendPassword('password', label='Password', masked=True))
    cookie = None
    headers = {
            'User-Agent':
                'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OSX; en-us) ' +
                'AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405'
            }

    def login(self):
        params = urlencode({
            'codeEspace': 'NO',
            'codeEFS': '01',
            'codeSi': '001',
            'noPersonne': self.config['login'].get(),
            'motDePasse': self.config['password'].get()
            })
        conn = HTTPSConnection("www.cmb.fr")
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        conn.request("POST",
                     "/domiweb/servlet/Identification",
                     params,
                     headers)
        response = conn.getresponse()
        if response.status == 302:
            self.cookie = response.getheader('Set-Cookie').split(';')[0]
            self.cookie += ';'
            return True
        else:
            raise BrowserIncorrectPassword()
        return False

    def iter_accounts(self):
        if not self.cookie:
            self.login()

        def do_http():
            conn = HTTPSConnection("www.cmb.fr")
            headers = self.headers
            headers['Cookie'] = self.cookie
            conn.request("GET",
                         '/domiweb/prive/particulier/releve/0-releve.act',
                         {},
                         headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            return data

        data = do_http()
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(data), parser)

        table = tree.xpath('/html/body/table')
        if len(table) == 0:
            title = tree.xpath('/html/head/title')[0].text
            if title == u"Utilisateur non identifié":
                self.login()
                data = do_http()

                parser = etree.HTMLParser()
                tree = etree.parse(StringIO(data), parser)
                table = tree.xpath('/html/body/table')
                if len(table) == 0:
                    raise BrokenPageError
            else:
                raise BrokenPageError

        for tr in table[1].getiterator('tr'):
            if tr.get('class') != 'LnTit' and tr.get('class') != 'LnTot':
                account = Account()
                td = tr.xpath('td')

                a = td[0].xpath('a')
                account.label = unicode(a[0].text).strip()
                href = a[0].get('href')
                m = match(r"javascript:releve\((.*),'(.*)','(.*)'\)",
                             href)
                account.id = unicode(m.group(1) + m.group(2) + m.group(3))
                account.cmbvaleur = m.group(1)
                account.cmbvaleur2 = m.group(2)
                account.cmbtype = m.group(3)


                balance = td[1].text
                balance = balance.replace(',','.').replace(u"\xa0",'')
                account.balance = float(balance)

                span = td[3].xpath('a/span')
                if len(span):
                    coming = span[0].text.replace(' ','').replace(',','.')
                    coming = coming.replace(u"\xa0",'')
                    account.coming = float(coming)
                else:
                    account.coming = NotAvailable

                yield account

    def get_account(self, _id):
        for account in self.iter_accounts():
            if account.id == _id:
                return account

        raise AccountNotFound()

    def iter_history(self, account):
        if not self.cookie:
            self.login()

        page = "/domiweb/prive/particulier/releve/"
        if account.cmbtype == 'D':
            page += "10-releve.act"
        else:
            page += "2-releve.act"
        page +="?noPageReleve=1&indiceCompte="
        page += account.cmbvaleur
        page += "&typeCompte="
        page += account.cmbvaleur2
        page += "&deviseOrigineEcran=EUR"

        def do_http():
            conn = HTTPSConnection("www.cmb.fr")
            headers = self.headers
            headers['Cookie'] = self.cookie
            conn.request("GET", page, {}, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close
            return data

        data = do_http()
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(data), parser)


        tables = tree.xpath('/html/body/table')
        if len(tables) == 0:
            title = tree.xpath('/html/head/title')[0].text
            if title == u"Utilisateur non identifié":
                self.login()
                data = do_http()

                parser = etree.HTMLParser()
                tree = etree.parse(StringIO(data), parser)
                tables = tree.xpath('/html/body/table')
                if len(tables) == 0:
                    raise BrokenPageError
            else:
                raise BrokenPageError

        i = 0

        for table in tables:
            if table.get('id') != "tableMouvements":
                continue
            for tr in table.getiterator('tr'):
                if (tr.get('class') != 'LnTit' and
                    tr.get('class') != 'LnTot'):
                    operation = Operation(i)
                    td = tr.xpath('td')

                    div = td[1].xpath('div')
                    d = div[0].text.split('/')
                    operation.date = date(*reversed([int(x) for x in d]))

                    div = td[2].xpath('div')
                    label = div[0].xpath('a')[0].text.replace('\n','')
                    operation.label = unicode(' '.join(label.split()))

                    amount = td[3].text
                    if amount.count(',') != 1:
                        amount = td[4].text
                        amount = amount.replace(',','.').replace(u'\xa0','')
                        print repr(amount)
                        operation.amount = float(amount)
                    else:
                        amount = amount.replace(',','.').replace(u'\xa0','')
                        operation.amount = - float(amount)

                    i += 1
                    yield operation
