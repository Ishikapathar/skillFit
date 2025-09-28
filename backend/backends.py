import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from fuzzywuzzy import fuzz
import random
from pathlib import Path

# ----------------------------
# Load dataset
# ----------------------------
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "student_internship_matches_stratified (1).csv"
matches_df = pd.read_csv(DATA_FILE)

# Normalize column names
matches_df.columns = [c.strip().lower() for c in matches_df.columns]

# Ensure skills column is list
matches_df["skills"] = matches_df["skills"].fillna("").apply(
    lambda x: [s.strip().lower() for s in str(x).split(",")] if x else []
)

# ----------------------------
# FastAPI setup
# ----------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Request model
# ----------------------------
class RecommendationRequest(BaseModel):
    name: str
    course: Optional[str] = None
    skills: List[str] = []
    locations: List[str] = []
    field: str = ""
    top_n: int = 5

# ----------------------------
# Root check
# ----------------------------
@app.get("/")
def root():
    return {"message": "FastAPI server is running. Use /get_recommendations to get results."}

# ----------------------------
# Recommendation endpoint
# ----------------------------
@app.post("/get_recommendations")
def get_recommendations(req: RecommendationRequest):
    student_skills = [s.lower().strip() for s in req.skills]
    student_field = req.field.lower().strip()
    student_locations = [l.lower().strip() for l in req.locations]

    df = matches_df.copy()

    # ---- Scoring logic ----
    def calculate_score(row):
        score = 0
        # Skills match (weight 0.6)
        if student_skills:
            match_count = len(set(student_skills) & set(row["skills"]))
            score += (match_count / max(len(student_skills), 1)) * 0.6
        # Field fuzzy match (weight 0.4)
        if student_field:
            similarity = fuzz.ratio(row["field"].lower(), student_field)
            if similarity >= 80:
                score += 0.4
        return round(score, 3)

    results = []

    # Handle each location separately
    for loc in student_locations:
        df_loc = df[df["location"].str.contains(loc, case=False, na=False)]
        if df_loc.empty:
            continue
        df_loc = df_loc.copy()
        df_loc["match_score"] = df_loc.apply(calculate_score, axis=1)
        # Sort by score
        top_loc = df_loc.sort_values(by="match_score", ascending=False)
        # Pick up to top_n
        selected = top_loc.head(req.top_n).to_dict(orient="records")
        # If less than top_n, fill randomly
        if len(selected) < req.top_n:
            remaining = df_loc.loc[~df_loc.apply(lambda r: (r['company'], r['internship_title'], r['location']) in 
                                                 [(s['company'], s['internship_title'], s['location']) for s in selected], axis=1)]
            if not remaining.empty:
                extra = remaining.sample(min(req.top_n - len(selected), len(remaining))).to_dict(orient="records")
                selected.extend(extra)
        results.extend(selected)

    # Remove duplicates using company + internship_title + location
    seen_keys = set()
    unique_recs = []
    for r in results:
        key = (r['company'], r['internship_title'], r['location'])
        if key not in seen_keys:
            seen_keys.add(key)
            if isinstance(r["skills"], list):
                r["skills"] = ", ".join(r["skills"])
            r["apply_link"] = f"https://company.com/apply/{r['internship_title'].replace(' ', '-')}"
            unique_recs.append(r)

    return {"recommendations": unique_recs}