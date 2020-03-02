# -*- encoding: utf-8 -*-

import unittest
import contextlib
from erppeek_wst import ClientWST
from yamlns import namespace as ns
from .claims import Claims
try:
    import dbconfig
except ImportError:
    dbconfig = None


@contextlib.contextmanager
def discarded_transaction(Client):
    t = Client.begin()
    try:
        yield t
    finally:
        t.rollback()
        t.close()


@unittest.skipIf(
    not dbconfig or not dbconfig.erppeek,
    "Requires configuring dbconfig.erppeek"
)
class Claims_Test(unittest.TestCase):

    from somutils.testutils import assertNsEqual

    @classmethod
    def setUpClass(cls):
        if not dbconfig:
            return
        if not dbconfig.erppeek:
            return
        cls.Client = ClientWST(**dbconfig.erppeek)
        cls.data_atc = dbconfig.data_atc

    def test_getAllClaims(self):
        claims = Claims(self.Client)
        reclamacions = claims.get_claims()
        reclamacio_obj = self.Client.GiscedataSubtipusReclamacio
        nombre_reclamacions = reclamacio_obj.count()

        self.assertEqual(len(reclamacions), nombre_reclamacions)

    def test_createAtcCase_ok(self):
        with discarded_transaction(self.Client) as t:
            data_crm = {
                'description': 'Some tests.',
                'section_id': 28,
                'name': 'Descripcio del cas'
            }

            claims = Claims(t)
            case_id = claims.create_atc_case(data_crm, self.data_atc)

            last_atc_case_id = self.Client.GiscedataAtc.search()[-1]
            self.assertEqual(case_id, last_atc_case_id)


# vim: et ts=4 sw=4
