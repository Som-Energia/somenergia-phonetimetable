#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import dbconfig
import erppeek
import logging
import os
from datetime import date
from tomatic.claims import Claims
from yamlns import namespace as ns
from pathlib import Path

# python -m scripts.create_atc_case --d atc_cases


def main(yaml_directory):
    erp = erppeek.Client(**dbconfig.erppeek)
    claims = Claims(erp)

    config = ns.load('config.yaml')

    entries = os.listdir(yaml_directory)
    for entry in entries:

        if not entry.endswith(".yaml"):
            logging.warning(" Skipped file '{}': Not a yaml.".format(entry))
            continue

        atc_yaml_path = os.path.join(yaml_directory, entry)
        if atc_yaml_path == config.my_calls_log:
            logging.warning(" Skipped file '{}': No info file.".format(entry))
            continue

        try:
            atc_yaml = ns.load(atc_yaml_path)
            for person in atc_yaml:
                for case in atc_yaml[person]:
                    case_id = claims.create_atc_case(case)
                    logging.info(" Case {} created.".format(case_id))

        except Exception as e:
            logging.error(" Something went wrong in {}: {}".format(
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

    today = date.today()
    current_date = today.strftime("%Y%m%d")

    logs_directory = os.path.join(args.yaml_directory, "logs")
    Path(logs_directory).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename='{}/{}.log'.format(
            logs_directory,
            current_date
        ),
        level=logging.INFO
    )
    logging.info(" Script starts: let's go!")

    try:
        main(args.yaml_directory)
    except Exception as e:
        logging.error(" Script not completed successfully: {}", str(e))
    else:
        logging.info(" Script ends: success!")


# vim: et ts=4 sw=4
