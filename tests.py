import unittest
from app import create_app, db
from flask import current_app
from app.models import Clinics, Robots, Patients, Users

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

    def test_snils_hashing(self):
        p = Patients()
        p.get_snils_hash('123-123-33-47')
        self.assertEqual(p.snils_hash,'c1b4957c9cd6208fb59a26d2638ba844')


if __name__ == '__main__':
    unittest.main(verbosity=2)
