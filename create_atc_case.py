#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import dbconfig
import erppeek
import os
from consolemsg import step, success, error
from tomatic.claims import Claims
from yamlns import namespace as ns

# python -m scripts.create_atc_case --d atc_cases


def main(yaml_directory):
    entries = os.listdir(yaml_directory)
    config = ns.load('config.yaml')
    erp = erppeek.Client(**dbconfig.erppeek)
    claims = Claims(erp)
    for entry in entries:
        if not entry.endswith(".yaml"):
            continue

        atc_yaml_path = os.path.join(yaml_directory, entry)
        if atc_yaml_path == config.my_calls_log:
            continue

        try:
            atc_yaml = ns.load(atc_yaml_path)
            for person in atc_yaml:
                for case in atc_yaml[person]:
                    case_id = claims.create_atc_case(case)
                    step("Case {} created.", case_id)
        except Exception as e:
            error("Hi ha hagut algún problema al fitxer {}: {}".format(
                atc_yaml_path,
                str(e))
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--dir',
        dest='yaml_directory',
        required=True,
        help="Directori que conté els fitxers YAML a partir dels \
            quals es crean els casos ATC"
    )
    args = parser.parse_args()
    try:
        main(args.yaml_directory)
    except Exception as e:
        error("El procés no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalizado")

# vim: et ts=4 sw=4
