#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from sheetfetcher import SheetFetcher
from consolemsg import error, warn, step
from yamlns import namespace as ns
import os.path
import random
from pathlib2 import Path
import datetime



def singlePonderatedLoad(person, load, businessDays, daysoff, leaves):
    return load*workingDays(person, businessDays, daysoff, leaves)/float(5)

def ponderatedLoad(idealLoad, businessDays, daysoff, leaves):
    return {
        person: singlePonderatedLoad(
            person=person,
            load=load,
            businessDays = businessDays,
            daysoff = daysoff,
            leaves = leaves,
            )
        for person, load in idealLoad.items()
    }

def workingDays(person, businessDays, daysoff, leaves):
    if person in leaves: return 0
    ndaysoff = sum(
            day.person == person
            for day in daysoff
            if day.weekday in businessDays
            )
    return len(businessDays)-ndaysoff

def dayCapacity(busy, maxPerDay):
    if busy == '1111': return 0
    if maxPerDay == 1: return 1
    if maxPerDay == 2:
        # Restriction: consecutive and not arround the lunch time, to be two
        if busy[:2] == '00': return 2
        if busy[2:] == '00': return 2
        return 1
    if maxPerDay == 4 and busy=='0000': return 4
    if '000' in busy: return 3
    if '00' in busy: return 2
    return 1


def weekCapacity(busy, maxPerDay):
    return sum(dayCapacity(b, maxPerDay) for b in busy)


args = None

FULL_CARREGA = 0
FULL_DE_CALCUL = 'generacio_automatica_0101'
INTERVAL_IDEALS = 'idealsTelefon'
INTERVAL_PERSONES = 'personesTelefon'
FILE_NAME = 'excedents.yaml'
EXCEDENTS_FILE = 'excedents.yaml'


def get_ideals_sheet(lines):
    try:
        fetcher = SheetFetcher(
            documentName=FULL_DE_CALCUL,
            credentialFilename='drive-certificate.json',
        )
        step("Accedint al full de càlcul...")
        ideals = fetcher.get_range(FULL_CARREGA, INTERVAL_IDEALS)
        persones = fetcher.get_range(FULL_CARREGA, INTERVAL_PERSONES)
        step("Tenim els ideals!")
    except IOError:
        message = 'error_get_fullsheet'
        error("Error accedint al full de càlcul: {}.", FULL_DE_CALCUL)

    all_ideals = {}
    for i, p in zip(ideals, persones):
        all_ideals[p[0].strip().lower()] = int(i[0])
    all_ideals['all'] = int(all_ideals[''])
    del all_ideals['']  # last row

    return all_ideals


def apply_baixes(charge, baixes):
    step("Aplicant baixes...")
    for baixa in baixes:
        charge['all'] -= charge[baixa]
        del charge[baixa]


def apply_holidays(charge):
    step("Aplicant vacances...")
    loadLimit = {}
    with open('indisponibilitats-vacances.conf') as holidays_file:
        for line in holidays_file:
            name = line.split(" ")[0]
            if name in loadLimit.keys():
                loadLimit[name] += 1
            else:
                loadLimit[name] = 1

    for person in charge:  # warning: name has to be ok
        if person is not 'all':
            ndays = 5
            maxLoadPerDay = 2
            # carrega maxima absoluta
            loadLimit[person] = (ndays - loadLimit.get(person,0))*maxLoadPerDay
            # TODO: el ponderat
            days = min(charge[person],loadLimit[person])
            before = charge[person]
            charge[person] = max(days,0)
            charge['all'] -= (before - charge[person])
    return loadLimit


def pay_debts(maxim, charge, debts):
    step("Pagant deutes...")
    # TODO: Fer en funcio de la situacio
    for person in debts:
        if person != 'all':
            days = charge[person] + debts[person]
            if days <= maxim[person]:
                charge[person] = days if days > 0 else 0
                charge['all'] += debts[person]
                del debts[person]
    return debts


def achieveFullLoad(fullLoad, shifts, limits, credits):
    currentLoad = sum(shifts.values())
    if currentLoad > fullLoad:
        return decreaseUntilFullLoad(fullLoad, shifts, limits, credits)
    return increaseUntilFullLoad(fullLoad, shifts, limits, credits)


def decreaseUntilFullLoad(fullLoad, shifts, limits, credits):
    result = ns(shifts)
    currentLoad = sum(shifts.values())
    operatingWithCredit = True
    while True:
        load = currentLoad
        for person, credit in sorted(credits.items(), key=lambda x: -x[1]):
            if currentLoad == fullLoad: break
            if result[person] <= 0: continue
            if operatingWithCredit and credit <= 0: continue
            credits[person] -= 1
            result[person] -= 1
            currentLoad -= 1
        if load == currentLoad:
            if not operatingWithCredit: break
            operatingWithCredit = False
    return result


def increaseUntilFullLoad(fullLoad, shifts, limits, credits):
    result = ns(shifts)
    currentLoad = sum(shifts.values())
    operatingWithDebts = True
    while True:
        load = currentLoad
        for person, credit in sorted(credits.items(), key=lambda x: x[1]):
            if currentLoad == fullLoad: break
            if result[person] >= limits[person]: continue
            if operatingWithDebts and credit >= 0: continue
            credits[person] += 1
            result[person] += 1
            currentLoad += 1
        if load == currentLoad:
            if not operatingWithDebts: break
            operatingWithDebts = False
    return result


def compensar_torns_que_sobren(fullLoad, charge, debts):
    step("Compensant torns que sobren amb criteri 'random'...")
    possibles_afortunats = list(charge.keys())
    compensat = False
    while not compensat:
        random_person = random.choice(possibles_afortunats)
        if charge[random_person] > 0:
            charge[random_person] -= 1
            charge['all'] -= 1
            if random_person in debts:
                debts[random_person] += 1
            else:
                debts[random_person] = 1
        compensat = charge['all'] == fullLoad 
    return charge


def clusteritzar(lines, fullLoad, charge):
    return charge


def parseArgs():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-l',
        '--lines',
        default=None,
        type=int,
        help="nombre de linies"
    )
    parser.add_argument(
        '-c',
        '--charge',
        default=None,
        type=int,
        help="carrega necessaria"
    )
    parser.add_argument(
        '-b',
        '--baixes',
        default=None,
        nargs='+',
        help="llista de baixes"
    )
    return parser.parse_args()


def showInfo():
    warn("REQUIERED: --l 'nombre de linies' --c 'carrega necessaria'")  # --d 'data graelles'")
    print("carrega necesaria = nombre de torns * nombre de dies")


def oldmain():
    global args
    args = parseArgs()

    if args.lines is None or args.charge is None:  # or args.d is None:
        error("Missing arguments!")
        showInfo()
        return -1
    
    excedents = ns.load(EXCEDENTS_FILE)

    lines = args.lines
    ideals = get_ideals_sheet(lines)
    fullLoad = lines*args.charge

    charge = ideals
    if args.baixes:
        apply_baixes(charge, args.baixes)

    situation = apply_holidays(charge)
    # TODO: mirar les indisponibilitats
    
    debts = pay_debts(situation, charge, excedents.deutes)

    if charge['all'] < lines*args.charge:
        compensat = achieveFullLoad(situation, fullLoad, charge, debts)
    else:
        compensat = compensar_torns_que_sobren(fullLoad, charge, debts)
    
    if not compensat:
        error("No es pot assolir la càrrega mínima amb les línies especificades.")

    debts = ns({'deutes': debts})
    debts.dump(EXCEDENTS_FILE)

    final_charge = clusteritzar(lines, fullLoad, charge)

    return 0


def parseArgs():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--keep',
        action='store_true',
        help="no baixa les dades del drive"
        )

    parser.add_argument(
        dest='date',
        nargs='?',
        default=None,
        help='generates the schedule for the week including such date',
        )

    parser.add_argument(
        '--certificate','-C',
        metavar='CERTIFICATE.json',
        default='drive-certificate.json',
        help='certificat amb permisos per accedir al document gdrive',
        )

    parser.add_argument(
        '--holidays',
        default='drive',
        help="Origen d'on agafa les vacances",
    )

    parser.add_argument(
        '-l',
        '--lines',
        default=None,
        type=int,
        help="Number of concurrent phone lines",
    )

    parser.add_argument(
        '--drive-file',
        help="Document del drive origen de dades externes"
        )

    parser.add_argument(
        '--config-file',
        default='config.yaml',
        help="fitxer de configuració principal",
    )

    parser.add_argument(
        '--personsfile',
        default='persons.yaml',
        help="fitxer de configuració de les persones",
    )

    parser.add_argument(
        '--idealshifts',
        default=None,
        help="fitxer tsv amb la carrega ideal de cada persona (fila)",
    )

    return parser.parse_args()

args=None

from .scheduler import (
    baixaPersones,
    baixaIndisponibilitatsTomatic,
    baixaVacancesNotoi,
    baixaVacancesDrive,
    baixaCarregaIdeal,
)

def main():
    global args

    args = parseArgs()

    step('Carregant configuració {}...', args.config_file)
    from yamlns import namespace as ns
    try:
        config = ns.load(args.config_file)
    except:
        error("Configuració incorrecta")
        raise

    if args.personsfile:
        config.personsfile = args.personsfile

    if not args.keep:
        baixaPersones(config)

    if args.personsfile and Path(args.personsfile).exists():
        config.update(ns.load(args.personsfile))

    if args.date is not None:
        # take the monday of the week including that date
        givenDate = datetime.datetime.strptime(args.date,"%Y-%m-%d").date()
        config.monday = givenDate - timedelta(days=givenDate.weekday())
    else:
        # If no date provided, take the next monday
        today = datetime.date.today()
        config.monday = today + datetime.timedelta(days=7-today.weekday())

    if args.lines:
        config.nTelefons = args.lines

    if args.drive_file:
        config.documentDrive = args.drive_file

    mustDownloadShifts = not args.idealshifts and not config.get('idealshifts')
    config.idealshifts = config.get('idealshifts') or args.idealshifts or 'idealshifts.csv'

    if not args.keep:
        if mustDownloadShifts:
            baixaCarregaIdeal(config, args.certificate)
        if not config.get('busyFiles'):
            baixaIndisponibilitatsTomatic(config)
            if args.holidays == 'notoi':
                baixaVacancesNotoi(config)
            else: # args.holidays == 'drive':
                baixaVacancesDrive(config, args.certificate)

    step('Generant carrega...')






if __name__ == '__main__':
    main()

# vim: et ts=4 sw=4
