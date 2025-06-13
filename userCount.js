
import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import { MongoClient } from "mongodb";

dotenv.config();

const uri = process.env.MONGO_URI;
if (!uri) {
  console.error("❌ MONGO_URI is not defined in .env");
  process.exit(1);
}

const statsFile = path.join(process.cwd(), "user-stats.json");

const client = new MongoClient(uri);

(async () => {
  try {
    await client.connect();
    const db = client.db();
    const collection = db.collection("settings");
    const count = await collection.countDocuments({ _id: { $exists: true } });

    const today = new Date().toISOString().slice(0, 10);
    let stats = [];

    if (fs.existsSync(statsFile)) {
      stats = JSON.parse(fs.readFileSync(statsFile, "utf-8"));
    }

    const existingIndex = stats.findIndex(entry => entry.date === today);

    if (existingIndex >= 0) {
      stats[existingIndex].count = count;
    } else {
      stats.push({ date: today, count });
    }

    fs.writeFileSync(statsFile, JSON.stringify(stats, null, 2));
    console.log(count);
  } catch (err) {
    console.error("❌ Error:", err);
    process.exit(1);
  } finally {
    await client.close();
  }
})();
