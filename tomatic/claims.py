# -*- encoding: utf-8 -*-
import re
from yamlns import namespace as ns
from consolemsg import error, warn

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


def userId(Client, emails, person):
    email = emails[person]
    partner_address_model = Client.ResPartnerAddress
    address_id = partner_address_model.read(
        [('email', '=', email)],
        ['id']
    )
    users_model = Client.ResUsers
    try:
        user_id = users_model.read(
            [('address_id', '=', address_id)],
            ['login']
        )[0].get("id")
        return user_id
    except IndexError as e:
        warn("user '{}' not found, {}. Using default.", person, e)
        return None


def resultat(Client, procedente, improcedente):
    if procedente:
        return '01'
    if improcedente:
        return '02'
    return '03'


def sectionName(Client, section_id):
    claims_model = Client.GiscedataSubtipusReclamacio
    return claims_model.read(section_id, ['desc']).get('desc')


class Claims(object):

    def __init__(self, Client):
        self.Client = Client
        config = ns.load('config.yaml')

        self.assign_user = config.assign_user
        self.emails = config.emails

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
        section_id = int(re.search('\d+', case.reason).group())
        data_crm = {
            'section_id': section_id,
            'name': sectionName(self.Client, section_id),
            'description': case.observations,
            'canal_id': PHONE,
            'polissa_id': contractId(self.Client, case.contract),
            'partner_id': partner_id,
            'partner_address_id': partner_address.get('id'),
            'state': 'done' if case.solved else 'open'
        }
        # TODO: 'user_id': userId(self.Client, case.person)
        user_id = userId(self.Client, self.emails, case.person)

        if user_id:
            data_crm['user_id'] = user_id

        crm_obj = self.Client.CrmCase
        crm_id = crm_obj.create(data_crm).id

        data_atc = {
            'provincia': partner_address.get('state_id')[0],
            'total_cups': 1,
            'cups_id': cupsId(self.Client, case.cups),
            'subtipus_id': section_id,
            'reclamante': COMERCIALIZADORA,
            'resultat': resultat(self.Client, case.procedente, case.improcedente),
        }
        data_atc['crm_id'] = crm_id
        atc_obj = self.Client.GiscedataAtc
        case = atc_obj.create(data_atc)

        return case.id

# vim: et ts=4 sw=4
