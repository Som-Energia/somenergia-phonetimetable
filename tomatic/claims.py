# -*- encoding: utf-8 -*-
import re
from yamlns import namespace as ns
from consolemsg import error

PHONE = 2
COMERCIALIZADORA = '06'

def partnerId(Client, partner):
    partner_model = Client.ResPartner
    return partner_model.browse([('ref', '=', partner)])[0].id

def partnerAddress(Client, partner_id):
    partner_address_model = Client.ResPartnerAddress
    return partner_address_model.read(
        [('partner_id', '=', partner_id)],
        ['id', 'state_id']
    )[0]

def contractId(Client, contract):
    contract_model = Client.GiscedataPolissa
    return contract_model.browse([("name", "=", contract)])[0].id


def cupsId(Client, cups):
    cups_model = Client.GiscedataCupsPs
    return cups_model.browse([('name', '=', cups)])[0].id


def userId(Client, person):
    users_model = Client.ResUsers
    try:
        user_id = users_model.browse([('login', '=', person)])[0].id
        return user_id
    except IndexError as e:
        error("User {} not found: {}", person, e)


def resultat(Client, procedente, improcedente):
    if procedente:
        return '01'
    if improcedente:
        return '02'
    return '03'


class Claims(object):

    def __init__(self, Client):
        self.Client = Client
        config = ns.load('config.yaml')

        self.assign_user = config.assign_user

    def get_claims(self):
        claims_model = self.Client.GiscedataSubtipusReclamacio
        claims = []
        all_claim_ids = claims_model.search()

        for claim_id in all_claim_ids:
            claim = claims_model.read(
                claim_id,
                ['default_section', 'name', 'desc']
            )
            claim_section = claim.get("default_section")

            if claim_section:
                section = claim_section[1].split("/")[-1].strip()
            else:
                section = self.assign_user

            message = u"[{}] {} - {}".format(
                section,
                claim.get("name"),
                claim.get("desc")
            )
            claims.append(message)

        return claims


    def create_atc_case(self, case):
        '''
        Expected case:

        namespace(
            person:
                - date: D-M-YYYY H:M:S
                person: person
                reason: '[section.name] claim.name - claim.desc'
                partner: partner number
                contract: contract number
                procedente: ''
                improcedente: ''
                solved: ''
                user: section.name
                cups: cups number
                observations: comments
                - ...
            ...
        )
        '''

        partner_id = partnerId(self.Client, case.partner)
        partner_address = partnerAddress(self.Client, partner_id)

        data_crm = {
            'section_id': int(re.search('\d+', case.reason).group()),
            'name': case.reason.split("-")[1].strip(),
            'description': case.observations,
            'canal_id': PHONE,
            'polissa_id': contractId(self.Client, case.contract),
            'partner_id': partner_id,
            'partner_address_id': partner_address.get('id'),
            'state': 'done' if case.solved else 'open'
        }
        # TODO: 'user_id': userId(self.Client, case.person)
        crm_obj = self.Client.CrmCase
        crm_id = crm_obj.create(data_crm).id

        data_atc = {
            'provincia': partner_address.get('state_id')[0],
            'total_cups': 1,
            'cups_id': cupsId(self.Client, case.cups),
            'subtipus_id': int(re.search('\d+', case.reason).group()),
            'reclamante': COMERCIALIZADORA,
            'resultat': resultat(self.Client, case.procedente, case.improcedente),
        }
        data_atc['crm_id'] = crm_id

        atc_obj = self.Client.GiscedataAtc
        case = atc_obj.create(data_atc)

        return case.id

# vim: et ts=4 sw=4
