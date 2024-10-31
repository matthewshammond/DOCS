# Dispatching Operational Chopper Software

This software maintains a database of landing zones for _Helicopter Air Ambulance (HAA)_ programs. You can export your database for _Computer Aided Dispatching (CAD)_ software, _avionics_, and _ForeFlight_.

![DOCS](https://raw.githubusercontent.com/matthewshammond/docs/main/docs/docs_app/static/docs_app/docs.png)

DOCS is an application designed for managing landing zones for HAA programs. The app features user authentication, CAD import/export, ForeFlight user waypoints export, and settings management. This project is fully containerized with Docker for easy deployment.

**Default login information is:**

```bash
username: leadpilot
password: password
```

## Features

- **User Management**: Register, login, and manage users with the admin user.
- **Hospital Data Management**: Add, view, and import hospital data from CAD files.
- **CSV Export/Import**: Export hospital data to CAD formats.
- **Admin Panel**: Built-in admin interface for managing users.
- **Database**: Uses PostgreSQL as the database backend.
- **Dockerized**: Easy setup and deployment using Docker and Docker Compose.

## Table of Contents

- [Installation](#installation)
  - [Install Docker](#install-docker)
    - [Windows](#install-docker-on-windows)
    - [macOS](#install-docker-on-macos)
    - [Linux](#install-docker-on-linux)
  - [Installation from GitHub](#installation-from-github)
- [Usage](#usage)
- [Future Plans](#future-plans)

---

## Installation

### Install Docker

#### Install Docker on Windows

1. **Install WSL 2**:

   - Press `Win + X` and select **Windows PowerShell (Admin)**.
   - Run:
     ```bash
     wsl --install
     ```
   - After installation, restart your computer if prompted.

2. **Download and Install Docker Desktop**:

   - Visit the [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop) download page.
   - Install Docker Desktop. During installation, ensure that the option to use WSL 2 instead of Hyper-V is selected.
   - Once Docker Desktop is installed, launch it, and ensure the Docker whale icon appears in the system tray.

3. **Check Installation**:
   - Open PowerShell and run:
     ```bash
     docker --version
     ```
   - This should display the installed Docker version, confirming Docker is running.

#### Install Docker on macOS

1. **Download Docker Desktop for macOS**:

   - Visit the [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop) download page.
   - Select the appropriate version for your processor (Apple Silicon or Intel).

2. **Install Docker Desktop**:

   - Open the downloaded `.dmg` file and drag Docker into the **Applications** folder.
   - Launch Docker from the **Applications** folder.
   - Follow any installation prompts and ensure the Docker whale icon is visible in the top-right menu bar.

3. **Verify Installation**:
   - Open **Terminal** and run:
     ```bash
     docker --version
     ```
   - This command will show the Docker version, confirming successful installation.

#### Install Docker on Linux

1. **Install Docker**:

   - Update your package manager and install Docker by running the following commands:
     ```bash
     sudo apt update
     sudo apt install docker.io
     ```

2. **Start and Enable Docker**:

   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Add User to Docker Group** (optional but recommended):

   ```bash
   sudo usermod -aG docker ${USER}
   ```

4. **Verify Installation**:
   - Log out and back in for group changes to take effect, and then check:
     ```bash
     docker --version
     ```

---

### Installation from GitHub

1. **Clone the Repository**:

   - Open your terminal and run:
     ```bash
     git clone https://github.com/matthewshammond/DOCS.git
     cd DOCS
     cp .env.sample .env
     ```

2. **Enable Password Reset (Optional)**

   - If you want to enable users to reset their passwords, you need to update the `EMAIL_USER` and `EMAIL_PASS` environment variables in `.env`
     - simply have the lead pilot replace the `EMAIL_USER` environment variable with their email address
     - create an app-specific password for the `EMAIL_PASS` environment variable
       - simply google search your email provider and app specific password (i.e. gmail app specific password) and follow the steps

3. **Build and Start Services**:

   - Run the following command to build the application using Docker Compose:
     ```bash
     docker compose up -d
     ```
   - If you want to build from source, comment out `image` and uncomment `build` and `context` lines.

   ```bash
   services:
     docs:
       container_name: docs
       # build:
       #   context: .
       image: matthewshammond/docs:v1.0
   ```

4. **Access the Application**:

   - After the build process is complete, visit `localhost` in your web browser to access DOCS.
   - Default login information:

   ```bash
   Username: leadpilot
   Password: password
   ```

---

## Usage

Once DOCS is running, you can use it to:

- Import hospital data via CAD file.
- Add hospitals.
- View and manage hospital locations.
- Export data in CAD and ForeFlight formats.

Once logged in with leadpilot account, you'll have admin rights. You can access the admin panel from `Settings`-`Admin`. Here you can change your password and add/manage other pilot accounts.

A Sample CAD file has been included. Use this as a template if you are going to do a mass import of landing zones. Ensure your columns are in the same order as the included CAD file. Below shows you the possible formats for Latitude and Longitude. The `Airport` column is whether the landing zone has an FAA Identifier. You can use `Yes/True` or `No/False` when determining if the Landing Zone has an FAA Identifier.
| LATITUDE | LONGITUDE | TITLE | CAD Identifiers and/or Description | FAA IDENTIFIER | AIRPORT |
| --------------- | --------------- | --------------- | --------------- | --------------- | --------------- |
| 34 9.50 N | 82 22.92 W | ABVLE | "Abbeville Area Med Ctr-Abbeville, SC" | SC83 | True |
| 31 35.48 N | 84 9.41 W | ABYFP | "Phoebe Putney Mem Hosp-Albany, GA" | | False |
| 32 57.09 N | 081 14.94 W | ALNDL | "Allendale County Hosp-Fairfax, SC" | | No |
| 32 04.05 N | 084 15.32 W | AMERI | "Phoebe Sumter Med Ctr-Americus, GA" | 1GA7 | Yes |

---

## Future Plans

- **ForeFlight Content Packs**: Users will be able to create ForeFlight content packs directly within the DOCS application.
- **County Map Export**: Ability to export maps of counties across the lower 48 states for use in dispatch operations.
