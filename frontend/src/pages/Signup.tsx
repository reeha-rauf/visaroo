import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCategories } from "../api/categories";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const { signup } = useAuth();
  const categories = useCategories();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [visa, setVisa] = useState("OPT");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await signup(email, username, password, visa);
      navigate("/onboarding");  // new users set up their full profile first
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Could not create account.");
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <h2>Join Visaroo 🦘</h2>
      <p className="muted">A community for international students and visa holders.</p>
      <form onSubmit={submit} className="card">
        {error && <div className="warn">{error}</div>}
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Password (min 8 chars)</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        <label>Your visa category</label>
        <select value={visa} onChange={(e) => setVisa(e.target.value)}>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <button className="btn" type="submit">Create account</button>
      </form>
    </div>
  );
}
