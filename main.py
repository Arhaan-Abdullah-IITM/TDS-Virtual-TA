from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

# Load discourse data
with open("discourse_posts.json", "r", encoding="utf-8") as f:
    discourse_posts = json.load(f)

# Load TDS pages
tds_pages_md_dir = "tds_pages_md"
tds_pages = {}
for filename in os.listdir(tds_pages_md_dir):
    if filename.endswith(".md"):
        with open(os.path.join(tds_pages_md_dir, filename), "r", encoding="utf-8") as f:
            tds_pages[filename] = f.read()

# Request format
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64 image string (optional)

# Response format
class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

@app.post("/api/", response_model=AnswerResponse)
def get_answer(req: QuestionRequest):
    q = req.question.lower()
    
    # Search discourse posts
    matched_posts = [
        post for post in discourse_posts
        if q in post["content"].lower() or q in (post["topic_title"] or "").lower()
    ]
    
    # Search TDS pages
    matched_pages = [
        {"filename": fn, "content": content}
        for fn, content in tds_pages.items()
        if q in content.lower()
    ]
    
    # Compose answer
    answer_lines = []
    links = []
    
    if matched_posts:
        answer_lines.append("Here’s what I found on Discourse:")
        for post in matched_posts[:2]:
            answer_lines.append(post["content"][:200])  # snippet
            links.append({"url": post["url"], "text": post["topic_title"]})
    
    if matched_pages:
        answer_lines.append("\nHere’s what I found in course material:")
        for page in matched_pages[:2]:
            answer_lines.append(f"Matched in: {page['filename']}")
            links.append({"url": "https://tds.s-anand.net/#/", "text": page['filename']})
    
    if not answer_lines:
        raise HTTPException(status_code=404, detail="No relevant answer found.")
    
    return AnswerResponse(
        answer="\n".join(answer_lines),
        links=[Link(**l) for l in links]
    )
