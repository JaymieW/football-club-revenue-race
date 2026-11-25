# football-club-revenue-race
Documents the Python/Flask/Matplotlib project itself and points back to your portfolio[cite: 1, 12]:

```markdown
# Football Club Revenue Bar Chart Race

Flask and Python data visualization service generating animated bar chart races from multi-year football club revenue data using Pandas, Matplotlib, and Pillow[cite: 12].

- **Live Service:** `https://football-club-revenue-race.onrender.com`[cite: 1]
- **Portfolio Demo:** Embedded in `My_Portfolio`[cite: 12]

## Stack & Setup

- **Backend:** Flask + Gunicorn (`gunicorn --timeout 120 app:app`)
- **Visualization:** Matplotlib (`Agg` backend), Pandas, Pillow[cite: 12]
- **Cross-Origin Access:** Configured for cross-origin requests from the portfolio frontend

```powershell
pip install -r requirements.txt
gunicorn --timeout 120 app:app