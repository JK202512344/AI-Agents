"use client";

import { useState, useEffect, useCallback } from "react";
import axios from "axios";

type DocumentType = {
  name: string;
  folder: string;
  chunkCount: number;
};

export default function AdminDashboard() {
  const [files, setFiles] = useState<File[]>([]);
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [hasNewUpload, setHasNewUpload] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);

  // ================= FETCH DOCUMENTS =================
  const fetchDocuments = async () => {
    try {
      const res = await axios.get("/api/documents");

      setDocuments(res.data);
    } catch (err) {
      console.error("Error fetching documents", err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  // ================= DRAG & DROP =================
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
  }, []);

  const handleDragOver = (e: any) => {
    e.preventDefault();
  };

  const handleDrop = (e: any) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    onDrop(droppedFiles as File[]);
  };

  const handleFileBrowse = (e: any) => {
    const selectedFiles = Array.from(e.target.files);
    onDrop(selectedFiles as File[]);
  };

  // ================= UPLOAD =================
  const handleUpload = async () => {
    if (!files.length) return;

    try {
      const formData = new FormData();

      files.forEach((file) => {
        formData.append("files", file);
      });

      await axios.post("/api/upload", formData);

      setFiles([]);
      setHasNewUpload(true);

      fetchDocuments();
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  // ================= REINDEX =================
  const handleReindex = async () => {
    try {
      setIsReindexing(true);

      await axios.post("/api/reindex");

      setHasNewUpload(false);
      setIsReindexing(false);
    } catch (err) {
      console.error("Reindex failed", err);
    }
  };

  // ================= GROUP DOCUMENTS =================
  const groupedDocs = documents.reduce((acc: any, doc) => {
    if (!acc[doc.folder]) acc[doc.folder] = [];
    acc[doc.folder].push(doc);
    return acc;
  }, {});

  return (
    <div className="p-6 text-white bg-[#0b1220] min-h-screen">
      <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

      {/* ================= UPLOAD SECTION ================= */}
      <div
        className="border-2 border-dashed border-gray-500 p-6 rounded-lg mb-6 text-center cursor-pointer"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <p className="mb-2">
          Drag & Drop files here OR click to browse
        </p>

        <input
          type="file"
          multiple
          onChange={handleFileBrowse}
          className="hidden"
          id="fileInput"
        />

        <label
          htmlFor="fileInput"
          className="bg-blue-600 px-4 py-2 rounded cursor-pointer"
        >
          Browse Files
        </label>

        {/* Selected Files */}
        {files.length > 0 && (
          <div className="mt-4 text-left">
            <p className="font-semibold">Selected Files:</p>
            {files.map((f, i) => (
              <p key={i}>{f.name}</p>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleUpload}
        disabled={!files.length}
        className="bg-green-600 px-4 py-2 rounded mb-6 disabled:opacity-50"
      >
        Upload
      </button>

      {/* ================= REINDEX ================= */}
      <div className="mb-6">
        <button
          onClick={handleReindex}
          disabled={!hasNewUpload && !documents.length}
          className="bg-purple-600 px-4 py-2 rounded disabled:opacity-50"
        >
          Reindex Documents
        </button>

        {isReindexing && <p className="mt-2">Reindexing...</p>}
        {hasNewUpload && (
          <p className="mt-2 text-yellow-400">
            New file uploaded. Please reindex.
          </p>
        )}
      </div>

      {/* ================= DOCUMENT TABLE ================= */}
      <div className="bg-[#111827] p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Documents</h2>

        <table className="w-full border border-gray-700">
          <thead>
            <tr className="bg-gray-800">
              <th className="p-2 border">Folder</th>
              <th className="p-2 border">File Name</th>
              <th className="p-2 border">Chunks</th>
            </tr>
          </thead>

          <tbody>
            {Object.entries(groupedDocs).map(([folder, files]: any) =>
              files.map((file: DocumentType, idx: number) => (
                <tr key={file.name}>
                  <td className="p-2 border">
                    {idx === 0 ? folder : ""}
                  </td>
                  <td className="p-2 border">{file.name}</td>
                  <td className="p-2 border">
                    {file.chunkCount}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
