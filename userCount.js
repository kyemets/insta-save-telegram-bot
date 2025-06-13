import { MongoClient } from "mongodb";

const uri = process.env.MONGO_URI;
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
