<div align="center">
  <h1><b>FlowMetriQ</b></h1>
  <img src="https://readme-typing-svg.demolab.com?font=Poppins&size=26&pause=1000&color=7D53F7&center=true&width=450&lines=Process+Mining+Dashboard;Simulation+Engine;Performance+Analytics" alt="Typing animation" />
</div>

---

## 📌 Overview

**FlowMetriQ** is a local, interactive **Process Mining & Simulation tool** built with:

- **Python (Dash + Flask)**
- **MongoDB**
- **Plotly Graphs**
- **Monte-Carlo Simulation Engine**

It allows you to:

✔ Upload event logs  
✔ Explore bottlenecks and performance  
✔ Visualize timelines and statistics  
✔ Run simulations with activity duration interventions  
✔ Compare original vs simulated outcomes  

All data is stored **locally** using your MongoDB instance — nothing is cloud-hosted.

---

## 🚀 Features

### 🔍 **Process Analysis**
- Activity performance tables  
- Case timelines  
- Duration distributions  
- Event frequency graphs  
- Bottleneck analysis  

### 🧪 **Simulation Engine**
- Markov-based path generation  
- Monte-Carlo simulation runs  
- Interventions:
  - Deterministic durations  
  - Speedup %  
  - Slowdown %  

### **Interactive Dashboard**
- `/analysis` → Performance analytics  
- `/simulation` → Run your simulations  
- `/home` → Overview page  
- `/config` → Settings  
- `/login/logout` → (optional) auth screens

---

## 🛠️ Tech Stack

**Backend:**  
- Python 3.10+  
- Flask  
- Dash  

**Storage:**  
- MongoDB (local)

**Visualization:**  
- Plotly  
- Dash Graphs  

---

## Project Structure

FlowMetriQ/
│ app.py
│ README.md
│ requirements.txt
│ .env # local environment variables (ignored by git)
│
├── config/
│ └── settings.json (safe version, no credentials)
│
├── components/
│ └── navbar.py
│
├── db/
│ ├── mongo.py
│ ├── logs.py
│ └── collections.py
│
├── pages/
│ ├── home.py
│ ├── analysis.py
│ ├── simulation.py
│ ├── prediction.py
│ ├── login.py
│ └── logout.py
│
└── services/
├── log_service.py
├── simulation_service.py
├── bottleneck_service.py
├── graph_service.py
└── performance_service.py

yaml
Copy code

---

## Environment Setup (Safe Local Version)

1. Create a `.env` file in the root folder:

MONGO_URI=mongodb://admin:YOURPASSWORD@localhost:27017/?authSource=admin
MONGO_DB=flowmetriq
HOST=127.0.0.1
PORT=8050
SECRET_KEY=your_secret_here

lua
Copy code

> `.env` is ignored by git — so your real credentials never get uploaded.

2. Update `config_manager` to read from environment variables:

```python
from dotenv import load_dotenv
import os

load_dotenv()

settings = {
    "database_uri": os.getenv("MONGO_URI"),
    "database_name": os.getenv("MONGO_DB"),
    "host": os.getenv("HOST", "127.0.0.1"),
    "port": int(os.getenv("PORT", 8050)),
    "secret_key": os.getenv("SECRET_KEY"),
}
🧑Running Locally
1. Clone the project
bash
Copy code
git clone https://github.com/erictracc/FlowMetriQ.git
cd FlowMetriQ
2. Create a virtual environment
bash
Copy code
python -m venv venv
.\venv\Scripts\activate   # Windows
3. Install dependencies
bash
Copy code
pip install -r requirements.txt
4. Start MongoDB locally
(Make sure MongoDB is running before launching FlowMetriQ.)

5. Run the dashboard
python app.py
6. Open browser
Copy code
http://localhost:PORT
Simulation Overview
FlowMetriQ allows you to test how process durations change under:

Deterministic adjustments

Speedups (%)

Slowdowns (%)

Results appear in:

Simulation summary

Histogram comparison

Case duration changes

📸 Screenshots (Add Later)
css
Copy code
[ Home Page ]
[ Analysis Dashboard ]
[ Simulation Engine ]
⭐ Support
If you like this project, please ⭐ the repo!

<div align="center"> Made locally with ❤️ by <b>Eric Traccitto</b> </div> ```