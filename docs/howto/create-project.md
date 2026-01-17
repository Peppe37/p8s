# How to Create a New Project

This guide walks you through creating a new full-stack application using the P8s framework.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend dashboard)
- Git

## Step 1: Install P8s

First, ensure you have the `p8s` CLI installed:

```bash
pip install p8s
```

## Step 2: Create Project Structure

Use the `new` command to scaffold a new project. This creates the backend structure and a React-based frontend.

```bash
p8s new --name my_awesome_project
```

This will create a directory `my_awesome_project` with:
- `backend/`: Python backend (FastAPI + SQLModel)
- `frontend/`: React Admin Dashboard (Vite)
- `manage.py`: Entry point scripts

## Step 3: Initialize Database

Navigate into your project and apply the initial migrations:

```bash
cd my_awesome_project
p8s migrate
```

## Step 4: Create Admin User

Create a superuser to access the admin panel:

```bash
p8s createsuperuser
```

Follow the prompts to set your email and password.

## Step 5: Run the Development Server

Start the backend server:

```bash
p8s runserver
```

You can now access:
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Admin Panel:** [http://localhost:8000/admin](http://localhost:8000/admin) (Requires frontend build or dev server)

## Step 6: Start Frontend (Optional for Dev)

If you are developing custom admin features, run the frontend dev server:

```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) to see the admin panel with hot reloading.
