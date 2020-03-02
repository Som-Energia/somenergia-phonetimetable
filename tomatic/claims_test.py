# -*- encoding: utf-8 -*-

import unittest
from yamlns import namespace as ns
from .claims import Claims
import erppeek
try:
    import dbconfig
except ImportError:
    dbconfig = None


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
        cls.O = erppeek.Client(**dbconfig.erppeek)
        cls.data_atc = dbconfig.data_atc

    def test_getAllClaims(self):
        claims = Claims(self.O)
        reclamacions = claims.get_claims()
        reclamacio_obj = self.O.GiscedataSubtipusReclamacio
        nombre_reclamacions = reclamacio_obj.count()

        self.assertEqual(len(reclamacions), nombre_reclamacions)

    @unittest.skip('WIP')
    def test_createAtcCase_ok(self):
        # with discarded_transaction(O) as t:
        data_crm = {
            'description': 'Some tests.',
            'section_id': 28,
            'name': 'Descripcio del cas'
        }

        claims = Claims(self.O)
        case_id = claims.create_atc_case(data_crm, self.data_atc)

        self.assertEqual(case_id, 5)


# vim: et ts=4 sw=4
