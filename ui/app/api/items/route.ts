import { NextResponse } from "next/server";
import { db } from "@/lib/db/client";
import { z } from "zod";

const bodySchema = z.object({
  title: z.string().min(1),
  description: z.string().max(200)
});

export async function POST(request: Request) {
  const payload = bodySchema.parse(await request.json());
  const created = await db.item.create({
    data: payload
  });
  return NextResponse.json(created, { status: 201 });
}
