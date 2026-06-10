import webbrowser
from urllib.parse import quote

def notify_owner_action(db, action_type, record):
    """
    إرسال إشعار للمالك عبر واتساب بتفاصيل العملية مع الإحصائيات اليومية.
    """
    try:
        # جلب رقم هاتف المالك من الإعدادات
        owner_phone_row = db.conn.execute("SELECT value FROM settings WHERE key='owner_phone'").fetchone()
        if not owner_phone_row or not owner_phone_row['value']:
            return  # لم يتم تعيين رقم
            
        phone = ''.join(filter(str.isdigit, owner_phone_row['value']))
        if phone.startswith("01") and len(phone) == 11:
            phone = "+2" + phone

        # جلب الإحصائيات
        stats = db.get_dashboard_stats()
        
        # بناء الرسالة
        msg = "🔔 إشعار من نظام التأجير 🔔\n\n"
        msg += f"نوع العملية: {action_type}\n"
        msg += "--------------------\n"
        msg += f"العميل: {record.get('customer_name', 'غير معروف')}\n"
        msg += f"الفستان: {record.get('dress_name', '')} ({record.get('dress_code', '')})\n"
        if action_type == "تأجير جديد":
            msg += f"تاريخ الاستلام: {record.get('rental_date', '')}\n"
        else:
            msg += f"تاريخ المناسبة: {record.get('event_date', '')}\n"
            
        if action_type == "تأجير جديد":
            paid = record.get('paid_amount')
            total = record.get('total_amount')
        else:
            paid = record.get('deposit')
            total = record.get('rental_price')
            
        if paid is None: paid = 0
        if total is None: total = 0
            
        msg += f"المدفوع: {paid:,.0f} ج\n"
        remaining = total - paid
        msg += f"المتبقي: {remaining:,.0f} ج\n"
        
        msg += "\n📊 إحصائيات اليوم حتى الآن:\n"
        msg += f"إيرادات اليوم: {stats.get('today_revenue', 0):,.0f} ج\n"
        msg += f"إجمالي الإيرادات (الشهر): {stats.get('monthly_revenue', 0):,.0f} ج\n"
        msg += f"حجوزات نشطة: {stats.get('active_bookings', 0)}\n"
        msg += f"تأجيرات نشطة: {stats.get('active_rentals', 0)}\n"
        
        url = f"https://api.whatsapp.com/send?phone={phone}&text={quote(msg)}"
        webbrowser.open(url)
    except Exception as e:
        print(f"Failed to notify owner: {e}")
