import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, createContext, useContext } from 'react';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SessionMonitorPage from './pages/SessionMonitorPage';
import CasesPage from './pages/CasesPage';
import PlayersPage from './pages/PlayersPage';
import AlertsPage from './pages/AlertsPage';

interface AuthCtx {
  token: string | null;
  user: { username: string; role: string } | null;
  login: (token: string, user: { username: string; role: string }) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthCtx>({
  token: null,
  user: null,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('access_token')
  );
  const [user, setUser] = useState<{ username: string; role: string } | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (t: string, u: { username: string; role: string }) => {
    setToken(t);
    setUser(u);
    localStorage.setItem('access_token', t);
    localStorage.setItem('user', JSON.stringify(u));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="sessions" element={<SessionMonitorPage />} />
            <Route path="cases" element={<CasesPage />} />
            <Route path="players" element={<PlayersPage />} />
            <Route path="alerts" element={<AlertsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}
