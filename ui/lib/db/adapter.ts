type DbClient = {
  item: {
    findMany(args: { take: number; orderBy: { createdAt: "desc" | "asc" } }): Promise<{ id: string; title: string; description: string }[]>;
  };
};

export interface DatabaseAdapter {
  client: DbClient;
  getItems(limit?: number): Promise<{ id: string; title: string; description: string }[]>;
}

export class PrismaAdapter implements DatabaseAdapter {
  constructor(public client: DbClient) {}

  async getItems(limit = 10) {
    return this.client.item.findMany({
      take: limit,
      orderBy: { createdAt: "desc" }
    });
  }
}

export function createAdapter(client: DbClient): DatabaseAdapter {
  return new PrismaAdapter(client);
}
