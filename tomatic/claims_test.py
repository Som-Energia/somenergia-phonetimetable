# -*- encoding: utf-8 -*-

import unittest
import os
from consolemsg import error
from erppeek_wst import ClientWST
from yamlns import namespace as ns
from xmlrpc import client as xmlrpclib
from .claims import Claims
try:
    import dbconfig
except ImportError:
    dbconfig = None


@unittest.skipIf(
    not dbconfig or not dbconfig.erppeek,
    "Requires configuring dbconfig.erppeek"
)
class Claims_Test(unittest.TestCase):

    def setUp(self):
        if not dbconfig:
            return
        if not dbconfig.erppeek:
            return
        self.erp = ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.data_atc = dbconfig.data_atc

    def tearDown(self):
        try:
            self.erp.rollback()
            self.erp.close()
        except xmlrpclib.Fault as e:
            if 'transaction block' not in e.faultCode:
                raise

    def test_getAllClaims(self):
        claims = Claims(self.erp)
        reclamacions = claims.get_claims()
        Reclamacio = self.erp.GiscedataSubtipusReclamacio
        nombre_reclamacions = Reclamacio.count()
        self.assertEqual(len(reclamacions), nombre_reclamacions)

    def test_createAtcCase_basicCase(self):
        file_name = "testdata/atc_basicCase.yaml"
        if not os.path.isfile(file_name):
            error("The file {} does not exists", file_name)
        else:
            atc_cases = ns.load(file_name)
            for person in atc_cases:
                for case in atc_cases[person]:
                    claims = Claims(self.erp)
                    case_id = claims.create_atc_case(case)
                    last_atc_case_id = self.erp.GiscedataAtc.search()[-1]
                    self.assertEqual(case_id, last_atc_case_id)

    def test_createAtcCase_multipleCases(self):
        file_name = "testdata/atc_multipleCases.yaml"
        if not os.path.isfile(file_name):
            error("The file {} does not exists", file_name)
        else:
            atc_cases = ns.load(file_name)
            for person in atc_cases:
                for case in atc_cases[person]:
                    claims = Claims(self.erp)
                    case_id = claims.create_atc_case(case)
                    last_atc_case_id = self.erp.GiscedataAtc.search()[-1]
                    self.assertEqual(case_id, last_atc_case_id)

    def test_createAtcCase_multiplePersons(self):
        file_name = "testdata/atc_multiplePersons.yaml"
        if not os.path.isfile(file_name):
            error("The file {} does not exists", file_name)
        else:
            atc_cases = ns.load(file_name)
            for person in atc_cases:
                for case in atc_cases[person]:
                    claims = Claims(self.erp)
                    case_id = claims.create_atc_case(case)
                    last_atc_case_id = self.erp.GiscedataAtc.search()[-1]
                    self.assertEqual(case_id, last_atc_case_id)


# vim: et ts=4 sw=4
