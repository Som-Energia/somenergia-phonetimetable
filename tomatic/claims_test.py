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

    def test_getAllClaims(self):
        claims = Claims(self.O)
        reclamacions = claims.get_claims()
        reclamacio_obj = self.O.GiscedataSubtipusReclamacio
        nombre_reclamacions = reclamacio_obj.count()

        self.assertEqual(len(reclamacions), nombre_reclamacions)


# vim: et ts=4 sw=4
