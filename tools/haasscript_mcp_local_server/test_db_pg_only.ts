import { Client } from 'pg';
import * as dotenv from 'dotenv';
import path from 'path';

// Load environment variables from the project root's .env file
dotenv.config({ path: path.resolve(__dirname, '..', '..', '.env') });

const DATABASE_URL = process.env.DATABASE_URL;

async function testDbConnection() {
  if (!DATABASE_URL) {
    console.error("DATABASE_URL environment variable not set.");
    return;
  }

  console.log(`Attempting to connect to PostgreSQL using: ${DATABASE_URL}`);
  const client = new Client({
    connectionString: DATABASE_URL,
  });

  try {
    await client.connect();
    const result = await client.query('SELECT NOW();');
    console.log('Successfully connected to PostgreSQL using pg library!');
    console.log('Database time:', result.rows[0].now);
  } catch (error: unknown) {
    console.error('Failed to connect to PostgreSQL using pg library.');
    if (error instanceof Error) {
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      if (error.cause) {
        console.error('Error cause:', error.cause);
      }
    } else {
      console.error('Non-Error object caught:', String(error));
    }
  } finally {
    await client.end(); // Close the client connection
    console.log('Released PostgreSQL client (pg library).');
  }
}

testDbConnection();
