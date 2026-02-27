type ItemRecord = {
  id: string;
  title: string;
  description: string;
  createdAt: Date;
};

type FindManyArgs = {
  take?: number;
  select?: Record<string, boolean>;
  orderBy?: { createdAt?: "asc" | "desc" };
};

type CreateArgs = {
  data: {
    title: string;
    description: string;
  };
};

type ItemApi = {
  findMany(args?: FindManyArgs): Promise<any[]>;
  create(args: CreateArgs): Promise<any>;
};

type DbApi = {
  item: ItemApi;
};

const fallbackStore: ItemRecord[] = [];

function pickSelected(record: ItemRecord, select?: Record<string, boolean>) {
  if (!select) return record;
  const out: Record<string, unknown> = {};
  for (const key of Object.keys(select)) {
    if (select[key]) out[key] = (record as Record<string, unknown>)[key];
  }
  return out;
}

const fallbackDb: DbApi = {
  item: {
    async findMany(args: FindManyArgs = {}) {
      const direction = args.orderBy?.createdAt === "asc" ? 1 : -1;
      const sorted = [...fallbackStore].sort((a, b) => (a.createdAt > b.createdAt ? direction : -direction));
      const sliced = typeof args.take === "number" ? sorted.slice(0, args.take) : sorted;
      return sliced.map((record) => pickSelected(record, args.select));
    },
    async create(args: CreateArgs) {
      const created: ItemRecord = {
        id: `local-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
        title: args.data.title,
        description: args.data.description,
        createdAt: new Date(),
      };
      fallbackStore.unshift(created);
      return created;
    },
  },
};

let loadedDb: DbApi | null = null;
let triedLoading = false;

async function loadPrismaDb(): Promise<DbApi | null> {
  if (triedLoading) return loadedDb;
  triedLoading = true;
  try {
    const prismaModuleId: string = "@prisma/client";
    const prismaModule = await import(/* webpackIgnore: true */ prismaModuleId);
    const PrismaClient = (prismaModule as any).PrismaClient;
    if (!PrismaClient) return null;
    const globalRef = globalThis as any;
    const prisma =
      globalRef.__substratePrisma ||
      new PrismaClient({
        log: ["warn"],
        errorFormat: "minimal",
      });
    if (process.env.NODE_ENV !== "production") {
      globalRef.__substratePrisma = prisma;
    }
    loadedDb = prisma as DbApi;
    return loadedDb;
  } catch {
    loadedDb = null;
    return null;
  }
}

const db: DbApi = {
  item: {
    async findMany(args?: FindManyArgs) {
      const prismaDb = await loadPrismaDb();
      if (prismaDb) return prismaDb.item.findMany(args as any);
      return fallbackDb.item.findMany(args);
    },
    async create(args: CreateArgs) {
      const prismaDb = await loadPrismaDb();
      if (prismaDb) return prismaDb.item.create(args as any);
      return fallbackDb.item.create(args);
    },
  },
};

export { db };
