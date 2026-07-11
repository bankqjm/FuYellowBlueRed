"""Add new columns for ordering feature enhancement."""
import pymysql

conn = pymysql.connect(
    host='obmt7986sozyczk0-mi.aliyun-cn-hangzhou-internet.oceanbase.cloud',
    port=3306,
    user='fuybr',
    password='FuybR@1266!',
    database='fuybr'
)
cursor = conn.cursor()

alter_statements = [
    "ALTER TABLE orders ADD COLUMN dining_count INT DEFAULT 1",
    "ALTER TABLE orders ADD COLUMN pay_channel VARCHAR(20) DEFAULT 'BALANCE'",
    "ALTER TABLE orders ADD COLUMN pay_time DATETIME NULL",
    "ALTER TABLE products ADD COLUMN tags VARCHAR(500) NULL",
    "ALTER TABLE products ADD COLUMN rating FLOAT DEFAULT 0.0",
    "ALTER TABLE cart_items ADD COLUMN options VARCHAR(500) NULL",
]

for stmt in alter_statements:
    try:
        cursor.execute(stmt)
        print(f"OK: {stmt[:60]}...")
    except Exception as e:
        if "Duplicate column" in str(e):
            print(f"SKIP (exists): {stmt[:60]}...")
        else:
            print(f"ERROR: {stmt[:60]}... -> {e}")

conn.commit()
cursor.close()
conn.close()
print("Migration complete!")
