import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import Matches from './components/Matches'
import LandingPage from './components/LandingPage'
import Login from './components/Login'
import Signup from './components/Signup'
import Onboarding from './pages/Onboarding'
import Preferences from './pages/Preferences'
import Images from './pages/Images'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/preferences"
          element={
            <ProtectedRoute>
              <Preferences />
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
        <Route
          path="/images"
          element={
            <ProtectedRoute>
              <Images />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
