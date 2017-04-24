# -*- coding: utf-8 -*-

import unittest
from .dbasterisk import DbAsterisk
from pony.orm import db_session, rollback
import os

class DbAsterisk_Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'setupclass'
        try: os.unlink('demo.sqlite')
        except: pass

    def setUp(self):
        self.a = DbAsterisk("sqlite", 'demo.sqlite')
        db_session.__enter__()

    def tearDown(self):
        rollback()
        db_session.__exit__()
        try: os.unlink('demo.sqlite')
        except: pass

    def fixture(self):
        return self.a

    def test_setQueue(self):
        a = self.fixture()
        a.setQueue(['200', '204', '202' ])
        self.assertEqual(a.currentQueue(), [
            ('200', False),
            ('204', False),
            ('202', False),
        ])

    def test_setQueue_overwrites(self):
        a = self.fixture()
        a.setQueue(['200', '204', '202' ])
        self.assertEqual(a.currentQueue(), [
            ('200', False),
            ('204', False),
            ('202', False),
        ])
        a.setQueue(['400', '404', '402' ])
        self.assertEqual(a.currentQueue(), [
            ('400', False),
            ('404', False),
            ('402', False),
        ])
        a.setQueue([])

    def test_setQueue_emptyClears(self):
        a = self.fixture()
        a.setQueue(['200', '204', '202' ])
        self.assertEqual(a.currentQueue(), [
            ('200', False),
            ('204', False),
            ('202', False),
        ])
        a.setQueue([])
        self.assertEqual(a.currentQueue(), [
        ])

# vim: ts=4 sw=4 et
