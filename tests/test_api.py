import unittest
from api.api_server import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_create_container(self):
        response = self.app.post('/api/containers', json={"image": "nginx", "name": "test_container"})
        self.assertEqual(response.status_code, 201)

    def test_delete_container(self):
        response = self.app.delete('/api/containers/test_container')
        self.assertEqual(response.status_code, 204)

if __name__ == "__main__":
    unittest.main()
