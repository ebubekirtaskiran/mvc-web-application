# MVC Web Application (Python)

This project is a simple **MVC (Model–View–Controller)** based web application written in Python.  
It demonstrates a clean separation of concerns by splitting responsibilities into Model, View, and Controller layers.

## Features
- MVC architecture (Model / View / Controller separation)
- Static UI files under `static/` (HTML/CSS)
- Example controller routing and basic request handling

## Project Structure

```text
.
├── controller.py
├── model.py
├── view.py
├── static/
│   ├── index.html
│   ├── gateway.html
│   └── arayuz.css
├── file_generator.py
└── README.md

Note: Some folders may contain sample/demo files used during development (e.g., masaustu/, indirilenler/, belgeler/, resimler/).

MVC Explanation
Model (model.py)

Responsible for data access, data processing, and business logic.

Stores the logic that should not depend on the UI.

View (view.py + static/)

Responsible for the user interface and rendering output.

static/ includes HTML/CSS resources.

Controller (controller.py)

Connects Model and View.

Handles requests and decides which view to display.

Requirements

Python 3.10+ (recommended)

How to Run

Open a terminal in the project folder.

Run the controller (example):

python controller.py


If your project supports specifying a port, you can run:

python controller.py --port 8081


Then open in the browser:

http://127.0.0.1:8081


Author

Ebubekir Taskiran