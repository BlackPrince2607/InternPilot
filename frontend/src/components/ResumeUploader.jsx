import { useState } from 'react'
import axios from 'axios'

function ResumeUploader() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [resumeId, setResumeId] = useState(null)
  const [parsedData, setParsedData] = useState(null)
  const [error, setError] = useState('')

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile)
      setError('')
    } else {
      setError('Please select a PDF file')
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setError('')

    try {
      // Step 1: Upload file
      const formData = new FormData()
      formData.append('file', file)

      const uploadRes = await axios.post(`${API_URL}/resumes/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setResumeId(uploadRes.data.resume_id)
      setUploading(false)

      // Step 2: Parse resume
      setParsing(true)
      const parseRes = await axios.post(
        `${API_URL}/resumes/parse/${uploadRes.data.resume_id}`
      )

      setParsedData(parseRes.data.parsed_data)
      setParsing(false)

    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
      setUploading(false)
      setParsing(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Upload Your Resume</h2>

      <div style={{ marginBottom: '20px' }}>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          style={{ marginBottom: '10px' }}
        />
        <br />
        <button
          onClick={handleUpload}
          disabled={!file || uploading || parsing}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: uploading || parsing ? 'not-allowed' : 'pointer'
          }}
        >
          {uploading ? 'Uploading...' : parsing ? 'Parsing...' : 'Upload & Parse'}
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {parsedData && (
        <div style={{ backgroundColor: '#f5f5f5', padding: '20px', borderRadius: '5px' }}>
          <h3>✅ Resume Parsed Successfully!</h3>

          <div style={{ marginTop: '20px' }}>
            <h4>Personal Info:</h4>
            <p><strong>Name:</strong> {parsedData.name}</p>
            <p><strong>Email:</strong> {parsedData.email}</p>
            <p><strong>College:</strong> {parsedData.college}</p>
            <p><strong>Graduation Year:</strong> {parsedData.graduation_year}</p>
          </div>

          <div style={{ marginTop: '20px' }}>
            <h4>Skills:</h4>
            {parsedData.skills && (
              <>
                <p><strong>Languages:</strong> {parsedData.skills.languages?.join(', ')}</p>
                <p><strong>Frameworks:</strong> {parsedData.skills.frameworks?.join(', ')}</p>
                <p><strong>Tools:</strong> {parsedData.skills.tools?.join(', ')}</p>
              </>
            )}
          </div>

          <div style={{ marginTop: '20px' }}>
            <h4>Projects:</h4>
            {parsedData.projects?.map((project, idx) => (
              <div key={idx} style={{ marginBottom: '15px', paddingLeft: '10px', borderLeft: '3px solid #007bff' }}>
                <p><strong>{project.name}</strong></p>
                <p>{project.description}</p>
                <p><em>Tech: {project.technologies?.join(', ')}</em></p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ResumeUploader