"""
Test cases for Error Handler Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel
"""

import os
import logging
import json
import unittest
from unittest.mock import patch

from service import app
from service.common import status
from service.models import init_db, db, Product, DataValidationError
from tests.factories import ProductFactory

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  E R R O R   H A N D L E R   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestErrorHandlers(unittest.TestCase):
    """Test cases for Error Handler Model"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up previous tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ##################################################################
    # 400 - Bad Request (DataValidationError)
    ##################################################################
    def test_data_validation_error(self):
        """Should return 400 Bad Request when DataValidationError is raised"""
        with app.test_request_context("/"):
            response = app.handle_user_exception(DataValidationError("Invalid data"))
            self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)
            body = json.loads(response[0].data.decode())
            self.assertEqual(body["error"], "Bad Request")

    def test_bad_request_handler(self):
        """Should return 400 Bad Request on malformed JSON"""
        response = self.client.post(
            "/products",
            data="not-json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = json.loads(response.data.decode())
        self.assertEqual(body["error"], "Bad Request")

    ##################################################################
    # 404 - Not Found
    ##################################################################
    def test_not_found_handler(self):
        """Should return 404 Not Found on missing endpoint"""
        response = self.client.get("/non-existent-endpoint")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        body = json.loads(response.data.decode())
        self.assertEqual(body["error"], "Not Found")

    ##################################################################
    # 405 - Method Not Allowed
    ##################################################################
    def test_method_not_allowed_handler(self):
        """Should return 405 Method Not Allowed on invalid method"""
        response = self.client.put("/products")  # PUT not allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        body = json.loads(response.data.decode())
        self.assertEqual(body["error"], "Method not Allowed")

    ##################################################################
    # 415 - Unsupported Media Type
    ##################################################################
    def test_unsupported_media_type_handler(self):
        """Should return 415 Unsupported Media Type when not JSON"""
        response = self.client.post(
            "/products",
            data="bad data",
            content_type="text/plain"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        body = json.loads(response.data.decode())
        self.assertEqual(body["error"], "Unsupported media type")

    ##################################################################
    # 500 - Internal Server Error
    ##################################################################
    def test_internal_server_error_handler(self):
        """Should return 500 Internal Server Error on unexpected exception"""
        with patch.object(Product, "find", side_effect=Exception("boom")):
            response = self.client.get("/products/1")
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
