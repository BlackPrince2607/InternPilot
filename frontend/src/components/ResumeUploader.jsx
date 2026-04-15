import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'

function ResumeUploader() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [parsedData, setParsedData] = useState(null)
  const [error, setError] = useState('')
  const { isAuthenticated, signOut, user } = useAuth()

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
    if (!isAuthenticated) {
      setError('Please log in before uploading your resume')
      return
    }

    if (!file) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setParsing(false)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const uploadRes = await api.post('/resumes/upload', formData)

      setUploading(false)
      setParsing(true)

      const parseRes = await api.post(`/resumes/parse/${uploadRes.data.resume_id}`)

      setParsedData(parseRes.data.parsed_data)
      setParsing(false)
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Your session expired. Please log in again.')
      } else {
        setError(err.response?.data?.detail || 'Upload failed')
      }
      setUploading(false)
      setParsing(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Upload Your Resume</h2>
      <p style={{ color: '#555' }}>
        Logged in as: {user?.email || 'Unknown user'}
      </p>

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
            cursor: uploading || parsing ? 'not-allowed' : 'pointer',
          }}
        >
          {uploading ? 'Uploading...' : parsing ? 'Parsing...' : 'Upload & Parse'}
        </button>
        <button onClick={() => signOut()} style={{ marginLeft: '10px' }}>
          Logout
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {parsedData && (
        <div style={{ backgroundColor: '#f5f5f5', padding: '20px', borderRadius: '5px' }}>
          <h3>Resume parsed successfully.</h3>

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
                <p><strong>Databases:</strong> {parsedData.skills.databases?.join(', ')}</p>
              </>
            )}
          </div>

          <div style={{ marginTop: '20px' }}>
            <h4>Projects:</h4>
            {parsedData.projects?.map((project, idx) => (
              <div
                key={idx}
                style={{ marginBottom: '15px', paddingLeft: '10px', borderLeft: '3px solid #007bff' }}
              >
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
