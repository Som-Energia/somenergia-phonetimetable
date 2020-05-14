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
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
                open_cases: []
                is_titular: True
                is_partner: True
                is_notifier: True
                is_payer: True
                cups_adress: '...ig)'
                titular_name: '...iol'
                energetica: False
                generation: True
                iban: '...029'
                lot_facturacio: '02/2020'
                no_estimable: True
                lectures_comptadors:
                - comptador: '...241'
                  data: '2020-01-20'
                  lectura: '...570'
                  origen: Telegestió
                  periode: 2.0DHA (P1)
                invoices:
                - amount: 51.69
                  days_invoiced: 32
                  due_date: '2020-02-04'
                  energy_invoiced: 304
                  final_date: '2020-01-20'
                  initial_date: '2019-12-20'
                  invoice_date: '2020-01-28'
                  number: '...911'
                  payer: '...iol'
                  state: paid
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
                open_cases: []
                is_titular: False
                is_partner: True
                is_notifier: True
                is_payer: True
                cups_adress: '...ig)'
                titular_name: '...xes'
                energetica: False
                generation: True
                iban: '...200'
                lot_facturacio: '02/2020'
                no_estimable: True
                lectures_comptadors:
                - comptador: '...028'
                  data: '2020-01-20'
                  lectura: '...462'
                  origen: Telegestió
                  periode: 2.0A (P1)
                invoices:
                - amount: 7.6
                  days_invoiced: 32
                  due_date: '2020-02-04'
                  energy_invoiced: 6
                  final_date: '2020-01-20'
                  initial_date: '2019-12-20'
                  invoice_date: '2020-01-28'
                  number: '...926'
                  payer: '...iol'
                  state: paid
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
                open_cases: []
                is_titular: false
                is_partner: true
                is_notifier: false
                is_payer: false
                cups_adress: '...ig)'
                titular_name: '...ero'
                energetica: False
                generation: False
                iban: '...835'
                lot_facturacio: '02/2020'
                no_estimable: True
                lectures_comptadors:
                - comptador: '...309'
                  data: '2020-01-19'
                  lectura: '...379'
                  origen: Telegestió
                  periode: 2.0DHA (P1)
                invoices:
                - amount: 75.49
                  days_invoiced: 32
                  due_date: '2020-02-04'
                  energy_invoiced: 347
                  final_date: '2020-01-19'
                  initial_date: '2019-12-19'
                  invoice_date: '2020-01-28'
                  number: '...883'
                  payer: '...ero'
                  state: paid
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
                open_cases: []
                is_titular: false
                is_partner: true
                is_notifier: false
                is_payer: false
                cups_adress: '...ig)'
                titular_name: '...nia'
                energetica: False
                generation: False
                iban: '...768'
                lot_facturacio: '02/2020'
                no_estimable: True
                lectures_comptadors:
                - comptador: '...595'
                  data: '2020-01-19'
                  lectura: '...197'
                  origen: Telegestió
                  periode: 2.0DHA (P1)
                invoices:
                - amount: 46.23
                  days_invoiced: 32
                  due_date: '2020-02-04'
                  energy_invoiced: 196
                  final_date: '2020-01-19'
                  initial_date: '2019-12-19'
                  invoice_date: '2020-01-28'
                  number: '...778'
                  payer: '...nia'
                  state: paid
            """)

    def test_contractInfo_whenAskNone(self):
        info = CallInfo(self.O, anonymize=True)
        contractsData = info.contractInfo([0], 1234)
        self.assertNsEqual(contractsData, """\
            contracts: []
            """)

    def test_contractInfo_whenAskOne(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases: []
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...ig)'
              titular_name: '...iol'
              energetica: False
              generation: True
              iban: '...029'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...241'
                data: '2020-01-20'
                periode: '2.0DHA (P1)'
                lectura: '...570'
                origen: Telegestió
              invoices:
              - amount: 51.69
                days_invoiced: 32
                due_date: '2020-02-04'
                energy_invoiced: 304
                final_date: '2020-01-20'
                initial_date: '2019-12-20'
                invoice_date: '2020-01-28'
                number: '...911'
                payer: '...iol'
                state: paid
            """)

    def test_contractInfo_whenNoSoci(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases: []
              is_titular: True
              is_partner: False
              is_notifier: False
              is_payer: False
              cups_adress: '...rú)'
              titular_name: '...ger'
              energetica: False
              generation: False
              iban: '...445'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...747'
                data: '2020-01-11'
                lectura: '...803'
                origen: Telegestió
                periode: 2.0A (P1)
              invoices:
              - amount: 33.97
                days_invoiced: 31
                due_date: '2020-01-30'
                energy_invoiced: 102
                final_date: '2020-01-11'
                initial_date: '2019-12-12'
                invoice_date: '2020-01-23'
                number: '...521'
                payer: '...ard'
                state: paid
            """)

    def test_contractInfo_whenEnergetica(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases: []
              is_titular: True
              is_partner: False
              is_notifier: True
              is_payer: True
              cups_adress: '...ón)'
              titular_name: '...tín'
              energetica: True
              generation: False
              iban: '...113'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...002'
                data: '2020-01-15'
                lectura: '...446'
                origen: Telegestió
                periode: 2.0A (P1)
              invoices:
              - amount: 22.3
                days_invoiced: 29
                due_date: '2020-01-30'
                energy_invoiced: 34
                final_date: '2020-01-15'
                initial_date: '2019-12-18'
                invoice_date: '2020-01-23'
                number: '...083'
                payer: '...tín'
                state: paid
            """)

    def test_contractInfo_whenAskOne_withR1(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases:
                - R1
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...La)'
              titular_name: '...cís'
              energetica: False
              generation: False
              iban: '...195'
              lot_facturacio: '01/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...881'
                data: '2020-02-12'
                lectura: '...508'
                origen: Autolectura
                periode: 2.0A (P1)
              invoices:
              - amount: 65.62
                days_invoiced: 35
                due_date: '2020-02-23'
                energy_invoiced: 240
                final_date: '2019-12-09'
                initial_date: '2019-11-05'
                invoice_date: '2020-01-23'
                number: '...223'
                payer: '...cís'
                state: open
            """)

    def test_contractInfo_whenAskOne_withB1(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases: [B1]
              is_titular: True
              is_partner: False
              is_notifier: True
              is_payer: True
              cups_adress: '...es)'
              titular_name: '...Mar'
              energetica: False
              generation: False
              iban: '...933'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...144'
                data: '2020-01-25'
                lectura: '...868'
                origen: Telegestió
                periode: 2.0DHA (P1)
              invoices:
              - amount: 134.34
                days_invoiced: 30
                due_date: '2020-02-06'
                energy_invoiced: 754
                final_date: '2020-01-25'
                initial_date: '2019-12-27'
                invoice_date: '2020-01-30'
                number: '...453'
                payer: '...Mar'
                state: open

            """)

    def test_contractInfo_whenAskOne_withC1(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([260522], 164754)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...Z0F
              start_date: False
              state: esborrany
              power: 3.3
              fare: 2.0A
              number: '0151980'
              last_invoiced: false
              suspended_invoicing: false
              pending_state: 'Correct'
              open_cases: [C1]
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...da)'
              titular_name: '...lex'
              energetica: False
              generation: False
              iban: '...839'
              lot_facturacio: ''
              no_estimable: True
              lectures_comptadors: []
              invoices: []
            """)

    def test_contractInfo_whenAskOne_withC2(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([260052], 35641)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...K0F
              start_date: false
              state: esborrany
              power: 4.5
              fare: 2.0DHA
              number: '0151510'
              last_invoiced: false
              suspended_invoicing: false
              pending_state: false
              open_cases: [C2]
              is_titular: true
              is_partner: false
              is_notifier: true
              is_payer: true
              cups_adress: '...ès)'
              titular_name: '...tse'
              energetica: False
              generation: False
              iban: '...163'
              lot_facturacio: ''
              no_estimable: True
              lectures_comptadors: []
              invoices: []
            """)

    def test_contractInfo_whenAskOne_withM1(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([260922], 164993)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...Y0F
              start_date: '2020-02-01'
              state: activa
              power: 3.3
              fare: 2.0A
              number: '0152380'
              last_invoiced: false
              suspended_invoicing: false
              pending_state: 'Correct'
              open_cases: [M1]
              is_titular: true
              is_partner: false
              is_notifier: true
              is_payer: true
              cups_adress: '...na)'
              titular_name: '... Cb'
              energetica: False
              generation: False
              iban: '...809'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors: []
              invoices: []
            """)

    def test_contractInfo_whenAskOne_withA3(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([261096], 165075)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...M0F
              start_date: false
              state: esborrany
              power: 3.45
              fare: 2.0DHA
              number: '0152554'
              last_invoiced: false
              suspended_invoicing: false
              pending_state: 'Correcte'
              open_cases: [A3]
              is_titular: true
              is_partner: false
              is_notifier: true
              is_payer: true
              cups_adress: '...la)'
              titular_name: '...tín'
              energetica: False
              generation: False
              iban: '...958'
              lot_facturacio: ''
              no_estimable: True
              lectures_comptadors: []
              invoices: []
            """)

    def test_contractInfo_whenAskOne_withD1s(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([39518], 28971)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...Z0F
              start_date: '2014-10-14'
              state: activa
              power: 4.5
              fare: 2.0DHA
              number: '0019379'
              last_invoiced: '2019-12-15'
              suspended_invoicing: false
              pending_state: 'Correct'
              open_cases: [D1, D1, D1, D1]
              is_titular: true
              is_partner: false
              is_notifier: true
              is_payer: true
              cups_adress: '...da)'
              titular_name: '... Mª'
              energetica: False
              generation: False
              iban: '...920'
              lot_facturacio: '01/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...121'
                data: '2020-01-14'
                lectura: '...656'
                origen: Telegestió
                periode: 2.0DHA (P1)
              invoices:
              - amount: 28.93
                days_invoiced: 30
                due_date: '2020-01-22'
                energy_invoiced: 262
                final_date: '2020-01-14'
                initial_date: '2019-12-16'
                invoice_date: '2020-01-18'
                number: '...104'
                payer: '... L.'
                state: paid
            """)

    def test_contractInfo_whenAskOne_titular_not_partner(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases: []
              is_titular: True
              is_partner: False
              is_notifier: True
              is_payer: True
              cups_adress: '...na)'
              titular_name: '...rat'
              energetica: False
              generation: False
              iban: '...167'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...359'
                data: '2020-01-14'
                lectura: '...511'
                origen: Telegestió
                periode: 2.0A (P1)
              invoices:
              - amount: 64.74
                days_invoiced: 30
                due_date: '2020-01-30'
                energy_invoiced: 280
                final_date: '2020-01-14'
                initial_date: '2019-12-16'
                invoice_date: '2020-01-23'
                number: '...234'
                payer: '...rat'
                state: paid
            """)

    def test_contractInfo_whenNoBank(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([82920], 56964)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...V0F
              start_date: '2016-11-13'
              state: activa
              power: 10.0
              fare: 2.0A
              number: '0041864'
              last_invoiced: '2020-01-08'
              suspended_invoicing: false
              pending_state: 'Correct'
              open_cases: []
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...eu)'
              titular_name: '...deu'
              energetica: False
              generation: False
              iban: ''
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...392'
                data: '2020-01-08'
                lectura: '...791'
                origen: Telegestió
                periode: 2.0A (P1)
              invoices:
              - amount: 45.11
                days_invoiced: 32
                due_date: '2020-02-13'
                energy_invoiced: 1
                final_date: '2020-01-08'
                initial_date: '2019-12-08'
                invoice_date: '2020-01-14'
                number: '...819'
                payer: '...deu'
                state: open

            """)

    def test_contractInfo_whenNoInvoicing(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
        contractsData = info.contractInfo([120937], 80903)
        self.assertNsEqual(contractsData, """\
            contracts:
            -
              end_date: ''
              cups: ...K0F
              start_date: False
              state: esborrany
              power: 3.3
              fare: 2.0A
              number: '0061206'
              last_invoiced: False
              suspended_invoicing: false
              pending_state: False
              open_cases: []
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...na)'
              titular_name: '...aúl'
              energetica: False
              generation: False
              iban: '...087'
              lot_facturacio: ''
              no_estimable: False
              lectures_comptadors: []
              invoices: []
            """)

    def test_contractInfo_whenAskMore(self):
        info = CallInfo(
            self.O, anonymize=True, invoices_limit=1, meter_readings_limit=1
        )
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
              open_cases: []
              is_titular: True
              is_partner: True
              is_notifier: True
              is_payer: True
              cups_adress: '...ig)'
              titular_name: '...iol'
              energetica: False
              generation: True
              iban: '...029'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...241'
                data: '2020-01-20'
                periode: '2.0DHA (P1)'
                lectura: '...570'
                origen: Telegestió
              invoices:
              - amount: 51.69
                days_invoiced: 32
                due_date: '2020-02-04'
                energy_invoiced: 304
                final_date: '2020-01-20'
                initial_date: '2019-12-20'
                invoice_date: '2020-01-28'
                number: '...911'
                payer: '...iol'
                state: paid
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
              open_cases: []
              is_titular: False
              is_partner: False
              is_notifier: False
              is_payer: False
              cups_adress: '...na)'
              titular_name: '...nna'
              energetica: False
              generation: True
              iban: '...421'
              lot_facturacio: '02/2020'
              no_estimable: True
              lectures_comptadors:
              - comptador: '...638'
                data: '2020-01-21'
                periode: '2.0A (P1)'
                lectura: '...957'
                origen: Telegestió
              invoices:
              - amount: 32.29
                days_invoiced: 30
                due_date: '2020-02-04'
                energy_invoiced: 107
                final_date: '2020-01-21'
                initial_date: '2019-12-23'
                invoice_date: '2020-01-28'
                number: '...923'
                payer: '...nna'
                state: paid
            """)

    def test_getPartnerRelatedContracts_ordered(self):
        info = CallInfo(self.O, anonymize=True)
        contracts_ids = info.getPartnerRelatedContracts(17465)
        self.assertEqual(
            contracts_ids,
            [169183, 38127]
        )

    @unittest.skip("Review and save expected.")
    def test_getByPhone_global(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        data = info.getByPhone("630079522")
        self.assertB2BEqual(data.dump())

    @unittest.skip("Review and save expected.")
    def test_getByPhone_global2(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        data = info.getByPhone("935514714")
        self.assertB2BEqual(data.dump())

    @unittest.skip("Review and save expected.")
    def test_getByEmail_global(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        data = info.getByEmail("testing%@somenergia.coop")
        self.assertB2BEqual(data.dump())

    @unittest.skip("Review and save expected.")
    def test_getBySoci_global(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        data = info.getBySoci(dbconfig.personaldata["nsoci"])
        self.assertB2BEqual(data.dump())

    @unittest.skip("Review and save expected.")
    def test_getByDni_global(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        data = info.getByDni(dbconfig.personaldata["nif"])
        self.assertB2BEqual(data.dump())

    @unittest.skip("Review and save expected.")
    def test_getByName_global(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        complete_name = dbconfig.personaldata["surname"]
        complete_name += ", "
        complete_name += dbconfig.personaldata["name"]
        data = info.getByName(complete_name)
        self.assertB2BEqual(data.dump())

    @unittest.skip("Review and save expected.")
    def test_getByPartnersId_global(self):
        info = CallInfo(self.O, invoices_limit=1, meter_readings_limit=1)
        data = info.getByPartnersId([dbconfig.personaldata["partnerid"]])
        self.assertB2BEqual(data.dump())

    def test_getByPartnersId_whenTooManyResults(self):
        info = CallInfo(
            self.O, results_limit=3, invoices_limit=2, meter_readings_limit=1
        )
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
