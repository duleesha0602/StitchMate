# StitchMate · Tailor Customer Management & Custom Measurement Locker System

A bespoke atelier tailor management web application built with Python (Flask), MySQL, and modern HTML/CSS following the StitchMate aesthetic palette.

---

## 🏗️ Modular Backend Architecture (Flask Blueprints)
The backend is organized into clean, independent modules inside the [`modules/`](file:///c:/Users/PC/Desktop/Project1/modules) folder:

| Module File | Purpose & Responsibilities |
| :--- | :--- |
| [`modules/auth.py`](file:///c:/Users/PC/Desktop/Project1/modules/auth.py) | **Authentication Module:** First page, Tailor Login/Registration, Customer Login, Logout |
| [`modules/dashboard.py`](file:///c:/Users/PC/Desktop/Project1/modules/dashboard.py) | **Tailor Dashboard Module:** Workroom metrics (Total Customers, Due Today, Overdue, Ready), Recent Orders |
| [`modules/customers.py`](file:///c:/Users/PC/Desktop/Project1/modules/customers.py) | **Customer Management Module:** Directory, Search, Add Patron (Walk-in vs Online), Contact History, Walk-in to Online Account conversion |
| [`modules/measurements.py`](file:///c:/Users/PC/Desktop/Project1/modules/measurements.py) | **Digital Measurement Locker Module:** Measurements List, Multi-unit Add (Inches / CM) with history preservation |
| [`modules/orders.py`](file:///c:/Users/PC/Desktop/Project1/modules/orders.py) | **Order Management Module:** Commissions List with status filters, 6-Section New Order Form, Details & Status Progression |
| [`modules/schedule.py`](file:///c:/Users/PC/Desktop/Project1/modules/schedule.py) | **Work Schedule Module:** Overdue, Due Today, Upcoming, and Ready schedule columns |
| [`modules/notifications.py`](file:///c:/Users/PC/Desktop/Project1/modules/notifications.py) | **Notification Center Module:** Customer Ready Notifications and Mark as Read |
| [`modules/customer_portal.py`](file:///c:/Users/PC/Desktop/Project1/modules/customer_portal.py) | **Customer Portal Module:** Patron Fitting Locker, Commissions Tracker, Atelier Contact & Calling |
| [`app.py`](file:///c:/Users/PC/Desktop/Project1/app.py) | **App Entry Point:** Registers all blueprints and starts server |
| [`db.py`](file:///c:/Users/PC/Desktop/Project1/db.py) | **Database Layer:** Connection pooling, schema creation, sample data seeding |
| [`utils.py`](file:///c:/Users/PC/Desktop/Project1/utils.py) | **Utilities:** Safe file & image upload handlers |

---

## 🎨 Theme & Color Palette
- **Main Background (Cream):** `#F8EFE8`
- **Sidebar (Dark Brown):** `#59433F`
- **Buttons / Actions (Soft Brown):** `#A87870`
- **Highlights & Active Menu (Dusty Pink):** `#E8C6C8`
- **Cards:** Clean White (`#FFFFFF`) with soft borders

---

## 🚀 How to Run the Project

1. **Start XAMPP MySQL and Apache**:
   - Ensure MySQL and Apache are started in the XAMPP Control Panel.
   - phpMyAdmin is accessible at: [http://localhost/phpmyadmin/](http://localhost/phpmyadmin/)

2. **Run Flask Application**:
   Open a terminal in `C:\Users\PC\Desktop\Project1` and run:
   ```bash
   python app.py
   ```
   Or double-click **`Start_StitchMate.bat`** on your Desktop!
   Open your browser at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Default Login Credentials

### 1. Tailor Account (Master Atelier)
- **Email / Username:** `tailor@stitchmate.lk`
- **Password:** `tailor123`

### 2. Online Customer Account (Nilu)
- **Username / ID:** `nilu` (or `CUS001`)
- **Password:** `customer123`
