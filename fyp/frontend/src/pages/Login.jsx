import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Couldn't sign in. Check your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1
            className="text-4xl text-ink"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Athenaeum
          </h1>
          <p className="text-ink-soft text-sm mt-2 font-mono">
            sign in to the reading room
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-card border border-rule rounded-sm p-8 space-y-5"
        >
          {error && (
            <div className="text-sm text-danger border border-danger/30 bg-danger/5 px-3 py-2 rounded-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-xs uppercase tracking-wide text-ink-soft mb-1.5 font-mono">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-rule rounded-sm bg-paper focus:outline-none focus:ring-2 focus:ring-lamp"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-ink-soft mb-1.5 font-mono">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-rule rounded-sm bg-paper focus:outline-none focus:ring-2 focus:ring-lamp"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-lamp hover:bg-lamp-dark text-paper py-2.5 rounded-sm transition-colors disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-center text-sm text-ink-soft mt-6">
          New here?{" "}
          <Link to="/register" className="text-lamp-dark underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
