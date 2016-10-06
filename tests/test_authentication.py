try:
    import unittest2 as unittest
except ImportError:
    import unittest
from object_storage.transport import BaseAuthentication


class BaseAuthenticationTest(unittest.TestCase):

    def test_instance_setup(self):
        self.assertTrue(self.auth.storage_url is None,
                     "Storage url is set correctly")
        self.assertTrue(self.auth.auth_token is None, "auth_token set correctly")

    def test_authenticate(self):
        self.auth.authenticate()
        self.assertTrue(self.auth.storage_url == 'STORAGE_URL',
                     "storage_url set correctly")
        self.assertTrue(self.auth.auth_token == 'AUTH_TOKEN',
                     "auth_token set correctly")

    def setUp(self):
        self.auth = BaseAuthentication(auth_url='auth_url')

if __name__ == "__main__":
    unittest.main()
