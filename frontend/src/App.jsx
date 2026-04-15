import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import Login from './components/Login'
import Signup from './components/Signup'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './components/Home'
import Matches from './components/Matches'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <h1>InternPilot AI</h1>

        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/matches"
            element={
              <ProtectedRoute>
                <Matches />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  )
}

export default App
