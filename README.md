# HomeFinder - Property Search Application

A web-based property search application that compares the performance of Hash-Set vs Posting-List indexing methods for real estate data.

## Project Overview

This application demonstrates practical implementations of two different data structure approaches for property filtering:
- **Hash-Set Index**: Uses Python sets for fast membership testing with set intersection
- **Posting-List Index**: Uses sorted lists with merge-based intersection algorithms

## Features

- Search properties by bedrooms, bathrooms, price range, and year built
- Filter by additional features (basement, fireplace, attic, garage)
- Interactive map visualization showing property locations
- Real-time performance comparison between indexing methods
- Uses Chicago real estate dataset with 192,000+ properties

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository**
```bash
   git clone https://github.com/ShivankJoginipalli/Homefinder.git
   cd Homefinder
```

2. **Create a virtual environment**
```bash
   python3 -m venv .venv
```

3. **Activate the virtual environment**
   
   On macOS/Linux:
```bash
   source .venv/bin/activate
```
   
   On Windows:
```bash
   .venv\Scripts\Activate.ps1
```

4. **Install required packages**
```bash
   pip install -r requirements.txt
```

## Running the Application

The application consists of two components that need to run simultaneously:

### Step 1: Start the Backend Server

Open a terminal and run:
```bash
# Activate virtual environment on Mac
source .venv/bin/activate

# Activate virtual environment on Windows
.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend-ngin

# Start the Flask server
python backend_api.py
```

You should see:
```
Loading data from ../data/chicago_data_cleaned.csv...
Loaded 192828 properties
Building hash-set index...
Hash-set index built in XYZs
Building posting-list index...
Posting-list index built in XYZs
Starting Flask server on http://127.0.0.1:5000
```

**Keep this terminal running!**

### Step 2: Start the Frontend

Open a **new terminal** and run:
```bash
# Activate virtual environment on Mac
source .venv/bin/activate

# Activate virtual environment on Windows
.venv\Scripts\Activate.ps1

# Navigate to frontend directory
cd frontend-ngin

# Start the Streamlit app
streamlit run streamlit.py
```

You should see:
```
Local URL: http://localhost:8501
Network URL: http://10.4.8.20:8501
```

### Step 3: Use the Application

Open your web browser and go to:
```
http://localhost:8501
```

You can now search for properties and compare the performance of different indexing methods!

## Stopping the Application

To stop the application:

1. In the **backend terminal**: Press `Ctrl+C`
2. In the **frontend terminal**: Press `Ctrl+C`
3. Deactivate virtual environment (optional): `deactivate`

## Troubleshooting

**Backend won't start:**
- Make sure you're in the `backend-ngin` directory
- Check that `../data/chicago_data_cleaned.csv` exists
- Verify port 5000 is not already in use

**Frontend won't connect:**
- Make sure the backend is running first
- Check that you see "Starting Flask server on http://127.0.0.1:5000"
- Verify port 8501 is not already in use

**Map not displaying:**
- Ensure `streamlit-folium` is installed: `pip install streamlit-folium`
- Check browser console for JavaScript errors

## Project Structure
```
Homefinder/
├── backend-ngin/
│   ├── backend_api.py          # Flask REST API server
│   ├── posting_hashsets.py     # Hash-set index implementation
│   ├── posting_lists.py        # Posting-list index implementation
│   └── hash_table.py           # Custom hash table implementation
├── frontend-ngin/
│   └── streamlit.py            # Streamlit web interface
├── data/
│   └── chicago_data_cleaned.csv # Chicago property dataset
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Course Information

COP3530 - Data Structures & Algorithms  
Project 2 - Fall 2024

## License

This project is for educational purposes.