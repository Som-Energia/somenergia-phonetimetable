#!/usr/bin/env python

import itertools
import random

hores = [
	 '9:00-10:15',
	'10:15-11:30',
	'11:30-12:45',
	'12:45-14:00',
	]
nhores=len(hores)
nnivells=3
dies = 'dl','dm','dx','dj','dv'
ndies=len(dies)

torns = dict(
	(nom, [int(primer), int(segon), int(tercer)])
	for nom, primer, segon, tercer in (
		line.split("\t")
		for line in open('torns.csv')
		)
	)

indisponibilitats = [
	('tania','dl',None),
	('judit','dl',None),
	('monica','dv',None),
	('david','dl',None),
	('david','dv',None),
	('david',None,'1100'),
	('pere',None,'1000'),
	('erola',None,'1000'),
	('marc',None,'1000'),
	]

caselles = list(itertools.product(dies, range(nhores), range(nnivells)))

class Backtracker:
	def __init__(self, shuffle=True) :
		self.doshuffle=shuffle
		self.companys = list(torns.keys())
		self.disponible = dict((
			((dia,hora,nom), not self.indisponible(dia, hora, nom))
			for nom, dia, hora in itertools.product(self.companys, dies, range(nhores))
			))
		self.horesDiaries = dict(((nom,dia), 0) for nom,dia in itertools.product(self.companys,dies))
		self.nbactracks = 0

	def solve(self) :
		while True:
			self.nbactracks = 0
			self.solveTorn([])

	def indisponible(self, dia, hora, company) :
		for acompany, adia, ahora in indisponibilitats:
			if company != acompany: continue
			if adia is not None and dia != adia: continue
			if ahora is not None and ahora[hora] == '0': continue
			return True
		return False


	def solveTorn(self, partial):
		if len(partial) == len(caselles):
			self.reportSolution(partial)
			return
		day, hora, nivell = caselles[len(partial)]
#		print partial
		companys = list(torns.keys())
		if self.doshuffle:
			random.shuffle(companys)
		for company in companys:
			if torns[company][nivell] == 0:
#				print "En {} ja ha exhaurit els seus torns de {} nivell".format( company, nivell)
				continue
			if not self.disponible[day, hora, company]:
#				print "En {} no esta disponible el {} a la hora {}".format( company, day, hora)
				continue
			if self.horesDiaries[company, day]==2:
#				print "No li posem mes a {} que ja te {} hores el {}".format( company, self.horesDiaries[company], day)
				continue
			if self.horesDiaries[company, day]==1 and hora==1:
#				print "Deixem esmorzar a {} el {}".format( company, day)
				continue

			if len(partial) < 20 : print "  "*len(partial)+company[:2]

			self.disponible[day, hora, company]=False
			self.horesDiaries[company,day]+=1
			torns[company][nivell]-=1

			self.solveTorn(partial+[company])
			self.nbactracks += 1

			torns[company][nivell]+=1
			self.horesDiaries[company,day]-=1
			self.disponible[day, hora, company]=True

			if self.nbactracks > 1000:
				break
			

	def reportSolution(self, solution) :
		solution = dict(zip(caselles, solution))
		with open("taula.html",'w') as output:
			output.write("""\
	<style>
	td, th {
		border:1px solid black;
		width: 8em;
		text-align: center;
	}
	td { padding: 1ex;}
	"""+ ''.join(".{} {{ background-color: #{:02x}{:02x}{:02x}; }}\n".format(
		nom, random.randint(127,255), random.randint(127,255), random.randint(127,255)) for nom in self.companys)
	+""")
	</style>
			""")
			output.write( '\n'.join(
				[
					'<table>',
					'<tr><td></td><th colspan=3>' + '</th><td></td><th colspan=3>'.join(
						dia for dia in dies
					) + '</th><tr>',
					'<tr><td></td><th>' + 
					'<th>'.join(
						'</th><th>'.join(
							'T{}'.format(nivell+1)
							for nivell in range(nnivells))+'</th><td></td>'
						for dia in dies
					) + '</th><tr>',
				]+
				[
					'<tr><th>{}</th>'.format(h) +
					'<td>&nbsp;</td>'.join(
						'</td>'.join("<td class='{0}'>{0}</td>".format(solution[d,hi,l]) for l in range(nnivells))
						for d in dies)
					+ '</tr>'
					for hi, h in enumerate(hores)
				]
				+ ['</table>']
				))
		exit(0)

b = Backtracker()
b.solve()







