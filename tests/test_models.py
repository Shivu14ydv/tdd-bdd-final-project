# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from nose.tools import raises, assert_raises
from service.models import DataValidationError
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""   
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        response = product.find(product.id)
        self.assertEqual(response.id, product.id)
        self.assertEqual(response.name, product.name)
        self.assertEqual(response.description, product.description)
        self.assertEqual(response.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)
    
    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)
    
    def test_update_with_empty_id_raises_error(self):
        product = Product(name="Test Product")
        product.id = None
        with assert_raises(DataValidationError):
            product.update()

            
    def test_deserialize_success(self):
        """ Successfully deserialize a valid product dict """
        self.product = Product()
        data = {
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": "1200.50",
            "available": True,
            "category": "AUTOMOTIVE"
        }
        product = self.product.deserialize(data)
        assert product.name == "Laptop"
        assert product.description == "Gaming laptop"
        assert product.price == Decimal("1200.50")
        assert product.available is True
        assert product.category == Category.AUTOMOTIVE

    @raises(DataValidationError)
    def test_deserialize_missing_field_raises(self):
        """ Missing 'name' should raise DataValidationError """
        self.product = Product()
        data = {
            # "name": "Laptop",   # Missing!
            "description": "Gaming laptop",
            "price": "1200.50",
            "available": True,
            "category": "ELECTRONICS"
        }
        self.product.deserialize(data)

    @raises(DataValidationError)
    def test_deserialize_invalid_boolean_type(self):
        """ Non-bool available should raise DataValidationError """
        self.product = Product()
        data = {
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": "1200.50",
            "available": "True",   # ❌ string instead of bool
            "category": "ELECTRONICS"
        }
        self.product.deserialize(data)

    @raises(DataValidationError)
    def test_deserialize_invalid_category(self):
        """ Invalid category should raise DataValidationError """
        self.product = Product()
        data = {
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": "1200.50",
            "available": True,
            "category": "NON_EXISTENT"  # ❌ not in Category enum
        }
        self.product.deserialize(data)

    @raises(DataValidationError)
    def test_deserialize_with_none_input(self):
        """ None as input should raise DataValidationError """
        self.product = Product()
        self.product.deserialize(None)

    def test_deserialize_price_as_decimal(self):
        """ Ensure price is converted to Decimal """
        self.product = Product()
        data = {
            "name": "Phone",
            "description": "Smartphone",
            "price": "999.99",
            "available": False,
            "category": "AUTOMOTIVE"
        }
        product = self.product.deserialize(data)
        assert isinstance(product.price, Decimal)

from unittest.mock import MagicMock, patch
from decimal import Decimal

class TestProductFindByPrice(unittest.TestCase):

    def setUp(self):
        self.price_decimal = Decimal("19.99")
        self.price_str = "19.99"

    def test_find_by_price_with_decimal(self):
        """ find_by_price should call filter with Decimal price """
        with patch.object(Product, "query") as mock_query:
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            result = Product.find_by_price(self.price_decimal)

            # check filter was called once
            assert mock_query.filter.call_count == 1
            called_arg = mock_query.filter.call_args[0][0]

            # right-hand side of SQLAlchemy expression should equal Decimal
            assert called_arg.right.value == self.price_decimal
            assert result == mock_filter

    def test_find_by_price_with_string(self):
        """ find_by_price should convert string to Decimal """
        with patch.object(Product, "query") as mock_query:
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            result = Product.find_by_price(self.price_str)

            called_arg = mock_query.filter.call_args[0][0]
            assert called_arg.right.value == self.price_decimal
            assert result == mock_filter

    def test_find_by_price_with_extra_quotes_in_string(self):
        """ find_by_price should strip quotes and spaces """
        with patch.object(Product, "query") as mock_query:
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            price_input = ' "19.99" '
            result = Product.find_by_price(price_input)

            called_arg = mock_query.filter.call_args[0][0]
            assert called_arg.right.value == self.price_decimal
            assert result == mock_filter

