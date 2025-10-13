# 🐍 Django Project Setup Guide

Welcome to this Django project!  
Follow the steps below to **set up and run the project locally** after cloning it.

---

##  1. Clone the Repository

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>


2. Create a Virtual Environment
For Windows:
python -m venv venv

For Linux / macOS:
python3 -m venv venv

⚙️ 3. Activate the Virtual Environment
Windows (Command Prompt):
venv\Scripts\activate

Linux / macOS:
source venv/bin/activate

4. Install Required Dependencies

Make sure you have pip updated and install all required packages:

pip install -r requirements.txt

5. Apply Database Migrations

Run the following commands to create and apply the database tables:

python manage.py makemigrations
python manage.py migrate


6. Run the Development Server

Start the Django development server:

python manage.py runserver

7. Deactivate the Virtual Environment (when done)

When you’re finished working on the project:

deactivate


This command is not for you Akib = pip freeze > requirements.txt
