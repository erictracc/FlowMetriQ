<div align="center">
  <h1><b>FlowMetriQ</b></h1>
  <img src="https://readme-typing-svg.demolab.com?font=Poppins&size=26&pause=1000&color=7D53F7&center=true&width=450&lines=Process+Mining+Dashboard;Simulation+Engine;Performance+Analytics" alt="Typing animation" />
<img width="1588" height="1201" alt="Screenshot 2025-12-12 000551" src="https://github.com/user-attachments/assets/38dca365-2be4-4933-9a3e-514c0df589db" />

</div>

---

## Overview

**FlowMetriQ** is a local, interactive **Process Mining & Simulation tool** designed to analyze, visualize, and experiment with real-world event logs.

Built using:

- **Python (Dash + Flask)**
- **MongoDB**
- **Plotly Graphs**
- **Monte-Carlo Simulation Engine**

It allows users to:

✔ Upload and manage event logs                                          
✔ Explore bottlenecks and performance issues  
✔ Visualize timelines and statistical distributions  
✔ Run simulations with activity duration interventions  
✔ Compare baseline vs simulated process outcomes  

All data is stored **locally** using your MongoDB instance, nothing is cloud-hosted.

---

## Features

### **Process Analysis**
- Activity performance tables  
- Case timelines  
- Duration distributions and boxplots  
- Event frequency graphs  
- Bottleneck detection  

<img width="1592" height="1187" alt="Screenshot 2025-12-12 000610" src="https://github.com/user-attachments/assets/a05d794c-412c-4a45-98bf-10192566dda5" />


### **Simulation Engine**
- Markov-based path generation  
- Monte-Carlo simulation runs  
- Activity interventions:
  - Deterministic durations  
  - Speedup (%)  
  - Slowdown (%)  

<img width="1582" height="1190" alt="Screenshot 2025-12-12 000854" src="https://github.com/user-attachments/assets/8efaebad-e7c5-4b12-9851-ea3e906a6a02" />


### **Interactive Dashboard**
- `/analysis` → Performance analytics  
- `/simulation` → Scenario-based simulations  
- `/home` → Overview page  
- `/config` → Application settings  
- `/login` / `/logout` → Optional authentication screens  

<img width="1582" height="1187" alt="Screenshot 2025-12-12 001946" src="https://github.com/user-attachments/assets/8eb45f0c-4cf8-4502-8dd9-790653da3a7c" />


---

## Process Analysis & Insights

FlowMetriQ is designed not only to visualize event logs, but to **support structured process analysis and decision-making**. Using the application, analysts can systematically uncover inefficiencies and formulate actionable recommendations.

### What the Application Enables

Using FlowMetriQ, we can:

- Visualize the **end-to-end claim-handling process**
- Identify:
  - Bottlenecks
  - Delays
  - Rework loops
  - Repetitions
- Inspect individual cases in detail
- Validate data quality issues
- Make **evidence-based process improvement recommendations**

---

## Application Core Requirements Checklist

FlowMetriQ satisfies the following core process mining requirements:

- ✔ Directly-Follows Graph (DFG) generation  
- ✔ Interactive visualizations  
- ✔ Case viewer with filters  
- ✔ Bottleneck detection  
- ✔ Basic statistics dashboard  
- ✔ Case timelines  
- ✔ Duration distributions and boxplots  

---

## Demonstrated Process Insights

### Rework Loops (Internally Pending Events)

Rework loops—such as repeated *internally pending* events—are a strong indicator of inefficiency.

<img width="1588" height="977" alt="Screenshot 2025-12-12 002104" src="https://github.com/user-attachments/assets/aaaf9bbc-d23a-46d8-92f9-f7629d7c57d6" />

- On the **Analysis page**, filtering by the *internally pending* activity reveals:
  - High frequency
  - Elevated median and average durations
- In **Additional Visual Insights**, this event has the **highest count**
- Its **boxplot is highly skewed**, indicating long-tail delays

<img width="1585" height="1192" alt="Screenshot 2025-12-12 000629" src="https://github.com/user-attachments/assets/a8878ff8-4392-4d02-8ff3-104f48abd313" />


**Interpretation:**  
This suggests repeated internal handoffs or unresolved dependencies, making it a prime candidate for process redesign.

---

### Longest Cases

FlowMetriQ enables deep inspection of long-running cases:

- The **Case Timeline feature** visualizes how each activity unfolds over time
- This allows analysts to:
  - Select the longest case (by total duration or number of events)
  - Understand which activities contribute most to delays

<img width="1582" height="1198" alt="Screenshot 2025-12-12 000710" src="https://github.com/user-attachments/assets/1781e4cd-5ecd-40f2-ba4b-c954f652edd7" />


**Use Case:**  
After identifying extreme cases through statistical analysis, those cases can be visually inspected to understand *why* they took longer.

---

### Timestamp Anomalies & Ordering Issues

In **Additional Visual Insights**, users can inspect:

- Event frequencies
- Direct successorship relationships

This helps identify:
- Unexpected activity ordering
- Timestamp inconsistencies
- Potential logging or automation artifacts

**Example:**  
If an approval event consistently precedes data collection, this may indicate data recording issues.

---

### Negative Durations

Some activities initially appeared with **negative durations**.

**Handling decision:**
- Negative durations were treated as **data entry or logging errors**
- These records were removed from the analysis

**Implications:**
- Certain variants may no longer be representable
- Artificial variants could appear or disappear

**Alternative approaches considered:**
- Converting negative values to positive
- Consulting stakeholders to interpret their semantic meaning

---

### Activities with Very Few Duration Values

Some activities appear only once or a handful of times, resulting in unusual boxplots.

**Observed effects:**
- No visible box (Q1 = median = Q3)
- Single dots or flat lines
- Sparse distributions

**Examples:**
- Paid  
- Review Completed  
- Reviewed Documentation  

**Why this happens:**
- Rare event types  
- Automated activities (often duration = 0)  
- Activities occurring in very few cases  

**Important Note:**  
Boxplots require **multiple observations** to display meaningful quartiles. Sparse activities should be interpreted cautiously.

---

## From Analysis to Simulation

Insights discovered during analysis directly inform the **Simulation Engine**:

- Bottleneck activities can be targeted for:
  - Deterministic duration changes
  - Speedups
  - Slowdowns
- Simulation results quantify:
  - Expected improvement
  - Distributional changes
  - Risk of unintended delays

This closes the loop between **diagnosis → intervention → evaluation**.

---

## Tech Stack

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
│ └── settings.json # safe version, no credentials
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

---

## Environment Setup (Safe Local Version)

### 1. Create a `.env` file

MONGO_URI=mongodb://admin:YOURPASSWORD@localhost:27017/?authSource=admin
MONGO_DB=flowmetriq
HOST=127.0.0.1
PORT=8050
SECRET_KEY=your_secret_here


> `.env` is ignored by git — credentials are never uploaded.

---

### 2. Configuration Loader Example

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
🧑‍💻 Running Locally
Clone the repository:

bash
Copy code
git clone https://github.com/erictracc/FlowMetriQ.git
cd FlowMetriQ
Create a virtual environment:

bash
Copy code
python -m venv venv
.\venv\Scripts\activate   # Windows
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Start MongoDB locally
(Make sure MongoDB is running before launching FlowMetriQ.)

Run the application:

bash
Copy code
python app.py
Open your browser:

http://localhost:PORT




Support
If you like this project, please ⭐ the repository!

<div align="center"> Made locally with ❤️ by <b>Eric Traccitto</b> </div> ```
