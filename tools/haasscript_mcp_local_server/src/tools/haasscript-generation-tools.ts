import { Pool } from 'pg'; // Changed from @neondatabase/serverless
import { embed } from '../utils/embedding'; // Placeholder for embedding function

// Define the Env interface for this local server
interface Env {
  DATABASE_URL: string;
  // Add other environment variables as needed
}

/**
 * Core logic for generating HaasScript code based on a natural language prompt.
 * This function prepares a comprehensive prompt for an external LLM to generate HaasScript code,
 * leveraging a knowledge base for RAG.
 */
export async function generateHaasScript(params: {
  prompt: string;
  context_keywords?: string[];
  strategy_type?: string;
}, env: Env): Promise<{
  llm_prompt: string;
  retrieved_context: string;
}> {
  const { prompt, context_keywords, strategy_type } = params;
  const pool = new Pool({ connectionString: env.DATABASE_URL });

  try {
    // 1. Generate embedding for the prompt
    console.log('generateHaasScript: Generating prompt embedding...');
    const promptEmbedding = await embed(prompt);
    console.log('generateHaasScript: Prompt embedding generated.');

    // 2. Retrieve relevant context from PostgreSQL knowledge base (RAG)
    let retrievedContext = '';
    console.log('generateHaasScript: Attempting to connect to database...');
    let client;
    try {
      client = await pool.connect();
      console.log('generateHaasScript: Connected to database. Executing queries...');

      // Example: Search haasscript_functions
      console.log('generateHaasScript: Querying haasscript_functions...');
      const funcRes = await client.query(
        `SELECT name, description, syntax FROM haasscript_functions ORDER BY embedding <-> $1 LIMIT 3`,
        [promptEmbedding]
      );
      funcRes.rows.forEach(row => {
        retrievedContext += `Function: ${row.name}\nDescription: ${row.description}\nSyntax: ${row.syntax}\n\n`;
      });
      console.log(`generateHaasScript: Found ${funcRes.rows.length} functions.`);

      // Example: Search haasscript_examples (if strategy_type is provided)
      if (strategy_type) {
        console.log('generateHaasScript: Querying haasscript_examples...');
        const exampleRes = await client.query(
          `SELECT title, script_content FROM haasscript_examples WHERE strategy_type = $1 ORDER BY embedding <-> $2 LIMIT 1`,
          [strategy_type, promptEmbedding]
        );
        exampleRes.rows.forEach(row => {
          retrievedContext += `Example Strategy: ${row.title}\nScript:\n${row.script_content}\n\n`;
        });
        console.log(`generateHaasScript: Found ${exampleRes.rows.length} examples.`);
      }

      // Example: Search haasscript_concepts
      console.log('generateHaasScript: Querying haasscript_concepts...');
      const conceptRes = await client.query(
        `SELECT concept_name, description FROM haasscript_concepts ORDER BY embedding <-> $1 LIMIT 2`,
        [promptEmbedding]
      );
      conceptRes.rows.forEach(row => {
        retrievedContext += `Concept: ${row.concept_name}\nDescription: ${row.description}\n\n`;
      });
      console.log(`generateHaasScript: Found ${conceptRes.rows.length} concepts.`);

    } finally {
      if (client) {
        console.log('generateHaasScript: Releasing database client.');
        client.release();
      }
    }

    // 3. Construct comprehensive prompt for the external LLM
    const llmPrompt = `You are an expert HaasScript coder. Your task is to generate HaasScript code based on the user's request, using the provided context.\n        \nUser Request: ${prompt}\n${context_keywords && context_keywords.length > 0 ? `Keywords: ${context_keywords.join(', ')}\n` : ''}\n${strategy_type ? `Strategy Type: ${strategy_type}\n` : ''}\n\n---\nContext from HaasScript Knowledge Base:\n${retrievedContext}\n---\n\nGenerate the HaasScript code. Ensure it is syntactically correct and ready to be used in HaasOnline Trade Server. Also, provide a brief explanation of the generated code.\n\nRespond in the following JSON format:\n{\n  "haasscript_code": "...",\n  "explanation": "..."\n}\n`;

    // 4. Return the prepared prompt and retrieved context
    console.log('generateHaasScript: Returning prepared LLM prompt and context.');
    return {
      llm_prompt: llmPrompt,
      retrieved_context: retrievedContext,
    };

  } catch (error) {
    console.error('Error in generateHaasScript function:', error);
    return {
      llm_prompt: '// Error preparing HaasScript prompt.',
      retrieved_context: `An error occurred: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
