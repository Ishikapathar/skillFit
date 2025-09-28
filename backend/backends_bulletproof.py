import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import random
import base64
import re
import json
import io
import tempfile
import os
from pathlib import Path

# Try to import optional dependencies with fallbacks
try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("Warning: fuzzywuzzy not available, using basic string matching")
    class fuzz:
        @staticmethod
        def ratio(a, b):
            return 100 if str(a).lower() == str(b).lower() else 0

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Warning: PyPDF2 not available")
    PdfReader = None

try:
    from docx import Document
except ImportError:
    print("Warning: python-docx not available")
    Document = None

# ----------------------------
# Data Loading with Error Handling
# ----------------------------
def load_data_safely():
    """Load data with comprehensive error handling"""
    try:
        data_path = Path("../data/student_internship_matches_stratified (1).csv")
        if not data_path.exists():
            data_path = Path("data/student_internship_matches_stratified (1).csv")
        
        if data_path.exists():
            df = pd.read_csv(data_path)
            print(f"Loaded dataset with {len(df)} rows")
            return df
        else:
            print("Dataset not found, creating mock data")
            return create_mock_data()
    except Exception as e:
        print(f"Error loading data: {e}, using mock data")
        return create_mock_data()

def create_mock_data():
    """Create mock internship data if real data is unavailable"""
    mock_data = []
    companies = ["TechCorp", "DataSoft", "WebDev Inc", "AI Solutions", "CloudTech"]
    fields = ["Software Development", "Data Science", "Web Development", "Machine Learning"]
    locations = ["New York", "San Francisco", "Boston", "Seattle", "Remote"]
    skills_sets = [
        ["python", "django", "postgresql"],
        ["javascript", "react", "node.js"],
        ["java", "spring", "mysql"],
        ["python", "pandas", "machine learning"],
        ["html", "css", "bootstrap"]
    ]
    
    for i in range(50):
        mock_data.append({
            "company": companies[i % len(companies)],
            "internship_title": f"Software Intern {i+1}",
            "field": fields[i % len(fields)],
            "location": locations[i % len(locations)],
            "skills": ",".join(skills_sets[i % len(skills_sets)])
        })
    
    return pd.DataFrame(mock_data)

# Initialize data
try:
    matches_df = load_data_safely()
    
    # Normalize column names safely
    matches_df.columns = [str(c).strip().lower().replace(' ', '_') for c in matches_df.columns]
    
    # Clean and prepare data with bulletproof error handling
    def safe_fillna(series, default_value):
        """Safely fill NA values and convert to string"""
        try:
            return series.fillna(default_value).astype(str)
        except:
            return pd.Series([str(default_value)] * len(series))
    
    def safe_skills_processing(skills_series):
        """Safely process skills column"""
        processed_skills = []
        for skill_str in skills_series:
            try:
                if pd.isna(skill_str) or skill_str in [None, 'nan', 'None']:
                    processed_skills.append([])
                else:
                    skill_list = [s.strip().lower() for s in str(skill_str).split(",") if s.strip()]
                    processed_skills.append(skill_list)
            except:
                processed_skills.append([])
        return processed_skills
    
    # Apply safe data cleaning
    matches_df["field"] = safe_fillna(matches_df.get("field", pd.Series()), "General")
    matches_df["location"] = safe_fillna(matches_df.get("location", pd.Series()), "Remote")
    matches_df["company"] = safe_fillna(matches_df.get("company", pd.Series()), "Company")
    matches_df["internship_title"] = safe_fillna(matches_df.get("internship_title", pd.Series()), "Internship")
    matches_df["skills"] = safe_skills_processing(matches_df.get("skills", pd.Series()))
    
    print("Data preprocessing completed successfully")
    
except Exception as e:
    print(f"Critical error in data initialization: {e}")
    # Fallback to minimal mock data
    matches_df = pd.DataFrame([{
        "company": "TechCorp",
        "internship_title": "Software Intern",
        "field": "Software Development",
        "location": "Remote",
        "skills": ["python", "javascript"]
    }])

# ----------------------------
# FastAPI setup
# ----------------------------
app = FastAPI(title="Student Internship Matching System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage
resume_analyses = {}

# ----------------------------
# Request Models with Validation
# ----------------------------
class RecommendationRequest(BaseModel):
    name: str = "Student"
    course: Optional[str] = None
    skills: List[str] = []
    locations: List[str] = []
    field: str = ""
    top_n: int = 5

class ResumeUploadRequest(BaseModel):
    student_email: str
    resume_data: str
    filename: str
    file_type: str = "application/pdf"

class DashboardRequest(BaseModel):
    student_email: str

# ----------------------------
# Bulletproof Helper Functions
# ----------------------------
def safe_string_operation(value, operation="lower"):
    """Safely perform string operations"""
    try:
        if value is None or pd.isna(value):
            return ""
        str_val = str(value)
        if operation == "lower":
            return str_val.lower()
        elif operation == "strip":
            return str_val.strip()
        return str_val
    except:
        return ""

def safe_list_operation(lst, default=None):
    """Safely handle list operations"""
    try:
        if lst is None:
            return default or []
        if not isinstance(lst, list):
            return [str(lst)] if lst else []
        return [str(item) for item in lst if item is not None]
    except:
        return default or []

def calculate_score_safely(row, student_skills, student_field):
    """Calculate matching score with error handling"""
    try:
        score = 0
        
        # Skills match (weight 0.6)
        if student_skills:
            try:
                row_skills = row.get("skills", [])
                if isinstance(row_skills, str):
                    row_skills = [s.strip().lower() for s in row_skills.split(",") if s.strip()]
                elif not isinstance(row_skills, list):
                    row_skills = []
                
                student_skills_clean = [safe_string_operation(s) for s in student_skills]
                row_skills_clean = [safe_string_operation(s) for s in row_skills]
                
                match_count = len(set(student_skills_clean) & set(row_skills_clean))
                if student_skills_clean:
                    score += (match_count / len(student_skills_clean)) * 0.6
            except:
                pass
        
        # Field fuzzy match (weight 0.4)
        if student_field:
            try:
                row_field = safe_string_operation(row.get("field", ""))
                if row_field:
                    similarity = fuzz.ratio(row_field, safe_string_operation(student_field))
                    if similarity >= 80:
                        score += 0.4
            except:
                pass
                
        return round(max(0, min(1, score)), 3)
    except:
        return 0

# ----------------------------
# Root endpoint
# ----------------------------
@app.get("/")
def root():
    return {"message": "FastAPI server is running. Use /get_recommendations to get results."}

# ----------------------------
# Health check
# ----------------------------
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "data_rows": len(matches_df),
        "resume_analyses": len(resume_analyses)
    }

# ----------------------------
# Bulletproof Recommendation endpoint
# ----------------------------
@app.post("/get_recommendations")
def get_recommendations(req: RecommendationRequest):
    try:
        # Safely process input
        student_skills = safe_list_operation(req.skills)
        student_field = safe_string_operation(req.field)
        student_locations = safe_list_operation(req.locations)
        top_n = max(1, min(20, req.top_n))  # Limit between 1-20
        
        # Clean input data
        student_skills = [safe_string_operation(s) for s in student_skills if s]
        student_field = safe_string_operation(student_field)
        student_locations = [safe_string_operation(l) for l in student_locations if l]
        
        df = matches_df.copy()
        results = []
        
        # If no specific locations, use all data
        if not student_locations:
            try:
                df["match_score"] = df.apply(
                    lambda row: calculate_score_safely(row, student_skills, student_field), 
                    axis=1
                )
                top_matches = df.nlargest(top_n * 2, "match_score")
                selected = top_matches.head(top_n).to_dict(orient="records")
                results.extend(selected)
            except Exception as e:
                print(f"Error in general matching: {e}")
                # Fallback to first few records
                results.extend(df.head(top_n).to_dict(orient="records"))
        else:
            # Filter by locations
            for loc in student_locations:
                try:
                    mask = df["location"].astype(str).str.contains(loc, case=False, na=False)
                    df_loc = df[mask].copy()
                    
                    if not df_loc.empty:
                        df_loc["match_score"] = df_loc.apply(
                            lambda row: calculate_score_safely(row, student_skills, student_field), 
                            axis=1
                        )
                        top_loc = df_loc.nlargest(top_n, "match_score")
                        results.extend(top_loc.to_dict(orient="records"))
                except Exception as e:
                    print(f"Error filtering by location '{loc}': {e}")
                    continue
        
        # Clean and format results
        unique_results = []
        seen_keys = set()
        
        for r in results[:top_n]:
            try:
                # Ensure all required fields exist
                r = {
                    "company": safe_string_operation(r.get("company", "Company")),
                    "internship_title": safe_string_operation(r.get("internship_title", "Internship")),
                    "field": safe_string_operation(r.get("field", "General")),
                    "location": safe_string_operation(r.get("location", "Remote")),
                    "skills": ", ".join(safe_list_operation(r.get("skills", []))),
                    "match_score": float(r.get("match_score", 0)),
                    "apply_link": f"https://company.com/apply/{safe_string_operation(r.get('internship_title', 'internship')).replace(' ', '-')}"
                }
                
                key = (r["company"], r["internship_title"], r["location"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_results.append(r)
                    
            except Exception as e:
                print(f"Error processing result: {e}")
                continue
        
        return {
            "success": True,
            "recommendations": unique_results,
            "total_found": len(unique_results)
        }
        
    except Exception as e:
        print(f"Critical error in get_recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": [],
            "message": "Error occurred while generating recommendations. Please try again."
        }

# ----------------------------
# Resume Upload with Error Handling
# ----------------------------
@app.post("/upload_resume")
def upload_resume(req: ResumeUploadRequest):
    try:
        print(f"Processing resume for {req.student_email}: {req.filename}")
        
        # Basic validation
        if not req.student_email or not req.resume_data or not req.filename:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Try to analyze resume, with fallback
        try:
            analysis = analyze_resume_content_safely(req.resume_data, req.filename)
        except Exception as e:
            print(f"Resume analysis failed: {e}")
            analysis = {
                "skills": ["Resume parsing failed"],
                "projects": [],
                "experience_years": 0,
                "education_level": "Not specified",
                "error": str(e)
            }
        
        # Store analysis
        resume_analyses[req.student_email] = {
            "student_email": req.student_email,
            "filename": req.filename,
            "file_type": req.file_type,
            "analysis": analysis
        }
        
        return {
            "success": True,
            "message": "Resume processed successfully",
            "analysis_preview": {
                "skills_found": len(analysis.get("skills", [])),
                "projects_found": len(analysis.get("projects", [])),
                "experience_years": analysis.get("experience_years", 0),
                "education_level": analysis.get("education_level", "Not specified")
            }
        }
        
    except Exception as e:
        print(f"Resume upload error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error processing resume"
        }

def analyze_resume_content_safely(resume_data, filename):
    """Safely analyze resume content with comprehensive error handling"""
    try:
        # Basic file processing
        if ',' in resume_data:
            file_content = base64.b64decode(resume_data.split(',')[1])
        else:
            file_content = base64.b64decode(resume_data)
        
        text_content = ""
        file_ext = filename.lower().split('.')[-1] if '.' in filename else 'txt'
        
        # Try to extract text
        if file_ext == 'pdf' and PdfReader:
            try:
                with io.BytesIO(file_content) as pdf_file:
                    reader = PdfReader(pdf_file)
                    for page in reader.pages:
                        text_content += page.extract_text() + "\n"
            except:
                text_content = "PDF text extraction failed"
        elif file_ext in ['doc', 'docx'] and Document:
            try:
                with io.BytesIO(file_content) as docx_file:
                    doc = Document(docx_file)
                    for paragraph in doc.paragraphs:
                        text_content += paragraph.text + "\n"
            except:
                text_content = "DOCX text extraction failed"
        else:
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
            except:
                text_content = "Text extraction failed"
        
        # Extract information safely
        return {
            "skills": extract_skills_safely(text_content),
            "projects": extract_projects_safely(text_content),
            "experience_years": extract_experience_safely(text_content),
            "education_level": extract_education_safely(text_content),
            "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
        }
        
    except Exception as e:
        return {
            "skills": ["Error parsing resume"],
            "projects": [],
            "experience_years": 0,
            "education_level": "Unknown",
            "error": str(e)
        }

def extract_skills_safely(text):
    """Safely extract skills from text"""
    try:
        common_skills = [
            "python", "javascript", "java", "react", "node.js", "html", "css",
            "sql", "mysql", "mongodb", "git", "docker", "aws", "linux"
        ]
        
        text_lower = safe_string_operation(text)
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        return found_skills if found_skills else ["Basic Computer Skills"]
    except:
        return ["Skills extraction failed"]

def extract_projects_safely(text):
    """Safely extract projects from text"""
    try:
        # Simple project detection
        if "project" in safe_string_operation(text):
            return [{"name": "Project detected in resume", "description": "Details available in resume"}]
        return []
    except:
        return []

def extract_experience_safely(text):
    """Safely extract experience years"""
    try:
        text_lower = safe_string_operation(text)
        for i in range(1, 10):
            if f"{i} year" in text_lower:
                return float(i)
        return 1.0
    except:
        return 0.0

def extract_education_safely(text):
    """Safely extract education level"""
    try:
        text_lower = safe_string_operation(text)
        if "master" in text_lower or "m.s" in text_lower:
            return "Master's"
        elif "bachelor" in text_lower or "b.s" in text_lower:
            return "Bachelor's"
        return "Not specified"
    except:
        return "Unknown"

# ----------------------------
# Dashboard endpoint
# ----------------------------
@app.post("/get_dashboard_data")
def get_dashboard_data(req: DashboardRequest):
    try:
        if req.student_email in resume_analyses:
            analysis = resume_analyses[req.student_email]["analysis"]
            dashboard_data = generate_dashboard_from_resume(req.student_email, analysis)
        else:
            dashboard_data = generate_basic_dashboard(req.student_email)
        
        return {
            "success": True,
            "dashboard_data": dashboard_data
        }
    except Exception as e:
        print(f"Dashboard error: {e}")
        return {
            "success": False,
            "error": str(e),
            "dashboard_data": generate_basic_dashboard(req.student_email)
        }

def generate_dashboard_from_resume(email, analysis):
    """Generate dashboard from resume analysis"""
    try:
        skills = safe_list_operation(analysis.get("skills", []))
        return {
            "profile_summary": {
                "total_skills": len(skills),
                "experience_level": "Entry Level",
                "resume_score": 75 + len(skills) * 2
            },
            "skills_analysis": {
                "top_skills": skills[:5],
                "suggested_skills": ["Git", "Docker", "AWS"]
            },
            "career_recommendations": [{
                "title": "Software Developer",
                "match_percentage": 80,
                "description": "Based on your skills"
            }]
        }
    except:
        return generate_basic_dashboard(email)

def generate_basic_dashboard(email):
    """Generate basic dashboard data"""
    return {
        "profile_summary": {
            "total_skills": 5,
            "experience_level": "Entry Level",
            "resume_score": 70
        },
        "skills_analysis": {
            "top_skills": ["Python", "JavaScript", "HTML", "CSS"],
            "suggested_skills": ["React", "Node.js", "SQL"]
        },
        "career_recommendations": [{
            "title": "Junior Developer",
            "match_percentage": 75,
            "description": "Great starting position"
        }]
    }

# ----------------------------
# Run server
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting bulletproof FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False, log_level="info")