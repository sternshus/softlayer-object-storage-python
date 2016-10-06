try:
    import unittest2 as unittest
except ImportError:
    import unittest
from mock import Mock
from object_storage.client import Client
from object_storage.errors import ResponseError, ContainerNotEmpty


class ClientTest(unittest.TestCase):
    def test_instance_setup(self):
        self.assertTrue(self.client.username == 'username', "username set")
        self.assertTrue(self.client.api_key == 'api_key', "api_key set")
        self.assertTrue(self.client.container_class == self.container_class,
                     "container_class set")
        self.assertTrue(self.client.object_class == self.object_class,
                     "object_class set")
        self.assertTrue(self.client.conn == self.connection, "connection set")
        self.assertTrue(self.client.delimiter == '/', "default delimiter set")

    def test_set_delimiter(self):
        delimiter = Mock()
        self.client.set_delimiter(delimiter)
        self.assertTrue(self.client.delimiter == delimiter,
                     "set_delimiter sets the delimiter")

    def test_container(self):
        self.client.container('container')
        self.container_class.assert_called_once_with('container',
                                                     client=self.client,
                                                     headers=None)

    def test_container_with_props(self):
        self.client.container('container', {'properties': 'property'})
        self.container_class.assert_called_once_with(
            'container',
            client=self.client,
            headers={'properties': 'property'})

    def test_get_container(self):
        loaded_item = Mock()
        self.container_class().load.return_value = loaded_item
        result = self.client.get_container('container_name')
        self.assertTrue(loaded_item == result)
        self.container_class.assert_called_with('container_name',
                                                client=self.client,
                                                headers=None)

    def test_create_container(self):
        created_item = Mock()
        self.container_class().create.return_value = created_item
        result = self.client.create_container('container_name')
        self.assertTrue(created_item == result, 'returns the container itself')
        self.container_class.assert_called_with('container_name',
                                                client=self.client,
                                                headers=None)

    def test_delete_container_raises_not_empty(self):
        self.client.make_request = Mock()
        self.client.make_request.side_effect = ResponseError(
            409, '409 Client Error')
        self.connection.make_request().content
        self.assertRaises(ContainerNotEmpty,
                          self.client.delete_container,
                          'container')

    def test_delete_container_raises_other_error(self):
        self.client.make_request = Mock()
        self.client.make_request.side_effect = ResponseError(
            404, '404 Not Found')
        self.connection.make_request().content
        self.assertRaises(ResponseError,
                          self.client.delete_container,
                          'container')

    def test_list_containers(self):
        self.connection.storage_url = 'storage_url'
        s = '[{"name":"container_name","count":10,"bytes":100}]'
        self.connection.make_request().content = s

    def test_object(self):
        self.client.storage_object('container', 'name')
        self.object_class.assert_called_once_with(
            'container', 'name', client=self.client, headers=None)

    def test_object_with_props(self):
        self.client.storage_object('container', 'name',
                                   {'properties': 'property'})
        self.object_class.assert_called_once_with(
            'container', 'name',
            client=self.client,
            headers={'properties': 'property'})

    def test_get_object(self):
        loaded_item = Mock()
        self.object_class().load.return_value = loaded_item
        result = self.client.get_object('object_name', 'container_name')
        self.assertTrue(loaded_item == result, "Returns the correct object")
        self.object_class.assert_called_with('object_name', 'container_name',
                                             client=self.client, headers=None)

    def test_make_request(self):
        self.connection.storage_url = 'storage_url'
        self.client.make_request('METHOD', 'PATH')
        self.connection.make_request.assert_called_once_with(
            'METHOD', 'storage_url/PATH')

    def test_make_request_listpath(self):
        self.connection.storage_url = 'storage_url'
        self.client.make_request('METHOD', ['PATH', 'PATH2'])
        self.connection.make_request.assert_called_once_with(
            'METHOD', 'storage_url/PATH/PATH2')

    def test_is_dir(self):
        self.assertTrue(self.client.is_dir() is True,
                     'Client itself is a directory')

    def test_path(self):
        self.assertTrue(self.client.path == '',
                     "Path returns an empty string for Client")

    def test_get_url(self):
        self.connection.storage_url = 'storage_url'
        url = self.client.get_url(['path'])
        self.assertTrue(url == 'storage_url/path',
                     "URL Returns correctly with one-item list path")

        self.connection.storage_url = 'storage_url'
        url = self.client.get_url(['path', 'path2'])
        self.assertTrue(url == 'storage_url/path/path2',
                     "URL Returns correctly with two-item list path")

        self.connection.storage_url = 'storage_url'
        self.storage_url = None
        url = self.client.get_url(['path'])
        self.assertTrue(url == 'storage_url/path',
                     "The storage_url is retreived from connection object "
                     "when it isn't set")

        self.connection.storage_url = 'storage_url'
        url = self.client.get_url(['path'])
        self.assertTrue(url == 'storage_url/path',
                     'URL is returned correctly with a string path')

    def test_chunk_upload(self):
        _headers = Mock()
        _chunkable = Mock()
        _size = Mock()
        _url = Mock()
        self.client.get_url = Mock(return_value=_url)
        self.connection.chunk_upload.return_value = _chunkable
        chunkable = self.client.chunk_upload('path',
                                             headers=_headers, size=_size)
        self.assertTrue(chunkable == _chunkable,
                     'Chunkable returns from conn.get_chunkable')
        self.connection.chunk_upload.assert_called_once_with('PUT', _url,
                                                             headers=_headers,
                                                             size=_size)

    def test_getitem(self):
        _container = Mock()
        self.client.container = Mock(return_value=_container)
        container = self.client['CONTAINER']
        self.assertTrue(container == _container,
                     'Container returns from client.container()')
        self.client.container.assert_called_once_with('CONTAINER')

    def setUp(self):
        self.connection = Mock()
        self.container_class = Mock()
        self.object_class = Mock()
        self.connection_class = Mock()
        self.client = Client('username', 'api_key',
                             container_class=self.container_class,
                             object_class=self.object_class,
                             connection=self.connection)

if __name__ == "__main__":
    unittest.main()
