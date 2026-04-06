"use client";

import { useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const login = async () => {
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/login",
        {},
        { auth: { username, password } }
      );

      localStorage.setItem("user", username);
      localStorage.setItem("password", password);
      localStorage.setItem("role", res.data.role);

      router.push(res.data.role === "admin" ? "/admin" : "/chat");
    } catch {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="h-screen flex bg-gradient-to-r from-[#0f172a] to-[#1e293b] text-white">

      {/* LEFT SIDE (CLEAN STORY SECTION) */}
      <div className="w-1/2 flex items-center justify-center px-16">

        <div className="max-w-xl space-y-6">

          <h1 className="text-4xl font-bold leading-tight">
            FinSolve Technologies
          </h1>

          <p className="text-gray-300 leading-7">
            A rapidly growing fintech company serving banking, insurance,
            and investment clients with large-scale internal knowledge systems.
          </p>

          <p className="text-gray-400 leading-7">
            As the organization scaled, its knowledge base became fragmented —
            spread across financial reports, HR policies, engineering docs,
            and marketing assets.
          </p>

          <p className="text-gray-400 leading-7">
            Employees now spend hours searching for information, with no access
            control — exposing sensitive data across departments.
          </p>

          <div className="border-l-4 border-indigo-500 pl-4 space-y-3">
            <p className="text-indigo-400 font-semibold">
              Introducing FinBot
            </p>

            <ul className="list-disc ml-5 text-gray-300 space-y-2">
              <li>Ask questions in natural language</li>
              <li>Get accurate answers from documents</li>
              <li>Access only what your role allows (RBAC)</li>
            </ul>
          </div>

          <p className="text-gray-500 text-sm italic">
            Built a secure, intelligent enterprise knowledge system.
          </p>

        </div>

      </div>

      {/* RIGHT SIDE */}
      <div className="w-1/2 flex items-center justify-center">

        <div className="space-y-6">

          {/* LOGIN CARD */}
          <div className="bg-gray-800/80 backdrop-blur p-8 rounded-xl w-[360px] shadow-xl border border-gray-700">

            <h2 className="text-2xl font-bold mb-6 text-center">
              FinSolve Login
            </h2>

            <input
              placeholder="Username"
              className="w-full mb-3 p-3 bg-gray-900 rounded outline-none focus:ring-2 focus:ring-indigo-500"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              className="w-full mb-4 p-3 bg-gray-900 rounded outline-none focus:ring-2 focus:ring-indigo-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button
              onClick={login}
              className="w-full bg-indigo-600 py-3 rounded hover:bg-indigo-500 transition"
            >
              Login
            </button>
          </div>

          {/* AVAILABLE USERS (MOVED BELOW LOGIN ✅) */}
          <div className="text-center text-gray-300">

            <p className="text-indigo-400 mb-2 tracking-wider font-semibold">
              AVAILABLE USERS
            </p>

            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <span>engineeruser</span>
              <span>financeuser</span>
              <span>marketinguser</span>
              <span>hruser</span>
              <span>admin</span>
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
