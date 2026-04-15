import { useNavigate } from 'react-router-dom'
import ResumeUploader from './ResumeUploader'
import Preferences from './preferences'

function Home() {
  const navigate = useNavigate()

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <button onClick={() => navigate('/matches')}>
          View Matches
        </button>
      </div>
      <ResumeUploader />
      <hr />
      <Preferences />
    </>
  )
}

export default Home
      