# ร้านค้าและตะกร้าสินค้า

## ติดตั้ง

```sh
python -m pip install -r requirements.txt
```

## เตรียมข้อมูลเริ่มต้น

```sh
python -m app.seed
```

## รันแอปที่พอร์ต 8080

```sh
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## รัน tests

```sh
pytest -q
```

## Environment

- `DB_PATH`: path ของ SQLite database; ค่าเริ่มต้นคือ `cart.db`
- `APP_ENV=test`: เปิดใช้งาน `POST /api/test/reset` (กำหนดก่อนเริ่มแอป)

## โครงสร้าง

- `app/`: API, database, repository, pricing และ seed data
- `tests/`: tests ของ API, database, pricing และ smoke tests
- `static/`: หน้าเว็บและไฟล์ CSS/JavaScript
- `docs/requirements.md`: [รายละเอียด requirements และ acceptance criteria](docs/requirements.md)
