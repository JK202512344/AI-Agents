"use client";

import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

type DocType = {
  name: string;
  folder?: string;
  chunk_count?: number;
};

type EvalRow = {
  question: string;
  answer: string;
  ground_truth: string;
  answer_correctness: number | null;
  answer_relevancy: number | null;
  faithfulness: number | null;
  context_precision: number | null;
  context_recall: number | null;
};

type EvalSummary = {
  answer_correctness: number | null;
  answer_relevancy: number | null;
  faithfulness: number | null;
  context_precision: number | null;
  context_recall: number | null;
};

type EvalResult = {
  mode: string;
  summary: EvalSummary;
  rows: EvalRow[];
  timestamp?: string;
};

export default function AdminPage() {
  const router = useRouter();

  const [tab, setTab] = useState<"users" | "documents" | "queries" | "evals">("users");

  const [adminUser, setAdminUser] = useState("");
  const [adminPass, setAdminPass] = useState("");

  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [docs, setDocs] = useState<DocType[]>([]);

  // Evals state
  const [evalResults, setEvalResults] = useState<EvalResult | null>(null);
  const [evalMode, setEvalMode] = useState<"full" | "no_guardrails" | "no_structured">("full");
  const [isRunningEval, setIsRunningEval] = useState(false);
  const [evalProgress, setEvalProgress] = useState<string>("");

  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);

  const [files, setFiles] = useState<File[]>([]);
  const [hasNewUpload, setHasNewUpload] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);

  const [message, setMessage] = useState("");

  // Create user
  const [newUser, setNewUser] = useState("");
  const [newPass, setNewPass] = useState("");
  const [newRole, setNewRole] = useState("hr");

  // Reset password
  const [resetUser, setResetUser] = useState("");
  const [resetPass, setResetPass] = useState("");

  // ================= DATE FORMAT =================
  const formatDate = (ts: string) => {
    if (!ts) return "-";
    const d = new Date(ts);
    return d.toLocaleString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  };

  // ================= FETCH FUNCTIONS =================
  const fetchUsers = useCallback(async (u: string, p: string) => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/users", {
        auth: { username: u, password: p },
      });

      const arr = Object.keys(res.data).map((k) => ({
        username: k,
        role: res.data[k].role,
      }));

      setUsers(arr);
      setRoles([...new Set(arr.map((user) => user.role))]);
    } catch (err) {
      console.error("Failed to fetch users:", err);
    }
  }, []);

  const fetchLogs = useCallback(async (u: string, p: string) => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/query-logs", {
        auth: { username: u, password: p },
      });
      setLogs(res.data.logs || []);
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    }
  }, []);

  const fetchDocs = useCallback(async (u: string, p: string) => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/documents", {
        auth: { username: u, password: p },
      });
      setDocs(res.data.documents || []);
    } catch (err) {
      console.error("Failed to fetch docs:", err);
    }
  }, []);

  const fetchEvalResults = useCallback(async () => {
    if (!adminUser || !adminPass) return;
    
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/eval-results", {
        auth: { username: adminUser, password: adminPass },
        params: { mode: evalMode },
      });

      if (res.status === 200 && res.data && res.data.summary) {
        setEvalResults(res.data);
      } else {
        setEvalResults(null);
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        console.log(`No evaluation results found for mode: ${evalMode}`);
      } else {
        console.error("Error fetching eval results:", err);
      }
      setEvalResults(null);
    }
  }, [adminUser, adminPass, evalMode]);

  // ================= INIT =================
  useEffect(() => {
    const user = localStorage.getItem("user");
    const pass = localStorage.getItem("password");
    const role = localStorage.getItem("role");

    if (!user || !pass) {
      router.push("/login");
      return;
    }
    if (role !== "admin") {
      router.push("/chat");
      return;
    }

    setAdminUser(user);
    setAdminPass(pass);

    fetchUsers(user, pass);
    fetchLogs(user, pass);
    fetchDocs(user, pass);
  }, [router, fetchUsers, fetchLogs, fetchDocs]);

  // Clear message when switching tabs
  useEffect(() => {
    setMessage("");
  }, [tab]);

  // Fetch existing eval results when switching to evals tab
  useEffect(() => {
    if (tab === "evals" && adminUser && adminPass) {
      fetchEvalResults();
    }
  }, [tab, adminUser, adminPass, fetchEvalResults]);

  // ================= USER ACTIONS =================
  const createUser = async () => {
    try {
      await axios.post(
        "http://127.0.0.1:8000/admin/create-user",
        {},
        {
          params: { username: newUser, password: newPass, role: newRole },
          auth: { username: adminUser, password: adminPass },
        }
      );

      setMessage(`User "${newUser}" created`);
      setNewUser("");
      setNewPass("");
      fetchUsers(adminUser, adminPass);
    } catch (err) {
      setMessage("Failed to create user");
    }
  };

  const resetPassword = async () => {
    try {
      await axios.post(
        "http://127.0.0.1:8000/admin/reset-password",
        {},
        {
          params: { username: resetUser, new_password: resetPass },
          auth: { username: adminUser, password: adminPass },
        }
      );

      setMessage(`Password reset for "${resetUser}"`);
      setResetUser("");
      setResetPass("");
    } catch (err) {
      setMessage("Failed to reset password");
    }
  };

  const deleteUsers = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/admin/delete-users", null, {
        params: { users: selectedUsers.join(",") },
        auth: { username: adminUser, password: adminPass },
      });

      setMessage(`${selectedUsers.join(", ")} deleted successfully`);
      setSelectedUsers([]);
      fetchUsers(adminUser, adminPass);
    } catch (err) {
      setMessage("Failed to delete users");
    }
  };

  const toggleUser = (u: string) => {
    setSelectedUsers((prev) =>
      prev.includes(u) ? prev.filter((x) => x !== u) : [...prev, u]
    );
  };

  // ================= FILE HANDLING =================
  const handleBrowse = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const uploadDoc = async () => {
    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));

      await axios.post("http://127.0.0.1:8000/admin/upload-doc", form, {
        auth: { username: adminUser, password: adminPass },
      });

      setMessage("Files uploaded successfully");
      setFiles([]);
      setHasNewUpload(true);
      fetchDocs(adminUser, adminPass);
    } catch (err) {
      setMessage("Failed to upload files");
    }
  };

  const reindex = async () => {
    setIsReindexing(true);
    try {
      await axios.post(
        "http://127.0.0.1:8000/admin/reindex",
        {},
        { auth: { username: adminUser, password: adminPass } }
      );

      setHasNewUpload(false);
      setMessage("Reindex completed");
    } catch (err) {
      setMessage("Failed to reindex");
    }
    setIsReindexing(false);
  };

  // ================= EVAL ACTIONS =================
  const runEvaluation = async () => {
    setIsRunningEval(true);
    setEvalProgress("Starting evaluation... This may take several minutes.");
    setEvalResults(null);
    setMessage("");

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/admin/run-eval",
        {},
        {
          params: { mode: evalMode },
          auth: { username: adminUser, password: adminPass },
          timeout: 600000,
        }
      );

      if (res.data && res.data.summary) {
        setEvalResults(res.data);
        setMessage(`Evaluation completed: ${res.data.rows?.length || 0} questions evaluated`);
      } else {
        setMessage("Evaluation completed but no results returned");
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "Unknown error";
      setMessage(`Evaluation failed: ${errorMsg}`);
      console.error("Evaluation error:", err);
    }

    setEvalProgress("");
    setIsRunningEval(false);
  };

  const runAblation = async () => {
    setIsRunningEval(true);
    setEvalProgress("Running ablation study (this may take 15-30 minutes)...");
    setMessage("");

    try {
      await axios.post(
        "http://127.0.0.1:8000/admin/run-ablation",
        {},
        {
          auth: { username: adminUser, password: adminPass },
          timeout: 1800000,
        }
      );

      setMessage("Ablation study completed successfully.");
      await fetchEvalResults();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "Unknown error";
      setMessage(`Ablation failed: ${errorMsg}`);
      console.error("Ablation error:", err);
    }

    setEvalProgress("");
    setIsRunningEval(false);
  };

  // ================= GROUP DOCS =================
  const groupedDocs = docs.reduce((acc: Record<string, DocType[]>, doc) => {
    const folder = doc.folder || "root";
    if (!acc[folder]) acc[folder] = [];
    acc[folder].push(doc);
    return acc;
  }, {});

  const logout = () => {
    localStorage.clear();
    router.push("/login");
  };

  // ================= SCORE COLOR =================
  const getScoreColor = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "text-gray-400";
    if (score >= 0.8) return "text-green-400";
    if (score >= 0.6) return "text-yellow-400";
    return "text-red-400";
  };

  const formatScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "-";
    return (score * 100).toFixed(1) + "%";
  };

  return (
    <div className="p-8 space-y-6 text-white min-h-screen bg-gray-950">
      {/* HEADER */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>

        <div className="flex gap-2">
          <button
            onClick={() => router.push("/chat")}
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded transition"
          >
            Back
          </button>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-500 px-4 py-2 rounded transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* MESSAGE */}
      {message && (
        <div className={`px-4 py-2 rounded ${message.includes("failed") || message.includes("Failed") ? "bg-red-700" : "bg-green-700"}`}>
          {message}
        </div>
      )}

      {/* TABS */}
      <div className="flex gap-6 border-b border-gray-700 pb-2">
        {["users", "documents", "queries", "evals"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t as any)}
            className={`pb-2 transition ${
              tab === t
                ? "border-b-2 border-indigo-500 text-indigo-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      {/* USERS TAB */}
      {tab === "users" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-gray-900 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Create User</h3>
              <input
                placeholder="Username"
                value={newUser}
                onChange={(e) => setNewUser(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              />
              <input
                placeholder="Password"
                type="password"
                value={newPass}
                onChange={(e) => setNewPass(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              />
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              >
                {roles.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
              <button
                onClick={createUser}
                className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded transition"
              >
                Create
              </button>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Reset Password</h3>
              <input
                placeholder="Username"
                value={resetUser}
                onChange={(e) => setResetUser(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              />
              <input
                placeholder="New Password"
                type="password"
                value={resetPass}
                onChange={(e) => setResetPass(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              />
              <button
                onClick={resetPassword}
                className="bg-yellow-600 hover:bg-yellow-500 px-4 py-2 rounded transition"
              >
                Reset
              </button>
            </div>
          </div>

          <div className="bg-gray-900 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">User List</h3>
            {users.map((u, i) => (
              <div
                key={u.username}
                className={`flex justify-between items-center border-b border-gray-700 p-3 ${
                  i % 2 === 0 ? "bg-gray-900" : "bg-gray-800"
                }`}
              >
                <div>
                  <p className="font-medium">{u.username}</p>
                  <p className="text-sm text-gray-400">{u.role}</p>
                </div>
                <input
                  type="checkbox"
                  checked={selectedUsers.includes(u.username)}
                  onChange={() => toggleUser(u.username)}
                  className="w-5 h-5"
                />
              </div>
            ))}

            <button
              onClick={deleteUsers}
              disabled={!selectedUsers.length}
              className="bg-red-600 hover:bg-red-500 mt-4 px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Delete Selected
            </button>
          </div>
        </div>
      )}

      {/* DOCUMENTS TAB */}
      {tab === "documents" && (
        <div className="space-y-6">
          <div className="flex items-center gap-4 flex-wrap">
            <input
              type="file"
              multiple
              id="fileInput"
              onChange={handleBrowse}
              className="hidden"
            />

            <label
              htmlFor="fileInput"
              className="cursor-pointer bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded transition"
            >
              📁 Browse
            </label>

            {files.length > 0 && (
              <span className="text-sm text-gray-300">
                {files.length} file(s) selected
              </span>
            )}

            <button
              onClick={uploadDoc}
              disabled={!files.length}
              className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Upload
            </button>

            <button
              onClick={reindex}
              disabled={!hasNewUpload}
              className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isReindexing ? "Reindexing..." : "Reindex"}
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border border-gray-700 border-collapse">
              <thead>
                <tr className="bg-gray-800">
                  <th className="border border-gray-700 px-4 py-2 text-left">Folder</th>
                  <th className="border border-gray-700 px-4 py-2 text-left">File Name</th>
                  <th className="border border-gray-700 px-4 py-2 text-center">Chunks</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(groupedDocs).map(([folder, files]) =>
                  files.map((file, idx) => (
                    <tr
                      key={`${folder}-${file.name}-${idx}`}
                      className={idx % 2 === 0 ? "bg-gray-900" : "bg-gray-800"}
                    >
                      {idx === 0 && (
                        <td
                          rowSpan={files.length}
                          className="border border-gray-700 px-4 py-2 font-medium"
                        >
                          {folder}
                        </td>
                      )}
                      <td className="border border-gray-700 px-4 py-2">{file.name}</td>
                      <td className="border border-gray-700 px-4 py-2 text-center">
                        {file.chunk_count}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* QUERIES TAB */}
      {tab === "queries" && (
        <div className="bg-gray-900 p-6 rounded-lg overflow-x-auto">
          <table className="w-full border border-gray-700 border-collapse">
            <thead>
              <tr className="bg-gray-800">
                <th className="border border-gray-700 px-3 py-2">User</th>
                <th className="border border-gray-700 px-3 py-2">Role</th>
                <th className="border border-gray-700 px-3 py-2">Query</th>
                <th className="border border-gray-700 px-3 py-2">Route</th>
                <th className="border border-gray-700 px-3 py-2">Date</th>
                <th className="border border-gray-700 px-3 py-2">Guardrail</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l, i) => (
                <tr
                  key={i}
                  className={i % 2 === 0 ? "bg-gray-900" : "bg-gray-800"}
                >
                  <td className="border border-gray-700 px-3 py-2">{l.username}</td>
                  <td className="border border-gray-700 px-3 py-2">{l.role}</td>
                  <td className="border border-gray-700 px-3 py-2 max-w-md truncate">
                    {l.query}
                  </td>
                  <td className="border border-gray-700 px-3 py-2">{l.route}</td>
                  <td className="border border-gray-700 px-3 py-2">
                    {formatDate(l.timestamp)}
                  </td>
                  <td className="border border-gray-700 px-3 py-2 text-center">
                    {l.guardrail ? (
                      <span className="text-red-400">Yes</span>
                    ) : (
                      <span className="text-green-400">No</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* EVALS TAB */}
      {tab === "evals" && (
        <div className="space-y-6">
          {/* Controls */}
          <div className="bg-gray-900 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">RAG Evaluation (RAGAS)</h3>

            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-gray-400">Mode:</label>
                <select
                  value={evalMode}
                  onChange={(e) => {
                    setEvalMode(e.target.value as any);
                    setEvalResults(null);
                  }}
                  className="bg-gray-800 px-3 py-2 rounded"
                  disabled={isRunningEval}
                >
                  <option value="full">Full Pipeline</option>
                  <option value="no_guardrails">No Guardrails</option>
                  <option value="no_structured">No Structured Query</option>
                </select>
              </div>

              <button
                onClick={runEvaluation}
                disabled={isRunningEval}
                className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isRunningEval ? "Running..." : "Run Evaluation"}
              </button>

              <button
                onClick={runAblation}
                disabled={isRunningEval}
                className="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                Run Ablation Study
              </button>

              <button
                onClick={fetchEvalResults}
                disabled={isRunningEval}
                className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded disabled:opacity-50 transition"
              >
                Load Previous Results
              </button>
            </div>

            {evalProgress && (
              <div className="mt-4 text-yellow-400 flex items-center gap-2">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="[w3.org](http://www.w3.org/2000/svg)"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                {evalProgress}
              </div>
            )}
          </div>

          {/* Summary Cards */}
          {evalResults && evalResults.summary && (
            <div className="grid grid-cols-5 gap-4">
              {[
                { key: "answer_correctness", label: "Answer Correctness" },
                { key: "answer_relevancy", label: "Answer Relevancy" },
                { key: "faithfulness", label: "Faithfulness" },
                { key: "context_precision", label: "Context Precision" },
                { key: "context_recall", label: "Context Recall" },
              ].map(({ key, label }) => (
                <div key={key} className="bg-gray-900 p-4 rounded-lg text-center">
                  <p className="text-gray-400 text-sm mb-2">{label}</p>
                  <p
                    className={`text-2xl font-bold ${getScoreColor(
                      evalResults.summary[key as keyof EvalSummary]
                    )}`}
                  >
                    {formatScore(
                      evalResults.summary[key as keyof EvalSummary]
                    )}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Detailed Results Table */}
          {evalResults && evalResults.rows && evalResults.rows.length > 0 && (
            <div className="bg-gray-900 p-6 rounded-lg overflow-x-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">
                  Detailed Results ({evalResults.rows.length} questions)
                </h3>
                {evalResults.timestamp && (
                  <span className="text-sm text-gray-400">
                    Run: {formatDate(evalResults.timestamp)}
                  </span>
                )}
              </div>
              <table className="w-full border border-gray-700 border-collapse text-sm">
                <thead>
                  <tr className="bg-gray-800">
                    <th className="border border-gray-700 px-3 py-2 text-left">Question</th>
                    <th className="border border-gray-700 px-3 py-2 text-center w-24">Correctness</th>
                    <th className="border border-gray-700 px-3 py-2 text-center w-24">Relevancy</th>
                    <th className="border border-gray-700 px-3 py-2 text-center w-24">Faithfulness</th>
                    <th className="border border-gray-700 px-3 py-2 text-center w-24">Precision</th>
                    <th className="border border-gray-700 px-3 py-2 text-center w-24">Recall</th>
                  </tr>
                </thead>
                <tbody>
                  {evalResults.rows.map((row, i) => (
                    <tr
                      key={i}
                      className={i % 2 === 0 ? "bg-gray-900" : "bg-gray-800"}
                    >
                      <td className="border border-gray-700 px-3 py-2 max-w-md">
                        <div className="truncate" title={row.question}>
                          {row.question}
                        </div>
                      </td>
                      <td
                        className={`border border-gray-700 px-3 py-2 text-center ${getScoreColor(
                          row.answer_correctness
                        )}`}
                      >
                        {formatScore(row.answer_correctness)}
                      </td>
                      <td
                        className={`border border-gray-700 px-3 py-2 text-center ${getScoreColor(
                          row.answer_relevancy
                        )}`}
                      >
                        {formatScore(row.answer_relevancy)}
                      </td>
                      <td
                        className={`border border-gray-700 px-3 py-2 text-center ${getScoreColor(
                          row.faithfulness
                        )}`}
                      >
                        {formatScore(row.faithfulness)}
                      </td>
                      <td
                        className={`border border-gray-700 px-3 py-2 text-center ${getScoreColor(
                          row.context_precision
                        )}`}
                      >
                        {formatScore(row.context_precision)}
                      </td>
                      <td
                        className={`border border-gray-700 px-3 py-2 text-center ${getScoreColor(
                          row.context_recall
                        )}`}
                      >
                        {formatScore(row.context_recall)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* No Results Message */}
          {!evalResults && !isRunningEval && (
            <div className="bg-gray-900 p-8 rounded-lg text-center text-gray-400">
              <p>No evaluation results available for mode: <strong>{evalMode}</strong></p>
              <p className="text-sm mt-2">
                Click &quot;Run Evaluation&quot; to evaluate the RAG pipeline with RAGAS metrics.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
