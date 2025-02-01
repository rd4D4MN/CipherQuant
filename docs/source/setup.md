# Setup

This guide will help you set up CipherQuant on your local machine.

## Prerequisites

- **Git**
- **Go** (version 1.16 or higher)
- **Python** (version 3.8 or higher)
- **PostgreSQL**

## Installation Steps

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/rd4D4MN/CipherQuant.git
   cd CipherQuant

2. **Install Dependencies**  
   - For Go components, ensure Go is installed and properly configured.
   - For Python scripts, set up a virtual environment and install required packages:  
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows use `venv\Scripts\activate`
     pip install -r requirements.txt

3. **Database Setup**

   Install and start PostgreSQL.
   Create a database and update the connection details in the `config.yaml` file.

4. **Configuration**

   Edit `config.yaml` to specify your scraping targets, API keys, and other settings.

5. **Run Initial Setup Scripts**

   Execute any provided scripts to initialize the database schema or pre-load essential data.