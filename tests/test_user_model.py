import unittest
from app.models import Users

class UserModelTestCase(unittest.TestCase):

    def test_password_setter(self):
        u = Users()
        u.set_password('cat')
        self.assertTrue(u.password_hash is not None)

    #def test_no_password_getter(self):
    #    u = Users.set_password('cat')
    #    with self.assertRaises(AttributeError):
    #        u.password

    def test_password_verification(self):
        u = Users()
        u.set_password('cat')
        self.assertTrue(u.check_password('cat'))
        self.assertFalse(u.check_password('dog'))

    def test_password_salts_are_random(self):
        u = Users()
        u.set_password('cat')
        u2 = Users()
        u2.set_password('cat')
        self.assertTrue(u.password_hash != u2.password_hash)
