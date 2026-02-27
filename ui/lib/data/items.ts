import { db } from "@/lib/db/client";

type Item = {
  id: string;
  title: string;
  description: string;
};

export async function getItems(limit = 5): Promise<Item[]> {
  return db.item.findMany({
    take: limit,
    select: {
      id: true,
      title: true,
      description: true
    },
    orderBy: { createdAt: "desc" }
  });
}
