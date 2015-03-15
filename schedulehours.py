#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import random

class Backtracker:
	class ErrorConfiguracio(Exception): pass

	def __init__(self, shuffle=True) :

		self.maxHoresDiaries = 2
		self.doshuffle = shuffle
		self.ntelefons = 3
		self.dies = 'dl','dm','dx','dj','dv'
		self.ndies = len(self.dies)
		self.hores = self.llegeixHores('hores.csv')
		self.nhores = len(self.hores)
		self.torns = self.llegeixTorns('torns.csv', self.ntelefons)
		self.companys = list(self.torns.keys())
		self.caselles = list(itertools.product(self.dies, range(self.nhores), range(self.ntelefons)))
		self.topesDiaris = self.llegeixTopesDiaris('topesDiaris.csv')
		self.disponible = self.initAvailability(
			'indisponibilitats.conf', self.companys, self.dies, self.nhores)

		self.teTelefon = dict((
			((dia,hora,nom), False)
			for nom, dia, hora in itertools.product(self.companys, self.dies, range(self.nhores))
			))
		self.tePrincipal = dict((
			((nom, dia), False)
			for nom, dia in itertools.product(self.companys, self.dies)
			))
		self.horesDiaries = dict(
			((nom,dia), 0)
			for nom, dia in itertools.product(self.companys, self.dies))

		self.nbactracks = 0
		self.cutters = {}
		self.longer = []

		self.cost = 0
		self.minimumCost = 60
		self.penalties=[]

	def llegeixHores(self, horesfile):
		linees = [
			l.strip() for l in open(horesfile) if l.strip() ]
		return ['-'.join((h1,h2)) for h1,h2 in zip(linees,linees[1:]) ]

	def llegeixTorns(self,tornsfile, ntelefons):
		result = dict()
		with open(tornsfile) as thefile:
			for numline, line in enumerate(thefile):
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
					telefon, horesTelefon, self.ndies*self.nhores, tornsfile))
		return result

	def llegeixTopesDiaris(self, filename) :
		result = dict((
			(nom.strip(), int(tope))
				for nom, tope in (
					line.split('\t')
					for line in open(filename)
					)
			))
		for nom in result:
			if nom in self.torns: continue
			raise Backtracker.ErrorConfiguracio("Eps, '{}' que apareix a '{}' no surt a torns.csv"
				.format(nom, filename))
		return result

	def initAvailability(self, filename, companys, dies, nhores) :
		availability = dict(
			((dia,hora,nom), True)
			for nom, dia, hora in itertools.product(companys, dies, range(nhores))
			)
		with open(filename) as thefile:
			for linenum,row in enumerate(line.split() for line in thefile) :
				row = [col.strip() for col in row]
				company = row[0]
				affectedDays = [row[1]] if row[1] in dies else dies
				affectedTurns = row[1].strip() if row[1] not in dies else (
					row[2] if len(row)>2 else '1'*nhores
					)
				if len(affectedTurns)!=nhores :
					raise Backtracker.ErrorConfiguracio(
						"'{}':{}: Expected busy string of lenght {} containing '1' on busy hours, found '{}'".format(
						filename, linenum, nhores, affectedTurns))
				for hora, busy in enumerate(affectedTurns) :
					if busy!='1': continue
					for dia in affectedDays:
						availability[dia, hora, company] = False
		return availability

	def isBusy(self, person, day, hour):
		return not self.disponible[day, hour, person]

	def setBusy(self, person, day, hour, busy=True):
		self.disponible[day, hour, person] = not busy


	def solve(self) :
		while True:
			self.nbactracks = 0
			self.solveTorn([])

	def printCuts(self):
		for (depth, motiu), many in sorted(self.cutters.items()):
			print depth, motiu, many

	def cut(self, motiu, partial):
		try:
			self.cutters[len(partial), motiu]+=1
		except KeyError:
			self.cutters[len(partial), motiu]=1
			

	def maxTornsDiaris(self, company):
		return self.topesDiaris.get(company, self.maxHoresDiaries)


	def solveTorn(self, partial):
		if (len(self.longer), -self.minimumCost) <= (len(partial), -self.cost):
			self.longer=partial
			print len(partial), self.cost

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

			if idia and self.cost*self.ndies / idia > self.minimumCost:
				self.cut("NoEarlyCost", partial)
				return

			for company in self.companys:
				if self.torns[company][0] > diesRestants:
					self.cut("PreveigT1", partial)
#					print "Eps a {} li queden massa T1 per posar".format(company)
					return
				tornsPendents = sum(self.torns[company][torn] for torn in range(self.ntelefons))
				tornsColocables = diesRestants*self.maxTornsDiaris(company)
				if tornsPendents > tornsColocables:
					self.cut("PreveigTots", partial)
#					print "Eps a {} no li queden dies per posar les seves hores".format(company)
					return

		shuffled = list(self.companys)
		if self.doshuffle:
			random.shuffle(shuffled)

		for company in shuffled:

			cost = 0
			penalties = []

			if self.torns[company][telefon] < 1:
#				print "{} ja ha exhaurit els seus torns de {} telefon".format( company, telefon)
				self.cut("TotColocat", partial)
				continue

			if self.isBusy(company, day, hora):
#				print "{} no esta disponible el {} a la hora {}".format( company, day, hora)
				self.cut("Indisponible", partial)
				continue

			if telefon==0 and self.tePrincipal[company, day]:
#				print "Dos principals per {} el {} no, sisplau".format(company,day)
				continue

			if self.horesDiaries[company, day] >= self.maxTornsDiaris(company):
#				print "No li posem mes a {} que ja te {} hores el {}".format( company, self.horesDiaries[company], day)
				self.cut("DiaATope", partial)
				continue

			if hora==2 and self.teTelefon[day, 1, company]:
#				print "{} es queda sense esmorzar el {}".format(company, day)
				self.cut("Esmorzar", partial)
				continue

			def penalize(value, short, reason):
				penalties.append((value,reason))
				return value

			if hora and self.horesDiaries[company, day] and not self.teTelefon[day, hora-1, company]:
				if self.maxTornsDiaris(company) < 3:
					self.cut("Discontinu", partial)
#					print("{} te hores separades el {}".format(company,day))
					continue

				cost += penalize(40, "Discontinu",
					"{} te hores separades el {}".format(company, day))

			if self.horesDiaries[company, day]>0 :
				cost += penalize(self.horesDiaries[company, day], "Repartiment",
					"{} te mes de {} hores el {}".format(company, self.horesDiaries[company, day], day))

			if self.cost + cost > self.minimumCost :
#				print "Solucio masa costosa: {}".format(self.cost+cost)
				self.cut("TooMuchCost", partial)
				break

			if self.cost + cost == self.minimumCost and len(partial)<len(self.caselles)*0.7 :
#				print "Solucio segurament massa costosa, no perdem temps: {}".format(self.cost+cost)
				self.cut("CostEqual", partial)
				break

			self.cost += cost
			self.penalties += penalties

#			if len(partial) < 60 : print "  "*len(partial)+company[:2]

			if telefon == 0: self.tePrincipal[company, day]=True
			self.teTelefon[day, hora, company]=True
			self.setBusy(company,day,hora)
			self.horesDiaries[company,day]+=1
			self.torns[company][telefon]-=1

			self.solveTorn(partial+[company])
			self.nbactracks += 1

			self.torns[company][telefon]+=1
			self.horesDiaries[company,day]-=1
			self.setBusy(company,day,hora, False)
			self.teTelefon[day, hora, company]=False
			if telefon == 0: self.tePrincipal[company, day]=False
			if penalties:
				del self.penalties[-len(penalties):]
			self.cost -= cost

			if self.nbactracks > 1000: break

	def reportSolution(self, solution) :

		# resetejar el fitxer de zero, si el cost es diferent
		if self.minimumCost != self.__dict__.get('storedCost', 'resEsComparaAmbMi'):
			with open("taula.html",'w') as output:
				self.storedCost = self.minimumCost
				output.write("""\
					<style>
					td, th {
						border:1px solid black;
						width: 8em;
						text-align: center;
					}
					td { padding: 1ex;}
					"""+ ''.join("""\
					.{} {{ background-color: #{:02x}{:02x}{:02x}; }}
					""".format(
						nom, random.randint(127,255), random.randint(127,255), random.randint(127,255)) for nom in self.companys)
					+""")
					</style>
						""")

		solution = dict(zip(self.caselles, solution))
		with open("taula.html",'a') as output:
			output.write( '\n'.join(
				[
					'<table>',
					'<tr><td></td><th colspan=3>' + '</th><td></td><th colspan=3>'.join(
						dia for dia in self.dies
					) + '</th><tr>',
					'<tr><td></td><th>' + 
					'<th>'.join(
						'</th><th>'.join(
							'T{}'.format(telefon+1)
							for telefon in range(self.ntelefons))+'</th><td></td>'
						for dia in self.dies
					) + '</th><tr>',
				]+
				[
					'<tr><th>{}</th>'.format(h) +
					'<td>&nbsp;</td>'.join(
						'</td>'.join("<td class='{0}'>{0}</td>".format(solution[d,hi,l].capitalize()) for l in range(self.ntelefons))
						for d in self.dies)
					+ '</tr>'
					for hi, h in enumerate(self.hores)
				]
				+ [
					'</table>',
					"<p>Penalitzacio: {}</p>".format(self.cost),
					"<ul>",
					"\n".join(
						"<li>{}: {}</li>".format(*reason)
						for reason in self.penalties
					),
					"</ul>",
				]
				))
#		exit(0)


import sys
import unittest

class Backtracker_Test(unittest.TestCase):
	def test_availability(self):
		availability = initAvailability()

if '--test' in sys.argv:
	sys.argv.remove('--test')
	unittest.main()

import signal 
import subprocess

def signal_handler(signal, frame):
	print 'You pressed Ctrl-C!'
	b.printCuts()
	if len(b.longer) != len(b.caselles):
		print(b.longer)
		b.reportSolution((b.longer+['?']*60)[:60] )
	sys.exit(-1)

signal.signal(signal.SIGINT, signal_handler)

b = Backtracker()
for k,v in sorted(b.disponible.items()) : 
	if 'david' not in k: continue
	print k,v
b.solve()







