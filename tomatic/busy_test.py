#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from . import busy
from .busy import isodate
from yamlns import namespace as ns

dl='Dilluns'
date='11/07/2017'
ts='05/07/2017 14:51:14'
user='Mate'
t9='9:00 - 10:15'
t10='10:15 - 11:30'
t11='11:30 - 12:45'
t12='12:45 - 14:00'
def turns(*ts):
	return ', '.join(ts)
needed=u'Necessària'
optional=u'Descartable'
reason=u'reunió POL'

class BusyTest(unittest.TestCase):

	def test_gformDataLine_whenBothModesActivated(self):
		line = [ts, user, date, dl, turns(t11,t12), needed, reason]
		with self.assertRaises(busy.GFormError) as ctx:
			busy.gformDataLine(line)
		self.assertEqual(format(ctx.exception),
				"Indisponibilitat especifica dia puntual 11/07/2017 "
				"i dia de la setmana Dilluns")

	def test_gformDataLine_permanentNotAllowed(self):
		line = [ts, user, '', dl, turns(t11,t12), needed, reason]
		with self.assertRaises(busy.GFormError) as ctx:
			busy.gformDataLine(line)
		self.assertEqual(format(ctx.exception),
			"Hi ha indisponibilitats permaments al drive, "
			"afegeix-les a ma i esborra-les del drive")

	def tupleToNs(self, opcional, person, when, turns, reason):
		import datetime
		if type(when) == datetime.date:
			when = dict(date=when)
		else:
			when = dict(weekday=when)
		return ns(
			optional = opcional!='F',
			person = person,
			turns = turns,
			reason = reason,
			**when)

	from testutils import assertNsEqual
	def assertBusyEqual(self, result, expected):
		self.assertNsEqual(result, self.tupleToNs(*expected))

	def assertBusyListEqual(self, result, expected):
		result = ns(lines=[
			entry
			for entry in result
			])
		expected = ns(lines=[
			self.tupleToNs(*entry)
			for entry in expected
			])

		self.assertNsEqual(result, expected)

	def test_gformDataLine_singleHour(self):
		line = [ts, user, date, '', t11, needed, reason]
		result = busy.gformDataLine(line)
		self.assertBusyEqual(result,
			('F', 'mate', isodate('2017-07-11'), '0010', u'reunió POL'))

	def test_gformDataLine_manyHours(self):
		line = [ts, user, date, '', turns(t9,t10,t12), needed, reason]
		result = busy.gformDataLine(line)
		self.assertBusyEqual(result,
			('F', 'mate', isodate('2017-07-11'), '1101', u'reunió POL'))

	def test_gformDataLine_transliteratesNames(self):
		line = [ts, u'María', date, '', turns(t9,t10,t11,t12), needed, reason]
		result = busy.gformDataLine(line)
		self.assertBusyEqual(result,
			('F', 'maria', isodate('2017-07-11'), '1111', u'reunió POL'))

	def test_gformDataLine_withOptional(self):
		line = [ts, 'Mate', date, '', turns(t9,t10,t11,t12), optional, reason]
		result = busy.gformDataLine(line)
		self.assertBusyEqual(result,
			('O', 'mate', isodate('2017-07-11'), '1111', u'reunió POL'))


	def test_gform2Singular_firstIgnored(self):
		gform=[
			['headers ignored']*7,
		]
		self.assertEqual(list(busy.gform2Singular(gform)), [
			])

	def test_gform2Singular_singleEntry(self):
		gform=[
			['headers ignored']*7,
			[ts, u'María', date, '', turns(t9,t10,t12), needed, u'reuni\xf3 POL']
		]
		self.assertBusyListEqual(list(busy.gform2Singular(gform)), [
			('F', 'maria', isodate('2017-07-11'), '1101', u'reunió POL'),
			])


	def test_onWeek_oneOnMonday(self):
		sequence = busy.onWeek(isodate('2018-01-01'), [
			self.tupleToNs('F', 'maria', isodate('2018-01-01'), '1101', u'reunió POL'),
			])
		self.assertBusyListEqual(list(sequence), [
			('F', 'maria', u'dl', '1101', u'reuni\xf3 POL'),
		])

	def test_onWeek_oneOnSunday(self):
		sequence = busy.onWeek(isodate('2018-01-01'), [
			self.tupleToNs('F','maria', isodate('2018-01-07'), '1101', u'reunió POL'),
			])
		self.assertBusyListEqual(list(sequence), [
			('F','maria', u'dg', '1101', u'reuni\xf3 POL'),
		])

	def test_onWeek_optional(self):
		sequence = busy.onWeek(isodate('2018-01-01'), [
			self.tupleToNs('O', 'maria', isodate('2018-01-01'), '1101', u'reunió POL'),
			])
		self.assertBusyListEqual(list(sequence), [
			('O', 'maria', u'dl', '1101', u'reuni\xf3 POL'),
		])

	def test_onWeek_earlyDateIgnored(self):
		sequence = busy.onWeek(isodate('2018-01-01'), [
			self.tupleToNs('F','maria', isodate('2017-12-31'), '1101', u'reunió POL'),
			])
		self.assertBusyListEqual(list(sequence), [
		])

	def test_onWeek_lateDateIgnored(self):
		sequence = busy.onWeek(isodate('2018-01-01'), [
			self.tupleToNs('F','maria', isodate('2018-01-08'), '1101', u'reunió POL'),
			])
		self.assertBusyListEqual(list(sequence), [
		])


	def test_parseBusy_whenEmpty(self):
		lines = [
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			])

	def test_parseBusy_commentsIgnored(self):
		lines = [
			"# comment"
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			])

	def test_parseBusy_emptyLineIgnored(self):
		lines = [
			" "
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			])

	def test_parseBusy_singleWeekDay(self):
		lines = [
			"someone dx 0101 # Reason"
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			ns(
				person='someone',
				weekday='dx',
				turns='0101',
				reason='Reason',
				optional=True,
				),
			])

	def test_parseBusy_forced(self):
		lines = [
			"+someone dx 0101 # Reason" # a plus behind
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			ns(
				person='someone',
				weekday='dx',
				turns='0101',
				reason='Reason',
				optional=False,
				),
			])

	def test_parseBusy_allWeek(self):
		lines = [
			"someone 0101 # Reason"
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			ns(
				person='someone',
				weekday='',
				turns='0101',
				reason='Reason',
				optional=True,
				),
			])

	def test_parseBusy_singleDay(self):
		lines = [
			"someone 2015-01-02 0101 # Reason"
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			ns(
				person='someone',
				date=isodate('2015-01-02'),
				turns='0101',
				reason='Reason',
				optional=True,
				),
			])

	def test_parseBusy_allTurns(self):
		lines = [
			"someone dl # Reason"
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			ns(
				person='someone',
				weekday='dl',
				turns='1111',
				reason='Reason',
				optional=True,
				),
			])

	def test_parseBusy_allTurnsAndDays(self):
		lines = [
			"someone  # Reason"
		]
		self.assertEqual(list(busy.parseBusy(lines)), [
			ns(
				person='someone',
				weekday='',
				turns='1111',
				reason='Reason',
				optional=True,
				),
			])

	def test_parseBusy_missingReason(self):
		lines = [
			"someone dl 1111"
		]
		with self.assertRaises(Exception) as ctx:
			list(busy.parseBusy(lines))

		self.assertEqual(format(ctx.exception),
			"1: Your have to specify a reason "
			"for the busy event after a # sign")

	def test_parseBusy_emtpyReason(self):
		lines = [
			"someone dl 1111 # "
		]
		with self.assertRaises(Exception) as ctx:
			list(busy.parseBusy(lines))

		self.assertEqual(format(ctx.exception),
			"1: Your have to specify a reason "
			"for the busy event after a # sign")

	def test_parseBusy_shortTurns(self):
		lines = [
			"someone dl 111 # Reason"
		]
		with self.assertRaises(Exception) as ctx:
			list(busy.parseBusy(lines))

		self.assertEqual(format(ctx.exception),
			"1: Expected busy string of lenght 4 "
			"containing '1' on busy hours, found '111'")

	def test_parseBusy_badTurns(self):
		lines = [
			"someone dl 0bad # Reason"
		]
		with self.assertRaises(Exception) as ctx:
			list(busy.parseBusy(lines))

		self.assertEqual(format(ctx.exception),
			"1: Expected busy string of lenght 4 "
			"containing '1' on busy hours, found '0bad'")


	def test_parseBusy_customErrorHandler(self):
		lines = [
			"someone dl 0bad # Reason"
		]
		def handler(msg):
			raise Exception(msg+"Added")

		with self.assertRaises(Exception) as ctx:
			list(busy.parseBusy(lines,handler))

		self.assertEqual(format(ctx.exception),
			"1: Expected busy string of lenght 4 "
			"containing '1' on busy hours, found '0bad'"
			"Added")

	def test_parseBusy_continueAfterErrors(self):
		lines = [
			"someone dl 0bad # Reason",
			"someone dl 111 # Reason",
			"someone dl 1111",
			"someone dl 1111 # ",
			"someone dm 1111 # Reason ",
		]
		errors=[]
		def handler(msg):
			errors.append(msg)

		self.assertEqual(list(busy.parseBusy(lines, handler)), [
			ns(
				person='someone',
				weekday='dm',
				turns='1111',
				reason='Reason',
				optional=True,
				),
			])

		self.assertEqual(errors, [
			"1: Expected busy string of lenght 4 "
			"containing '1' on busy hours, found '0bad'",
			"2: Expected busy string of lenght 4 "
			"containing '1' on busy hours, found '111'",
			"3: Your have to specify a reason "
			"for the busy event after a # sign",
			"4: Your have to specify a reason "
			"for the busy event after a # sign",
		])

	def test_formatItem_withWeekday(self):
		item = ns(
			person='someone',
			weekday='dm',
			turns='1111',
			reason=u'La razón',
			optional=True,
			)
		self.assertEqual(
			busy.formatItem(item),
			u"someone dm 1111 # La razón\n"
			)

	def test_formatItem_withDate(self):
		item = ns(
			person='someone',
			date=isodate('2015-02-03'),
			turns='1111',
			reason=u'La razón',
			optional=True,
			)
		self.assertEqual(
			busy.formatItem(item),
			u"someone 2015-02-03 1111 # La razón\n"
			)

	def test_formatItem_forced(self):
		item = ns(
			person='someone',
			weekday='dm',
			turns='1111',
			reason=u'La razón',
			optional=False,
			)
		self.assertEqual(
			busy.formatItem(item),
			u"+someone dm 1111 # La razón\n"
			)




# vim: noet ts=4 sw=4
