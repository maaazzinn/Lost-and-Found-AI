# Lost and Found Web Application

## Overview

This project is a web-based Lost and Found system built using Flask. It allows users to report lost and found items, upload images, and search for matching items.

## Features

- Users can submit lost and found item reports with descriptions and images.
- The system matches lost and found items based on descriptions and images.
- A user-friendly interface built with HTML, CSS, and JavaScript.
- Stores data in an SQLite database.

## Installation

### Prerequisites

- Python 3.x
- Flask and required dependencies

### Steps

1. **Clone the repository**

   ```sh
   git clone https://github.com/maaazzinn/Lost-and-Found-AI
   cd Lost-and-Found-AI
   ```

2. **Create a virtual environment (optional but recommended)**

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```sh
   python app/app.py
   ```

   The server will start running at `http://localhost:5000/`

## Project Structure

```
ansalna/
│── app/
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   ├── uploads/
│   │       ├── lost/
│   │       ├── found/
│   ├── templates/
│   │   ├── index.html
│   │   ├── lost_form.html
│   │   ├── found_form.html
│   │   ├── results.html
│   ├── app.py
│── instance/
│   ├── database.db
│── requirements.txt
```

## Usage

1. Open the web application in a browser (`http://localhost:5000/`).
2. Submit lost or found item details.
3. View matching results.

## License

This project is licensed under the MIT License.

