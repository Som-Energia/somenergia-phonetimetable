# -*- encoding: utf-8 -*-
from yamlns import namespace as ns

PHONE = 2
COMERCIALIZADORA = 1
RECLAMANTE = '01'


def partnerId(erp, partner):
    partner_model = erp.ResPartner
    return partner_model.browse([('ref', '=', partner)])[0].id


def partnerAddress(erp, partner_id):
    partner_address_model = erp.ResPartnerAddress
    return partner_address_model.read(
        [('partner_id', '=', partner_id)],
        ['id', 'state_id', 'email']
    )[0]


def contractId(erp, contract):
    contract_model = erp.GiscedataPolissa
    return contract_model.browse([("name", "=", contract)])[0].id


def cupsId(erp, cups):
    cups_model = erp.GiscedataCupsPs
    return cups_model.browse([('name', '=', cups)])[0].id


def userId(erp, emails, person):
    email = emails[person]
    partner_address_model = erp.ResPartnerAddress
    address_id = partner_address_model.read(
        [('email', '=', email)],
        ['id']
    )
    users_model = erp.ResUsers
    try:
        user_id = users_model.read(
            [('address_id', '=', address_id)],
            ['login']
        )[0].get("id")
        return user_id
    except IndexError:
        return None


def resultat(erp, procedente, improcedente):
    if procedente:
        return '01'
    if improcedente:
        return '02'
    return '03'


def sectionName(erp, section_id):
    claims_model = erp.GiscedataSubtipusReclamacio
    return claims_model.read(section_id, ['desc']).get('desc')


def claimSectionID(erp, section_description):
    claims_model = erp.GiscedataSubtipusReclamacio
    return claims_model.search([('desc', '=', section_description)])[0]


def crmSectionID(erp, section):
    sections_model = erp.CrmCaseSection
    return sections_model.search([('name', 'ilike', section)])[0]


class Claims(object):

    def __init__(self, erp):
        self.erp = erp
        config = ns.load('config.yaml')

        self.assign_user = config.assign_user
        self.emails = config.emails

    def get_claims(self):
        claims_model = self.erp.GiscedataSubtipusReclamacio
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
        partner_id = partnerId(self.erp, case.partner)
        partner_address = partnerAddress(self.erp, partner_id)
        crm_section_id = crmSectionID(self.erp, case.user)
        claim_section_id = claimSectionID(
            self.erp, case.reason.split('-')[-1].strip()
        )
        data_crm = {
            'section_id': crm_section_id,
            'name': sectionName(self.erp, claim_section_id),
            'description': case.observations,
            'canal_id': PHONE,
            'polissa_id': contractId(self.erp, case.contract),
            'partner_id': partner_id,
            'partner_address_id': partner_address.get('id'),
            'state': 'done' if case.solved else 'open'
        }

        user_id = userId(self.erp, self.emails, case.person)
        if user_id:
            data_crm['user_id'] = user_id

        crm_obj = self.erp.CrmCase
        crm_id = crm_obj.create(data_crm).id

        data_atc = {
            'provincia': partner_address.get('state_id')[0],
            'total_cups': 1,
            'cups_id': cupsId(self.erp, case.cups),
            'subtipus_id': claim_section_id,
            'reclamante': RECLAMANTE,
            'resultat': resultat(
                self.erp,
                case.procedente,
                case.improcedente
            ) if case.solved else "",
            'date': case.date,
            'email_from': partner_address.get('email'),
            'time_tracking_id': COMERCIALIZADORA
        }
        data_atc['crm_id'] = crm_id
        atc_obj = self.erp.GiscedataAtc
        case = atc_obj.create(data_atc)

        return case.id

# vim: et ts=4 sw=4
