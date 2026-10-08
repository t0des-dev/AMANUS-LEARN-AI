import React from "react";
import { RegisterForm } from "../../features/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4 py-12">
      <RegisterForm />
    </div>
  );
}
