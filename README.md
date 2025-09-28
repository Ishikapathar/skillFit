# SkillFit 🎯

**AI-Powered Internship & Career Matching System**

SkillFit is an intelligent web application that matches students with internship opportunities based on their skills, location preferences, and field of interest using advanced fuzzy matching algorithms.

## 🚀 Features

- **Smart Matching Algorithm**: Uses fuzzy string matching to find the best internship matches
- **Skills-Based Filtering**: Matches students based on their technical and soft skills
- **Location Preferences**: Finds opportunities in preferred geographic locations
- **Field Specialization**: Matches by area of study or career interest
- **RESTful API**: Fast and scalable FastAPI backend
- **Interactive Frontend**: User-friendly HTML interface
- **Real-time Recommendations**: Get instant personalized suggestions

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for APIs
- **Python 3.13** - Core programming language
- **Pandas** - Data manipulation and analysis
- **FuzzyWuzzy** - String matching algorithms
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI web server

### Frontend
- **HTML5** - Markup structure
- **CSS3** - Styling and responsive design
- **JavaScript** - Interactive functionality
- **Bootstrap** (if applicable) - UI components

### Infrastructure
- **Nginx** - Web server and reverse proxy
- **CSV Database** - Internship data storage

## 📁 Project Structure

```
skillFit/
├── backend/
│   ├── __init__.py
│   ├── backends.py          # Main FastAPI application
│   └── backends_bulletproof.py
├── frontend/
│   ├── dashboard.html       # Main dashboard
│   ├── form.html           # Student input form
│   ├── login.html          # Authentication page
│   ├── results.html        # Recommendation results
│   └── test*.html          # Testing pages
├── data/
│   └── student_internship_matches_stratified (1).csv
├── nginx.conf              # Nginx configuration
├── requirements.txt        # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Ishikapathar/skillFit.git
cd skillFit
```

2. **Create virtual environment**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate     # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
# Start the FastAPI server
uvicorn backend:app --reload --port 8000

# Or using the module path
uvicorn backend.backends:app --reload --port 8000
```

5. **Access the application**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: Open `frontend/form.html` in your browser

## 📝 API Usage

### Get Recommendations
```bash
POST /get_recommendations
Content-Type: application/json

{
  "name": "John Doe",
  "course": "Computer Science",
  "skills": ["Python", "Machine Learning", "JavaScript"],
  "locations": ["New York", "San Francisco"],
  "field": "Software Development",
  "top_n": 5
}
```

### Response Example
```json
{
  "recommendations": [
    {
      "company": "Tech Corp",
      "internship_title": "Software Development Intern",
      "location": "New York",
      "skills": "Python, JavaScript, React",
      "field": "Software Development",
      "match_score": 0.85,
      "apply_link": "https://company.com/apply/software-development-intern"
    }
  ]
}
```

## 🔧 Configuration

### Environment Setup
Create a `.env` file (optional):
```env
DEBUG=True
PORT=8000
DATA_FILE=data/student_internship_matches_stratified (1).csv
```

### Nginx Configuration
For production deployment, use the provided `nginx.conf`:
- Reverse proxy setup
- Static file serving
- Load balancing (if needed)

## 🧪 Testing

Run the test pages to verify functionality:
- `frontend/test.html` - Basic functionality test
- `frontend/test_resume_upload.html` - File upload testing

## 📊 Algorithm Details

### Matching Logic
1. **Skills Matching** (60% weight)
   - Calculates intersection of student skills with job requirements
   - Uses fuzzy string matching for partial matches

2. **Field Matching** (40% weight)
   - Compares student's field of interest with job categories
   - Minimum 80% similarity threshold for matches

3. **Location Filtering**
   - Filters opportunities by preferred locations
   - Supports multiple location preferences

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

YOUTUBE LINK: https://youtu.be/-JnNI3XBD88


## 👥 Authors

- **Ishika Pathar** - *Initial work* - [@Ishikapathar](https://github.com/Ishikapathar)

## 🙏 Acknowledgments

- FastAPI team for the excellent web framework
- FuzzyWuzzy library for string matching capabilities
- Open source community for inspiration and tools

## 📞 Support

For support, email patharishika68@gmail.com or create an issue in this repository.

---

⭐ **Star this repository if you find it helpful!**
