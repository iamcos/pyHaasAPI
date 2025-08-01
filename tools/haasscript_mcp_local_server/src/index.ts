import express from 'express';
import { Pool } from 'pg'; // Changed from @neondatabase/serverless
import * as dotenv from 'dotenv';
import path from 'path';
import { generateHaasScript } from './tools/haasscript-generation-tools'; // Import the standalone function

// Load environment variables from the project root's .env file
dotenv.config({ path: path.resolve(__dirname, '..', '..', '..', '.env') });

const app = express();
app.use(express.json()); // Enable JSON body parsing

// Define a simple Env interface for this local server
interface Env {
  DATABASE_URL: string;
  // Add other environment variables as needed
}

// Create a mock Env object for local development
const env: Env = {
  DATABASE_URL: process.env.DATABASE_URL || '',
};

// Handle MCP tool calls
app.post('/mcp', async (req, res) => {
  try {
    const jsonRpcRequest = req.body; // The incoming request body is the JSON-RPC message

    if (jsonRpcRequest.jsonrpc !== '2.0' || !jsonRpcRequest.method) {
      return res.status(400).json({
        jsonrpc: '2.0',
        id: jsonRpcRequest.id || null,
        error: { code: -32600, message: 'Invalid Request' },
      });
    }

    // Dispatch based on method
    let result: any;
    let error: any;

    switch (jsonRpcRequest.method) {
      case 'tool_call':
        const { tool_name, args } = jsonRpcRequest.params;
        switch (tool_name) {
          case 'generate_haasscript':
            result = await generateHaasScript(args, env); // Call the standalone function
            break;
          // Add other tool_call cases here as they are implemented
          default:
            error = { code: -32601, message: `Method not found: ${tool_name}` };
            break;
        }
        break;
      // Add other top-level JSON-RPC methods here if needed
      default:
        error = { code: -32601, message: `Method not found: ${jsonRpcRequest.method}` };
        break;
    }

    if (error) {
      return res.status(500).json({
        jsonrpc: '2.0',
        id: jsonRpcRequest.id || null,
        error: error,
      });
    } else {
      return res.json({
        jsonrpc: '2.0',
        id: jsonRpcRequest.id || null,
        result: result,
      });
    }

  } catch (err: unknown) { // Explicitly type err as unknown
    console.error('Error handling MCP request:', err);
    // Type guard to safely access properties of Error
    if (err instanceof Error) {
        console.error('Full error object:', JSON.stringify(err, Object.getOwnPropertyNames(err), 2)); 
        console.error('Error stack:', err.stack);
        if ('cause' in err && err.cause) { // Check for 'cause' property existence
            console.error('Error cause:', err.cause);
        }
    } else {
        console.error('Non-Error object caught:', String(err));
    }
    res.status(500).json({
      jsonrpc: '2.0',
      id: req.body.id || null,
      error: { code: -32000, message: `Server error: ${err instanceof Error ? err.message : String(err)}` },
    });
  }
});

// --- NEW TEST ENDPOINT FOR POSTGRESQL CONNECTION ---
app.get('/test-db-connection', async (req, res) => {
  let client;
  try {
    console.log('Attempting to connect to PostgreSQL for /test-db-connection...');
    console.log('DATABASE_URL:', env.DATABASE_URL); // Log the URL being used
    const pool = new Pool({ connectionString: env.DATABASE_URL });
    client = await pool.connect();
    const result = await client.query('SELECT NOW();');
    console.log('Successfully connected to PostgreSQL for /test-db-connection.');
    res.json({ status: 'success', db_time: result.rows[0].now });
  } catch (error: unknown) { // Explicitly type error as unknown
    console.error('Error testing DB connection (caught in /test-db-connection endpoint):', error);
    // Log the full error object for detailed debugging
    console.error('Full error object:', JSON.stringify(error, Object.getOwnPropertyNames(error), 2)); 
    console.error('Error stack:', (error instanceof Error) ? error.stack : 'N/A');
    if (error instanceof Error && 'cause' in error && error.cause) {
        console.error('Error cause:', error.cause);
    }
    res.status(500).json({ status: 'error', message: error instanceof Error ? error.message : String(error) });
  } finally {
    if (client) {
      client.release();
      console.log('Released PostgreSQL client for /test-db-connection.');
    }
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`HaasScript Coder Local MCP Server running on http://localhost:${PORT}`);
  console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
  console.log(`Test FastAPI connection: http://localhost:${PORT}/test-fastapi-connection`);
  console.log(`Test DB connection: http://localhost:${PORT}/test-db-connection`);
});