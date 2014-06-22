```
├── CONTRIBUTING.md - Info about helping in the project
├── LICENSE - MIT
├── README.md - Information to get started
├── remedy - The web application
│   ├── config.py - Configurations for the web application
│   ├── rad - The database codebase
│   │   ├── db
│   │   │   ├── migrations - Database migrations using Alembic
│   │   │   │   └── versions - Database migration files
│   │   │   ├── models.py - The models(structure) for the database
│   │   │   └── rad.db - SQLite database, will be removed for postgres
│   │   ├── get_save_data.py - Runs all scrapers and saves them to the database
│   │   └── scrapinglib - Code for different scrapers and data sources
│   │       ├── howardbrown.py - Howard Brown website scraper
│   ├── radremedy.py - The main entry point for the web application
│   ├── search.py - Code that will control different website search and forms logic
│   ├── static - Static files and assets
│   │   ├── css - CSS files
│   │   │   └── remedy.css - Main look for the website built on top of bootstrap
│   │   ├── fonts - Custom fonts for the website
│   │   ├── img - Some images and Icons
│   │   ├── js - Javascript libraries and code
│   │   └── mockups - Design Mock ups for the website
│   └── templates - Templates and components for the website used by Flask(coded in Jinja)
├── requirements.txt - Project requirements
├── scripts - Some scripts to ease actions
│   ├── bootstrap.py - Ran to create some records for the database, ran once
└── STRUCTURE.md - This file
```
