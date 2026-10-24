from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
import pg8000.native
import json
import os
from fastapi.middleware.cors import CORSMiddleware
# New Gemini SDK Imports
from google import genai
from google.genai import types


# Initialize Gemini Client (Paste your AQ. key here!)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the API
app = FastAPI(title="AICTE Smart Automation Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Allows your React app to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 1. Database Connection Helper
def get_db():
    try:
        return pg8000.native.Connection(
            database="KRATOS_aicte",
            user="postgres",
            password="#Qazwsx123edc?", # Keep this updated
            host="127.0.0.1",
            port=5432
        )
    except Exception as e:
        print(f"DB Error: {e}")
        return None

# 2. Basic Health Check Route
@app.get("/")
async def root():
    return {"status": "success", "message": "Backend engine is live and ready."}

# 3. Fetch Applications for the Regional Officer Dashboard
@app.get("/applications/pending")
async def get_pending_applications():
    conn = get_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        query = "SELECT id, institution_id, status, submission_date FROM applications WHERE status = 'submitted';"
        rows = conn.run(query)
        conn.close()
        
        applications = [{"id": row[0], "institution_id": row[1], "status": row[2], "date": row[3]} for row in rows]
        return {"data": applications}
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# 4. Automated Scrutiny & Document Upload (POSTGRESQL SYNTAX FIXED)
@app.post("/upload-document/")
async def upload_document(
    application_id: int = Form(...),
    user_id: int = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...)
):
    conn = get_db()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # Step 1: Save the file locally so Gemini can read it
        file_content = await file.read()
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file_content)
            
        # Step 2: Upload to Gemini using the new SDK
        gemini_file = client.files.upload(file=temp_file_path)
        
        prompt = """
        Analyze this AICTE document. Extract the following data in strict JSON format. 
        Do not include any markdown formatting.
        {
          "detected_expiry_date": "YYYY-MM-DD" (or null if not found),
          "is_valid": true/false (true if expiry is in the future),
          "faculty_count": integer (if applicable, else 0)
        }
        """
        
        # Call Gemini 3.8 Flash
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[gemini_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        # Step 3: Parse the AI's JSON response
        ai_data = json.loads(response.text.strip())
        mock_expiry_date = ai_data.get("detected_expiry_date")
        file_storage_url = f"/secure_vault/{file.filename}" 

        # Step 4: Insert into PostgreSQL (Fixed syntax for pg8000)
        doc_query = """
            INSERT INTO documents (application_id, doc_type, file_url, extracted_data, expiry_date)
            VALUES (:app_id, :type, :url, :data, :expiry) RETURNING id;
        """
        db_json_data = json.dumps(ai_data) 
        conn.run(doc_query, 
                 app_id=application_id, 
                 type=doc_type, 
                 url=file_storage_url, 
                 data=db_json_data, 
                 expiry=mock_expiry_date)
        
        # Step 5: Write to the immutable Audit Trail (Fixed syntax for pg8000)
        audit_query = """
            INSERT INTO audit_logs (application_id, user_id, action, comments)
            VALUES (:app_id, :user, :act, :com);
        """
        audit_action = f"{doc_type} Uploaded & Auto-Scrutinized"
        conn.run(audit_query, 
                 app_id=application_id, 
                 user=user_id, 
                 act=audit_action, 
                 com=f"AI extracted validity: {ai_data.get('is_valid')}")
        
        # Cleanup local and cloud files
        conn.close()
        os.remove(temp_file_path)
        client.files.delete(name=gemini_file.name)
        
        return {
            "status": "success", 
            "message": f"{file.filename} processed successfully.",
            "extracted_data": ai_data
        }

    except Exception as e:
        if conn:
            conn.close()
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))