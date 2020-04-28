# -*- coding: utf-8 -*-

import unittest
import b2btest
import os
from yamlns import namespace as ns
from .callinfo import CallInfo

import erppeek
try:
    import dbconfig
except ImportError:
    dbconfig = None


@unittest.skipIf(os.environ.get("TRAVIS"),
    "Database not available in Travis")
@unittest.skipIf(not dbconfig or not dbconfig.erppeek,
    "Requires configuring dbconfig.erppeek")
class CallInfo_Test(unittest.TestCase):

    from somutils.testutils import assertNsEqual

    def setUp(self):
        self.maxDiff = None
        self.b2bdatapath = "testdata"

    def ns(self, content):
        return ns.loads(content)

    @classmethod
    def setUpClass(cls):
        if os.environ.get("TRAVIS"): return
        if not dbconfig: return
        if not dbconfig.erppeek: return
        cls.O = erppeek.Client(**dbconfig.erppeek)

    def test_addressByPhone_whenMatchesNone(self):
        info = CallInfo(self.O)
        ids = info.addressByPhone('badphone')
        self.assertEqual(ids, [])

    def test_addressByPhone_whenMatchesOnePhone(self):
        info = CallInfo(self.O)
        ids = info.addressByPhone('933730976')
        self.assertEqual(ids, [12073])

    def test_addressByPhone_whenMatchesMoreThanOnePhone(self):
        info = CallInfo(self.O)
        ids = info.addressByPhone('659509872')
        self.assertEqual(ids, [2286, 42055, 43422])

    def test_addressByPhone_whenMatchesOneMobile(self):
        info = CallInfo(self.O)
        ids = info.addressByPhone('699515879')
        self.assertEqual(ids, [34])

    def test_addressByPhone_whenMatchesMoreThanOneMobile(self):
        info = CallInfo(self.O)
        ids = info.addressByPhone('630079522')
        self.assertEqual(ids, [33, 42])

    def test_addressByEmail_whenMatchesNone(self):
        info = CallInfo(self.O)
        ids = info.addressByEmail('badmail')
        self.assertEqual(ids, [])

    def test_addressByEmail_whenMatchesOne(self):
        info = CallInfo(self.O)
        ids = info.addressByEmail('testing@somenergia.coop')
        self.assertEqual(ids, [81065])

    def test_addressByEmail_moreThanOne(self):
        info = CallInfo(self.O)
        ids = info.addressByEmail('testing2@somenergia.coop')
        self.assertEqual(ids, [42750, 52543])

    def test_addressByEmail_partial(self):
        info = CallInfo(self.O)
        ids = info.addressByEmail('testing%')
        self.assertEqual(ids, [42750, 52543, 81065])

    def test_partnerBySoci_whenMatchesNone(self):
        info = CallInfo(self.O)
        ids = info.partnerBySoci('badsoci')
        self.assertEqual(ids, [])

    def test_partnerBySoci_whenMatchesOne(self):
        info = CallInfo(self.O)
        ids = info.partnerBySoci('S000197')
        self.assertEqual(ids, [217])

    def test_partnerBySoci_partial(self):
        info = CallInfo(self.O)
        ids = info.partnerBySoci('S00019')
        self.assertEqual(
            ids,
            [215, 212, 209, 210, 217, 208, 216, 218, 214, 219]
        )

    def test_partnerByDni_whenMatchesNone(self):
        info = CallInfo(self.O)
        ids = info.partnerByDni('baddni')
        self.assertEqual(ids, [])

    def test_partnerByDni_whenMatchesOne(self):
        info = CallInfo(self.O)
        ids = info.partnerByDni(dbconfig.personaldata["nif"])
        self.assertEqual(ids, [217])

    def test_partnerByDni_partial(self):
        info = CallInfo(self.O)
        ids = info.partnerByDni(dbconfig.personaldata["nif"][:-3])
        self.assertEqual(ids, [133888, 72676, 217])

    def test_partnerByName_whenMatchesNone(self):
        info = CallInfo(self.O)
        ids = info.partnerByName('badname')
        self.assertEqual(ids, [])

    def test_partnerByName_whenMatchesOne(self):
        info = CallInfo(self.O)
        complete_name = dbconfig.personaldata["surname"]
        complete_name += ", "
        complete_name += dbconfig.personaldata["name"]
        ids = info.partnerByName(
            complete_name
        )
        self.assertEqual(ids, [217])

    def test_partnerByName_partial(self):
        info = CallInfo(self.O)
        ids = info.partnerByName(dbconfig.personaldata["surname"][:-3])
        self.assertEqual(ids, [67747, 217])

    def test_partnerByAddressId_whenMatchesNone(self):
        info = CallInfo(self.O)
        partner_ids = info.partnerByAddressId([999999999])
        self.assertEqual(partner_ids, [])

    def test_partnerByAddressId_whenMatchesOnePartner(self):
        info = CallInfo(self.O)
        partner_ids = info.partnerByAddressId([12073])
        self.assertEqual(partner_ids, [11709])

    def test_partnerByAddressId_whenEmpty(self):
        info = CallInfo(self.O)
        partner_ids = info.partnerByAddressId([])
        self.assertEqual(partner_ids, [])

    def test_partnerByAddressId_whenAddreswithNoPartner(self):
        info = CallInfo(self.O)
        partner_ids = info.partnerByAddressId([67234])
        self.assertEqual(partner_ids, [])

    def test_partnerByAddressId_whenMatchesMoreThanOnePartner(self):
        info = CallInfo(self.O)
        partner_ids = info.partnerByAddressId([2286, 42055, 43422])
        self.assertEqual(partner_ids, [410, 39933, 41193])

    def test_partnerByAddressId_whenMatchesMoreThanOnePartnerAndNotFound(self):
        info = CallInfo(self.O)
        partner_ids = info.partnerByAddressId([2286, 42055, 43422, 999999999])
        self.assertEqual(partner_ids, [410, 39933, 41193])

    def test_getPartnerRelatedContracts_when_none(self):
        info = CallInfo(self.O)
        contracts_ids = info.getPartnerRelatedContracts(None)
        self.assertEqual(contracts_ids, [])

    def test_getPartnerRelatedContracts_when_soci5(self):
        info = CallInfo(self.O)
        contracts_ids = info.getPartnerRelatedContracts(410)
        self.assertEqual(contracts_ids, [155, 56427, 58367, 69104])

    def test_getPartnerRelatedContracts_when_convidat(self):
        info = CallInfo(self.O)
        contracts_ids = info.getPartnerRelatedContracts(134916)
        self.assertEqual(contracts_ids, [207413])

    def test_partnerInfo_whenMatchesOne(self):
        info = CallInfo(self.O, anonymize=True)
        data = self.O.ResPartner.read([410], [
            'city',
            'www_email',
            'www_provincia',
            'www_municipi',
            'polisses_ids',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
            'category_id',
        ])[0]
        partner_data = info.partnerInfo(ns(data))
        self.assertNsEqual(partner_data, """\
            lang: ca_ES
            name: ...iol
            city: Vilanova de Bellpuig
            email: ...oop
            id_soci: ...367
            state: Lleida
            dni: ...82V
            ov: True
            energetica: False
            """)

    def test_partnerInfo_whenMatchesOne_noOV(self):
        info = CallInfo(self.O, anonymize=True)
        data = self.O.ResPartner.read([51444], [
            'city',
            'www_email',
            'www_provincia',
            'www_municipi',
            'polisses_ids',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
            'category_id',
        ])[0]
        partner_data = info.partnerInfo(ns(data))
        self.assertNsEqual(partner_data, """\
            lang: es_ES
            name: ...avo
            city: Barcelona
            email: ...oop
            id_soci: ...225
            state: Barcelona
            dni: ...36L
            ov: True
            energetica: False
            """)

    def test_partnerInfo_whenMatchesOne_energetica(self):
        info = CallInfo(self.O, anonymize=True)
        data = self.O.ResPartner.read([29460], [
            'city',
            'www_email',
            'www_provincia',
            'www_municipi',
            'polisses_ids',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
            'category_id',
        ])[0]
        partner_data = info.partnerInfo(ns(data))
        self.assertNsEqual(partner_data, """\
            lang: es_ES
            name: ...sar
            city: Valladolid
            email: ...oop
            id_soci: ...295
            state: Valladolid
            dni: ...88S
            ov: True
            energetica: True
            """)

    def test_partnerInfo_whenNoProvincia(self):
        info = CallInfo(self.O, anonymize=True)
        data = self.O.ResPartner.read([49781], [
            'city',
            'www_email',
            'www_provincia',
            'www_municipi',
            'polisses_ids',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
            'category_id',
        ])[0]
        partner_data = info.partnerInfo(ns(data))
        self.assertNsEqual(partner_data, """\
            lang: es_ES
            name: ...cal
            city: Valencia
            email: ...oop
            id_soci: ...533
            state: ''
            dni: ...13X
            ov: True
            energetica: False
            """)

    def test_partnerInfo_whenNoMunicipi(self):
        info = CallInfo(self.O, anonymize=True)
        data = self.O.ResPartner.read([3293], [
            'city',
            'www_email',
            'www_provincia',
            'www_municipi',
            'polisses_ids',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
            'category_id',
        ])[0]
        partner_data = info.partnerInfo(ns(data))
        self.assertNsEqual(partner_data, """\
            lang: ca_ES
            name: ...ena
            city: ''
            email: ...oop
            id_soci: ''
            state: Barcelona
            dni: ...82J
            ov: True
            energetica: False
            """)

    def test_partnersInfo_whenMatchesOne(self):
        info = CallInfo(self.O, anonymize=True)
        partner_data = info.partnersInfo([410])
        self.assertNsEqual(partner_data, """\
            partners:
            -
              lang: ca_ES
              city: Vilanova de Bellpuig
              state: Lleida
              name: ...iol
              id_soci: ...367
              email: ...oop
              dni: ...82V
              ov: True
              energetica: False
              contracts:
              -
                end_date: ''
                cups: ...F0F
                start_date: '2011-11-19'
                state: activa
                power: 3.45
                fare: 2.0DHA
                number: '0000155'
                last_invoiced: '2020-01-20'
                suspended_invoicing: false
                pending_state: 'Correct'
                has_open_r1s: False
                has_open_bs: False
                is_titular: True
                is_partner: True
                is_notifier: True
                is_payer: True
                cups_adress: '...ig)'
                titular_name: '...iol'
                energetica: False
                generation: True
              -
                end_date: ''
                cups: ...H0F
                start_date: '2015-07-17'
                state: activa
                power: 1.15
                fare: 2.0A
                number: '0028042'
                last_invoiced: '2020-01-20'
                suspended_invoicing: false
                pending_state: 'Correcte'
                has_open_r1s: False
                has_open_bs: False
                is_titular: False
                is_partner: True
                is_notifier: True
                is_payer: True
                cups_adress: '...ig)'
                titular_name: '...xes'
                energetica: False
                generation: True
              -
                end_date: ''
                cups: ...A0F
                start_date: '2015-10-21'
                state: activa
                power: 4.6
                fare: 2.0DHA
                number: '0029062'
                last_invoiced: '2020-01-19'
                suspended_invoicing: false
                pending_state: 'Correct'
                has_open_r1s: false
                has_open_bs: false
                is_titular: false
                is_partner: true
                is_notifier: false
                is_payer: false
                cups_adress: '...ig)'
                titular_name: '...ero'
                energetica: False
                generation: False
              -
                end_date: ''
                cups: ...V0F
                start_date: '2016-02-18'
                state: activa
                power: 3.45
                fare: 2.0DHA
                number: '0034613'
                last_invoiced: '2020-01-19'
                suspended_invoicing: false
                pending_state: 'Correct'
                has_open_r1s: false
                has_open_bs: false
                is_titular: false
                is_partner: true
                is_notifier: false
                is_payer: false
                cups_adress: '...ig)'
                titular_name: '...nia'
                energetica: False
                generation: False
            """)

    def test_contractInfo_whenAskNone(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([0], 1234)
        self.assertNsEqual(contractsData, """\
            contracts: []
            """)

    def test_contractInfo_whenAskOne(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([155], 410)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...F0F
              start_date: '2011-11-19'
              state: activa
              power: 3.45
              fare: 2.0DHA
              number: '0000155'
              last_invoiced: '2020-01-20'
              suspended_invoicing: false
              pending_state: 'Correct'
              has_open_r1s: False
              has_open_bs: False
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...ig)'
              titular_name: '...iol'
              energetica: False
              generation: True
            """)

    def test_contractInfo_whenNoSoci(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([14817], 13597)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...N0F
              start_date: '2013-08-21'
              state: activa
              power: 3.45
              fare: 2.0A
              number: '0008597'
              last_invoiced: '2020-01-11'
              suspended_invoicing: false
              pending_state: 'Correct'
              has_open_r1s: False
              has_open_bs: False
              is_titular: True
              is_partner: False
              is_notifier: False
              is_payer: False
              cups_adress: '...rú)'
              titular_name: '...ger'
              energetica: False
              generation: False
            """)

    def test_contractInfo_whenEnergetica(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([102631], 69906)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...D0F
              start_date: '2017-03-02'
              state: activa
              power: 3.3
              fare: 2.0A
              number: '0051861'
              last_invoiced: '2020-01-15'
              suspended_invoicing: false
              pending_state: 'Correct'
              has_open_r1s: False
              has_open_bs: False
              is_titular: True
              is_partner: False
              is_notifier: True
              is_payer: True
              cups_adress: '...ón)'
              titular_name: '...tín'
              energetica: True
              generation: False
            """)

    def test_contractInfo_whenAskOne_withR1(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([231889], 57407)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...K0F
              start_date: '2019-07-30'
              state: activa
              power: 4.4
              fare: 2.0A
              number: '0123347'
              last_invoiced: '2019-12-09'
              suspended_invoicing: true
              pending_state: 'Correct'
              has_open_r1s: True
              has_open_bs: False
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...La)'
              titular_name: '...cís'
              energetica: False
              generation: False
            """)

    def test_contractInfo_whenAskOne_withB1(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([227854], 146156)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...Z0F
              start_date: '2019-05-23'
              state: activa
              power: 3.464
              fare: 2.0DHA
              number: '0119312'
              last_invoiced: '2020-01-25'
              suspended_invoicing: false
              pending_state: 'Tall'
              has_open_r1s: False
              has_open_bs: True
              is_titular: True
              is_partner: False
              is_notifier: True
              is_payer: True
              cups_adress: '...es)'
              titular_name: '...Mar'
              energetica: False
              generation: False
            """)

    def test_contractInfo_whenAskOne_titular_not_partner(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([4], 2104)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...X0F
              start_date: '2011-11-22'
              state: activa
              power: 3.4
              fare: 2.0A
              number: '0000004'
              last_invoiced: '2020-01-14'
              suspended_invoicing: false
              pending_state: 'Correct'
              has_open_r1s: False
              has_open_bs: False
              is_titular: True
              is_partner: False
              is_notifier: True
              is_payer: True
              cups_adress: '...na)'
              titular_name: '...rat'
              energetica: False
              generation: False
            """)

    def test_contractInfo_whenAskMore(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([155, 250], 410)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              start_date: '2011-11-19'
              end_date: ''
              cups: ...F0F
              state: activa
              power: 3.45
              fare: 2.0DHA
              number: '0000155'
              last_invoiced: '2020-01-20'
              suspended_invoicing: false
              pending_state: 'Correct'
              has_open_r1s: False
              has_open_bs: False
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...ig)'
              titular_name: '...iol'
              energetica: False
              generation: True
            -
              start_date: '2012-03-29'
              end_date: ''
              cups: ...P0F
              state: activa
              power: 3.45
              fare: 2.0A
              number: '0000250'
              last_invoiced: '2020-01-21'
              suspended_invoicing: false
              pending_state: 'Correct'
              has_open_r1s: False
              has_open_bs: False
              is_titular: False
              is_partner: False
              is_notifier: False
              is_payer: False
              cups_adress: '...na)'
              titular_name: '...nna'
              energetica: False
              generation: True
            """)

    def test_getPartnerRelatedContracts_ordered(self):
        info = CallInfo(self.O, anonymize=True)
        contracts_ids = info.getPartnerRelatedContracts(17465)
        self.assertEqual(
            contracts_ids,
            [169183, 38127]
        )

    def test_getByPhone_global(self):
        info = CallInfo(self.O)
        data = info.getByPhone("630079522")
        self.assertB2BEqual(data.dump())

    def test_getByPhone_global2(self):
        info = CallInfo(self.O)
        data = info.getByPhone("935514714")
        self.assertB2BEqual(data.dump())

    def test_getByEmail_global(self):
        info = CallInfo(self.O)
        data = info.getByEmail("testing%@somenergia.coop")
        self.assertB2BEqual(data.dump())

    def test_getBySoci_global(self):
        info = CallInfo(self.O)
        data = info.getBySoci(dbconfig.personaldata["nsoci"])
        self.assertB2BEqual(data.dump())

    def test_getByDni_global(self):
        info = CallInfo(self.O)
        data = info.getByDni(dbconfig.personaldata["nif"])
        self.assertB2BEqual(data.dump())

    def test_getByName_global(self):
        info = CallInfo(self.O)
        complete_name = dbconfig.personaldata["surname"]
        complete_name += ", "
        complete_name += dbconfig.personaldata["name"]
        data = info.getByName(complete_name)
        self.assertB2BEqual(data.dump())

    def test_getByPartnersId_global(self):
        info = CallInfo(self.O)
        data = info.getByPartnersId([dbconfig.personaldata["partnerid"]])
        self.assertB2BEqual(data.dump())

    def test_getByPartnersId_whenTooManyResults(self):
        info = CallInfo(self.O, results_limit=3)
        data = info.getByPartnersId([
                    37957,
                    38073,
                    38043,
                    37988,
                ])
        self.assertNsEqual(data, """\
            partners : Masses resultats
            """)


unittest.TestCase.__str__ = unittest.TestCase.id


# vim: ts=4 sw=4 et
