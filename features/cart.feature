Feature: Shopping cart

  @AC-01
  Scenario: Add a tote bag and calculate shipping and total
    Given the cart is empty
    When I add "กระเป๋าผ้า" (฿499.00) to the cart
    Then the subtotal is ฿499.00
    And shipping is ฿50.00
    And the total is ฿549.00

  @AC-02
  Scenario: Reject a discount below the minimum subtotal
    Given the cart subtotal is ฿499.00
    When I apply the "SAVE10" discount code
    Then I see "ยอดซื้อขั้นต่ำ ฿500.00"
    And the cart total does not change

  @AC-03
  Scenario: Apply a discount at the minimum subtotal
    Given the cart subtotal is ฿500.00
    When I apply the "SAVE10" discount code
    Then the discount is ฿50.00

  @AC-04
  Scenario: Prevent increasing the cable quantity beyond stock
    Given "สายชาร์จ USB-C" has stock 2
    And its quantity in the cart is 2
    When I press "+" to increase its quantity
    Then I see "สินค้าไม่พอ"
    And its quantity remains 2

  @AC-05
  Scenario: Disable the add button for an out-of-stock keyboard
    Given "คีย์บอร์ด" has stock 0
    Then its add button is disabled

  @AC-06
  Scenario: Keep the cart after reloading the page
    Given there are items in the cart
    When I reload the page
    Then the cart contents are unchanged
