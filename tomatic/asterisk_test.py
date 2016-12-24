# -*- coding: utf-8 -*-

import asterisk
from paramiko import SSHClient,AutoAddPolicy
from Asterisk.Manager import Manager

config=None
try:
    import config
except ImportError:
    pass

import unittest

class Asterisk_Test(unittest.TestCase):

    def ns(self,content):
        return ns.loads(content)

    def tearDown(self):
        return # TODO: Recover this
        if config:
            sshconfig = config.pbx['scp']
            with SSHClient() as ssh:
                ssh.set_missing_host_key_policy(AutoAddPolicy())
                ssh.connect(sshconfig['pbxhost'],
                    username=sshconfig['username'],
                    password=sshconfig['password'])
                path= "/".join(sshconfig['path'].split("/")[:-1])
                file = sshconfig['path'].split("/")[-1]
                ssh.exec_command('cd {}; git checkout {}'.format(path,file))
            pbx = Manager(**config.pbx['pbx'])
            pbx.Command('reload')


    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskSend_oneTurnOneSip(self):
       h = HtmlGenFromYaml(self.ns("""\
        timetable:
          dl:
            1:
            - ana
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        extensions:
          ana: 217
        setmana: 2016-07-25
        companys:
        - ana
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """)
       )
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       queues = pbx.receiveConf()
       self.assertIn('entrada_cua_dl_1',queues)
       queue = queues['entrada_cua_dl_1']
       self.assertIn('members',queue)
       members = queue['members']
       self.assertIn('SIP/217',members)

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskSend_oneTurnManySip(self):
       h = HtmlGenFromYaml(self.ns("""\
        timetable:
          dl:
            1:
            - ana
            - jordi
            - pere
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        extensions:
          ana: 217
          jordi: 210
          pere: 224
        setmana: 2016-07-25
        companys:
        - ana
        - pere
        - jordi
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """)
       )
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       queues = pbx.receiveConf()
       self.assertIn('entrada_cua_dl_1',queues)
       queue = queues['entrada_cua_dl_1']
       self.assertIn('members',queue)
       members = queue['members']
       self.assertIn('SIP/217',members)
       self.assertIn('SIP/210',members)
       self.assertIn('SIP/224',members)

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskSend_manyTurnManySip(self):
       h = HtmlGenFromYaml(self.ns("""\
        timetable:
          dl:
            1:
            - ana
            - jordi
            - pere
            2:
            - pere
            - jordi
          dm:
            1:
            - jordi
            - ana
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        extensions:
          ana: 217
          jordi: 210
          pere: 224
        setmana: 2016-07-25
        companys:
        - ana
        - pere
        - jordi
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """)
       )
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       queues = pbx.receiveConf()
       self.assertIn('entrada_cua_dl_1',queues)
       queue = queues['entrada_cua_dl_1']
       self.assertIn('members',queue)
       members = queue['members']
       self.assertIn('SIP/217',members)
       self.assertIn('SIP/210',members)
       self.assertIn('SIP/224',members)
       self.assertIn('entrada_cua_dl_2',queues)
       queue = queues['entrada_cua_dl_2']
       self.assertIn('members',queue)
       members = queue['members']
       self.assertIn('SIP/210',members)
       self.assertIn('SIP/224',members)
       self.assertIn('entrada_cua_dm_1',queues)
       queue = queues['entrada_cua_dm_1']
       self.assertIn('members',queue)
       members = queue['members']
       self.assertIn('SIP/210',members)
       self.assertIn('SIP/217',members)

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskReceive_oneTurnManySip(self):
       yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        setmana: 2016-07-25
        companys:
        - ana
        - pere
        - jordi
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """
       h = HtmlGenFromYaml(self.ns(yaml))
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
       h_asterisk_yaml = h_asterisk.getYaml()
       self.assertIn('timetable',h_asterisk_yaml)
       self.assertIn('dl',h_asterisk_yaml.timetable)
       self.assertIn(1,h_asterisk_yaml.timetable.dl)
       self.assertEqual(
           set(h_asterisk.getYaml().timetable.dl[1]),
           set(self.ns(yaml).timetable.dl[1])
       )

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskReceive_manyTurnManySip(self):
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
            - jordi
            2:
            - pere
            - jordi
            - ana
        hores:
        - '09:00'
        - '10:15'
        - '11:30'
        torns:
        - T1
        - T2
        - T3

        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        setmana: 2016-07-25
        companys:
        - ana
        - pere
        - jordi
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """
       h = HtmlGenFromYaml(self.ns(yaml))
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
       h_asterisk_yaml = h_asterisk.getYaml()
       self.assertIn('timetable',h_asterisk_yaml)
       self.assertIn('dl',h_asterisk_yaml.timetable)
       self.assertIn(1,h_asterisk_yaml.timetable.dl)
       self.assertEqual(
           set(h_asterisk.getYaml().timetable.dl[1]),
           set(self.ns(yaml).timetable.dl[1])
       )
       self.assertIn('dm',h_asterisk_yaml.timetable)
       self.assertIn(1,h_asterisk_yaml.timetable.dm)
       self.assertIn(2,h_asterisk_yaml.timetable.dm)
       self.assertEqual(
           set(h_asterisk.getYaml().timetable.dm[1]),
           set(self.ns(yaml).timetable.dm[1])
       )
       self.assertEqual(
           set(h_asterisk.getYaml().timetable.dm[2]),
           set(self.ns(yaml).timetable.dm[2])
       )

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskPause_oneSipPaused(self):
       yaml = """\
        timetable:
          dl:
            1:
            - ana
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        colors:
          ana: 98bdc0
        extensions:
          ana: 217
        setmana: 2016-07-25
        companys:
        - ana
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """
       h = HtmlGenFromYaml(self.ns(yaml))
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       pbx.pause('dl',1,217)
       h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
       h_asterisk_yaml = h_asterisk.getYaml()
       self.assertIn('paused',h_asterisk_yaml)
       self.assertIn('dl',h_asterisk_yaml.paused)
       self.assertIn(1,h_asterisk_yaml.paused.dl)
       self.assertEqual(h_asterisk_yaml.paused.dl[1],['ana'])

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskPause_manySipOnePaused(self):
       yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        setmana: 2016-07-25
        companys:
        - ana
        - pere
        - jordi
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        """
       h = HtmlGenFromYaml(self.ns(yaml))
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       pbx.pause('dl',1,217)
       h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
       h_asterisk_yaml = h_asterisk.getYaml()
       self.assertIn('paused',h_asterisk_yaml)
       self.assertIn('dl',h_asterisk_yaml.paused)
       self.assertIn(1,h_asterisk_yaml.paused.dl)
       self.assertEqual(h_asterisk_yaml.paused.dl[1],['ana'])

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskResume_oneSipOneResumed(self):
       yaml = """\
        timetable:
          dl:
            1:
            - ana
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        colors:
          ana: 98bdc0
        extensions:
          ana: 217
        setmana: 2016-07-25
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        companys:
        - ana
        """
       h = HtmlGenFromYaml(self.ns(yaml))
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       pbx.pause('dl',1,217)
       pbx.resume('dl',1,217)
       h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
       h_asterisk_yaml = h_asterisk.getYaml()
       self.assertIn('paused',h_asterisk_yaml)
       self.assertIn('dl',h_asterisk_yaml.paused)
       self.assertIn(1,h_asterisk_yaml.paused.dl)
       self.assertEqual(h_asterisk_yaml.paused.dl[1],[])

    @unittest.skipIf(not config, "depends on pbx")
    def test_asteriskPause_OnePausedOneResumed(self):
       yaml = """\
        timetable:
          dl:
            1:
            - ana
            - pere
            - jordi
        hores:
        - '09:00'
        - '10:15'
        torns:
        - T1
        - T2
        - T3
        colors:
          pere: 8f928e
          ana: 98bdc0
          jordi: ff9999
        noms: # Els que no només cal posar en majúscules
           silvia: Sílvia
           monica: Mònica
           tania: Tània
           cesar: César
           victor: Víctor
        extensions:
          ana: 217
          pere: 218
          jordi: 219
        setmana: 2016-07-25
        companys:
        - ana
        - pere
        - jordi
        """
       h = HtmlGenFromYaml(self.ns(yaml))
       asterisk_conf = h.asteriskParse()
       pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
       pbx.sendConfNow(asterisk_conf)
       pbx.pause('dl',1,217)
       pbx.pause('dl',1,218)
       pbx.resume('dl',1,217)
       h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
       h_asterisk_yaml = h_asterisk.getYaml()
       self.assertIn('paused',h_asterisk_yaml)
       self.assertIn('dl',h_asterisk_yaml.paused)
       self.assertIn(1,h_asterisk_yaml.paused.dl)
       self.assertEqual(h_asterisk_yaml.paused.dl[1],['pere'])

    @unittest.skipIf(not config, "depends on pbx")
    def test_parsePause_onePaused(self):
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
                - jordi
            hores:
            - '09:00'
            - '10:15'
            torns:
            - T1
            - T2
            - T3
            noms: # Els que no només cal posar en majúscules
              silvia: Sílvia
              monica: Mònica
              tania: Tània
              cesar: César
              victor: Víctor
            colors:
              pere: 8f928e
              ana: 98bdc0
              jordi: ff9999
            extensions:
              ana: 217
              pere: 218
              jordi: 219
            setmana: 2016-07-25
            companys:
            - ana
            - pere
            - jordi
            """
        difference = self.ns("""\
            dm:
              1:
                219: added
            """)
        h = HtmlGenFromYaml(self.ns(yaml))
        asterisk_conf = h.asteriskParse()
        pbx = asterisk.Pbx(Manager(**config.pbx['pbx']),config.pbx['scp'])
        pbx.sendConfNow(asterisk_conf)
        pbx.parsePause(difference)
        h_asterisk = HtmlGenFromAsterisk(h.getYaml(),pbx.receiveConf())
        h_asterisk_yaml = h_asterisk.getYaml()
        self.assertIn('paused',h_asterisk_yaml)
        self.assertIn('dm',h_asterisk_yaml.paused)
        self.assertIn(1,h_asterisk_yaml.paused.dm)
        self.assertEqual(h_asterisk_yaml.paused.dm[1],['jordi'])


# vim: ts=4 sw=4 et