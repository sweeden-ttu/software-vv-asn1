"""
Structural Tests for Shopping Cart (orders.py)

These tests target uncovered lines (86-89) in DynamicallyPricedItem.get_latest_price()
to increase statement coverage toward 100%.

Lines 86-89:
    def get_latest_price(self):
        endpoint = 'https://api.pandastore.com/getitem/' + str(self.id)
        response = requests.get(endpoint)
        price = response.json()['price']
        return price

Strategy: Mock the `requests.get` call at the module level to test the actual
method logic without making real HTTP calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from orders import DynamicallyPricedItem, Order, Item


# --------------------------------------------------------------------------
# Structural Test 1: Cover get_latest_price (lines 86-89)
# Mock requests.get to return a controlled response
# --------------------------------------------------------------------------
def test_structural_get_latest_price_normal():
    """Cover lines 86-89: get_latest_price makes API call and parses JSON"""
    item = DynamicallyPricedItem(42)

    mock_response = MagicMock()
    mock_response.json.return_value = {'price': 19.99}

    with patch('orders.requests.get', return_value=mock_response) as mock_get:
        price = item.get_latest_price()

    assert price == 19.99
    mock_get.assert_called_once_with('https://api.pandastore.com/getitem/42')


# --------------------------------------------------------------------------
# Structural Test 2: get_latest_price with string ID
# Ensures str(self.id) works for non-integer IDs
# --------------------------------------------------------------------------
def test_structural_get_latest_price_string_id():
    """Cover line 86: endpoint construction with str(self.id)"""
    item = DynamicallyPricedItem('ABC-123')

    mock_response = MagicMock()
    mock_response.json.return_value = {'price': 5.50}

    with patch('orders.requests.get', return_value=mock_response) as mock_get:
        price = item.get_latest_price()

    assert price == 5.50
    mock_get.assert_called_once_with('https://api.pandastore.com/getitem/ABC-123')


# --------------------------------------------------------------------------
# Structural Test 3: Full integration — DynamicallyPricedItem in an Order
# Covers lines 86-89 via calculate_item_total → get_latest_price chain
# --------------------------------------------------------------------------
def test_structural_dynamic_item_in_order():
    """Integration: DynamicallyPricedItem used within an Order"""
    order = Order(shipping=5, discount=0, tax_percent=0.10)

    dynamic_item = DynamicallyPricedItem(99, quantity=3)

    mock_response = MagicMock()
    mock_response.json.return_value = {'price': 20.00}

    with patch('orders.requests.get', return_value=mock_response):
        order.add_item(dynamic_item)
        # item total = 3 * 20.00 = 60.00
        # subtotal = 60.00;  amount = 60 + 5 - 0 = 65;  total = 65 * 1.10 = 71.50
        total = order.calculate_order_total()

    assert total == 71.50


# --------------------------------------------------------------------------
# Structural Test 4: get_latest_price with zero price from API
# --------------------------------------------------------------------------
def test_structural_get_latest_price_zero_price():
    """Cover lines 86-89: API returns price of 0"""
    item = DynamicallyPricedItem(1)

    mock_response = MagicMock()
    mock_response.json.return_value = {'price': 0}

    with patch('orders.requests.get', return_value=mock_response):
        price = item.get_latest_price()

    assert price == 0


# --------------------------------------------------------------------------
# Structural Test 5: Order with mix of Item and DynamicallyPricedItem
# --------------------------------------------------------------------------
def test_structural_order_mixed_items():
    """Integration: Order with both Item and DynamicallyPricedItem"""
    order = Order(shipping=10, discount=5, tax_percent=0.05)

    static_item = Item('book', 15.00, 2)       # 30.00
    dynamic_item = DynamicallyPricedItem(7, 1)  # will be 25.00

    mock_response = MagicMock()
    mock_response.json.return_value = {'price': 25.00}

    with patch('orders.requests.get', return_value=mock_response):
        order.add_item(static_item)
        order.add_item(dynamic_item)
        # subtotal = 30 + 25 = 55;  amount = 55 + 10 - 5 = 60;  total = 60 * 1.05 = 63.00
        total = order.calculate_order_total()

    assert total == 63.00
