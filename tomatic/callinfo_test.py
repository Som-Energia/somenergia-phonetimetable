# -*- coding: utf-8 -*-

import unittest
from callinfo import CallInfo
import ooop
try:
    import dbconfig
except ImportError:
    dbconfig = None

@unittest.skipIf(not dbconfig or not dbconfig.ooop,
    "Requires configuring dbconfig.ooop")
class CallInfo_Test(unittest.TestCase):

    def setUp(self):
        print "setup"

    @classmethod
    def setUpClass(cls):
        print "classSetUp"
        cls.O = ooop.OOOP(**dbconfig.ooop)

    def test_searchAddressByPhone_whenMatchesNone(self):
        info = CallInfo(self.O)
        ids = info.searchAddresByPhone('badphone')
        self.assertEqual(ids, [])

    def test_searchAddressByPhone_whenMatchesOnePhone(self):
        info = CallInfo(self.O)
        ids = info.searchAddresByPhone('933730976')
        self.assertEqual(ids, [12073])

    def test_searchAddressByPhone_whenMatchesMoreThanOnePhone(self):
        info = CallInfo(self.O)
        ids = info.searchAddresByPhone('659509872')
        self.assertEqual(ids, [2286, 42055, 43422])

    def test_searchPartnerByAddressId_whenMatchesNone(self):
        info = CallInfo(self.O)
        partner_ids = info.searchPartnerByAddressId([999999999])
        self.assertEqual(partner_ids,[])

    def test_searchPartnerByAddressId_whenMatchesOnePartner(self):
        info = CallInfo(self.O)
        partner_ids = info.searchPartnerByAddressId([12073])
        self.assertEqual(partner_ids, [11709])

    def test_searchPartnerByAddressId_whenEmpty(self):
        info = CallInfo(self.O)
        partner_ids = info.searchPartnerByAddressId([])
        self.assertEqual(partner_ids, [])

    def test_searchPartnerByAddressId_whenAddreswithNoPartner(self):
        info = CallInfo(self.O)
        partner_ids = info.searchPartnerByAddressId([67234])
        self.assertEqual(partner_ids, [])

    def test_searchPartnerByAddressId_whenMatchesMoreThanOnePartner(self):
        info = CallInfo(self.O)
        partner_ids = info.searchPartnerByAddressId([2286, 42055, 43422])
        self.assertEqual(partner_ids, [410, 39933, 41193])

    def test_searchPartnerByAddressId_whenMatchesMoreThanOnePartnerAndNotFound(self):
        info = CallInfo(self.O)
        partner_ids = info.searchPartnerByAddressId([2286, 42055, 43422, 999999999])
        self.assertEqual(partner_ids, [410, 39933, 41193])

unittest.TestCase.__str__ = unittest.TestCase.id


# vim: ts=4 sw=4 et
