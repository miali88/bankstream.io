import { SignUp } from "@clerk/remix";

export default function SignUpPageRoute() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <SignUp />
    </div>
  );
}
