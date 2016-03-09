#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import product as xproduct
import random
from datetime import date, timedelta
import datetime
import glob
from consolemsg import step, error, warn, fail
import codecs
import sys

monitoringFile = 'taula.html'
worksheet_unavailabilities = 6
worksheet_load = 5

# Dirty Hack: Behave like python3 open regarding unicode
def open(*args, **kwd):
	return codecs.open(encoding='utf8', *args, **kwd)

def iniciSetmana():
	if args.date is None:
		# If no date provided, take the next monday
		today = date.today()
		return today + timedelta(days=7-today.weekday())

	 # take the monday of the week including that date
	givenDate = datetime.datetime.strptime(args.date,"%Y-%m-%d").date()
	return givenDate - timedelta(days=givenDate.weekday())

def outputFile():
	return "graella-telefons-{}.html".format(iniciSetmana())

def transliterate(word):
	word=unicode(word).lower()
	for old, new in zip(
		u'àèìòùáéíóúçñ',
		u'aeiouaeioucn',
	) :
		word = word.replace(old,new)
	return word

class SheetFetcher():
	def __init__(self, documentName, credentialFilename):
		import json
		import gspread
		from oauth2client.client import SignedJwtAssertionCredentials
		try:
			with open(credentialFilename) as credentialFile:
				json_key = json.load(credentialFile)
		except Exception as e:
			fail(str(e))

		credentials = SignedJwtAssertionCredentials(
			json_key['client_email'],
			json_key['private_key'],
			scope = ['https://spreadsheets.google.com/feeds']
			)

		gc = gspread.authorize(credentials)
		try:
			self.doc = gc.open(documentName)
		except:
			error("No s'ha trobat el document, o no li has donat permisos a l'aplicacio")
			error("Cal compartir el document '{}' amb el següent correu:"
				.format(documentName,json_key['client_email']))
			error(str(e))
			sys.exit(-1)

	def get_range(self, worksheetIndex, rangeName):
		workSheet = self.doc.get_worksheet(worksheetIndex)
		cells = workSheet.range(rangeName)
		width = cells[-1].col-cells[0].col +1
		height = cells[-1].row-cells[0].row +1
		return [ 
			[cell.value for cell in row]
			for row in zip( *(iter(cells),)*width)
			]

	def get_fullsheet(self, worksheetIndex):
		workSheet = self.doc.get_worksheet(worksheetIndex)
		return workSheet.get_all_values()


def baixaDades(monday) :

    def table(sheet, name):
        cells = sheet.range(name)
        width = cells[-1].col-cells[0].col +1
        height = cells[-1].row-cells[0].row +1
        return [ 
            [cell.value for cell in row]
            for row in zip( *(iter(cells),)*width)
            ]


    step('Autentificant al Google Drive')
    fetcher = SheetFetcher(
		documentName='Quadre de Vacances',
		credentialFilename='drive-certificate.json',
		)

    step('Baixant carrega setmanal...')

    carregaRangeName = 'Carrega_{:02d}_{:02d}_{:02d}'.format(
        *monday.timetuple())
    step("  Descarregant el rang '{}'...".format(carregaRangeName))
    carrega = fetcher.get_range(worksheet_load, carregaRangeName)
    step("  Guardant-ho com '{}'...".format('carrega.csv'))
    with open('carrega.csv','w') as phoneload :
        phoneload.write(
            "\n".join(
                '\t'.join(c for c in row)
                for row in carrega
                )
            )

    step('Baixant vacances...')

    nextFriday = monday+timedelta(days=4)
    mondayYear = monday.year
    startingSemester = 1 if monday < date(mondayYear,7,1) else 2
    startingOffset = (monday - date(mondayYear,1 if startingSemester is 1 else 7,1)).days

    holidays2SRange = 'Vacances{}Semestre{}'.format(
        mondayYear,
        startingSemester,
        )
    step("  Baixant vacances de l'interval {}".format(holidays2SRange))
    holidays2S = fetcher.get_range(0, holidays2SRange)

#    endingSemester = 1 if nextFriday < date(mondayYear,7,1) else 2
#    if startingSemester == endingSemester :
    who = [row[0] for row in holidays2S ]
    holidays = [
        (transliterate(name), [
            day for day, value in zip(
                ['dl','dm','dx','dj','dv'],
                row[startingOffset+1:startingOffset+6]
                )
            if value.strip()
            ])
        for name, row in zip(who, holidays2S)
        ]
    step("  Guardant indisponibilitats per vacances a 'indisponibilitats-vacances.conf'...")
    with open('indisponibilitats-vacances.conf','w') as holidaysfile:
        for name, days in holidays:
            for day in days:
                holidaysfile.write("{} {} # vacances\n".format(name, day))
    

    step("Baixant altres indisponibilitats setmanals...")

    step("  Baixant el full {}...".format(worksheet_unavailabilities))
    indis = fetcher.get_fullsheet(worksheet_unavailabilities)
    step("  Guardant indisponibilitats setmanals a 'indisponibilitats-setmana.conf'...")
    with open('indisponibilitats-setmana.conf','w') as indisfile:
        for _, who, day, weekday, hours, need, comment in indis[1:] :
            if weekday and day:
                fail("Indisponibilitat especifica dia puntual {} i dia de la setmana {}"
                    .format(day,weekday))
            if weekday.strip():
                fail("Hi ha indisponibilitats permaments al drive, afegeix-les a ma i esborra-les")
            theDay = datetime.datetime.strptime(day, "%d/%m/%Y").date()
            if theDay < iniciSetmana(): continue
            if theDay > iniciSetmana()+timedelta(days=6): continue

            startHours = [ h.split(':')[0].strip() for h in hours.split(',')]
            bitmap = ''.join((
                ('1' if '9' in startHours else '0'),
                ('1' if '10' in startHours else '0'),
                ('1' if '11' in startHours else '0'),
                ('1' if '12' in startHours else '0'),
            ))
            weekdayShort = u'dl dm dx dj dv ds dg'.split()[theDay.weekday()]

            line = u"{} {} {} # {}\n".format(
                transliterate(who),
                weekdayShort,
                bitmap,
                comment)
            indisfile.write(line)

class Backtracker:
	class ErrorConfiguracio(Exception): pass

	def __init__(self, config) :

		self.config = config
		self.globalMaxTurnsADay = config.maximHoresDiariesGeneral
		self.ntelefons = config.nTelefons
		self.dies = config.diesCerca
		self.diesVisualitzacio = config.diesVisualitzacio
		diesErronis = set(self.dies) - set(self.diesVisualitzacio)
		if diesErronis:
			raise Backtracker.ErrorConfiguracio(
				"Aquests dies no son a la llista de visualitzacio: {}".format(diesErronis))

		self.ndies = len(self.dies)
		self.hores = self.llegeixHores()
		self.nhores = len(self.hores)
		self.torns = self.llegeixTorns('carrega.csv', self.ntelefons)
		self.companys = list(self.torns.keys())
		self.caselles = list(xproduct(self.dies, range(self.nhores), range(self.ntelefons)))
		self.topesDiaris = self.llegeixTopesDiaris(self.companys)
		self.disponible = self.initBusyTable(
			*glob.glob('indisponibilitats*.conf'))

		def createTable(defaultValue, *iterables) :
			"""Creates a table with as many cells as the cross product of the iterables"""
			return dict((keys, defaultValue) for keys in xproduct(*iterables))

		self.teTelefon = createTable(False,  self.dies, range(self.nhores), self.companys)
		self.tePrincipal = createTable(0,  self.companys, self.dies)
		self.horesDiaries = createTable(0,  self.companys, self.dies)

		self.taules = config.taules
		self.telefonsALaTaula = createTable(0,
			self.dies, range(self.nhores), set(self.taules.values()))

		# Number of hours available each day
		self.disponibilitatDiaria = dict(
			((nom,dia), min(
				self.maxTornsDiaris(nom),
				sum(
					0 if self.isBusy(nom,dia,hora) else 1
					for hora in xrange(self.nhores))
				))
			for nom, dia in xproduct(self.companys, self.dies))

		self.grupsAlliberats = dict([
			(company, [
				group 
				for group, companysDelGrup in self.config.sempreUnLliure.items()
				if company in companysDelGrup])
			for company in self.companys
			])

		self.lliuresEnGrupDAlliberats = dict([
			((group, dia, hora), len(companysDelGrup))
			for (group, companysDelGrupa), dia, hora
			in xproduct(
				self.config.sempreUnLliure.items(),
				self.dies,
				xrange(self.nhores),
				)
			])


		self.nbactracks = 0
		self.backtrackDepth = config.backtrackDepth
		self.cutLog = {}
		self.deeperCutDepth = 0
		self.deeperCutLog = None

		# just for tracking
		self.bestSolution = []
		self.bestCost = 1000000000

		self.cost = 0
		self.minimumCost = config.costLimit
		self.penalties=[]

		self.terminated=False

	def llegeixHores(self):
		lines = [str(h) for h in self.config.hores ]
		return ['-'.join((h1,h2)) for h1,h2 in zip(lines,lines[1:]) ]

	def llegeixTorns(self,tornsfile, ntelefons):
		result = dict()
		with open(tornsfile) as thefile:
			for numline, line in enumerate(thefile):
				if not line.strip(): continue
				row = [col.strip() for col in line.split('\t') ]
				name = row[0]
				if len(row)!=ntelefons+1 :
					raise Backtracker.ErrorConfiguracio(
						"{}:{}: S'experaven {} telefons per {} pero tenim {}".format(
							tornsfile, numline, ntelefons, name, len(row)-1
						))
				result[name] = [int(c) for c in row[1:]]

		# checks
		for telefon in range(ntelefons):
			horesTelefon = sum(v[telefon] for nom, v in result.items())
			if horesTelefon == self.ndies*self.nhores:
				continue
			raise Backtracker.ErrorConfiguracio(
				"Les hores de T{} sumen {} i no pas {}, revisa {}".format(
					telefon+1, horesTelefon, self.ndies*self.nhores, tornsfile))
		return result


	def llegeixTopesDiaris(self, persons) :
		dailyMaxPerPerson = dict(
			(nom, int(value))
			for nom, value
			in self.config.maximHoresDiaries.items()
			)
		for name in dailyMaxPerPerson:
			if name in persons: continue
			raise Backtracker.ErrorConfiguracio(
				"El nom '{}' de maximHoresDiaries a config.yaml no surt a carrega.csv"
				.format(nom))
		return dailyMaxPerPerson

	def maxTornsDiaris(self, company):
		return self.topesDiaris.get(company, self.globalMaxTurnsADay)


	def initBusyTable(self, *filenames) :
		availability = dict(
			((dia,hora,nom), True)
			for nom, dia, hora in xproduct(self.companys, self.dies, range(self.nhores))
			)
		for filename in filenames:
			with open(filename) as thefile:
				for linenum,row in enumerate(thefile) :
					row = row.split('#')[0]
					row = row.split()
					if not row: continue
					row = [col.strip() for col in row]
					company = row[0]
					affectedDays = self.dies
					remain = row[1:]
					if row[1] in self.diesVisualitzacio:
						if row[1] not in self.dies: # holyday
							continue
						affectedDays = [row[1]]
						remain = row[2:]
					affectedTurns = remain[0].strip() if remain else '1'*self.nhores

					if len(affectedTurns)!=self.nhores :
						raise Backtracker.ErrorConfiguracio(
							"'{}':{}: Expected busy string of lenght {} containing '1' on busy hours, found '{}'".format(
							filename, linenum+1, self.nhores, affectedTurns))
					for hora, busy in enumerate(affectedTurns) :
						if busy!='1': continue
						for dia in affectedDays:
							availability[dia, hora, company] = False
		return availability

	def isBusy(self, person, day, hour):
		return not self.disponible[day, hour, person]

	def setBusy(self, person, day, hour, busy=True):
		self.disponible[day, hour, person] = not busy


	def printCuts(self):
		for (depth, motiu), many in sorted(self.cutLog.items()):
			print depth, motiu, many

	def cut(self, motiu, partial, log=None):
		try:
			self.cutLog[len(partial), motiu]+=1
		except KeyError:
			self.cutLog[len(partial), motiu]=1
		if motiu in args.verbose:
			warn(log or motiu)
		if self.deeperCutLog and len(self.deeperCutLog) > len(partial): return
		self.deeperCutDepth = len(partial)
		self.deeperCutLog = log or motiu
		


	def solve(self) :
		while not self.terminated:
			self.nbactracks = 0
			self.solveTorn([])
			if self.nbactracks < self.backtrackDepth:
				break

		if len(self.bestSolution) != len(self.caselles):
			self.printCuts()
			self.minimumCost = self.bestCost
			self.reportSolution((self.bestSolution+['?']*60)[:60] )
			error("Impossible trobar solució\n{}".format( self.deeperCutLog))
		else:
			step("Millor graella grabada a '{}'".format(outputFile()))

	def solveTorn(self, partial):
		if self.terminated: return

		if (len(self.bestSolution), -self.bestCost) <= (len(partial), -self.cost):
			if len(partial) == len(self.caselles):
				print 'Solució trobada amb cost {}.'.format(self.cost)
			else:
				print 'Solució incomplerta {}/{} caselles, cost {}'.format(
					len(partial), len(self.caselles), self.cost)
			self.bestSolution=partial
			self.bestCost=self.cost

		if len(partial) == len(self.caselles):
			self.minimumCost = self.cost
			self.minimumCostReason = self.penalties
			self.reportSolution(partial)
			return

		day, hora, telefon = self.caselles[len(partial)]

		# Comencem dia, mirem si podem acomplir els objectius amb els dies restants
		if not telefon and not hora:

			idia = self.dies.index(day)
			diesRestants =  self.ndies-idia

			# TODO: Heuristica que pot tallar bones solucions
			if self.config.descartaNoPrometedores :
				if idia and self.cost*self.ndies / idia > self.minimumCost:
					self.cut("NoEarlyCost", partial,
						"Tallant una solucio poc prometedora")
					return

			for company in self.companys:
				if self.torns[company][0] > diesRestants * self.config.maximsT1PerDia:
					self.cut("T1RestantsIncolocables", partial,
						"A {} li queden massa T1 per posar"
						.format(company))
					return

				tornsPendents = sum(
					self.torns[company][torn]
					for torn in range(self.ntelefons)
					)
				tornsColocables = sum(
					self.disponibilitatDiaria[company,dia]
					for dia in self.dies[idia:]
					)
				if tornsPendents > tornsColocables:
					self.cut("RestantsIncolocables", partial,
						"A {} nomes li queden {} forats per posar {} hores"
						.format(company, tornsColocables, tornsPendents))
					return

		shuffled = list(self.companys)
		if self.config.aleatori:
			random.shuffle(shuffled)

		for company in shuffled:

			cost = 0
			penalties = []
			taula=self.taules[company]

			# Motius de rebuig del camí

			if self.torns[company][telefon] <= 0:
				self.cut("TotColocat", partial,
					"{} ja ha exhaurit els seus torns de telefon {}ari"
					.format( company, telefon))
				continue

			if self.isBusy(company, day, hora):
				self.cut("Indisponible", partial,
					"{} no esta disponible el {} a la hora {}"
					.format( company, day, hora+1))
				continue

			if telefon==0 and self.tePrincipal[company, day] >= self.config.maximsT1PerDia:
				self.cut("MassesPrincipals", partial,
					"Dos principals per {} el {} no, sisplau"
					.format(company,day))
				continue

			if self.telefonsALaTaula[day, hora, taula]>=self.config.maximPerTaula :
				self.cut("TaulaSorollosa", partial,
					"{} te {} persones a la mateixa taula amb telefon a {}a hora del {}"
					.format(company, self.telefonsALaTaula[day, hora, taula], hora+1, day))
				continue

			def lastInIdleGroup():
				for group in self.grupsAlliberats[company] :
					if self.lliuresEnGrupDAlliberats[group, day, hora] > 1:
						continue

					return "El grup {} on pertany {} no te gent el {} a {} hora".format(group, company, day, hora+1)
				return False

			def markIdleGroups(company, day, hora):
				for g in self.grupsAlliberats[company] :
					self.lliuresEnGrupDAlliberats[g, day, hora] -= 1
				
			def unmarkIdleGroups(company, day, hora):
				for g in self.grupsAlliberats[company] :
					self.lliuresEnGrupDAlliberats[g, day, hora] += 1
				

			if lastInIdleGroup():
				self.cut("IdleGroupViolated", partial, lastInIdleGroup())
				continue

			if self.horesDiaries[company, day] >= self.maxTornsDiaris(company):
				self.cut("DiaATope", partial,
					"No li posem mes a {} que ja te {} hores el {}"
					.format( company, self.horesDiaries[company, day], day))
				continue

			if self.config.deixaEsmorzar and company not in self.config.noVolenEsmorzar:
				if hora==2 and self.teTelefon[day, 1, company]:
					self.cut("Esmorzar", partial,
						"{} es queda sense esmorzar el {}"
						.format(company, day))
					continue

			def penalize(value, short, reason):
				penalties.append((value,reason))
				return value

			if hora and self.horesDiaries[company, day] and not self.teTelefon[day, hora-1, company]:
				if self.maxTornsDiaris(company) < 3:
					self.cut("Discontinu", partial,
						"{} te hores separades el {}".format(company,day))
					continue

				if self.config.costHoresDiscontinues:
					cost += penalize(self.config.costHoresDiscontinues, "Discontinu",
						"{} te hores separades el {}".format(company, day))

			if self.horesDiaries[company, day]>0 :
				cost += penalize(
					self.config.costHoresConcentrades * self.horesDiaries[company, day],
					"Repartiment",
					"{} te mes de {} hores el {}".format(company, self.horesDiaries[company, day], day))

			if self.telefonsALaTaula[day, hora, taula]>0 :
				cost += penalize(
					self.config.costTaulaSorollosa * self.telefonsALaTaula[day, hora, taula],
					"Ocupacio",
					"{} te {} persones a la mateixa taula amb telefon a {}a hora del {}".format(
						company, self.telefonsALaTaula[day, hora, taula], hora+1, day))

			if self.cost + cost > self.minimumCost :
				self.cut("TooMuchCost", partial,
					"Solucio masa costosa: {}"
					.format(self.cost+cost))
				break

			if self.cost + cost == self.minimumCost and len(partial)<len(self.caselles)*0.7 :
				self.cut("CostEqual", partial,
					"Solucio segurament massa costosa, no perdem temps: {}"
					.format(self.cost+cost))
				break

			if self.config.mostraCami or args.track:
				if len(partial) < self.config.maximCamiAMostrar :
					print "  "*len(partial)+company[:2]

			# Anotem la casella
			self.cost += cost
			self.penalties += penalties
			if telefon == 0: self.tePrincipal[company, day]+=1
			self.teTelefon[day, hora, company]=True
			self.setBusy(company,day,hora)
			self.horesDiaries[company,day]+=1
			self.torns[company][telefon]-=1
			self.telefonsALaTaula[day,hora,taula]+=1
			markIdleGroups(company,day,hora)

			# Provem amb la seguent casella
			self.solveTorn(partial+[company])
			self.nbactracks += 1

			# Desanotem la casella
			unmarkIdleGroups(company,day,hora)
			self.telefonsALaTaula[day,hora,taula]-=1
			self.torns[company][telefon]+=1
			self.horesDiaries[company,day]-=1
			self.setBusy(company,day,hora, False)
			self.teTelefon[day, hora, company]=False
			if telefon == 0: self.tePrincipal[company, day]-=1
			if penalties:
				del self.penalties[-len(penalties):]
			self.cost -= cost

			# Si portem massa estona explorant el camí parem i provem un altre
			if self.config.aleatori and self.nbactracks > self.backtrackDepth: break

	def reportSolution(self, solution) :
		# buidar el fitxer, si el cost es diferent

		def properName(name):
			"""Capitalizes name unless configuration provides
			A better alternative, for example with tildes.
			"""
			return self.config.noms.get(name, name.title())

		monday = iniciSetmana()

		firstAtCost = self.minimumCost != self.__dict__.get('storedCost', 'resEsComparaAmbMi')

		if firstAtCost:
			self.storedCost = self.minimumCost
			personalColors = ''.join((
				".{} {{ background-color: #{}; }}\n".format(
					nom,
					self.config.colors[nom]
					if nom in self.config.colors
					and not self.config.randomColors
					else "{:02x}{:02x}{:02x}".format(
						random.randint(127,255),
						random.randint(127,255),
						random.randint(127,255),
						)
					)
				for nom in self.companys
				))
			header = ("""\
<!doctype html>
<html>
<head>
<meta charset='utf-8' />
<style>
h1 {
    color: #560;
}
td, th {
	border:1px solid black;
	width: 8em;
	text-align: center;
}
td:empty { border:0;}
td { padding: 1ex;}
.extensions { width: 60%; }
.extension {
	display: inline-block;
	padding: 1ex 0ex;
	width: 14%;
	text-align: center;
	margin: 2pt 0pt;
	border: 1pt solid black;
	height: 100%;
}
"""+ personalColors + """
</style>
</head>
<body>
""")
			extensions = (u"""\
<h3>Extensions</h3>
<div class="extensions">
""" + "".join((
			u'<div class="extension {name}">{properName}<br/>{extension}</div>\n'
			.format(
				name = name,
				extension = self.config.extensions.get(name, "???"),
				properName = properName(name),
			)
			for name in sorted(self.companys)))
			+
u"""\
</div>
"""
			)


			with open(outputFile(),'w') as output:
				output.write(header)
				output.write("<h1>Setmana {}</h1>".format(monday))
			with open(monitoringFile,'w') as output:
				output.write(header)

		solution = dict(zip(self.caselles, solution))
		taula = '\n'.join(
				[
					'<table>',
					'<tr><td></td><th colspan=3>' +
					'</th><td></td><th colspan=3>'.join(
						d for d in self.diesVisualitzacio
					) + '</th><tr>',
					'<tr><td></td>' +
					'\n<td></td>\n'.join(
						''.join(
							'<th>T{}</th>'.format(telefon+1)
							for telefon in range(self.ntelefons))
						+ '\n'
						for d in self.diesVisualitzacio
					) + '<tr>',
				]+
				[
					'<tr><th>{}</th>\n'.format(h) +
					'\n<td>&nbsp;</td>\n'.join(
						'\n'.join(
							u"<td class='{0}'>{1}</td>".format(
								solution.get((d,hi,l),'festiu').lower(),
								properName(solution.get((d,hi,l),'festiu')),
								) for l in range(self.ntelefons)
							) for d in self.diesVisualitzacio)
					+ '\n</tr>'
					for hi, h in enumerate(self.hores)
				]
				+ [
					'</table>',
				]
			)
		penalitzacions = '\n'.join([
					"",
					"<p>Penalitzacio: {}</p>".format(self.minimumCost),
					"<ul>",
					"\n".join(
						"<li>{}: {}</li>".format(*reason)
						for reason in self.penalties
					),
					"</ul>",
					'',
				])
		with open(monitoringFile,'a') as output:
			output.write(taula)
			output.write(penalitzacions)
		if firstAtCost:
			graellaFile = "graella-telefons-{}.html".format(monday)
			with open(graellaFile,'a') as output:
				output.write(taula)
				with open("extensions.html") as extensions_html:
					extensions += extensions_html.read()
				output.write('\n'.join([
					extensions,
					'',
					'</body>',
					'</html>',
                    '',
					]))



def parseArgs():
	import argparse
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'--keep',
		action='store_true',
		help="no baixa les dades del drive"
		)

	parser.add_argument(
		'--track',
		action='store_true',
		help="visualitza per pantalla el progres de la cerca (molt lent)"
		)

	parser.add_argument(
		'-v',
		dest='verbose',
		metavar='message',
		nargs='+',
		default=[],
		help="activa els missatges de tall del tipus indicat",
		)

	parser.add_argument(
		dest='date',
		nargs='?',
		default=None,
		help='generates the schedule for the week including such date',
		)

	return parser.parse_args()


import sys

args = parseArgs()

if not args.keep:
	baixaDades(iniciSetmana())

import signal
import subprocess

def signal_handler(signal, frame):
	print 'You pressed Ctrl-C!'
	b.terminated = True

signal.signal(signal.SIGINT, signal_handler)

from namespace import namespace as ns

step('Carregant configuració...')
try:
    b = Backtracker(ns.load("config.yaml"))
except:
    error("Configuració incorrecta")
    raise

step('Generant horari...')
b.solve()






# vim: noet
