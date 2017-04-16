#-*- coding: utf-8 -*-

import unittest
import datetime
from yamlns import namespace as ns
import b2btest
import sys
from parse import parse
import random
import datetime

from htmlgen import HtmlGenFromYaml
from htmlgen import schedule2asterisk
from htmlgen import solution2schedule

class Schedule_Test(unittest.TestCase):

    def eqOrdDict(self, dict1, dict2, msg=None):
        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(dict1)
        dict2 = sorteddict(dict2)

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump(), msg)


    def ns(self,content):
        return ns.loads(content)

    def assertYamlEqual(self, expected, result):
        if type(expected) != ns:
            expected = ns.loads(expected)
        if type(result) != ns:
            result = ns.loads(result)
        self.assertMultiLineEqual(expected.dump(), result.dump())

    def setUp(self):
        self.maxDiff = None
        self.b2bdatapath = "testdata"
        self.addTypeEqualityFunc(ns,self.eqOrdDict)

    def config_singleSlot(self):
        return ns.loads("""\
            nTelefons: 1
            diesVisualitzacio: ['dl']
            hours:  # La darrera es per tancar
            - '09:00'
            - '10:15'
            colors:
                ana: aa11aa
                belen: bb22bb
            extensions:
                ana: 1001
                belen: 1002
            names: {}
        """)

    def config_twoLines(self):
        c = self.config_singleSlot()
        c.nTelefons = 2
        return c

    def config_twoDays(self):
        c = self.config_singleSlot()
        c.diesVisualitzacio.append('dm')
        return c

    def config_twoTimes(self):
        c = self.config_singleSlot()
        c.hours.append('11:30')
        return c

    def config_twoEverything(self):
        c = self.config_singleSlot()
        c.diesVisualitzacio.append('dm')
        c.hours.append('11:30')
        c.nTelefons = 2
        return c

    def test_solution2schedule_oneholiday(self):
        config = self.config_singleSlot()

        result=solution2schedule(
            date=datetime.datetime.strptime(
                '2016-07-11','%Y-%m-%d').date(),
            config=config,
            solution={},
        )
        self.assertYamlEqual(result, """\
            week: '2016-07-11'
            days:
            - dl
            hours:
            - '09:00'
            - '10:15'
            turns:
            - 'T1'
            timetable:
              dl:
              - - festiu
            colors:
              ana:   aa11aa
              belen: bb22bb
            extensions:
              ana:   1001
              belen: 1002
            names: {}
            """)

    def test_solution2schedule_noWeekNextMonday(self):
        config = self.config_singleSlot()

        result=solution2schedule(
            # no date specified
            config=config,
            solution={},
        )

        today = datetime.date.today()
        week=datetime.datetime.strptime(result.week, "%Y-%m-%d").date()
        self.assertEqual(week.weekday(),0) # Monday
        self.assertTrue(week > today) # in the future
        self.assertTrue(week <= today+datetime.timedelta(days=7)) # A week at most

    def test_solution2schedule_oneslot(self):
        config = self.config_singleSlot()

        result=solution2schedule(
            date=datetime.datetime.strptime(
                '2016-07-18','%Y-%m-%d').date(),
            config=config,
            solution={
                ('dl',0,0):'ana',
            },
        )

        self.assertYamlEqual( result, """
            week: '2016-07-18'
            days:
            - dl
            hours:
            - '09:00'
            - '10:15'
            turns:
            - 'T1'
            timetable:
              dl:
              - - ana
            colors:
              ana:   aa11aa
              belen: bb22bb
            extensions:
              ana:   1001
              belen: 1002
            names: {}
        """)

    def test_solution2schedule_manyLines(self):
        config = self.config_twoLines()

        result=solution2schedule(
            date=datetime.datetime.strptime(
                '2016-07-18','%Y-%m-%d').date(),
            config=config,
            solution={
                ('dl',0,0):'ana',
                ('dl',0,1):'belen',
            },
        )

        self.assertYamlEqual( result, """
            week: '2016-07-18'
            days:
            - dl
            hours:
            - '09:00'
            - '10:15'
            turns:
            - 'T1'
            - 'T2'
            timetable:
              dl:
              - - ana
                - belen
            colors:
              ana: 'aa11aa'
              belen: 'bb22bb'
            extensions:
              ana:   1001
              belen: 1002
            names: {}
        """)

    def test_solution2schedule_manyTimes(self):
        config = self.config_twoTimes()

        result=solution2schedule(
            date=datetime.datetime.strptime(
                '2016-07-18','%Y-%m-%d').date(),
            config=config,
            solution={
                ('dl',0,0):'ana',
                ('dl',1,0):'belen',
            },
        )

        self.assertYamlEqual( result, """
            week: '2016-07-18'
            days:
            - dl
            hours:
            - '09:00'
            - '10:15'
            - '11:30'
            turns:
            - 'T1'
            timetable:
              dl:
              - - ana
              - - belen
            colors:
              ana: 'aa11aa'
              belen: 'bb22bb'
            extensions:
              ana:   1001
              belen: 1002
            names: {}
        """)

    def test_solution2schedule_manyDays(self):
        config = self.config_twoDays()

        result=solution2schedule(
            date=datetime.datetime.strptime(
                '2016-07-18','%Y-%m-%d').date(),
            config=config,
            solution={
                ('dl',0,0):'ana',
                ('dm',0,0):'belen',
            },
        )

        self.assertYamlEqual(result, """
            week: '2016-07-18'
            days:
            - dl
            - dm
            hours:
            - '09:00'
            - '10:15'
            turns:
            - 'T1'
            timetable:
              dl:
              - - ana
              dm:
              - - belen
            colors:
              ana:   'aa11aa'
              belen: 'bb22bb'
            extensions:
              ana:   1001
              belen: 1002
            names: {}
        """)

    def test_solution2schedule_manyEverything(self):
        config = self.config_twoEverything()

        result=solution2schedule(
            date=datetime.datetime.strptime(
                '2016-07-18','%Y-%m-%d').date(),
            config=config,
            solution={
                ('dl',0,0):'ana',
                ('dl',1,0):'belen',
                ('dm',0,1):'carla',
                ('dm',1,1):'diana',
            },
        )

        self.assertYamlEqual(result, """
            week: '2016-07-18'
            days:
            - dl
            - dm
            hours:
            - '09:00'
            - '10:15'
            - '11:30'
            turns:
            - 'T1'
            - 'T2'
            timetable:
              dl:
              - - ana
                - festiu
              - - belen
                - festiu
              dm:
              - - festiu
                - carla
              - - festiu
                - diana
            colors:
              ana:   'aa11aa'
              belen: 'bb22bb'
            extensions:
              ana:   1001
              belen: 1002
            names: {}
        """)

    completeConfig="""\
        nTelefons: 3
        diesCerca: ['dx','dm','dj', 'dl', 'dv',] # Els mes conflictius davant
        diesVisualitzacio: ['dl','dm','dx','dj','dv']

        hours:  # La darrera es per tancar
        - '09:00'
        - '10:15'
        - '11:30'
        - '12:45'
        - '14:00'
        randomColors: false # Si vols generar colors aleatoris o fer cas de 'colors'
        colors:
            marc:   'fbe8bc'
            eduard: 'd8b9c5'
            pere:   '8f928e'
            david:  'ffd3ac'
            aleix:  'eed0eb'
            carles: 'c98e98'
            marta:  'eb9481'
            monica: '7fada0'
            yaiza:  '90cdb9'
            erola:  '8789c8'
            manel:  '88dfe3'
            tania:  'c8abf4'
            judit:  'e781e8'
            silvia: '8097fa'
            joan:   'fae080'
            ana:    'aa11aa'
            victor: 'ff3333'
            jordi:  'ff9999'
            cesar:  '889988'
        extensions:
            marta:  3040
            monica: 3041
            manel:  3042
            erola:  3043
            yaiza:  3044
            eduard: 3045
            marc:   3046
            judit:  3047
            judith: 3057
            tania:  3048
            carles: 3051
            pere:   3052
            aleix:  3053
            david:  3054
            silvia: 3055
            joan:   3056
            ana:    1001
            victor: 3182
            jordi:  3183
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
       """

    def test_solution2schedule_completeTimetable(self):
        result=solution2schedule(
            config=self.ns(self.completeConfig),
            solution={
                ('dl',0,0):'jordi',
                ('dl',0,1):'marta',
                ('dl',0,2):'tania',
                ('dl',1,0):'tania',
                ('dl',1,1):'yaiza',
                ('dl',1,2):'silvia',
                ('dl',2,0):'judith',
                ('dl',2,1):'pere',
                ('dl',2,2):'ana',
                ('dl',3,0):'ana',
                ('dl',3,1):'judith',
                ('dl',3,2):'erola',
                ('dm',0,0):'pere',
                ('dm',0,1):'jordi',
                ('dm',0,2):'victor',
                ('dm',1,0):'carles',
                ('dm',1,1):'victor',
                ('dm',1,2):'ana',
                ('dm',2,0):'joan',
                ('dm',2,1):'silvia',
                ('dm',2,2):'eduard',
                ('dm',3,0):'david',
                ('dm',3,1):'joan',
                ('dm',3,2):'monica',
                ('dx',0,0):'yaiza',
                ('dx',0,1):'monica',
                ('dx',0,2):'pere',
                ('dx',1,0):'erola',
                ('dx',1,1):'joan',
                ('dx',1,2):'marta',
                ('dx',2,0):'victor',
                ('dx',2,1):'eduard',
                ('dx',2,2):'jordi',
                ('dx',3,0):'eduard',
                ('dx',3,1):'david',
                ('dx',3,2):'victor',
                ('dj',0,0):'judith',
                ('dj',0,1):'jordi',
                ('dj',0,2):'carles',
                ('dj',1,0):'silvia',
                ('dj',1,1):'tania',
                ('dj',1,2):'judith',
                ('dj',2,0):'monica',
                ('dj',2,1):'ana',
                ('dj',2,2):'judit',
                ('dj',3,0):'judit',
                ('dj',3,1):'erola',
                ('dj',3,2):'joan',
                ('dv',0,0):'ana',
                ('dv',0,1):'judith',
                ('dv',0,2):'jordi',
                ('dv',1,0):'jordi',
                ('dv',1,1):'ana',
                ('dv',1,2):'judith',
                ('dv',2,0):'victor',
                ('dv',2,1):'carles',
                ('dv',2,2):'yaiza',
                ('dv',3,0):'marta',
                ('dv',3,1):'victor',
                ('dv',3,2):'silvia',
                },
            date=datetime.datetime.strptime(
                '2016-07-11','%Y-%m-%d').date(),
        )

        self.assertYamlEqual(result, """\
                week: '2016-07-11'
                days:
                - dl
                - dm
                - dx
                - dj
                - dv
                hours:
                - '09:00'
                - '10:15'
                - '11:30'
                - '12:45'
                - '14:00'
                turns:
                - T1
                - T2
                - T3
                timetable:
                  dl:
                  - - jordi
                    - marta
                    - tania
                  - - tania
                    - yaiza
                    - silvia
                  - - judith
                    - pere
                    - ana
                  - - ana
                    - judith
                    - erola
                  dm:
                  - - pere
                    - jordi
                    - victor
                  - - carles
                    - victor
                    - ana
                  - - joan
                    - silvia
                    - eduard
                  - - david
                    - joan
                    - monica
                  dx:
                  - - yaiza
                    - monica
                    - pere
                  - - erola
                    - joan
                    - marta
                  - - victor
                    - eduard
                    - jordi
                  - - eduard
                    - david
                    - victor
                  dj:
                  - - judith
                    - jordi
                    - carles
                  - - silvia
                    - tania
                    - judith
                  - - monica
                    - ana
                    - judit
                  - - judit
                    - erola
                    - joan
                  dv:
                  - - ana
                    - judith
                    - jordi
                  - - jordi
                    - ana
                    - judith
                  - - victor
                    - carles
                    - yaiza
                  - - marta
                    - victor
                    - silvia
                colors:
                  marc:   'fbe8bc'
                  eduard: 'd8b9c5'
                  pere:   '8f928e'
                  david:  'ffd3ac'
                  aleix:  'eed0eb'
                  carles: 'c98e98'
                  marta:  'eb9481'
                  monica: '7fada0'
                  yaiza:  '90cdb9'
                  erola:  '8789c8'
                  manel:  '88dfe3'
                  tania:  'c8abf4'
                  judit:  'e781e8'
                  silvia: '8097fa'
                  joan:   'fae080'
                  ana:    'aa11aa'
                  victor: 'ff3333'
                  jordi:  'ff9999'
                  cesar:  '889988'
                extensions:
                  marta:  3040
                  monica: 3041
                  manel:  3042
                  erola:  3043
                  yaiza:  3044
                  eduard: 3045
                  marc:   3046
                  judit:  3047
                  judith: 3057
                  tania:  3048
                  carles: 3051
                  pere:   3052
                  aleix:  3053
                  david:  3054
                  silvia: 3055
                  joan:   3056
                  ana:    1001
                  victor: 3182
                  jordi:  3183
                names:
                  silvia: Sílvia
                  monica: Mònica
                  tania:  Tània
                  cesar:  César
                  victor: Víctor
            """)


    def test_htmlTable_oneslot(self):
        h=HtmlGenFromYaml(self.ns("""\
            week: '2016-07-25'
            timetable:
              dl:
              - - ana
            hours:
            - '09:00'
            - '10:15'
            turns:
            - T1
            colors:
              ana: aa11aa
            extensions:
              ana: 1001
            names: # Els que no només cal posar en majúscules
              silvia: Sílvia
              monica: Mònica
              tania: Tània
              cesar: César
              victor: Víctor
            """)
        )

        self.assertMultiLineEqual(
            h.htmlTable(),
            u"<table>\n"
            u"<tr><td></td><th colspan=1>dl</th></tr>\n"
            u"<tr><td></td><th>T1</th>"
            u"</tr>\n"""
            u"<tr><th>09:00-10:15</th>\n"
            u"<td class='ana'>Ana</td>\n"
            u"</tr>\n"
            u"</table>")

    def test_htmlTable_twoTelephonesOneTurnOneDay(self):
        h=HtmlGenFromYaml(self.ns("""\
            week: '2016-07-25'
            timetable:
              dl:
              - - ana
                - jordi
            hours:
            - '09:00'
            - '10:15'
            turns:
            - T1
            - T2
            colors:
              ana: aa11aa
              jordi: ff9999
            extensions:
              ana: 1001
              jordi: 3183
            names: # Els que no només cal posar en majúscules
              silvia: Sílvia
              monica: Mònica
              tania: Tània
              cesar: César
              victor: Víctor
            """)
        )
        self.assertMultiLineEqual(
            h.htmlTable(),
            u"""<table>\n"""
            u"""<tr><td></td><th colspan=2>dl</th></tr>\n"""
            u"""<tr><td></td><th>T1</th><th>T2</th>"""
            u"""</tr>\n"""
            u"""<tr><th>09:00-10:15</th>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""</tr>\n"""
            u"""</table>""")

    def test_htmlTable_twoTelephonesTwoTurnsOneDay(self):
        h=HtmlGenFromYaml(self.ns("""\
            week: '2016-07-25'
            timetable:
              dl:
              - - ana
                - jordi
              - - jordi
                - aleix
            hours:
            - '09:00'
            - '10:15'
            - '11:30'
            turns:
            - T1
            - T2
            colors:
              ana: aa11aa
              jordi: ff9999
            extensions:
              ana: 1001
              jordi: 3183
            names: # Els que no només cal posar en majúscules
               silvia: Sílvia
               monica: Mònica
               tania: Tània
               cesar: César
               victor: Víctor
            """)
        )
        self.assertMultiLineEqual(
            h.htmlTable(),
            u"""<table>\n"""
            u"""<tr><td></td><th colspan=2>dl</th></tr>\n"""
            u"""<tr><td></td><th>T1</th><th>T2</th>"""
            u"""</tr>\n"""
            u"""<tr><th>09:00-10:15</th>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""</tr>\n"""
            u"""<tr><th>10:15-11:30</th>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td class='aleix'>Aleix</td>\n"""
            u"""</tr>\n"""
            u"""</table>""")

    def test_htmlTable_twoTelephonesTwoTurnsTwoDays(self):
        h=HtmlGenFromYaml(self.ns("""\
            week: '2016-07-25'
            timetable:
              dl:
              -
                - ana
                - jordi
              -
                - jordi
                - aleix
              dm:
              -
                - victor
                - marta
              -
                - ana
                - victor
            hours:
            - '09:00'
            - '10:15'
            - '11:30'
            turns:
            - T1
            - T2
            colors:
              ana: aa11aa
              jordi: ff9999
            extensions:
              ana: 1001
              jordi: 3183
            names: # Els que no només cal posar en majúscules
               silvia: Sílvia
               monica: Mònica
               tania: Tània
               cesar: César
               victor: Víctor
            """)
        )
        self.assertMultiLineEqual(
            h.htmlTable(),
            u"""<table>\n"""
            u"""<tr><td></td><th colspan=2>dl</th><td></td><th colspan=2>dm</th>"""
            u"""</tr>\n"""
            u"""<tr><td></td><th>T1</th><th>T2</th><td></td><th>T1</th><th>T2</th>"""
            u"""</tr>\n"""
            u"""<tr><th>09:00-10:15</th>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td class='marta'>Marta</td>\n"""
            u"""</tr>\n"""
            u"""<tr><th>10:15-11:30</th>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td class='aleix'>Aleix</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""</tr>\n"""
            u"""</table>""")

    def test_htmlTable_manyTelephonesmanyTurnsmanyDays(self):
        h=HtmlGenFromYaml(self.ns("""\
            week: '2016-07-25'
            timetable:
              dl:
              -
                - ana
                - jordi
                - pere
              -
                - jordi
                - aleix
                - pere
              -
                - carles
                - joan
                - eduard
              -
                - yaiza
                - joan
                - eduard
              dm:
              -
                - victor
                - marta
                - ana
              -
                - ana
                - victor
                - marta
              -
                - silvia
                - eduard
                - monica
              -
                - david
                - silvia
                - marc
              dx:
              -
                - aleix
                - pere
                - yaiza
              -
                - pere
                - aleix
                - carles
              -
                - marc
                - judit
                - victor
              -
                - david
                - silvia
                - victor
              dj:
              -
                - judit
                - jordi
                - carles
              -
                - joan
                - silvia
                - jordi
              -
                - monica
                - marc
                - tania
              -
                - tania
                - monica
                - marc
              dv:
              -
                - marta
                - victor
                - judit
              -
                - victor
                - joan
                - judit
              -
                - eduard
                - yaiza
                - jordi
              -
                - jordi
                - carles
                - aleix
            hours:
            - '09:00'
            - '10:15'
            - '11:30'
            - '12:45'
            - '14:00'
            turns:
            - T1
            - T2
            - T3
            names: # Els que no només cal posar en majúscules
              silvia: Sílvia
              monica: Mònica
              tania: Tània
              cesar: César
              victor: Víctor
            """)
        )
        self.assertMultiLineEqual(
            h.htmlTable(),
            u"""<table>\n"""
            u"""<tr><td></td><th colspan=3>dl</th>"""
            u"""<td></td><th colspan=3>dm</th>"""
            u"""<td></td><th colspan=3>dx</th>"""
            u"""<td></td><th colspan=3>dj</th>"""
            u"""<td></td><th colspan=3>dv</th></tr>\n"""
            u"""<tr>"""
            u"""<td></td><th>T1</th><th>T2</th><th>T3</th>"""
            u"""<td></td><th>T1</th><th>T2</th><th>T3</th>"""
            u"""<td></td><th>T1</th><th>T2</th><th>T3</th>"""
            u"""<td></td><th>T1</th><th>T2</th><th>T3</th>"""
            u"""<td></td><th>T1</th><th>T2</th><th>T3</th>"""
            u"""</tr>\n"""
            u"""<tr><th>09:00-10:15</th>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td class='pere'>Pere</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td class='marta'>Marta</td>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='aleix'>Aleix</td>\n"""
            u"""<td class='pere'>Pere</td>\n"""
            u"""<td class='yaiza'>Yaiza</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='judit'>Judit</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td class='carles'>Carles</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='marta'>Marta</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td class='judit'>Judit</td>\n"""
            u"""</tr>\n"""
            u"""<tr><th>10:15-11:30</th>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td class='aleix'>Aleix</td>\n"""
            u"""<td class='pere'>Pere</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='ana'>Ana</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td class='marta'>Marta</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='pere'>Pere</td>\n"""
            u"""<td class='aleix'>Aleix</td>\n"""
            u"""<td class='carles'>Carles</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='joan'>Joan</td>\n"""
            u"""<td class='silvia'>Sílvia</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td class='joan'>Joan</td>\n"""
            u"""<td class='judit'>Judit</td>\n"""
            u"""</tr>\n"""
            u"""<tr><th>11:30-12:45</th>\n"""
            u"""<td class='carles'>Carles</td>\n"""
            u"""<td class='joan'>Joan</td>\n"""
            u"""<td class='eduard'>Eduard</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='silvia'>Sílvia</td>\n"""
            u"""<td class='eduard'>Eduard</td>\n"""
            u"""<td class='monica'>Mònica</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='marc'>Marc</td>\n"""
            u"""<td class='judit'>Judit</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='monica'>Mònica</td>\n"""
            u"""<td class='marc'>Marc</td>\n"""
            u"""<td class='tania'>Tània</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='eduard'>Eduard</td>\n"""
            u"""<td class='yaiza'>Yaiza</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""</tr>\n"""
            u"""<tr><th>12:45-14:00</th>\n"""
            u"""<td class='yaiza'>Yaiza</td>\n"""
            u"""<td class='joan'>Joan</td>\n"""
            u"""<td class='eduard'>Eduard</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='david'>David</td>\n"""
            u"""<td class='silvia'>Sílvia</td>\n"""
            u"""<td class='marc'>Marc</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='david'>David</td>\n"""
            u"""<td class='silvia'>Sílvia</td>\n"""
            u"""<td class='victor'>Víctor</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='tania'>Tània</td>\n"""
            u"""<td class='monica'>Mònica</td>\n"""
            u"""<td class='marc'>Marc</td>\n"""
            u"""<td>&nbsp;</td>\n"""
            u"""<td class='jordi'>Jordi</td>\n"""
            u"""<td class='carles'>Carles</td>\n"""
            u"""<td class='aleix'>Aleix</td>\n"""
            u"""</tr>\n"""
            u"""</table>""")

    def test_htmlExtension_oneExtension(self):
        h = HtmlGenFromYaml(self.ns("""\
            extensions:
               marta:  3040
            names:
               cesar: César
               """)
        )
        self.assertMultiLineEqual(h.htmlExtensions(),
        """<h3>Extensions</h3>\n"""
        """<div class="extensions">\n"""
        """<div class="extension marta">Marta<br/>3040</div>\n"""
        """</div>""")

    def test_htmlExtension_twoExtensions(self):
        h = HtmlGenFromYaml(self.ns("""\
            extensions:
               marta:  3040
               aleix:  3053
            names:
               cesar: César
               """)
        )
        self.assertMultiLineEqual(h.htmlExtensions(),
        """<h3>Extensions</h3>\n"""
        """<div class="extensions">\n"""
        """<div class="extension aleix">Aleix<br/>3053</div>\n"""
        """<div class="extension marta">Marta<br/>3040</div>\n"""
        """</div>""")

    def test_htmlExtension_noExtensions(self):
        h = HtmlGenFromYaml(self.ns("""\
            names:
               cesar: César
               """)
        )
        self.assertMultiLineEqual(h.htmlExtensions(),
        """<h3>Extensions</h3>\n"""
        """<div class="extensions">\n"""
        """</div>""")

    def test_htmlHeader_properSetmana(self):
        h = HtmlGenFromYaml(self.ns("""\
            week: '2016-07-25'
                """)
        )
        self.assertMultiLineEqual(h.htmlSetmana(),"""<h1>Setmana 2016-07-25</h1>""")

    def test_htmlHeader_noSetmana(self):
        h = HtmlGenFromYaml(self.ns("""\
            names:
               cesar: César
                """)
        )
        self.assertMultiLineEqual(h.htmlSetmana(),"""<h1>Setmana ???</h1>""")

    def test_htmlColors_oneColor(self):
        h = HtmlGenFromYaml(self.ns("""\
            colors:
               marc: fbe8bc
            extensions:
              marc: 666
                """)
        )
        self.assertMultiLineEqual(
            h.htmlColors(),
            """.marc     { background-color: #fbe8bc; }"""
        )

    def test_htmlColors_forceRandomColor(self):
        h = HtmlGenFromYaml(self.ns("""\
            colors:
               marc: fbe8bc
            randomColors: true
            extensions:
              cesar: 555
                """)
        )
        colors = h.htmlColors()
        self.assertNotEqual(
            colors,
            """.marc      { background-color: #fbe8bc; }"""
        )

        self.assertRegexpMatches(
            colors,
            r"\.marc    * \{ background-color: #[0-9a-f]{6}; }",
        )

    def test_htmlColors_randomColor(self):
        h = HtmlGenFromYaml(self.ns("""\
            extensions:
              cesar: 555
                """)
        )
        self.assertRegexpMatches(
            h.htmlColors(),
            r"\.cesar    *\{ background-color: #[0-9a-f]{6}; \}",
            )

    def test_htmlParse_completeHtml(self):
       h = HtmlGenFromYaml(self.ns("""\
        timetable:
          dl:
          -
            - ana
            - jordi
            - pere
          -
            - jordi
            - aleix
            - pere
          -
            - carles
            - joan
            - eduard
          -
            - yaiza
            - joan
            - eduard
          dm:
          -
            - victor
            - marta
            - ana
          -
            - ana
            - victor
            - marta
          -
            - silvia
            - eduard
            - monica
          -
            - david
            - silvia
            - marc
          dx:
          -
            - aleix
            - pere
            - yaiza
          -
            - pere
            - aleix
            - carles
          -
            - marc
            - judit
            - victor
          -
            - david
            - silvia
            - victor
          dj:
          -
            - judit
            - jordi
            - carles
          -
            - joan
            - silvia
            - jordi
          -
            - monica
            - marc
            - tania
          -
            - tania
            - monica
            - marc
          dv:
          -
            - marta
            - victor
            - judit
          -
            - victor
            - joan
            - judit
          -
            - eduard
            - yaiza
            - jordi
          -
            - jordi
            - carles
            - aleix
        hours:
        - '09:00'
        - '10:15'
        - '11:30'
        - '12:45'
        - '14:00'
        turns:
        - T1
        - T2
        - T3
        colors:
          marc: fbe8bc
          eduard: d8b9c5
          pere: 8f928e
          david: ffd3ac
          aleix: eed0eb
          carles: c98e98
          marta: eb9481
          monica: 7fada0
          yaiza: 90cdb9
          erola: 8789c8
          manel: 88dfe3
          tania: c8abf4
          judit: e781e8
          silvia: 8097fa
          joan: fae080
          ana: aa11aa
          victor: ff3333
          jordi: ff9999
          judith: cb8a85
          cesar:  '889988'
        extensions:
          marta: 3040
          monica: 3041
          manel: 3042
          erola: 3043
          yaiza: 3044
          eduard: 3045
          marc: 3046
          judit: 3047
          judith: 3057
          tania: 3048
          carles: 3051
          pere: 3052
          aleix: 3053
          david: 3054
          silvia: 3055
          joan: 3056
          ana: 1001
          victor: 3182
          jordi: 3183
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """)
       )
       self.assertB2BEqual(h.htmlParse().encode('utf-8'))

    def test_htmlParse_completeHtmlWithHoliday(self):
       h = HtmlGenFromYaml(self.ns("""\
        timetable:
          dl:
          -
            - festiu
            - festiu
            - festiu
          -
            - festiu
            - festiu
            - festiu
          -
            - festiu
            - festiu
            - festiu
          -
            - festiu
            - festiu
            - festiu
          dm:
          -
            - victor
            - marta
            - ana
          -
            - ana
            - victor
            - marta
          -
            - silvia
            - eduard
            - monica
          -
            - david
            - silvia
            - marc
          dx:
          -
            - aleix
            - pere
            - yaiza
          -
            - pere
            - aleix
            - carles
          -
            - marc
            - judit
            - victor
          -
            - david
            - silvia
            - victor
          dj:
          -
            - judit
            - jordi
            - carles
          -
            - joan
            - silvia
            - jordi
          -
            - monica
            - marc
            - tania
          -
            - tania
            - monica
            - marc
          dv:
          -
            - marta
            - victor
            - judit
          -
            - victor
            - joan
            - judit
          -
            - eduard
            - yaiza
            - jordi
          -
            - jordi
            - carles
            - aleix
        hours:
        - '09:00'
        - '10:15'
        - '11:30'
        - '12:45'
        - '14:00'
        turns:
        - T1
        - T2
        - T3
        colors:
          marc: fbe8bc
          eduard: d8b9c5
          pere: 8f928e
          david: ffd3ac
          aleix: eed0eb
          carles: c98e98
          marta: eb9481
          monica: 7fada0
          yaiza: 90cdb9
          erola: 8789c8
          manel: 88dfe3
          tania: c8abf4
          judit: e781e8
          silvia: 8097fa
          joan: fae080
          ana: aa11aa
          victor: ff3333
          jordi: ff9999
          judith: cb8a85
          cesar:  '889988'
        extensions:
          marta: 3040
          monica: 3041
          manel: 3042
          erola: 3043
          yaiza: 3044
          eduard: 3045
          marc: 3046
          judit: 3047
          judith: 3057
          tania: 3048
          carles: 3051
          pere: 3052
          aleix: 3053
          david: 3054
          silvia: 3055
          joan: 3056
          ana: 1001
          victor: 3182
          jordi: 3183
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        """)
       )
       self.assertB2BEqual(h.htmlParse().encode('utf-8'))

    def test_nameToExtension_oneSip(self):
        yaml = """\
            timetable:
              dl:
                1:
                - ana
            hours:
            - '09:00'
            - '10:15'
            turns:
            - T1
            names: # Els que no només cal posar en majúscules
              silvia: Sílvia
              monica: Mònica
              tania: Tània
              cesar: César
              victor: Víctor
            colors:
              ana: aa11aa
            extensions:
              ana: 217
            week: '2016-07-25'
            """
        h = HtmlGenFromYaml(self.ns(yaml))
        self.assertEqual(h.nameToExtension('ana'),217)

    def test_nameToExtension_manySip(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        self.assertEqual(h.nameToExtension('ana'),217)

    def test_extensionToName_oneSip(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        self.assertEqual(h.extensionToName(217),'ana')
    def test_extensionToName_manySip(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        self.assertEqual(h.extensionToName(217),'ana')

    def test_comparePaused_oneDifference_added(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        yaml_paused="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        week: '2016-07-25'
        paused:
          dl:
            1:
            - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_paused = HtmlGenFromYaml(self.ns(yaml_paused))
        difference = self.ns("""\
                                dl:
                                  1:
                                    217:    added
                                """)

        self.assertEqual(h.comparePaused(h_paused),difference)

    def test_comparePaused_oneDifference_removed(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        paused:
          dl:
            1:
            - ana
        """
        yaml_paused="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_paused = HtmlGenFromYaml(self.ns(yaml_paused))
        difference = self.ns("""\
                                dl:
                                  1:
                                    217:    removed
                                """)

        self.assertEqual(h.comparePaused(h_paused),difference)

    def test_comparePaused_oneDifference_changed(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dl:
            1:
            - ana
        """
        yaml_paused="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dl:
            1:
            - jordi
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_paused = HtmlGenFromYaml(self.ns(yaml_paused))
        difference = self.ns("""\
            dl:
              1:
                217:  removed
                219:  added
            """)

        self.assertEqual(h.comparePaused(h_paused),difference)

    def test_comparePaused_oneDifference_dynamic(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dl:
            1:
            - ana
        """
        yaml_paused="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dynamic:
            - jordi
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_paused = HtmlGenFromYaml(self.ns(yaml_paused))
        difference = self.ns("""\
            dl:
                1:
                    217: removed
            dynamic:
                219:  added
            """)

        self.assertEqual(h.comparePaused(h_paused),difference)
    def test_comparePaused_oneDifference_dynamic(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        paused:
          dynamic:
            - pere
            - ana
        """
        yaml_paused="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dynamic:
            - jordi
            - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_paused = HtmlGenFromYaml(self.ns(yaml_paused))
        difference = self.ns("""\
                                dynamic:
                                    219: added
                                    218: removed
                                """)

        self.assertEqual(h.comparePaused(h_paused),difference)

    def test_comparePaused_manyDifferences(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
          dm:
            1:
            - ana
            - pere
          dx:
            2:
            - pere
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dl:
            1:
            - ana
          dx:
            2:
            - pere
        """
        yaml_paused="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        paused:
          dl:
            1:
            - ana
          dm:
            1:
            - jordi
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_paused = HtmlGenFromYaml(self.ns(yaml_paused))
        difference = self.ns("""\
            dx:
              2:
                218:  removed
            dm:
              1:
                219: added
            """)

        self.assertEqual(h.comparePaused(h_paused),difference)

    def test_compareDynamic_oneDifference_added(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        yaml_dynamic="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        dynamic:
        - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_dynamic = HtmlGenFromYaml(self.ns(yaml_dynamic))
        difference = self.ns("""\
                                217: added
                                """)

        self.assertEqual(h.compareDynamic(h_dynamic),difference)

    def test_compareDynamic_oneDifference_removed(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        dynamic:
        - jordi
        """
        yaml_dynamic="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_dynamic = HtmlGenFromYaml(self.ns(yaml_dynamic))
        difference = self.ns("""\
                                219: removed
                                """)

        self.assertEqual(h.compareDynamic(h_dynamic),difference)

    def test_compareDynamic_manyDifferences(self):
        yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        dynamic:
        - jordi
        - ana
        """
        yaml_dynamic="""\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        dynamic:
        - jordi
        - pere
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        h_dynamic = HtmlGenFromYaml(self.ns(yaml_dynamic))
        difference = self.ns("""\
                                217: removed
                                218: added
                                """)

        self.assertEqual(h.compareDynamic(h_dynamic),difference)

    def test_getCurrentQueue_getMonday(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        dynamic:
        - jordi
        - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        day, _= h.getCurrentQueue(datetime.datetime(2016,9,12,10,0))
        self.assertEqual(day,'dl')

    def test_getCurrentQueue_getFirstTurn(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi
        hours:
        - '09:00'
        - '10:15'
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        dynamic:
        - jordi
        - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        _, turn= h.getCurrentQueue(datetime.datetime(2016,9,12,10,0))
        self.assertEqual(turn,1)

    def test_getCurrentQueue_getSecondTurn(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi
          -
            - jordi
            - pere
            - ana

        hours:
        - '09:00'
        - '10:15'
        - '11:30'

        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor

        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        dynamic:
        - jordi
        - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        _, turn= h.getCurrentQueue(datetime.datetime(2016,9,12,11,29))
        self.assertEqual(turn,2)

    def test_getCurrentQueue_getIntermediateTurn(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi
          -
            - jordi
            - pere
            - ana
          dm:
          -
            - jordi
            - ana
            - pere
          -
            - jordi
            - pere
            - ana
          -
            - jordi
            - pere
            - ana

        hours:
        - '09:00'
        - '10:15'
        - '11:30'
        - '12:45'

        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        dynamic:
        - jordi
        - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        _, turn= h.getCurrentQueue(datetime.datetime(2016,9,13,11,29))
        self.assertEqual(turn,2)

    def test_getCurrentQueue_getInvalidTurn(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi
          -
            - jordi
            - pere
            - ana
          dm:
          -
            - jordi
            - ana
            - pere
          -
            - jordi
            - pere
            - ana
          -
            - jordi
            - pere
            - ana

        hours:
        - '09:00'
        - '10:15'
        - '11:30'
        - '12:45'

        names: # Els que no només cal posar en majúscules
          silvia: Sílvia
          monica: Mònica
          tania: Tània
          cesar: César
          victor: Víctor
        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        dynamic:
        - jordi
        - ana
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        with self.assertRaises(Exception):
            h.getCurrentQueue(datetime.datetime(2016,9,13,7,29))

    def test_partialCurrentQueue_getFirstTurn(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi

        hours:
        - '09:00'
        - '10:15'

        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor

        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        self.assertEqual(h.partialCurrentQueue('dl',1),
            (u"""<table>\n"""
             u"""<tr><td></td><th colspan="100%">dl"""
             u"""</th></tr>\n"""
             u"""<tr><td></td><th>T1</th>"""
             u"""<th>T2</th><th>T3</th>"""
             u"""</tr>\n"""
             u"""<tr><th>09:00-10:15</th>\n"""
             u"""<td class='ana'>Ana</td>\n"""
             u"""<td class='pere'>Pere</td>\n"""
             u"""<td class='jordi'>Jordi</td>\n"""
             u"""</tr>\n"""
             u"""</table>"""
             )
        )
    def test_partialCurrentQueue_getSecondTurn(self):
        yaml = """\
        timetable:
          dl:
          -
            - ana
            - pere
            - jordi
          -
            - jordi
            - pere
            - ana
        hours:
        - '09:00'
        - '10:15'
        - '11:30'

        names: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor

        turns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: aa11aa
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        week: '2016-07-25'
        """
        h = HtmlGenFromYaml(self.ns(yaml))
        self.assertEqual(h.partialCurrentQueue('dl',2),
            (u"""<table>\n"""
             u"""<tr><td></td><th colspan="100%">dl"""
             u"""</th></tr>\n"""
             u"""<tr><td></td><th>T1</th>"""
             u"""<th>T2</th><th>T3</th>"""
             u"""</tr>\n"""
             u"""<tr><th>10:15-11:30</th>\n"""
             u"""<td class='jordi'>Jordi</td>\n"""
             u"""<td class='pere'>Pere</td>\n"""
             u"""<td class='ana'>Ana</td>\n"""
             u"""</tr>\n"""
             u"""</table>"""
             )
        )

    def test_schedule2asterisk_oneTurnOneLocal(self):
        configuration = schedule2asterisk(self.ns("""\
            timetable:
              dl:
              -
                - ana
            hours:
            - '09:00'
            - '10:15'
            turns:
            - T1
            colors:
              pere: 8f928e
              ana: aa11aa
              jordi: ff9999
            extensions:
              ana: 217
            week: '2016-07-25'
            names: # Els que no només cal posar en majúscules
               silvia: Sílvia
               monica: Mònica
               tania: Tània
               cesar: César
               victor: Víctor
            """))
        self.assertMultiLineEqual(configuration,
            u"""[entrada_cua_dl_1]\n"""
            u"""music=default\n"""
            u"""strategy=linear\n"""
            u"""eventwhencalled=yes\n"""
            u"""timeout=15\n"""
            u"""retry=1\n"""
            u"""wrapuptime=0\n"""
            u"""maxlen = 0\n"""
            u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
            u"""Periodic-announce-frequency = 15\n"""
            u"""announce-frequency = 0\n"""
            u"""announce-holdtime = no\n"""
            u"""announce-position =no\n"""
            u"""context = bustia_veu\n"""
            u"""member = SIP/217,1\n"""
           )

    def test_schedule2asterisk_manyTurnOneLocal(self):
        configuration = schedule2asterisk(self.ns("""\
            timetable:
              dl:
              -
                - ana
                - jordi
                - pere
              -
                - jordi
                - aleix
                - pere
              -
                - carles
                - joan
                - eduard
              -
                - yaiza
                - joan
                - eduard
              dm:
              -
                - victor
                - marta
                - ana
              -
                - ana
                - victor
                - marta
              -
                - silvia
                - eduard
                - monica
              -
                - david
                - silvia
                - marc
              dx:
              -
                - aleix
                - pere
                - yaiza
              -
                - pere
                - aleix
                - carles
              -
                - marc
                - judit
                - victor
              -
                - david
                - silvia
                - victor
              dj:
              -
                - judit
                - jordi
                - carles
              -
                - joan
                - silvia
                - jordi
              -
                - monica
                - marc
                - tania
              -
                - tania
                - monica
                - marc
              dv:
              -
                - marta
                - victor
                - judit
              -
                - victor
                - joan
                - judit
              -
                - eduard
                - yaiza
                - jordi
              -
                - jordi
                - carles
                - aleix
            hours:
            - '09:00'
            - '10:15'
            - '11:30'
            - '12:45'
            - '14:00'
            turns:
            - T1
            - T2
            - T3
            colors:
              marc: fbe8bc
              eduard: d8b9c5
              pere: 8f928e
              david: ffd3ac
              aleix: eed0eb
              carles: c98e98
              marta: eb9481
              monica: 7fada0
              yaiza: 90cdb9
              erola: 8789c8
              manel: 88dfe3
              tania: c8abf4
              judit: e781e8
              silvia: 8097fa
              joan: fae080
              ana: aa11aa
              victor: ff3333
              jordi: ff9999
              judith: cb8a85
            extensions:
              marta:  206
              monica: 216
              manel:  212
              erola:  213
              yaiza:  205
              eduard: 222
              marc:   203
              judit:  202
              judith: 211
              tania:  208
              carles: 223
              pere:   224
              aleix:  214
              david:  204
              silvia: 207
              joan:   215
              ana:    217
              victor: 218
              jordi:  210
            week: '2016-07-25'
            names: # Els que no només cal posar en majúscules
               silvia: Sílvia
               monica: Mònica
               tania: Tània
               cesar: César
               victor: Víctor
            """)
        )
        self.assertMultiLineEqual(configuration,
        u"""[entrada_cua_dl_1]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/217,1\n"""
        u"""member = SIP/210,2\n"""
        u"""member = SIP/224,3\n"""
        u"""[entrada_cua_dl_2]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/210,1\n"""
        u"""member = SIP/214,2\n"""
        u"""member = SIP/224,3\n"""
        u"""[entrada_cua_dl_3]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/223,1\n"""
        u"""member = SIP/215,2\n"""
        u"""member = SIP/222,3\n"""
        u"""[entrada_cua_dl_4]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/205,1\n"""
        u"""member = SIP/215,2\n"""
        u"""member = SIP/222,3\n"""
        u"""[entrada_cua_dm_1]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/218,1\n"""
        u"""member = SIP/206,2\n"""
        u"""member = SIP/217,3\n"""
        u"""[entrada_cua_dm_2]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/217,1\n"""
        u"""member = SIP/218,2\n"""
        u"""member = SIP/206,3\n"""
        u"""[entrada_cua_dm_3]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/207,1\n"""
        u"""member = SIP/222,2\n"""
        u"""member = SIP/216,3\n"""
        u"""[entrada_cua_dm_4]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/204,1\n"""
        u"""member = SIP/207,2\n"""
        u"""member = SIP/203,3\n"""
        u"""[entrada_cua_dx_1]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/214,1\n"""
        u"""member = SIP/224,2\n"""
        u"""member = SIP/205,3\n"""
        u"""[entrada_cua_dx_2]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/224,1\n"""
        u"""member = SIP/214,2\n"""
        u"""member = SIP/223,3\n"""
        u"""[entrada_cua_dx_3]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/203,1\n"""
        u"""member = SIP/202,2\n"""
        u"""member = SIP/218,3\n"""
        u"""[entrada_cua_dx_4]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/204,1\n"""
        u"""member = SIP/207,2\n"""
        u"""member = SIP/218,3\n"""
        u"""[entrada_cua_dj_1]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/202,1\n"""
        u"""member = SIP/210,2\n"""
        u"""member = SIP/223,3\n"""
        u"""[entrada_cua_dj_2]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/215,1\n"""
        u"""member = SIP/207,2\n"""
        u"""member = SIP/210,3\n"""
        u"""[entrada_cua_dj_3]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/216,1\n"""
        u"""member = SIP/203,2\n"""
        u"""member = SIP/208,3\n"""
        u"""[entrada_cua_dj_4]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/208,1\n"""
        u"""member = SIP/216,2\n"""
        u"""member = SIP/203,3\n"""
        u"""[entrada_cua_dv_1]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/206,1\n"""
        u"""member = SIP/218,2\n"""
        u"""member = SIP/202,3\n"""
        u"""[entrada_cua_dv_2]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/218,1\n"""
        u"""member = SIP/215,2\n"""
        u"""member = SIP/202,3\n"""
        u"""[entrada_cua_dv_3]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/222,1\n"""
        u"""member = SIP/205,2\n"""
        u"""member = SIP/210,3\n"""
        u"""[entrada_cua_dv_4]\n"""
        u"""music=default\n"""
        u"""strategy=linear\n"""
        u"""eventwhencalled=yes\n"""
        u"""timeout=15\n"""
        u"""retry=1\n"""
        u"""wrapuptime=0\n"""
        u"""maxlen = 0\n"""
        u"""; Periodic-announce = /var/lib/asterisk/sounds/bienvenida\n"""
        u"""Periodic-announce-frequency = 15\n"""
        u"""announce-frequency = 0\n"""
        u"""announce-holdtime = no\n"""
        u"""announce-position =no\n"""
        u"""context = bustia_veu\n"""
        u"""member = SIP/210,1\n"""
        u"""member = SIP/223,2\n"""
        u"""member = SIP/214,3\n"""
        )


if __name__ == "__main__":

    if '--accept' in sys.argv:
        sys.argv.remove('--accept')
        unittest.TestCase.acceptMode = True
    if 'B2BACCEPT' in sys.env:
        unittest.TestCase.acceptMode = True

    unittest.main()

# vim: ts=4 sw=4 et
