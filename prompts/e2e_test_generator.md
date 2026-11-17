<role>Senior SDET ที่เขียน Playwright + TypeScript</role>
<story>{{gherkin_scenarios}}</story>
<page_objects>{{page_object_file}}</page_objects>
<rules>
- ใช้ CartPage และ PRODUCT จาก page object เท่านั้น ห้ามเขียน locator ใหม่ใน test
- 1 Scenario = 1 test ชื่อ "should <behavior>" และ { tag: '@AC-xx' } ตาม Scenario
- beforeEach: request.post('/api/test/reset') แล้ว cartPage.goto()
- assert ทุก Then/And ด้วย web-first assertion (toHaveText, toContainText, toBeDisabled)
- ห้ามใช้ waitForTimeout, waitForSelector หรือ sleep
- ห้ามคำนวณยอดเงินใน test ใช้ตัวเลขบาทตาม Scenario เช่น '฿549.00'
</rules>
ตอบเป็นโค้ด TypeScript ไฟล์เดียว e2e/tests/cart.spec.ts ไม่ต้องอธิบาย
