import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import Matches from './components/Matches'
import ColdEmail from './components/ColdEmail'
import Tracker from './components/Tracker'
import LandingPage from './components/LandingPage'
import Login from './components/Login'
import Signup from './components/Signup'
import AppLayout from './components/layout/AppLayout'
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
              <AppLayout>
                <Onboarding />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/preferences"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Preferences />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/matches"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Matches />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/cold-email"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ColdEmail />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tracker"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Tracker />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/images"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Images />
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
