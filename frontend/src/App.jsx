import { useState } from 'react'

function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a file first.");

    setLoading(true);
    
    // Package the exact same data we used in Swagger UI
    const formData = new FormData();
    formData.append("application_id", 1);
    formData.append("user_id", 1);
    formData.append("doc_type", "Lease Agreement");
    formData.append("file", file);

    try {
      // Send it to your FastAPI backend
      const response = await fetch("http://127.0.0.1:8000/upload-document/", {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      alert("Upload failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "3rem", fontFamily: "sans-serif", maxWidth: "600px", margin: "0 auto" }}>
      <h2>AICTE Document Scrutiny</h2>
      
      <form onSubmit={handleUpload} style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "2rem" }}>
        <input 
          type="file" 
          accept=".pdf" 
          onChange={(e) => setFile(e.target.files[0])} 
          style={{ padding: "0.5rem", border: "1px solid #ccc" }}
        />
        
        <button 
          type="submit" 
          disabled={loading}
          style={{ padding: "0.75rem", backgroundColor: loading ? "#ccc" : "#007bff", color: "white", border: "none", cursor: "pointer", fontWeight: "bold" }}
        >
          {loading ? "Processing with AI..." : "Upload & Analyze Document"}
        </button>
      </form>

      {result && result.extracted_data && (
        <div style={{ marginTop: "2rem", padding: "1.5rem", backgroundColor: "#f8f9fa", border: "1px solid #dee2e6", borderRadius: "4px" }}>
          <h3 style={{ marginTop: 0, color: "#28a745" }}>Verification Successful</h3>
          <p><strong>Faculty Count:</strong> {result.extracted_data.faculty_count}</p>
          <p><strong>Expiry Date:</strong> {result.extracted_data.detected_expiry_date}</p>
          <p><strong>Status:</strong> {result.extracted_data.is_valid ? "Valid" : "Expired"}</p>
        </div>
      )}
    </div>
  )
}

export default App