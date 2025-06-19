/**
 * MCP (Model Context Protocol) Server management
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import { state, addPanelMessage } from './state';

/**
 * Start MCP server
 */
export function startMcpServer() {
    if (state.mcpServerEnabled) {
        vscode.window.showInformationMessage('MCP server is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    state.outputChannel.appendLine('🚀 Starting PyTestEmbed MCP Server...');

    // Get Python interpreter from configuration
    const config = vscode.workspace.getConfiguration('pytestembed');
    const pythonInterpreter = config.get('pythonInterpreter', 'python');

    // Start the MCP server
    state.mcpServerProcess = cp.spawn(pythonInterpreter, ['-m', 'pytestembed.mcp_server', workspaceFolder.uri.fsPath], {
        cwd: workspaceFolder.uri.fsPath,
        shell: true
    });

    state.mcpServerProcess.stdout?.on('data', (data) => {
        state.outputChannel.append(data.toString());
    });

    state.mcpServerProcess.stderr?.on('data', (data) => {
        state.outputChannel.append(data.toString());
    });

    state.mcpServerProcess.on('close', (code) => {
        state.outputChannel.appendLine(`MCP server exited with code ${code}`);
        state.mcpServerEnabled = false;
        updateMcpServerStatus();
    });

    state.mcpServerEnabled = true;
    updateMcpServerStatus();
    addPanelMessage('MCP server started', 'success');
    vscode.window.showInformationMessage('MCP server started');
}

/**
 * Stop MCP server
 */
export function stopMcpServer() {
    if (!state.mcpServerEnabled) {
        vscode.window.showInformationMessage('MCP server is not running');
        return;
    }

    state.outputChannel.appendLine('🛑 Stopping PyTestEmbed MCP Server...');

    // Kill the server process
    if (state.mcpServerProcess) {
        state.mcpServerProcess.kill();
        state.mcpServerProcess = null;
    }

    state.mcpServerEnabled = false;
    updateMcpServerStatus();
    addPanelMessage('MCP server stopped', 'info');
    vscode.window.showInformationMessage('MCP server stopped');
}

/**
 * Update MCP server status in UI
 */
function updateMcpServerStatus() {
    vscode.commands.executeCommand('setContext', 'pytestembed.mcpServerEnabled', state.mcpServerEnabled);
}
