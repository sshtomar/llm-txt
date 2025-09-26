#!/usr/bin/env node

/**
 * llms-txt MCP Server Runner
 *
 * This wrapper ensures Python and the llms-txt package are installed,
 * then runs the MCP server. It provides a convenient npx-compatible interface.
 */

import { execa } from 'execa';
import { spawn } from 'child_process';
import { platform } from 'os';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Check if Python is available
async function checkPython() {
  const pythonCommands = ['python3', 'python'];

  for (const cmd of pythonCommands) {
    try {
      const { stdout } = await execa(cmd, ['--version']);
      const match = stdout.match(/Python (\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);
        if (major === 3 && minor >= 9) {
          return cmd;
        }
      }
    } catch {
      // Continue to next command
    }
  }

  throw new Error('Python 3.9+ is required. Please install Python from https://www.python.org/downloads/');
}

// Check if llms-txt package is installed
async function checkPackageInstalled(pythonCmd) {
  try {
    await execa(pythonCmd, ['-c', 'import llm_txt.mcp.server']);
    return true;
  } catch {
    return false;
  }
}

// Install the package if needed
async function installPackage(pythonCmd) {
  console.error('Installing llms-txt package...');

  try {
    await execa(pythonCmd, ['-m', 'pip', 'install', '--upgrade', 'llms-txt'], {
      stdio: 'inherit'
    });
    console.error('Package installed successfully!');
  } catch (error) {
    console.error('Failed to install llms-txt package.');
    console.error('You can manually install it with:');
    console.error(`  ${pythonCmd} -m pip install llms-txt`);
    process.exit(1);
  }
}

// Main execution
async function main() {
  try {
    // Check for Python
    const pythonCmd = await checkPython();

    // Check if package is installed
    const isInstalled = await checkPackageInstalled(pythonCmd);

    if (!isInstalled) {
      // Try to install the package
      await installPackage(pythonCmd);
    }

    // Parse arguments for configuration
    const args = process.argv.slice(2);
    const env = { ...process.env };

    // Look for --api-url argument
    const apiUrlIndex = args.indexOf('--api-url');
    if (apiUrlIndex !== -1 && args[apiUrlIndex + 1]) {
      env.LLM_TXT_API_BASE_URL = args[apiUrlIndex + 1];
      args.splice(apiUrlIndex, 2);
    }

    // Look for --api-token argument
    const apiTokenIndex = args.indexOf('--api-token');
    if (apiTokenIndex !== -1 && args[apiTokenIndex + 1]) {
      env.LLM_TXT_API_TOKEN = args[apiTokenIndex + 1];
      args.splice(apiTokenIndex, 2);
    }

    // Look for --timeout argument
    const timeoutIndex = args.indexOf('--timeout');
    if (timeoutIndex !== -1 && args[timeoutIndex + 1]) {
      env.LLM_TXT_API_TIMEOUT = args[timeoutIndex + 1];
      args.splice(timeoutIndex, 2);
    }

    // Run the MCP server
    const mcpProcess = spawn(pythonCmd, ['-m', 'llm_txt.mcp.server', ...args], {
      stdio: 'inherit',
      env
    });

    // Handle process termination
    process.on('SIGINT', () => {
      mcpProcess.kill('SIGINT');
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      mcpProcess.kill('SIGTERM');
      process.exit(0);
    });

    mcpProcess.on('exit', (code) => {
      process.exit(code || 0);
    });

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();