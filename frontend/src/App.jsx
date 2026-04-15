import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import Login from './components/Login'
import Signup from './components/Signup'
import ProtectedRoute from './components/ProtectedRoute'
import ResumeUploader from './components/ResumeUploader'
import Preferences from './components/preferences'

import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <h1>InternPilot AI</h1>

        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected route */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <>
                  <ResumeUploader />
                  <hr />
                  <Preferences />
                </>
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  )
}

export default App