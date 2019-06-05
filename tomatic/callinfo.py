# -*- coding: utf-8 -*-

from yamlns import namespace as ns 

class CallInfo(object):

    def __init__(self, O, anonymize=False):
        self.O = O
        self._anonymize = anonymize

    def anonymize(self, string):
        if not self._anonymize: return string
        return "..."+string[-3:]

    def addressByPhone(self, phone):
        return self.O.ResPartnerAddress.search([
            '|',
            ('phone','=',phone),
            ('mobile','=',phone),
            ])

    def partnerByAddressId(self, address_ids):
        result = []
        if len(address_ids) == 0:
            return result
        return [
            address[0]
            for address 
            in self.O.ResPartnerAddress.read(address_ids,'partner_id')
            if address and address[0]
            ]

    def partnerInfo(self, partner_data):
        result = ns(
            id_soci = self.anonymize(partner_data.ref),
            lang = partner_data.lang,
            name = self.anonymize(partner_data.name),
            city = partner_data.city,
            email = self.anonymize(partner_data.www_email),
            state = partner_data.www_provincia[1]['name'],
            dni = self.anonymize(partner_data.vat),
            ov = partner_data.empowering_token != False,
            )
        return result

    def getPartnerRelatedContracts(self,partner_id):
        contract_tp_ids = self.O.GiscedataPolissa.search([
            ('titular.id','=',partner_id),
            ('pagador.id','=',partner_id),
            ])
        contract_titular_ids = self.O.GiscedataPolissa.search([
            ('titular.id','=',partner_id),
            ])
        contract_pagador_ids = self.O.GiscedataPolissa.search([
            ('pagador.id','=',partner_id),
            ])
        contract_soci_ids = self.O.GiscedataPolissa.search([
            ('soci.id','=',partner_id),
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
        result = ns(partners = [])
        partners_data = self.O.ResPartner.read(partners_ids, [
            'city',
            'www_email',
            'www_provincia',
            'name',
            'ref',
            'lang',
            'vat',
            'empowering_token',
        ])
        for partner_data in partners_data or []:
            partner_data = ns(partner_data)
            partner_result = self.partnerInfo(partner_data)
            contracts_ids = self.getPartnerRelatedContracts(partner_data.id)
            partner_result.update(self.contractInfo(contracts_ids,partner_data.id))
            if partner_result.id_soci.startswith('S'):
                result.partners.append(partner_result)
            else:
                no_partners.append(partner_result)

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
            partner_ids = self.O.ResPartnerAddress.read([address_id],['partner_id'])
            return partner_ids[0]['partner_id'][0]

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
        ])

        all_contracts_dict = {c['id']:c for c in all_contracts if c}
        for contract_id in contracts_ids:
            if contract_id in all_contracts_dict:
                contract = all_contracts_dict[contract_id]
                ret.contracts.append(
                    ns(
                        start_date = contract['data_alta'],
                        end_date = contract['data_baixa'] if contract['data_baixa'] else '',
                        power = contract['potencia'],
                        cups = self.anonymize(contract['cups'][1]),
                        fare = contract['tarifa'][1],
                        state = contract['state'],
                        number = contract['name'],
                        last_invoiced = contract['data_ultima_lectura'],
                        suspended_invoicing = contract['facturacio_suspesa'],
                        pending_state = contract['pending_state'],
                        has_open_r1s = hasOpenATR(contract['id'],'R1'),
                        has_open_bs = hasOpenATR(contract['id'],'B1'),
                        is_titular = contract['titular'][0] == partner_id,
                        is_partner = contract['soci'][0] == partner_id,
                        is_notifier = getPartnerId(contract['direccio_notificacio'][0]) == partner_id,
                        is_payer = contract['pagador'][0] == partner_id,
                    )
                )
        return ret

    def getByPhone(self, phone):
        address_ids = self.addressByPhone(phone)
        partners_ids = self.partnerByAddressId(address_ids)
        clean_partners_ids = list(set(partners_ids))
        result = ns()
        result.callid = phone
        result.update(self.partnersInfo(clean_partners_ids))
        return result


# vim: ts=4 sw=4 et
