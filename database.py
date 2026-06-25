import sqlite3
import os
from datetime import date

from image_utils import save_dress_image, delete_dress_image


class Database:
    def __init__(self, db_path="dress_rental.db"):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.initialize()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def initialize(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS dresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                size TEXT,
                color TEXT,
                category TEXT,
                rental_price REAL NOT NULL,
                deposit REAL DEFAULT 0,
                status TEXT DEFAULT 'available',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                phone2 TEXT,
                address TEXT,
                id_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dress_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                rental_date DATE NOT NULL,
                expected_return_date DATE NOT NULL,
                actual_return_date DATE,
                rental_price REAL NOT NULL,
                deposit REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dress_id) REFERENCES dresses(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rental_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_method TEXT DEFAULT 'cash',
                notes TEXT,
                FOREIGN KEY (rental_id) REFERENCES rentals(id)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS registrars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                notes TEXT,
                is_archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dress_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                registered_by_id INTEGER,
                reservation_date DATE NOT NULL,
                event_date DATE NOT NULL,
                expected_return_date DATE,
                rental_price REAL NOT NULL,
                deposit REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dress_id) REFERENCES dresses(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (registered_by_id) REFERENCES registrars(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS notification_dismissals (
                type TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                PRIMARY KEY (type, record_id)
            );
        """)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        dress_cols = {row[1] for row in self.conn.execute("PRAGMA table_info(dresses)").fetchall()}
        if "image_path" not in dress_cols:
            self.conn.execute("ALTER TABLE dresses ADD COLUMN image_path TEXT")
            self.conn.commit()
        if "is_archived" not in dress_cols:
            self.conn.execute("ALTER TABLE dresses ADD COLUMN is_archived INTEGER DEFAULT 0")
            self.conn.commit()

        customer_cols = {row[1] for row in self.conn.execute("PRAGMA table_info(customers)").fetchall()}
        if "is_archived" not in customer_cols:
            self.conn.execute("ALTER TABLE customers ADD COLUMN is_archived INTEGER DEFAULT 0")
            self.conn.commit()
            
        # Free up codes for already archived dresses
        self.conn.execute("UPDATE dresses SET code = code || '-deleted-' || id WHERE is_archived = 1 AND code NOT LIKE '%-deleted-%'")
        self.conn.commit()
        
        # TEMPORARY RESTORE FIX: If user accidentally cancelled or dismissed today's notifications while testing
        from datetime import date
        today_iso = date.today().isoformat()
        self.conn.execute("UPDATE bookings SET status='active' WHERE status='cancelled' AND event_date=?", (today_iso,))
        self.conn.execute("DELETE FROM notification_dismissals")
        self.conn.commit()

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS registrars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                notes TEXT,
                is_archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

        booking_cols = {row[1] for row in self.conn.execute("PRAGMA table_info(bookings)").fetchall()}
        if "registered_by_id" not in booking_cols:
            self.conn.execute("ALTER TABLE bookings ADD COLUMN registered_by_id INTEGER REFERENCES registrars(id)")
            self.conn.commit()

        rental_cols = {row[1] for row in self.conn.execute("PRAGMA table_info(rentals)").fetchall()}
        if "registered_by_id" not in rental_cols:
            self.conn.execute("ALTER TABLE rentals ADD COLUMN registered_by_id INTEGER REFERENCES registrars(id)")
            self.conn.commit()

        # Ensure settings table exists and default password is set
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        pwd = self.conn.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()
        if not pwd:
            self.conn.execute("INSERT INTO settings (key, value) VALUES ('admin_password', 'admin')")
            
        owner_phone = self.conn.execute("SELECT value FROM settings WHERE key='owner_phone'").fetchone()
        if not owner_phone:
            self.conn.execute("INSERT INTO settings (key, value) VALUES ('owner_phone', '01096078609')")
        else:
            self.conn.execute("UPDATE settings SET value='01096078609' WHERE key='owner_phone'")
            
        self.conn.commit()

        self._normalize_existing_status_values()

    def verify_admin_password(self, password):
        row = self.conn.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()
        if row and row['value'] == password:
            return True
        return False

    def _normalize_existing_status_values(self):
        # Keep persisted status values canonical so filters/stats/constraints stay consistent.
        self.conn.execute(
            "UPDATE bookings SET status='active' WHERE LOWER(TRIM(status)) IN ('نشط')"
        )
        self.conn.execute(
            "UPDATE bookings SET status='cancelled' WHERE LOWER(TRIM(status)) IN ('ملغي', 'canceled')"
        )
        self.conn.execute(
            "UPDATE bookings SET status='converted' WHERE LOWER(TRIM(status)) IN ('تم التحويل')"
        )
        self.conn.execute(
            "UPDATE rentals SET status='active' WHERE LOWER(TRIM(status)) IN ('نشط')"
        )
        self.conn.execute(
            "UPDATE rentals SET status='overdue' WHERE LOWER(TRIM(status)) IN ('متأخر')"
        )
        self.conn.execute(
            "UPDATE rentals SET status='returned' WHERE LOWER(TRIM(status)) IN ('مُرجع', 'مرجع')"
        )
        self.conn.execute(
            "UPDATE rentals SET status='cancelled' WHERE LOWER(TRIM(status)) IN ('ملغي', 'canceled')"
        )
        self.conn.execute(
            "UPDATE dresses SET status='available' WHERE LOWER(TRIM(status)) IN ('متاح')"
        )
        self.conn.execute(
            "UPDATE dresses SET status='rented' WHERE LOWER(TRIM(status)) IN ('مؤجر')"
        )
        self.conn.execute(
            "UPDATE dresses SET status='maintenance' WHERE LOWER(TRIM(status)) IN ('صيانة')"
        )
        self.conn.commit()

    # ───────────── DRESSES ─────────────
    def _count_dress_links(self, did):
        rentals = self.conn.execute(
            "SELECT status, COUNT(*) as n FROM rentals WHERE dress_id=? GROUP BY status", (did,)
        ).fetchall()
        bookings = self.conn.execute(
            "SELECT status, COUNT(*) as n FROM bookings WHERE dress_id=? GROUP BY status", (did,)
        ).fetchall()
        rent_map = {r["status"]: r["n"] for r in rentals}
        book_map = {r["status"]: r["n"] for r in bookings}
        return rent_map, book_map

    def _count_customer_links(self, cid):
        rentals = self.conn.execute(
            "SELECT status, COUNT(*) as n FROM rentals WHERE customer_id=? GROUP BY status", (cid,)
        ).fetchall()
        bookings = self.conn.execute(
            "SELECT status, COUNT(*) as n FROM bookings WHERE customer_id=? GROUP BY status", (cid,)
        ).fetchall()
        rent_map = {r["status"]: r["n"] for r in rentals}
        book_map = {r["status"]: r["n"] for r in bookings}
        return rent_map, book_map

    @staticmethod
    def _format_link_message(rent_map, book_map):
        parts = []
        for st, label in [
            ("active", "تأجير نشط"),
            ("overdue", "تأجير متأخر"),
            ("returned", "تأجير مُرجع"),
            ("cancelled", "تأجير ملغي"),
        ]:
            if rent_map.get(st, 0):
                parts.append(f"{rent_map[st]} {label}")
        for st, label in [
            ("active", "حجز نشط"),
            ("converted", "حجز تم تحويله"),
            ("cancelled", "حجز ملغي"),
        ]:
            if book_map.get(st, 0):
                parts.append(f"{book_map[st]} {label}")
        if not parts:
            return None
        return "مرتبط بالسجلات التالية: " + "، ".join(parts)

    def add_dress(self, code, name, size, color, category, rental_price, deposit, description=""):
        try:
            c = self.conn.cursor()
            c.execute("""INSERT INTO dresses (code,name,size,color,category,rental_price,deposit,description)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (code, name, size, color, category, rental_price, deposit, description))
            self.conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_dress(self, did, code, name, size, color, category, rental_price, deposit, description=""):
        self.conn.execute("""UPDATE dresses SET code=?,name=?,size=?,color=?,category=?,
                             rental_price=?,deposit=?,description=? WHERE id=?""",
                          (code, name, size, color, category, rental_price, deposit, description, did))
        self.conn.commit()

    def delete_dress(self, did, force=False):
        dress = self.get_dress(did)
        rent_map, book_map = self._count_dress_links(did)
        linked_msg = self._format_link_message(rent_map, book_map)
        if linked_msg and not force:
            return False, f"لا يمكن حذف الفستان. {linked_msg}"
        try:
            if force:
                # Cascade delete
                self.conn.execute("DELETE FROM payments WHERE rental_id IN (SELECT id FROM rentals WHERE dress_id=?)", (did,))
                self.conn.execute("DELETE FROM rentals WHERE dress_id=?", (did,))
                self.conn.execute("DELETE FROM bookings WHERE dress_id=?", (did,))
                
            self.conn.execute("DELETE FROM dresses WHERE id=?", (did,))
            self.conn.execute("UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(id), 0) FROM dresses) WHERE name = 'dresses'")
            self.conn.commit()
        except sqlite3.IntegrityError:
            return False, "لا يمكن حذف الفستان لأنه مرتبط بعمليات مسجلة. يرجى تفعيل خيار الحذف الإجباري."
        if dress and dress["image_path"]:
            from image_utils import delete_dress_image
            delete_dress_image(dress["image_path"])
        return True, None

    def set_dress_image(self, did, source_path):
        dress = self.get_dress(did)
        if not dress:
            return None
        if dress["image_path"]:
            delete_dress_image(dress["image_path"])
        rel = save_dress_image(source_path, did, dress["code"])
        self.conn.execute("UPDATE dresses SET image_path=? WHERE id=?", (rel, did))
        self.conn.commit()
        return rel

    def clear_dress_image(self, did):
        dress = self.get_dress(did)
        if dress and dress["image_path"]:
            delete_dress_image(dress["image_path"])
            self.conn.execute("UPDATE dresses SET image_path=NULL WHERE id=?", (did,))
            self.conn.commit()

    def get_all_dresses(self, status=None, search=None, limit=None, offset=0):
        q = """
            SELECT d.*, 
                   (SELECT COUNT(*) FROM rentals r WHERE r.dress_id = d.id) as rental_count
            FROM dresses d
            WHERE COALESCE(d.is_archived,0)=0
        """
        p = []
        if status:
            q += " AND d.status=?"; p.append(status)
        if search:
            q += " AND (d.name LIKE ? OR d.code LIKE ? OR d.color LIKE ?)"
            p += [f"%{search}%"] * 3
        q += " ORDER BY d.id ASC"
        if limit is not None:
            q += " LIMIT ? OFFSET ?"
            p.extend([limit, offset])
        return self.conn.execute(q, p).fetchall()

    def get_dresses_count(self, status=None, search=None):
        q = "SELECT COUNT(*) as n FROM dresses d WHERE COALESCE(d.is_archived,0)=0"
        p = []
        if status:
            q += " AND d.status=?"; p.append(status)
        if search:
            q += " AND (d.name LIKE ? OR d.code LIKE ? OR d.color LIKE ?)"
            p += [f"%{search}%"] * 3
        return self.conn.execute(q, p).fetchone()['n']

    def get_dress(self, did):
        return self.conn.execute("SELECT * FROM dresses WHERE id=?", (did,)).fetchone()

    def update_dress_status(self, did, status):
        self.conn.execute("UPDATE dresses SET status=? WHERE id=?", (status, did))
        self.conn.commit()

    def get_available_dresses(self):
        return self.conn.execute(
            "SELECT * FROM dresses WHERE status='available' AND COALESCE(is_archived,0)=0 ORDER BY name"
        ).fetchall()

    # ───────────── CUSTOMERS ─────────────
    def add_customer(self, name, phone, phone2, address, id_number, notes=""):
        c = self.conn.cursor()
        c.execute("""INSERT INTO customers (name,phone,phone2,address,id_number,notes)
                     VALUES (?,?,?,?,?,?)""", (name, phone, phone2, address, id_number, notes))
        self.conn.commit()
        return c.lastrowid

    def update_customer(self, cid, name, phone, phone2, address, id_number, notes=""):
        self.conn.execute("""UPDATE customers SET name=?,phone=?,phone2=?,address=?,id_number=?,notes=?
                             WHERE id=?""", (name, phone, phone2, address, id_number, notes, cid))
        self.conn.commit()

    def delete_customer(self, cid):
        try:
            # بدلاً من المسح نهائياً ومسح السجلات المرتبطة به، 
            # سنقوم بإخفائه من واجهة العملاء (Soft Delete)
            self.conn.execute("UPDATE customers SET is_archived = 1 WHERE id=?", (cid,))
            self.conn.commit()
            return True, None
        except sqlite3.Error as e:
            return False, f"حدث خطأ أثناء أرشفة العميل: {str(e)}"

    def archive_dress(self, did):
        dress = self.get_dress(did)
        if not dress:
            return False, "الفستان غير موجود."
        if dress["status"] == "rented":
            return False, "لا يمكن أرشفة فستان مؤجر حالياً."
        active_bookings = self.conn.execute(
            "SELECT COUNT(*) as n FROM bookings WHERE dress_id=? AND status='active'", (did,)
        ).fetchone()["n"]
        if active_bookings:
            return False, "لا يمكن أرشفة فستان عليه حجز نشط."
        new_code = f"{dress['code']}-deleted-{did}"
        self.conn.execute("UPDATE dresses SET is_archived=1, code=? WHERE id=?", (new_code, did))
        self.conn.commit()
        return True, None

    def archive_customer(self, cid):
        customer = self.get_customer(cid)
        if not customer:
            return False, "العميل غير موجود."
        active_rentals = self.conn.execute(
            "SELECT COUNT(*) as n FROM rentals WHERE customer_id=? AND status IN ('active','overdue')", (cid,)
        ).fetchone()["n"]
        if active_rentals:
            return False, "لا يمكن أرشفة عميل لديه تأجير نشط."
        active_bookings = self.conn.execute(
            "SELECT COUNT(*) as n FROM bookings WHERE customer_id=? AND status='active'", (cid,)
        ).fetchone()["n"]
        if active_bookings:
            return False, "لا يمكن أرشفة عميل لديه حجز نشط."
        self.conn.execute("UPDATE customers SET is_archived=1 WHERE id=?", (cid,))
        self.conn.commit()
        return True, None

    def get_all_customers(self, search=None, limit=None, offset=0):
        q = "SELECT * FROM customers WHERE COALESCE(is_archived,0)=0"
        p = []
        if search:
            q += " AND (name LIKE ? OR phone LIKE ? OR id_number LIKE ?)"
            p += [f"%{search}%"] * 3
        q += " ORDER BY name"
        if limit is not None:
            q += " LIMIT ? OFFSET ?"
            p.extend([limit, offset])
        return self.conn.execute(q, p).fetchall()

    def get_customers_count(self, search=None):
        q = "SELECT COUNT(*) as n FROM customers WHERE COALESCE(is_archived,0)=0"
        p = []
        if search:
            q += " AND (name LIKE ? OR phone LIKE ? OR id_number LIKE ?)"
            p += [f"%{search}%"] * 3
        return self.conn.execute(q, p).fetchone()['n']

    def get_customer(self, cid):
        return self.conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()

    # ───────────── RENTALS ─────────────
    def add_rental(self, dress_id, customer_id, rental_date, expected_return_date,
                   rental_price, deposit, discount, total_amount, paid_amount, notes="", registered_by_id=None):
        c = self.conn.cursor()
        # Keep ledger consistent: rental starts with zero paid, then payment rows adjust it.
        remaining = total_amount
        c.execute("""INSERT INTO rentals
                     (dress_id,customer_id,registered_by_id,rental_date,expected_return_date,rental_price,
                      deposit,discount,total_amount,paid_amount,remaining_amount,notes)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (dress_id, customer_id, registered_by_id, rental_date, expected_return_date,
                   rental_price, deposit, discount, total_amount, 0, remaining, notes))
        self.conn.commit()
        rid = c.lastrowid
        self.update_dress_status(dress_id, 'rented')
        if paid_amount > 0:
            self.add_payment(rid, paid_amount, 'cash', 'دفعة مقدمة')
        return rid

    def update_rental(self, rid, dress_id, customer_id, rental_date, expected_return_date,
                      rental_price, deposit, discount, total_amount, paid_amount, notes="", registered_by_id=None):
        old = self.get_rental(rid)
        if not old:
            return False, "التأجير غير موجود"
        
        # إذا تم تغيير الفستان، نقوم بتحديث الحالات
        if old['dress_id'] != dress_id:
            self.update_dress_status(old['dress_id'], 'available')
            self.update_dress_status(dress_id, 'rented')

        # keep payments ledger in-sync: any increase in paid amount is recorded as payment entry.
        # decreasing paid is blocked because historical payments should remain immutable.
        old_paid = old['paid_amount'] or 0
        delta_paid = (paid_amount or 0) - old_paid
        if delta_paid < 0:
            return False, "لا يمكن تقليل المدفوع من تعديل التأجير. استخدم سجل الدفعات فقط."
        if delta_paid > 0:
            self.add_payment(rid, delta_paid, 'cash', 'تعديل على المدفوع أثناء تعديل التأجير')

        current = self.get_rental(rid)
        synced_paid = current['paid_amount'] if current else old_paid
        remaining = max(0, total_amount - synced_paid)
        self.conn.execute("""UPDATE rentals SET dress_id=?, customer_id=?, registered_by_id=?, rental_date=?, 
                             expected_return_date=?, rental_price=?, deposit=?, discount=?, 
                             total_amount=?, paid_amount=?, remaining_amount=?, notes=?
                             WHERE id=?""",
                          (dress_id, customer_id, registered_by_id, rental_date, expected_return_date,
                           rental_price, deposit, discount, total_amount, synced_paid, remaining, notes, rid))
        self.conn.commit()
        return True, None

    def return_dress(self, rental_id, actual_return_date, additional_payment=0, method='cash'):
        rental = self.get_rental(rental_id)
        if rental:
            self.conn.execute("""UPDATE rentals SET actual_return_date=?,status='returned'
                                 WHERE id=?""",
                              (actual_return_date, rental_id))
            self.conn.commit()
            
            # Check if there are other active rentals for this dress
            active_count = self.conn.execute("SELECT COUNT(*) as n FROM rentals WHERE dress_id=? AND status='active'", (rental['dress_id'],)).fetchone()['n']
            if active_count == 0:
                self.update_dress_status(rental['dress_id'], 'available')
                
            if additional_payment > 0:
                self.add_payment(rental_id, additional_payment, method, 'دفعة عند الإرجاع')
            # Ensure remaining is normalized after return.
            self.conn.execute("""UPDATE rentals
                                 SET remaining_amount = MAX(0, total_amount - paid_amount)
                                 WHERE id=?""", (rental_id,))
            self.conn.commit()

    def cancel_rental(self, rental_id):
        rental = self.get_rental(rental_id)
        if rental:
            if rental['paid_amount'] > 0:
                self.add_refund(rental_id, rental['paid_amount'], 'cash', 'إلغاء حجز - إسترداد مالي')
            
            self.conn.execute("UPDATE rentals SET status='cancelled' WHERE id=?", (rental_id,))
            self.conn.commit()
            
            # Check if there are other active rentals for this dress
            active_count = self.conn.execute("SELECT COUNT(*) as n FROM rentals WHERE dress_id=? AND status='active'", (rental['dress_id'],)).fetchone()['n']
            if active_count == 0:
                self.update_dress_status(rental['dress_id'], 'available')

    def delete_rental(self, rental_id):
        rental = self.get_rental(rental_id)
        if not rental:
            return False, "التأجير غير موجود."
        if rental['status'] in ('active', 'overdue'):
            self.update_dress_status(rental['dress_id'], 'available')
        self.conn.execute("DELETE FROM payments WHERE rental_id=?", (rental_id,))
        self.conn.execute("UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(id), 0) FROM payments) WHERE name = 'payments'")
        self.conn.execute("DELETE FROM rentals WHERE id=?", (rental_id,))
        self.conn.execute("UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(id), 0) FROM rentals) WHERE name = 'rentals'")
        self.conn.commit()
        return True, None

    def get_all_rentals(self, status=None, search=None, limit=None, offset=0):
        q = """SELECT r.*,d.name as dress_name,d.code as dress_code,d.image_path as dress_image_path,
                      c.name as customer_name,c.phone as customer_phone,
                      reg.name as registrar_name
               FROM rentals r
               JOIN dresses d ON r.dress_id=d.id
               JOIN customers c ON r.customer_id=c.id
               LEFT JOIN registrars reg ON r.registered_by_id=reg.id
               WHERE 1=1"""
        p = []
        if status:
            q += " AND r.status=?"; p.append(status)
        if search:
            q += " AND (c.name LIKE ? OR d.name LIKE ? OR d.code LIKE ?)"
            p += [f"%{search}%"] * 3
        q += " ORDER BY r.created_at DESC"
        if limit is not None:
            q += " LIMIT ? OFFSET ?"
            p.extend([limit, offset])
        return self.conn.execute(q, p).fetchall()

    def get_rentals_count(self, status=None, search=None):
        q = """SELECT COUNT(*) as n
               FROM rentals r
               JOIN dresses d ON r.dress_id=d.id
               JOIN customers c ON r.customer_id=c.id
               WHERE 1=1"""
        p = []
        if status:
            q += " AND r.status=?"; p.append(status)
        if search:
            q += " AND (c.name LIKE ? OR d.name LIKE ? OR d.code LIKE ?)"
            p += [f"%{search}%"] * 3
        return self.conn.execute(q, p).fetchone()['n']

    def get_rental(self, rid):
        return self.conn.execute("""
            SELECT r.*,d.name as dress_name,d.code as dress_code,d.size,d.color,d.image_path,
                   c.name as customer_name,c.phone as customer_phone,c.address,
                   reg.name as registrar_name
            FROM rentals r
            JOIN dresses d ON r.dress_id=d.id
            JOIN customers c ON r.customer_id=c.id
            LEFT JOIN registrars reg ON r.registered_by_id=reg.id
            WHERE r.id=?""", (rid,)).fetchone()

    def get_overdue_rentals(self):
        today = date.today().isoformat()
        return self.conn.execute("""
            SELECT r.*,d.name as dress_name,d.code as dress_code,
                   c.name as customer_name,c.phone as customer_phone
            FROM rentals r JOIN dresses d ON r.dress_id=d.id JOIN customers c ON r.customer_id=c.id
            WHERE r.status IN ('active','overdue') AND r.expected_return_date < ?
            ORDER BY r.expected_return_date""", (today,)).fetchall()

    def get_due_soon_rentals(self, days=3):
        today = date.today().isoformat()
        return self.conn.execute("""
            SELECT r.*,d.name as dress_name,c.name as customer_name,c.phone as customer_phone
            FROM rentals r JOIN dresses d ON r.dress_id=d.id JOIN customers c ON r.customer_id=c.id
            WHERE r.status='active' AND r.expected_return_date >= date('now')
              AND r.expected_return_date <= date('now',?) 
            ORDER BY r.expected_return_date""", (f"+{days} days",)).fetchall()

    def update_overdue_status(self):
        today = date.today().isoformat()
        self.conn.execute("""UPDATE rentals SET status='overdue'
                             WHERE status='active' AND expected_return_date < ?""", (today,))
        self.conn.commit()

    # ───────────── PAYMENTS ─────────────
    def add_payment(self, rental_id, amount, method='cash', notes=""):
        rental = self.get_rental(rental_id)
        if not rental:
            return None
        if amount <= 0:
            return None
        remaining = rental['remaining_amount'] or 0
        if amount > remaining:
            return None
        c = self.conn.cursor()
        c.execute("INSERT INTO payments (rental_id,amount,payment_method,notes) VALUES (?,?,?,?)",
                  (rental_id, amount, method, notes))
        self.conn.execute("""UPDATE rentals SET paid_amount=paid_amount+?,remaining_amount=remaining_amount-?
                             WHERE id=?""", (amount, amount, rental_id))
        self.conn.commit()
        return c.lastrowid

    def add_refund(self, rental_id, amount, method='cash', notes=""):
        if amount <= 0: return None
        c = self.conn.cursor()
        # insert negative payment
        c.execute("INSERT INTO payments (rental_id,amount,payment_method,notes) VALUES (?,?,?,?)",
                  (rental_id, -amount, method, notes))
        self.conn.execute("""UPDATE rentals SET paid_amount=paid_amount-?,remaining_amount=remaining_amount+?
                             WHERE id=?""", (amount, amount, rental_id))
        self.conn.commit()
        return c.lastrowid

    def get_rental_payments(self, rental_id):
        return self.conn.execute("SELECT * FROM payments WHERE rental_id=? ORDER BY payment_date DESC",
                                 (rental_id,)).fetchall()

    # ───────────── EXPENSES ─────────────
    def add_expense(self, description, amount, category, exp_date, notes=""):
        c = self.conn.cursor()
        c.execute("INSERT INTO expenses (description,amount,category,date,notes) VALUES (?,?,?,?,?)",
                  (description, amount, category, exp_date, notes))
        self.conn.commit()
        return c.lastrowid

    def get_all_expenses(self, month=None):
        q = "SELECT * FROM expenses WHERE 1=1"
        p = []
        if month:
            q += " AND strftime('%Y-%m', date)=?"; p.append(month)
        q += " ORDER BY date DESC"
        return self.conn.execute(q, p).fetchall()

    # ───────────── STATISTICS ─────────────
    def get_dashboard_stats(self):
        today = date.today().isoformat()
        stats = {}

        rows = self.conn.execute(
            "SELECT status, COUNT(*) as n FROM dresses WHERE COALESCE(is_archived,0)=0 GROUP BY status"
        ).fetchall()
        stats['dresses'] = {r['status']: r['n'] for r in rows}
        stats['archived_dresses'] = self.conn.execute(
            "SELECT COUNT(*) as n FROM dresses WHERE COALESCE(is_archived,0)=1"
        ).fetchone()['n']

        stats['total_customers'] = self.conn.execute(
            "SELECT COUNT(*) as n FROM customers WHERE COALESCE(is_archived,0)=0"
        ).fetchone()['n']
        stats['archived_customers'] = self.conn.execute(
            "SELECT COUNT(*) as n FROM customers WHERE COALESCE(is_archived,0)=1"
        ).fetchone()['n']
        stats['active_rentals'] = self.conn.execute(
            "SELECT COUNT(*) as n FROM rentals WHERE status IN ('active','overdue')").fetchone()['n']
        stats['overdue_rentals'] = self.conn.execute(
            "SELECT COUNT(*) as n FROM rentals WHERE status='overdue' OR (status='active' AND expected_return_date<?)",
            (today,)).fetchone()['n']
        stats['monthly_revenue'] = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) as n FROM payments WHERE strftime('%Y-%m',payment_date)=strftime('%Y-%m','now')"
        ).fetchone()['n']
        stats['today_revenue'] = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) as n FROM payments WHERE date(payment_date)=date('now')"
        ).fetchone()['n']
        stats['pending_payments'] = self.conn.execute(
            "SELECT COALESCE(SUM(remaining_amount),0) as n FROM rentals WHERE status IN ('active','overdue')"
        ).fetchone()['n']
        stats['active_bookings'] = self.conn.execute(
            "SELECT COUNT(*) as n FROM bookings WHERE status='active'"
        ).fetchone()['n']
        return stats

    def get_monthly_revenue(self, months=6):
        return self.conn.execute("""
            SELECT strftime('%Y-%m',payment_date) as month, SUM(amount) as total
            FROM payments GROUP BY month ORDER BY month DESC LIMIT ?""", (months,)).fetchall()

    def get_popular_dresses(self, limit=10):
        return self.conn.execute("""
            SELECT d.name, d.code, COUNT(r.id) as cnt, COALESCE(SUM(r.rental_price),0) as revenue
            FROM dresses d LEFT JOIN rentals r ON d.id=r.dress_id
            GROUP BY d.id ORDER BY cnt DESC LIMIT ?""", (limit,)).fetchall()

    # ───────────── REGISTRARS (المسجّلون) ─────────────
    def add_registrar(self, name, phone="", notes=""):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO registrars (name, phone, notes) VALUES (?,?,?)",
            (name, phone, notes),
        )
        self.conn.commit()
        return c.lastrowid

    def update_registrar(self, rid, name, phone="", notes=""):
        self.conn.execute(
            "UPDATE registrars SET name=?, phone=?, notes=? WHERE id=?",
            (name, phone, notes, rid),
        )
        self.conn.commit()

    def get_all_registrars(self, search=None, active_only=True):
        q = "SELECT * FROM registrars WHERE 1=1"
        p = []
        if active_only:
            q += " AND COALESCE(is_archived, 0)=0"
        if search:
            q += " AND (name LIKE ? OR phone LIKE ?)"
            p += [f"%{search}%", f"%{search}%"]
        q += " ORDER BY name"
        return self.conn.execute(q, p).fetchall()

    def get_registrar(self, rid):
        return self.conn.execute("SELECT * FROM registrars WHERE id=?", (rid,)).fetchone()

    def get_registrar_stats(self):
        return self.conn.execute("""
            SELECT r.id, r.name, r.phone, r.notes,
                   COUNT(b.id) as bookings_count,
                   SUM(CASE WHEN b.status='active' THEN 1 ELSE 0 END) as active_bookings
            FROM registrars r
            LEFT JOIN bookings b ON b.registered_by_id=r.id
            WHERE COALESCE(r.is_archived, 0)=0
            GROUP BY r.id
            ORDER BY r.name
        """).fetchall()

    def archive_registrar(self, rid):
        active = self.conn.execute(
            "SELECT COUNT(*) as n FROM bookings WHERE registered_by_id=? AND status='active'",
            (rid,),
        ).fetchone()["n"]
        if active:
            return False, "لا يمكن أرشفة موظف لديه حجوزات نشطة مسجّلة باسمه."
        self.conn.execute("UPDATE registrars SET is_archived=1 WHERE id=?", (rid,))
        self.conn.commit()
        return True, None

    # ───────────── BOOKINGS ─────────────
    def add_booking(self, dress_id, customer_id, reservation_date, event_date,
                    rental_price, deposit=0, expected_return_date=None, notes="",
                    registered_by_id=None):
        booking_end = expected_return_date or event_date
        conflict = self.conn.execute(
            """SELECT COUNT(*) as n FROM bookings
               WHERE dress_id=? AND status='active'
                 AND NOT (
                     COALESCE(expected_return_date, event_date) < ?
                     OR event_date > ?
                 )""",
            (dress_id, event_date, booking_end),
        ).fetchone()["n"]
        if conflict:
            return None
        c = self.conn.cursor()
        c.execute("""INSERT INTO bookings
                     (dress_id,customer_id,registered_by_id,reservation_date,event_date,
                      expected_return_date,rental_price,deposit,notes)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (dress_id, customer_id, registered_by_id, reservation_date, event_date,
                   expected_return_date, rental_price, deposit, notes))
        self.conn.commit()
        return c.lastrowid

    def get_all_bookings(self, status=None, search=None, limit=None, offset=0):
        q = """SELECT b.*, d.name as dress_name, d.code as dress_code, d.size as dress_size, d.image_path,
                      c.name as customer_name, c.phone as customer_phone,
                      reg.name as registrar_name
               FROM bookings b
               JOIN dresses d ON b.dress_id=d.id
               JOIN customers c ON b.customer_id=c.id
               LEFT JOIN registrars reg ON b.registered_by_id=reg.id
               WHERE 1=1"""
        p = []
        if status:
            q += " AND b.status=?"
            p.append(status)
        if search:
            q += " AND (c.name LIKE ? OR d.name LIKE ? OR d.code LIKE ? OR reg.name LIKE ?)"
            p += [f"%{search}%"] * 4
        q += " ORDER BY b.created_at DESC"
        if limit is not None:
            q += " LIMIT ? OFFSET ?"
            p.extend([limit, offset])
        return self.conn.execute(q, p).fetchall()

    def get_bookings_count(self, status=None, search=None):
        q = """SELECT COUNT(*) as n
               FROM bookings b
               JOIN dresses d ON b.dress_id=d.id
               JOIN customers c ON b.customer_id=c.id
               LEFT JOIN registrars reg ON b.registered_by_id=reg.id
               WHERE 1=1"""
        p = []
        if status:
            q += " AND b.status=?"
            p.append(status)
        if search:
            q += " AND (c.name LIKE ? OR d.name LIKE ? OR d.code LIKE ? OR reg.name LIKE ?)"
            p += [f"%{search}%"] * 4
        return self.conn.execute(q, p).fetchone()['n']

    def get_upcoming_bookings(self, days=7):
        from datetime import date, timedelta
        today = date.today()
        target_date = today + timedelta(days=days)
        return self.conn.execute(
            """SELECT b.*, d.name as dress_name, d.code as dress_code,
                      c.name as customer_name, c.phone as customer_phone,
                      reg.name as registrar_name
               FROM bookings b
               JOIN dresses d ON b.dress_id=d.id
               JOIN customers c ON b.customer_id=c.id
               LEFT JOIN registrars reg ON b.registered_by_id=reg.id
               WHERE b.status='active'
                 AND b.event_date >= ?
                 AND b.event_date <= ?
               ORDER BY b.event_date ASC""",
            (today.isoformat(), target_date.isoformat()),
        ).fetchall()

    def get_notifications(self):
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # حجوزات اليوم وغداً
        bookings = self.conn.execute(
            """SELECT 'booking' as type, b.event_date, b.id, d.name as dress_name, d.code as dress_code,
                      c.name as customer_name, c.phone as customer_phone, reg.name as registrar_name
               FROM bookings b
               JOIN dresses d ON b.dress_id=d.id
               JOIN customers c ON b.customer_id=c.id
               LEFT JOIN registrars reg ON b.registered_by_id=reg.id
               WHERE b.status='active'
                 AND (b.event_date = ? OR b.event_date = ?)
                 AND NOT EXISTS (SELECT 1 FROM notification_dismissals nd WHERE nd.type='booking' AND nd.record_id=b.id)
            """, (today.isoformat(), tomorrow.isoformat())
        ).fetchall()
        
        # تسليم تأجيرات (تأجيرات تبدأ اليوم أو غداً)
        deliveries = self.conn.execute(
            """SELECT 'delivery' as type, r.rental_date as event_date, r.id, d.name as dress_name, d.code as dress_code,
                      c.name as customer_name, c.phone as customer_phone, reg.name as registrar_name
               FROM rentals r
               JOIN dresses d ON r.dress_id=d.id
               JOIN customers c ON r.customer_id=c.id
               LEFT JOIN registrars reg ON r.registered_by_id=reg.id
               WHERE r.status='active'
                 AND (r.rental_date = ? OR r.rental_date = ?)
                 AND NOT EXISTS (SELECT 1 FROM notification_dismissals nd WHERE nd.type='delivery' AND nd.record_id=r.id)
            """, (today.isoformat(), tomorrow.isoformat())
        ).fetchall()
        
        # إرجاعات اليوم أو المتأخرة
        rentals = self.conn.execute(
            """SELECT 'rental' as type, r.expected_return_date as event_date, r.id, d.name as dress_name, d.code as dress_code,
                      c.name as customer_name, c.phone as customer_phone, reg.name as registrar_name
               FROM rentals r
               JOIN dresses d ON r.dress_id=d.id
               JOIN customers c ON r.customer_id=c.id
               LEFT JOIN registrars reg ON r.registered_by_id=reg.id
               WHERE r.status='active'
                 AND r.expected_return_date <= ?
                 AND NOT EXISTS (SELECT 1 FROM notification_dismissals nd WHERE nd.type='rental' AND nd.record_id=r.id)
            """, (today.isoformat(),)
        ).fetchall()
        
        combined = [dict(x) for x in bookings] + [dict(x) for x in deliveries] + [dict(x) for x in rentals]
        combined.sort(key=lambda x: (x['event_date'], x['id']), reverse=True)
        return combined

    def dismiss_notification(self, n_type, record_id):
        self.conn.execute("INSERT OR IGNORE INTO notification_dismissals (type, record_id) VALUES (?, ?)", (n_type, record_id))
        self.conn.commit()

    def update_booking(self, bid, dress_id, customer_id, reservation_date, event_date,
                       rental_price, deposit=0, expected_return_date=None, notes="",
                       registered_by_id=None):
        booking_end = expected_return_date or event_date
        conflict = self.conn.execute(
            """SELECT COUNT(*) as n FROM bookings
               WHERE dress_id=? AND status='active' AND id != ?
                 AND NOT (
                     COALESCE(expected_return_date, event_date) < ?
                     OR event_date > ?
                 )""",
            (dress_id, bid, event_date, booking_end),
        ).fetchone()["n"]
        if conflict:
            return False

        self.conn.execute("""UPDATE bookings 
                             SET dress_id=?, customer_id=?, registered_by_id=?, reservation_date=?, 
                                 event_date=?, expected_return_date=?, rental_price=?, deposit=?, notes=?
                             WHERE id=?""",
                          (dress_id, customer_id, registered_by_id, reservation_date, event_date,
                           expected_return_date, rental_price, deposit, notes, bid))
        self.conn.commit()
        return True

    def get_booking(self, bid):
        return self.conn.execute("""
            SELECT b.*, d.name as dress_name, d.code as dress_code, d.size as dress_size, d.image_path,
                   c.name as customer_name, c.phone as customer_phone,
                   reg.name as registrar_name
            FROM bookings b
            JOIN dresses d ON b.dress_id=d.id
            JOIN customers c ON b.customer_id=c.id
            LEFT JOIN registrars reg ON b.registered_by_id=reg.id
            WHERE b.id=?""", (bid,)).fetchone()

    @staticmethod
    def _normalize_booking_status(status):
        if status is None:
            return ""
        s = str(status).strip().lower()
        aliases = {
            "active": "active",
            "نشط": "active",
            "cancelled": "cancelled",
            "canceled": "cancelled",
            "ملغي": "cancelled",
            "converted": "converted",
            "تم التحويل": "converted",
        }
        return aliases.get(s, s)

    def cancel_booking(self, bid):
        row = self.conn.execute("SELECT status FROM bookings WHERE id=?", (bid,)).fetchone()
        if not row:
            return False, "الحجز غير موجود."
        if self._normalize_booking_status(row["status"]) != "active":
            return False, "لا يمكن إلغاء هذا الحجز لأنه غير نشط."
        self.conn.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
        self.conn.commit()
        return True, None

    def delete_booking(self, bid):
        row = self.conn.execute("SELECT status FROM bookings WHERE id=?", (bid,)).fetchone()
        if not row:
            return False, "الحجز غير موجود."
        self.conn.execute("DELETE FROM bookings WHERE id=?", (bid,))
        self.conn.execute("UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(id), 0) FROM bookings) WHERE name = 'bookings'")
        self.conn.commit()
        return True, None

    def convert_booking_to_rental(self, bid, rental_date=None, paid_amount=0, discount=0, notes=""):
        booking = self.get_booking(bid)
        if not booking or self._normalize_booking_status(booking["status"]) != "active":
            return None
        dress = self.get_dress(booking["dress_id"])
        if not dress or dress["status"] != "available":
            return None

        rental_date = rental_date or date.today().isoformat()
        expected_return_date = booking["expected_return_date"] or booking["event_date"]
        total_amount = max(0, booking["rental_price"] - discount)
        rental_notes = notes or booking["notes"] or "تحويل من حجز"

        rid = self.add_rental(
            dress_id=booking["dress_id"],
            customer_id=booking["customer_id"],
            rental_date=rental_date,
            expected_return_date=expected_return_date,
            rental_price=booking["rental_price"],
            deposit=booking["deposit"] or 0,
            discount=discount,
            total_amount=total_amount,
            paid_amount=paid_amount,
            notes=rental_notes,
        )
        self.conn.execute("DELETE FROM bookings WHERE id=?", (bid,))
        self.conn.commit()
        return rid
