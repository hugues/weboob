# -*- coding: utf-8 -*-

# Copyright(C) 2013      Bezleputh
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


from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.ordereddict import OrderedDict
from weboob.capabilities.job import ICapJob
from weboob.tools.value import Value
from .browser import IndeedBrowser
from .job import IndeedJobAdvert

__all__ = ['IndeedBackend']


class IndeedBackend(BaseBackend, ICapJob):
    NAME = 'indeed'
    DESCRIPTION = u'indeed website'
    MAINTAINER = u'Bezleputh'
    EMAIL = 'carton_ben@yahoo.fr'
    LICENSE = 'AGPLv3+'
    VERSION = '0.h'

    BROWSER = IndeedBrowser

    type_contrat_choices = OrderedDict([(k, u'%s' % (v)) for k, v in sorted({
        'all': u'Tous les emplois',
        'fulltime': u'Temps plein',
        'parttime': u'Temps partiel',
        'contract': u'Durée indéterminée',
        'internship': u'Stage / Apprentissage',
        'temporary': u'Durée déterminée',
    }.iteritems())])

    limit_date_choices = OrderedDict([(k, u'%s' % (v)) for k, v in sorted({
        'any': u'à tout moment',
        '15': u'depuis 15 jours',
        '7': u'depuis 7 jours',
        '3': u'depuis 3 jours',
        '1': u'depuis hier',
        'last': u'depuis ma dernière visite',
    }.iteritems())])

    CONFIG = BackendConfig(Value('metier', label=u'Job name', masked=False, default=''),
                           Value('limit_date', label=u'Date limite', choices=limit_date_choices, default=''),
                           Value('contrat', label=u'Contract', choices=type_contrat_choices, default=''))

    def search_job(self, pattern=None):
        with self.browser:
            return self.browser.search_job(pattern=pattern)

    def advanced_search_job(self):
        return self.browser.advanced_search_job(metier=self.config['metier'].get(),
                                                limit_date=self.config['limit_date'].get(),
                                                contrat=self.config['contrat'].get(),)

    def get_job_advert(self, _id, advert=None):
        with self.browser:
            return self.browser.get_job_advert(_id, advert)

    def fill_obj(self, advert, fields):
        self.get_job_advert(advert.id, advert)

    OBJECTS = {IndeedJobAdvert: fill_obj}
