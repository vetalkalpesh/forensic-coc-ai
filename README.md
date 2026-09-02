# Forensic Evidence Chain of Custody System ⚖️🔬🗺️

A high-fidelity, professional Forensic Evidence Management and Chain of Custody (CoC) system. Built as a full-stack web application for academic demonstration and professional use-cases.

## 🚀 Key Features

- **Interactive Forensic Map**: Visualize crime scenes, labs, and evidence movement trails on a high-fidelity geospatial dashboard.
- **Chain of Custody (CoC)**: Complete temporal and spatial tracking of evidence with digital auditing.
- **Integrity Verification**: Automatic SHA-256 hashing and tamper-detection alerts.
- **Role-Based Access Control (RBAC)**: Distinct permissions for Junior Officers, Senior Examiners, and Administrators.
- **Advanced Forensic Workflows**: Modules for Lab Analysis, Storage Management, Court Submissions, and "Dead Man Switch" inactivity alerts.

## 🛠️ Technology Stack

- **Backend**: Python (Flask)
- **Database**: MySQL 8.0 (with Triggers, Stored Procedures, and Recursive CTEs)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Geospatial**: Leaflet.js with CartoDB Dark Matter tiles

## 🔧 Installation & Setup

### 1. Database Setup
1.  Ensure **MySQL 8.0+** is installed and running.
2.  Import the database schema:
    ```bash
    mysql -u your_username -p < database/complete_database.sql
    ```
    *(Or open `database/complete_database.sql` in MySQL Workbench and run it.)*

### 2. Configure Backend
1.  Open `backend/app.py`.
2.  Update the `DB` dictionary with your MySQL credentials:
    ```python
    DB = dict(host='localhost', user='root', password='YOUR_PASSWORD',
              database='forensic_coc', charset='utf8mb4')
    ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
From the project root:
```bash
python backend/app.py
```
*(Or if you are inside the `backend/` folder: `python app.py`)*

Open **[http://localhost:5000](http://localhost:5000)** in your browser.

## 📂 Project Structure

- `frontend/`: HTML pages and static assets (CSS/JS).
- `backend/`: Flask application, API routes, and media storage.
- `database/`: SQL scripts for schema and sample data.
- `backups/`: Safety backups for critical project files.

## 👮 Demo Credentials
- **Badge Number**: `MH-2301`
- **Password**: `password123`

---
*Developed for intelligent forensic evidence management.*
