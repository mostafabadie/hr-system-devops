import sqlite3
from werkzeug.security import generate_password_hash
# إنشاء الاتصال
conn = sqlite3.connect("../data/hr.db")
cursor = conn.cursor()
c = conn.cursor()
DB_PATH = "../data/hr.db"
## إنشاء جدول الموظفين
c.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT,
    position TEXT,
    salary REAL,
    username TEXT UNIQUE,
    password_hash TEXT,
    phone TEXT,
    email TEXT,
    document TEXT,
    basic_salary REAL
)
''')

# منع تكرار أسماء الموظفين عن طريق فهرس فريد
try:
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_name_unique ON employees(name)"
    )
except sqlite3.OperationalError:
    # في حال وجود بيانات مكررة قد يفشل إنشاء الفهرس، يمكن معالجتها لاحقاً يدوياً
    pass

# جدول الرواتب مرتبط بـ employee_id
cursor.execute('''
CREATE TABLE IF NOT EXISTS payrolls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    basic_salary REAL NOT NULL,
    bonus REAL DEFAULT 0,
    deductions REAL DEFAULT 0,
    net_salary REAL NOT NULL,
    payment_date TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
)
''')
# إنشاء جدول الحضور
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER,
    date TEXT,
    status TEXT,
    FOREIGN KEY (emp_id) REFERENCES employees(id)
)
""")

# إضافة مستخدم مسؤول افتراضي (لتسجيل الدخول)
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
""")


cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))

# إضافة عمود document للموظفين إذا لم يكن موجوداً مسبقاً
try:
    cursor.execute("ALTER TABLE employees ADD COLUMN document TEXT")
except sqlite3.OperationalError:
    # العمود موجود بالفعل
    pass
conn.commit()
conn.close()

print("Database is ready and tables have been created.")

DB_PATH = "../data/hr.db"

# 1) اختَر كلمة السر
plain_password = "123"  # غيّرها لما تحب

# 2) جهّز الـ hash
pwd_hash = generate_password_hash(plain_password)
print(pwd_hash)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

employee_id = 1        # غيّرها إلى ID الموظف
username = "emp1"      # اسم المستخدم الذي سيدخل به الموظف

cur.execute(
    "UPDATE employees SET username = ?, password_hash = ? WHERE id = ?",
    (username, pwd_hash, employee_id)
)

conn.commit()
conn.close()