import dotenv from "dotenv";
import { MongoClient } from "mongodb";

dotenv.config();

const uri = process.env.MONGO_URI;
if (!uri) {
  console.error("❌ MONGO_URI is not defined in .env");
  process.exit(1);
}

const client = new MongoClient(uri);

(async () => {
  try {
    await client.connect();
    const db = client.db();
    const collection = db.collection("settings");
    const count = await collection.countDocuments({ _id: { $exists: true } });
    console.log(count);
  } catch (err) {
    console.error("❌ Error:", err);
    process.exit(1);
  } finally {
    await client.close();
  }
})();
