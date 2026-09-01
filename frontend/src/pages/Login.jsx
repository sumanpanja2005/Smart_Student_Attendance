import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/Card';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { ErrorMessage } from '../components/ErrorMessage';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, Lock, Mail } from 'lucide-react';

export const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password) {
      setError('Please enter both your email address and password.');
      return;
    }

    setLoading(true);
    try {
      const user = await login(email, password);
      
      // Redirect based on role or intended destination
      const from = location.state?.from?.pathname;
      if (from) {
        navigate(from, { replace: true });
        return;
      }

      const roleRoutes = {
        ADMIN: '/admin',
        TEACHER: '/teacher',
        STUDENT: '/student',
      };
      navigate(roleRoutes[user.role] || '/', { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid login credentials. Please check your email and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[75vh] py-8">
      <Card className="w-full max-w-md shadow-lg border-gray-200">
        <CardHeader className="text-center justify-center flex-col py-6 bg-slate-50/50">
          <div className="p-3 bg-indigo-600 rounded-2xl text-white shadow-sm mb-3">
            <GraduationCap className="w-7 h-7" />
          </div>
          <CardTitle className="text-xl">Account Login</CardTitle>
          <CardDescription>
            AI-Based Smart Attendance & Student Analytics System
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-6">
            {error && <ErrorMessage title="Login Failed" message={error} />}

            <Input
              label="Email Address"
              type="email"
              placeholder="admin@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={Mail}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={Lock}
              required
            />
          </CardContent>

          <CardFooter className="flex-col gap-3 py-4">
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={loading}
            >
              Sign In
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default Login;
