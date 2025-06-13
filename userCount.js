import "dotenv/config";
import { MongoClient } from "mongodb";

const uri = process.env.MONGO_URI;
const client = new MongoClient(uri);

try {
  await client.connect();
  const db = client.db();
  const collection = db.collection("settings");

  const count = await collection.countDocuments({ _id: { $exists: true } });
  console.log(`User count: ${count}`);
} catch (error) {
  console.error("❌ Failed to get user count:", error);
  process.exit(1);
} finally {
  await client.close();
}
