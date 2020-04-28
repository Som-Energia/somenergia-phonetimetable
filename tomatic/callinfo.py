# -*- coding: utf-8 -*-

from __future__ import print_function
from yamlns import namespace as ns


class CallInfo(object):

    def __init__(self, O, results_limit=None, anonymize=False):
        self.O = O
        self.results_limit = results_limit
        self._anonymize = anonymize

        if not self.results_limit:
            config = ns.load('config.yaml')
            self.results_limit = config.threshold_hits

    def anonymize(self, string):
        if not self._anonymize:
            return string
        return "..."+string[-3:]

    def addressByPhone(self, phone):
        return self.O.ResPartnerAddress.search([
            '|',
            ('phone', 'like', phone),
            ('mobile', 'like', phone),
            ])

    def addressByEmail(self, data):
        return self.O.ResPartnerAddress.search([
            ('email', 'ilike', data),
            ])

    def partnerBySoci(self, data):
        return self.O.ResPartner.search([
            ('ref', 'ilike', data),
            ])

    def partnerByDni(self, data):
        return self.O.ResPartner.search([
            ('vat', 'ilike', data),
            ])

    def partnerByName(self, data):
        return self.O.ResPartner.search([
            ('name', 'ilike', data),
            ])

    def partnerByAddressId(self, address_ids):
        result = []
        if len(address_ids) == 0:
            return result
        return [
            address[0]
            for address
            in self.O.ResPartnerAddress.read(address_ids, 'partner_id')
            if address and address[0]
            ]

    def partnerInfo(self, partner_data):
        result = ns(
            id_soci=self.anonymize(partner_data.ref) if partner_data.ref else "",
            lang=partner_data.lang,
            name=self.anonymize(partner_data.name),
            city=partner_data.www_municipi[1]['name'] if partner_data.www_municipi else "",
            email=self.anonymize(partner_data.www_email),
            state=partner_data.www_provincia[1]['name'] if partner_data.www_provincia else "",
            dni=self.anonymize(partner_data.vat),
            ov=partner_data.empowering_token != False,
            energetica=24 in partner_data.category_id,
            )
        return result

    def getPartnerRelatedContracts(self, partner_id):
        contract_tp_ids = self.O.GiscedataPolissa.search([
            ('titular.id', '=', partner_id),
            ('pagador.id', '=', partner_id),
            ])
        contract_titular_ids = self.O.GiscedataPolissa.search([
            ('titular.id', '=', partner_id),
            ])
        contract_pagador_ids = self.O.GiscedataPolissa.search([
            ('pagador.id', '=', partner_id),
            ])
        contract_soci_ids = self.O.GiscedataPolissa.search([
            ('soci.id', '=', partner_id),
            ])

        contracts = contract_tp_ids
        for contract_titular_id in contract_titular_ids:
            if contract_titular_id not in contracts:
                contracts.append(contract_titular_id)
        for contract_pagador_id in contract_pagador_ids:
            if contract_pagador_id not in contracts:
                contracts.append(contract_pagador_id)
        for contract_soci_id in contract_soci_ids:
            if contract_soci_id not in contracts:
                contracts.append(contract_soci_id)
        return contracts

    def partnersInfo(self, partners_ids):
        no_partners = []
        result = ns(partners=[])
        partners_data = self.O.ResPartner.read(partners_ids, [
            'city',
            'www_email',
            'www_provincia',
            'www_municipi',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
            'category_id',
        ])
        for partner_data in partners_data or []:
            partner_data = ns(partner_data)
            try:
                partner_result = self.partnerInfo(partner_data)
                contracts_ids = self.getPartnerRelatedContracts(
                    partner_data.id
                )
                partner_result.update(
                    self.contractInfo(contracts_ids, partner_data.id)
                )
                if partner_result.id_soci.startswith('S'):
                    result.partners.append(partner_result)
                else:
                    no_partners.append(partner_result)
            except Exception as e:
                print("Unexepected error found at partner id {}".format(
                    partner_data.id
                ))
                print(e)
        result.partners.extend(no_partners)
        return result

    def contractInfo(self, contracts_ids, partner_id):

        def hasOpenATR(contract_id, case):
            cases = self.O.GiscedataSwitching.search([
                ('cups_polissa_id', '=', contract_id),
                ('proces_id.name', '=', case),
                ('state', '!=', 'done')
            ])
            return len(cases) > 0

        def getPartnerId(address_id):
            partner_ids = self.O.ResPartnerAddress.read(
                [address_id],
                ['partner_id']
            )
            if partner_ids and partner_ids[0]['partner_id']:
                return partner_ids[0]['partner_id'][0]
            return None

        def getCUPSAdress(cups_id):
            cups_data = self.O.GiscedataCupsPs.read([cups_id], ['direccio'])
            return cups_data[0]['direccio']

        def hasGeneration(contract_id):
            assignations = self.O.GenerationkwhAssignment.search([
                ('contract_id', '=', contract_id),
                ('end_date', '=', None),
            ])
            return len(assignations) > 0

        if not contracts_ids:
            return ns(polisses=[])

        ret = ns(contracts=[])

        all_contracts = self.O.GiscedataPolissa.read(contracts_ids, [
            'data_alta',
            'data_baixa',
            'potencia',
            'cups',
            'state',
            'active',
            'tarifa',
            'name',
            'data_ultima_lectura',
            'facturacio_suspesa',
            'pending_state',
            'titular',
            'soci',
            'pagador',
            'direccio_notificacio',
            'bank',
        ])
        all_contracts_dict = {c['id']: c for c in all_contracts if c}
        for contract_id in contracts_ids:
            if contract_id in all_contracts_dict:
                contract = all_contracts_dict[contract_id]
                ret.contracts.append(
                    ns(
                        start_date=contract['data_alta'],
                        end_date=contract['data_baixa'] if contract['data_baixa'] else '',
                        power=contract['potencia'],
                        cups=self.anonymize(contract['cups'][1]),
                        fare=contract['tarifa'][1],
                        state=contract['state'],
                        number=contract['name'],
                        last_invoiced=contract['data_ultima_lectura'],
                        suspended_invoicing=contract['facturacio_suspesa'],
                        pending_state=contract['pending_state'],
                        has_open_r1s=hasOpenATR(contract['id'], 'R1'),
                        has_open_bs=hasOpenATR(contract['id'], 'B1'),
                        is_titular=contract['titular'] and contract['titular'][0] == partner_id,
                        is_partner=contract['soci'] and contract['soci'][0] == partner_id,
                        is_notifier=getPartnerId(contract['direccio_notificacio'][0]) == partner_id,
                        is_payer=contract['pagador'] and contract['pagador'][0] == partner_id,
                        cups_adress=self.anonymize(getCUPSAdress(contract['cups'][0])),
                        titular_name=self.anonymize(contract['titular'][1]),
                        energetica=contract['soci'] and contract['soci'][0] == 38039,
                        generation=hasGeneration(contract['id']),
                        iban=self.anonymize(contract['bank'][1])
                    )
                )
        return ret

    def getByPhone(self, phone):
        address_ids = self.addressByPhone(phone)
        partners_ids = self.partnerByAddressId(address_ids)
        return self.getByPartnersId(partners_ids)

    def getByEmail(self, email):
        email_ids = self.addressByEmail(email)
        email_p_ids = self.partnerByAddressId(email_ids)
        return self.getByPartnersId(email_p_ids)

    def getBySoci(self, soci):
        soci_p_ids = self.partnerBySoci(soci)
        return self.getByPartnersId(soci_p_ids)

    def getByDni(self, dni):
        dni_p_ids = self.partnerByDni(dni)
        return self.getByPartnersId(dni_p_ids)

    def getByName(self, name):
        name_p_ids = self.partnerByName(name)
        return self.getByPartnersId(name_p_ids)

    def getByData(self, data):
        address_ids = self.addressByPhone(data)
        address_p_ids = self.partnerByAddressId(address_ids)
        email_ids = self.addressByEmail(data)
        email_p_ids = self.partnerByAddressId(email_ids)
        soci_p_ids = self.partnerBySoci(data)
        dni_p_ids = self.partnerByDni(data)
        name_p_ids = self.partnerByName(data)
        ids = address_p_ids + email_p_ids + soci_p_ids + dni_p_ids + name_p_ids
        return self.getByPartnersId(ids)

    def getByPartnersId(self, partners_id):
        clean_partners_ids = list(set(partners_id))
        if self.results_limit and len(clean_partners_ids) > self.results_limit:
            return ns(partners='Masses resultats')
        elif len(clean_partners_ids) == 0:
            return ns(partners=None)
        result = ns()
        result.update(self.partnersInfo(clean_partners_ids))
        return result


# vim: ts=4 sw=4 et
