import { useNavigate } from 'react-router-dom'
import SignInFlow from "./ui/sign-in-flow";

export default function Signup() {
  const navigate = useNavigate();

  const handleSubmit = () => {
    localStorage.setItem("auth", "true");
    navigate("/app");
  };

  return <SignInFlow mode="signup" onSubmit={handleSubmit} />;
}
