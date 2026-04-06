import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const files = formData.getAll("files") as File[];

  const backendForm = new FormData();

  for (const file of files) {
    backendForm.append("files", file);
  }

  const res = await fetch("http://localhost:8000/upload", {
    method: "POST",
    body: backendForm,
  });

  const data = await res.json();

  return NextResponse.json(data);
}
