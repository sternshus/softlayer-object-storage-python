try:
    import unittest2 as unittest
except ImportError:
    import unittest
from mock import Mock
from object_storage.storage_object import StorageObject


class ClientTest(unittest.TestCase):
    def test_instance_setup(self):
        self.assertTrue(self.client == self.obj.client, "client is set")
        self.assertTrue(self.obj.container == 'CONTAINER', "container is set")
        self.assertTrue(self.obj.name == 'NAME', "name is set")

    def test_create(self):
        # no content_type and no ext
        _make_request = Mock()
        self.obj.make_request = _make_request
        self.obj.create()
        self.assertEqual(self.obj.make_request.call_args[0][0], 'PUT')
        self.assertEqual(self.obj.make_request.call_args[1]['headers'], {
            'Content-Length': '0',
            'content-type': 'application/octet-stream'})

    def test_create_w_headers(self):
        # no content_type and no ext
        _make_request = Mock()
        self.obj.make_request = _make_request
        self.obj.create(headers={'test1': 'test1value'})
        self.assertEqual(self.obj.make_request.call_args[0][0], 'PUT')
        self.assertEqual(self.obj.make_request.call_args[1]['headers'], {
            'test1': 'test1value',
            'Content-Length': '0',
            'content-type': 'application/octet-stream'})

    def test_update(self):
        # no content_type and no ext
        _make_request = Mock()
        self.obj.make_request = _make_request
        self.obj.update({'test1': 'test1value'})
        self.assertEqual(self.obj.make_request.call_args[0][0], 'POST')
        self.assertEqual(
            self.obj.make_request.call_args[1]['headers'],
            {'test1': 'test1value'})

    def test_delete(self):
        self.client.delete()
        self.client.delete_object.called_once_with(self.obj.container,
                                                   self.obj.name,
                                                   headers=None)

    def test_read(self):
        _result = Mock()
        self.obj.make_request = Mock(return_value=_result)
        self.obj.read()
        self.obj.make_request.called_once_with('GET')

    def test_read_with_offsets(self):
        _result = Mock()
        self.obj.make_request = Mock(return_value=_result)
        self.obj.read(size=1111, offset=2222)
        self.assertEqual(self.obj.make_request.call_args[1]['headers'],
                         {'Range': 'bytes=2222-3332'})

        self.obj.read(size=1111)
        self.assertEqual(self.obj.make_request.call_args[1]['headers'],
                         {'Range': 'bytes=0-1110'})

        self.obj.read(size=-1111)
        self.assertEqual(self.obj.make_request.call_args[1]['headers'],
                         {'Range': 'bytes=-1111'})

        self.obj.read(offset=2222)
        self.assertEqual(self.obj.make_request.call_args[1]['headers'],
                         {'Range': 'bytes=2222-'})

    def test_copy_to(self):
        _make_request = Mock()
        self.obj._make_request = _make_request
        self.obj._headers = Mock(return_value={})

        other_obj = Mock()
        self.obj.copy_to(other_obj, 1, 2, a1=1, a2=2)

        self.obj._headers.called_once_with()
        h = {'Destination': other_obj.path, 'Content-Length': 0}
        _make_request.called_once_with('COPY', 1, 2,
                                       headers=h,
                                       data='', a1=1, a2=2)

    def test_object_is_dir(self):
        dir_object = StorageObject('stuff', 'mydir',
                                   client=self.client,
                                   headers={'content-type':
                                            'application/directory'})
        legacy_dir_object = StorageObject('stuff', 'olddir',
                                          client=self.client,
                                          headers={'content-type':
                                                   'text/directory'})
        file_object = StorageObject('stuff', 'taco-recipe',
                                    client=self.client,
                                    headers={'content-type': 'text/taco'})

        self.assertTrue(dir_object.is_dir())
        self.assertTrue(legacy_dir_object.is_dir())
        self.assertFalse(file_object.is_dir())

    def test_rename(self):
        self.obj.copy_to = Mock()
        self.obj.delete = Mock()

        _new_obj = Mock()
        self.obj.rename(_new_obj, 1, 2, a1=1, a2=2)
        self.obj.copy_to.called_once_with(_new_obj, 1, 2, a1=1, a2=2)
        self.obj.delete.called_once_with()

    def setUp(self):
        self.client = Mock()
        self.obj = StorageObject('CONTAINER', 'NAME', client=self.client)

if __name__ == "__main__":
    unittest.main()
