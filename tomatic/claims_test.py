# -*- encoding: utf-8 -*-

import contextlib
import unittest
import os
from consolemsg import error
from datetime import datetime
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

    # @unittest.skip("WIP: how to undo transaction")
    def test_createAtcCase_ok(self):
        today = datetime.today()
        file_name = "atc_cases/{}{}{}.yaml".format(
            today.year,
            today.month if today.month//10 != 0 else "0{}".format(today.month),
            today.day if today.day//10 != 0 else "0{}".format(today.day)
        )
        if not os.path.isfile(file_name):
            error("The file {} does not exists", file_name)
        else:
            atc_cases = ns.load(file_name)

            with discarded_transaction(self.Client) as t:
                for person in atc_cases:
                    for case in atc_cases[person]:
                        claims = Claims(t)
                        case_id = claims.create_atc_case(case)
                        last_atc_case_id = t.GiscedataAtc.search()[-1]
                        self.assertEqual(case_id, last_atc_case_id)


# vim: et ts=4 sw=4
