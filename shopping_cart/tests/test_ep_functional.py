"""
20 Functional Tests based on Equivalence Partitioning (EP)
for the Shopping Cart (orders.py) project.

Equivalence Classes Identified:
=============================================================================
Source: calculate_total(subtotal, shipping, discount, tax_percent)
  EC1:  subtotal = 0         (boundary valid)
  EC2:  subtotal > 0         (valid positive)
  EC3:  subtotal < 0         (invalid)
  EC4:  shipping = 0         (boundary valid)
  EC5:  shipping > 0         (valid positive)
  EC6:  shipping < 0         (invalid)
  EC7:  discount = 0         (boundary valid)
  EC8:  0 < discount <= subtotal+shipping  (valid, amount >= 0)
  EC9:  discount > subtotal + shipping     (valid, amount < 0 → clamped to 0)
  EC10: discount < 0         (invalid)
  EC11: tax_percent = 0      (boundary valid)
  EC12: 0 < tax_percent < 1  (valid)
  EC13: tax_percent < 0      (invalid)

Source: Item(name, unit_price, quantity)
  EC14: unit_price = 0       (boundary)
  EC15: unit_price > 0       (valid positive)
  EC16: quantity = 0         (boundary)
  EC17: quantity = 1         (default/min normal)
  EC18: quantity > 1         (valid multiple)

Source: Order(shipping, discount, tax_percent)
  EC19: empty order (0 items)
  EC20: order with 1 item
  EC21: order with multiple items (>1)
  EC22: reward points < 1000  (no bonus)
  EC23: reward points >= 1000 (bonus +10)

Source: DynamicallyPricedItem(id, quantity)
  EC24: default quantity = 1
  EC25: quantity > 1
=============================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from orders import calculate_total, Item, Order, DynamicallyPricedItem


# --------------------------------------------------------------------------
# TC1: calculate_total — EC1 (subtotal=0), EC5, EC8, EC12
# Zero subtotal with positive shipping, discount, and tax
# --------------------------------------------------------------------------
def test_TC01_calculate_total_zero_subtotal():
    """EP: subtotal=0 (EC1), shipping>0 (EC5), discount in range (EC8), tax>0 (EC12)"""
    # subtotal=0, shipping=15, discount=5, tax=10%
    # amount = 0 + 15 - 5 = 10;  total = 10 * 1.10 = 11.00
    result = calculate_total(0, 15, 5, 0.10)
    assert result == 11.00


# --------------------------------------------------------------------------
# TC2: calculate_total — EC2, EC4, EC7, EC12
# Positive subtotal, no shipping, no discount, with tax
# --------------------------------------------------------------------------
def test_TC02_calculate_total_no_shipping_no_discount():
    """EP: subtotal>0 (EC2), shipping=0 (EC4), discount=0 (EC7), tax>0 (EC12)"""
    # amount = 50 + 0 - 0 = 50;  total = 50 * 1.08 = 54.00
    result = calculate_total(50, 0, 0, 0.08)
    assert result == 54.00


# --------------------------------------------------------------------------
# TC3: calculate_total — EC2, EC5, EC8, EC11
# All positive inputs except tax = 0
# --------------------------------------------------------------------------
def test_TC03_calculate_total_zero_tax():
    """EP: subtotal>0 (EC2), shipping>0 (EC5), discount>0 (EC8), tax=0 (EC11)"""
    # amount = 100 + 10 - 20 = 90;  total = 90 * 1.0 = 90.00
    result = calculate_total(100, 10, 20, 0)
    assert result == 90.00


# --------------------------------------------------------------------------
# TC4: calculate_total — EC2, EC5, EC9, EC12
# Discount exceeds subtotal+shipping → amount < 0 → clamped to 0
# --------------------------------------------------------------------------
def test_TC04_calculate_total_discount_exceeds_amount():
    """EP: discount > subtotal+shipping (EC9) → result clamped to 0.00"""
    # amount = 20 + 5 - 50 = -25 → clamped to 0
    result = calculate_total(20, 5, 50, 0.10)
    assert result == 0.00


# --------------------------------------------------------------------------
# TC5: calculate_total — EC3 (subtotal<0) → ValueError
# --------------------------------------------------------------------------
def test_TC05_calculate_total_negative_subtotal():
    """EP: subtotal < 0 (EC3) → should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        calculate_total(-10, 5, 3, 0.05)
    assert 'subtotal cannot be negative' in str(exc_info.value)


# --------------------------------------------------------------------------
# TC6: calculate_total — EC6 (shipping<0) → ValueError
# --------------------------------------------------------------------------
def test_TC06_calculate_total_negative_shipping():
    """EP: shipping < 0 (EC6) → should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        calculate_total(50, -5, 3, 0.05)
    assert 'shipping cannot be negative' in str(exc_info.value)


# --------------------------------------------------------------------------
# TC7: calculate_total — EC10 (discount<0) → ValueError
# --------------------------------------------------------------------------
def test_TC07_calculate_total_negative_discount():
    """EP: discount < 0 (EC10) → should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        calculate_total(50, 5, -10, 0.05)
    assert 'discount cannot be negative' in str(exc_info.value)


# --------------------------------------------------------------------------
# TC8: calculate_total — EC13 (tax_percent<0) → ValueError
# --------------------------------------------------------------------------
def test_TC08_calculate_total_negative_tax():
    """EP: tax_percent < 0 (EC13) → should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        calculate_total(50, 5, 3, -0.05)
    assert 'tax_percent cannot be negative' in str(exc_info.value)


# --------------------------------------------------------------------------
# TC9: calculate_total — EC1, EC4, EC7, EC11
# All inputs are zero → amount = 0, total = 0
# --------------------------------------------------------------------------
def test_TC09_calculate_total_all_zeros():
    """EP: all inputs zero (EC1, EC4, EC7, EC11) → 0.00"""
    result = calculate_total(0, 0, 0, 0)
    assert result == 0.00


# --------------------------------------------------------------------------
# TC10: calculate_total — EC2, EC5, EC8, EC12 with large values
# Large but valid inputs
# --------------------------------------------------------------------------
def test_TC10_calculate_total_large_values():
    """EP: large positive values (EC2, EC5, EC8, EC12)"""
    # amount = 10000 + 500 - 1000 = 9500;  total = 9500 * 1.15 = 10925.00
    result = calculate_total(10000, 500, 1000, 0.15)
    assert result == 10925.00


# --------------------------------------------------------------------------
# TC11: Item — EC14 (unit_price=0), EC18 (quantity>1)
# Zero price item with multiple quantity → total = 0
# --------------------------------------------------------------------------
def test_TC11_item_zero_price_multiple_quantity():
    """EP: unit_price=0 (EC14), quantity>1 (EC18) → total = 0"""
    item = Item('free sample', 0, 5)
    assert item.calculate_item_total() == 0


# --------------------------------------------------------------------------
# TC12: Item — EC15 (unit_price>0), EC17 (quantity=1 default)
# Default quantity, positive price → total = unit_price
# --------------------------------------------------------------------------
def test_TC12_item_default_quantity():
    """EP: unit_price>0 (EC15), quantity=1 default (EC17) → total = price"""
    item = Item('book', 29.99)
    assert item.quantity == 1
    assert item.calculate_item_total() == 29.99


# --------------------------------------------------------------------------
# TC13: Item — EC15, EC18
# Multiple quantity with positive price
# --------------------------------------------------------------------------
def test_TC13_item_multiple_quantity():
    """EP: unit_price>0 (EC15), quantity>1 (EC18) → total = price*qty"""
    item = Item('pen', 1.50, 10)
    assert item.calculate_item_total() == 15.00


# --------------------------------------------------------------------------
# TC14: Item — EC15, EC16 (quantity=0)
# Zero quantity → total = 0
# --------------------------------------------------------------------------
def test_TC14_item_zero_quantity():
    """EP: unit_price>0 (EC15), quantity=0 (EC16) → total = 0"""
    item = Item('eraser', 2.50, 0)
    assert item.calculate_item_total() == 0


# --------------------------------------------------------------------------
# TC15: Order — EC19 (empty order)
# Empty order → subtotal = 0, total = 0
# --------------------------------------------------------------------------
def test_TC15_order_empty():
    """EP: empty order (EC19) → subtotal=0, total=0"""
    order = Order(shipping=5, discount=0, tax_percent=0.10)
    assert order.calculate_subtotal() == 0
    # amount = 0 + 5 - 0 = 5;  total = 5 * 1.10 = 5.50
    assert order.calculate_order_total() == 5.50


# --------------------------------------------------------------------------
# TC16: Order — EC20 (single item) with shipping and tax
# --------------------------------------------------------------------------
def test_TC16_order_single_item():
    """EP: order with 1 item (EC20), shipping and tax applied"""
    order = Order(shipping=10, discount=5, tax_percent=0.07)
    order.add_item(Item('widget', 25.00, 2))
    # subtotal = 50.00;  amount = 50 + 10 - 5 = 55;  total = 55 * 1.07 = 58.85
    assert order.calculate_subtotal() == 50.00
    assert order.calculate_order_total() == 58.85


# --------------------------------------------------------------------------
# TC17: Order — EC21 (multiple items)
# --------------------------------------------------------------------------
def test_TC17_order_multiple_items():
    """EP: order with multiple items (EC21)"""
    order = Order(shipping=0, discount=0, tax_percent=0.05)
    order.add_item(Item('apple', 1.00, 3))     # 3.00
    order.add_item(Item('banana', 0.50, 6))    # 3.00
    order.add_item(Item('cherry', 2.00, 2))    # 4.00
    # subtotal = 10.00;  amount = 10 + 0 - 0 = 10;  total = 10 * 1.05 = 10.50
    assert order.calculate_subtotal() == 10.00
    assert order.calculate_order_total() == 10.50


# --------------------------------------------------------------------------
# TC18: Order — EC22 (reward points < 1000 → no bonus)
# --------------------------------------------------------------------------
def test_TC18_order_reward_points_below_threshold():
    """EP: total < 1000 (EC22) → reward points = int(total), no bonus"""
    order = Order(shipping=0, discount=0, tax_percent=0)
    order.add_item(Item('gadget', 99.99, 1))
    # total = 99.99;  points = int(99.99) = 99 (< 1000, no bonus)
    assert order.get_reward_points() == 99


# --------------------------------------------------------------------------
# TC19: Order — EC23 (reward points >= 1000 → bonus +10)
# --------------------------------------------------------------------------
def test_TC19_order_reward_points_above_threshold():
    """EP: total >= 1000 (EC23) → reward points = int(total) + 10"""
    order = Order(shipping=0, discount=0, tax_percent=0)
    order.add_item(Item('laptop', 1000.00, 1))
    # total = 1000.00;  points = int(1000) = 1000 → >=1000 bonus → 1010
    assert order.get_reward_points() == 1010


# --------------------------------------------------------------------------
# TC20: DynamicallyPricedItem — EC24 (default qty=1), EC25 (qty>1)
# Mocking get_latest_price for both default and multi-quantity
# --------------------------------------------------------------------------
def test_TC20_dynamic_item_default_and_multi_quantity(mocker):
    """EP: DynamicallyPricedItem with default qty (EC24) and qty>1 (EC25)"""
    # Test default quantity = 1
    item1 = DynamicallyPricedItem(101)
    assert item1.quantity == 1
    mocker.patch.object(item1, 'get_latest_price', return_value=49.99)
    assert item1.calculate_item_total() == 49.99

    # Test quantity > 1
    item2 = DynamicallyPricedItem(202, 4)
    assert item2.quantity == 4
    mocker.patch.object(item2, 'get_latest_price', return_value=10.00)
    assert item2.calculate_item_total() == 40.00
