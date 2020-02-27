# -*- encoding: utf-8 -*-
from yamlns import namespace as ns


class Claims(object):

    def __init__(self, O):
        self.O = O
        config = ns.load('config.yaml')

        self.assign_user = config.assign_user

    def get_claims(self):
        reclamacio_obj = self.O.GiscedataSubtipusReclamacio

        reclamacions = []
        all_reclamacio_ids = reclamacio_obj.search()

        for reclamacio_id in all_reclamacio_ids:
            reclamacio = reclamacio_obj.get(reclamacio_id)
            recl_section = reclamacio.default_section
            seccio = recl_section.name if recl_section else self.assign_user

            message = u"[{}] {} - {}".format(
                seccio,
                reclamacio.name,
                reclamacio.desc
            )

            reclamacions.append(message)

        return reclamacions


# vim: et ts=4 sw=4
