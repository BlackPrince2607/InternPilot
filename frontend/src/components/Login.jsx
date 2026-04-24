import { useNavigate } from 'react-router-dom'
import SignInFlow from "./ui/sign-in-flow";

export default function Login() {
  const navigate = useNavigate();

  const handleSubmit = () => {
    localStorage.setItem("auth", "true");
    navigate("/app");
  };

  return <SignInFlow mode="login" onSubmit={handleSubmit} />;
}
