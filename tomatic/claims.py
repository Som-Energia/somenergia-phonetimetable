# -*- encoding: utf-8 -*-
from yamlns import namespace as ns
import time


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

    def create_atc_case(self, data_crm, data_atc):
        crm_obj = self.Client.CrmCase
        crm_id = crm_obj.create(data_crm)

        data_atc['crm_id'] = crm_id
        atc_obj = self.Client.GiscedataAtc
        case = atc_obj.create(data_atc)

        return case.id


# vim: et ts=4 sw=4
