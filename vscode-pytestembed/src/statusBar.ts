/**
 * Status bar management for PyTestEmbed extension
 */

import * as vscode from 'vscode';
import { state } from './state';

/**
 * Create server status indicators in the status bar
 */
export function createServerStatusIndicators(context: vscode.ExtensionContext) {
    // Live Test Server status
    state.liveTestServerStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 200);
    state.liveTestServerStatusBar.text = '$(debug-disconnect) Live Test: Disconnected';
    state.liveTestServerStatusBar.tooltip = 'PyTestEmbed Live Test Server Status';
    state.liveTestServerStatusBar.command = 'pytestembed.toggleLiveTesting';
    context.subscriptions.push(state.liveTestServerStatusBar);

    // MCP Server status
    state.mcpServerStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 199);
    state.mcpServerStatusBar.text = '$(debug-disconnect) MCP: Disconnected';
    state.mcpServerStatusBar.tooltip = 'PyTestEmbed MCP Server Status (for Agentic Coding)';
    state.mcpServerStatusBar.command = 'pytestembed.toggleMcpServer';
    context.subscriptions.push(state.mcpServerStatusBar);

    // Show status bars
    state.liveTestServerStatusBar.show();
    state.mcpServerStatusBar.show();

    // Start periodic status checks
    startServerStatusChecks();
}

/**
 * Start periodic checks for server status
 */
function startServerStatusChecks() {
    // Check immediately
    checkServerStatus();

    // Check every 10 seconds
    state.serverStatusCheckInterval = setInterval(checkServerStatus, 10000);
}

/**
 * Check the status of both servers
 */
async function checkServerStatus() {
    // Check Live Test Server
    try {
        const response = await fetch('http://localhost:8765', {
            method: 'GET',
            signal: AbortSignal.timeout(2000)
        });
        updateLiveTestServerStatus(true);
    } catch (error) {
        updateLiveTestServerStatus(false);
    }

    // Check MCP Server
    try {
        const response = await fetch('http://localhost:3001', {
            method: 'GET',
            signal: AbortSignal.timeout(2000)
        });
        updateMcpServerStatus(true);
    } catch (error) {
        updateMcpServerStatus(false);
    }
}

/**
 * Update Live Test Server status indicator
 */
function updateLiveTestServerStatus(connected: boolean) {
    if (connected) {
        state.liveTestServerStatusBar.text = '$(debug-alt) Live Test: Connected';
        state.liveTestServerStatusBar.backgroundColor = undefined;
        state.liveTestServerStatusBar.tooltip = 'PyTestEmbed Live Test Server: Connected (Click to stop)';
    } else {
        state.liveTestServerStatusBar.text = '$(debug-disconnect) Live Test: Disconnected';
        state.liveTestServerStatusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        state.liveTestServerStatusBar.tooltip = 'PyTestEmbed Live Test Server: Disconnected (Click to start)';
    }
}

/**
 * Update MCP Server status indicator
 */
function updateMcpServerStatus(connected: boolean) {
    if (connected) {
        state.mcpServerStatusBar.text = '$(debug-alt) MCP: Connected';
        state.mcpServerStatusBar.backgroundColor = undefined;
        state.mcpServerStatusBar.tooltip = 'PyTestEmbed MCP Server: Connected - AI agents can use PyTestEmbed (Click to stop)';
    } else {
        state.mcpServerStatusBar.text = '$(debug-disconnect) MCP: Disconnected';
        state.mcpServerStatusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        state.mcpServerStatusBar.tooltip = 'PyTestEmbed MCP Server: Disconnected - AI agents cannot use PyTestEmbed (Click to start)';
    }
}
