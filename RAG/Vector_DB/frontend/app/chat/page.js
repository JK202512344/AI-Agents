"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { sendMessage } from "@/lib/api";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
  const router = useRouter();

  const [user, setUser] = useState(null);
  const [role, setRole] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // ================= AUTH CHECK =================
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const storedPassword = localStorage.getItem("password");
    const storedRole = localStorage.getItem("role");

    if (!storedUser || !storedPassword) {
      router.push("/login");
      return;
    }

    setUser(storedUser);
    setRole(storedRole);

    setMessages([
      {
        role: "assistant",
        text: "Welcome! Ask anything about FinSolve Technologies.",
      },
    ]);
  }, []);

  // ================= ROLE → COLLECTIONS =================
  const getCollections = (role) => {
    const map = {
      finance: ["finance", "general"],
      engineering: ["engineering", "general"],
      marketing: ["marketing", "general"],
      hr: ["hr", "general"],
      c_level: ["all"],
      admin: ["all"],
    };

    return map[role] || [];
  };

  // ================= SEND MESSAGE =================
  const handleSend = async () => {
    if (!input.trim()) return;

    const username = localStorage.getItem("user");
    const password = localStorage.getItem("password");

    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);

    setInput("");
    setLoading(true);

    try {
      const res = await sendMessage(input, username, password);

      const botMsg = {
        role: "assistant",
        text: res.answer || res.error || "No response",
        route: res.route,
        guardrail: res.guardrail_triggered || false,
        sources: res.sources || [],
        collections: res.collections || [],
        isError: !!res.error,
      };

      setMessages((prev) => [...prev, botMsg]);

    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Server error", isError: true },
      ]);
    }

    setLoading(false);
  };

  // ================= LOGOUT =================
  const logout = () => {
    localStorage.clear();
    router.push("/login");
  };

  // ================= UI =================
  return (
    <div className="flex h-screen">

      {/* ================= SIDEBAR ================= */}
      <div className="w-72 bg-black/40 border-r border-gray-800 p-6 flex flex-col justify-between">

        <div>
          <h1 className="text-2xl font-bold mb-6">AI Assistant</h1>

          <div className="space-y-4 text-sm">

            <div className="glass p-3">
              <p className="text-gray-400">User</p>
              <p className="font-semibold">{user}</p>
            </div>

            <div className="glass p-3">
              <p className="text-gray-400">Role</p>
              <p className="font-semibold text-indigo-400">{role}</p>
            </div>

            <div className="glass p-3">
              <p className="text-gray-400">Collections Access</p>
              <p className="text-sm">
                {getCollections(role).join(", ")}
              </p>
            </div>

          </div>
        </div>

        <div className="space-y-2">

          {role === "admin" && (
            <button
              onClick={() => router.push("/admin")}
              className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-xl text-sm w-full"
            >
              Admin Panel
            </button>
          )}

          <button
            onClick={logout}
            className="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-xl text-sm w-full"
          >
            Logout
          </button>

        </div>
      </div>

      {/* ================= CHAT ================= */}
      <div className="flex-1 flex flex-col">

        {/* HEADER */}
        <div className="border-b border-gray-800 p-4">
          <h2 className="text-lg font-semibold">
            Enterprise Knowledge Chat
          </h2>
        </div>

        {/* ================= MESSAGES ================= */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`max-w-2xl ${
                msg.role === "user" ? "ml-auto text-right" : ""
              }`}
            >
              <div
                className={`p-4 rounded-2xl ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white inline-block"
                    : "glass inline-block"
                }`}
              >
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>

              {/* ===== ASSISTANT META ===== */}
              {msg.role === "assistant" && (
                <div className="text-xs mt-2 space-y-2">

                  {/* ROUTE + ROLE */}
                  {msg.route && (
                    <div className="flex gap-2">
                      <span className="bg-indigo-500/20 text-indigo-300 px-2 py-1 rounded">
                        {msg.route}
                      </span>

                      <span className="bg-gray-700/40 text-gray-300 px-2 py-1 rounded">
                        {role}
                      </span>
                    </div>
                  )}

                  {/* SOURCES */}
                  {msg.sources?.length > 0 && (
                    <div className="text-gray-400">
                      📚 Sources: {msg.sources.join(", ")}
                    </div>
                  )}

                  {/* COLLECTIONS */}
                  {msg.collections?.length > 0 && (
                    <div className="text-gray-500">
                      Collections: {msg.collections.join(", ")}
                    </div>
                  )}

                  {/* GUARDRAIL */}
                  {msg.guardrail && (
                    <div className="text-yellow-400">
                      ⚠️ Guardrail triggered (input/output filtered)
                    </div>
                  )}

                  {/* RBAC ERROR */}
                  {msg.isError && (
                    <div className="text-red-400">
                      🚫 Access restricted or invalid query
                    </div>
                  )}

                </div>
              )}

            </div>
          ))}

          {loading && (
            <div className="text-gray-400 text-sm">
              AI is thinking...
            </div>
          )}

        </div>

        {/* ================= INPUT ================= */}
        <div className="p-4 border-t border-gray-800 flex gap-3">
          <input
            className="flex-1 px-4 py-3 rounded-xl bg-gray-900 border border-gray-700"
            placeholder="Ask about documents..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <button
            onClick={handleSend}
            className="bg-indigo-600 hover:bg-indigo-500 px-6 py-2 rounded-xl text-white"
          >
            Send
          </button>
        </div>

      </div>
    </div>
  );
}
