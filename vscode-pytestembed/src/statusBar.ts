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
    state.liveTestServerStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 203);
    state.liveTestServerStatusBar.text = '$(debug-disconnect) Live';
    state.liveTestServerStatusBar.tooltip = 'PyTestEmbed Live Test Server Status';
    state.liveTestServerStatusBar.command = 'pytestembed.toggleLiveTesting';
    context.subscriptions.push(state.liveTestServerStatusBar);

    // Dependency Service status
    state.dependencyServiceStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 202);
    state.dependencyServiceStatusBar.text = '$(debug-disconnect) Deps';
    state.dependencyServiceStatusBar.tooltip = 'PyTestEmbed Dependency Service Status';
    state.dependencyServiceStatusBar.command = 'pytestembed.toggleDependencyService';
    context.subscriptions.push(state.dependencyServiceStatusBar);

    // AI Generation Service status
    state.aiGenerationServiceStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 201);
    state.aiGenerationServiceStatusBar.text = '$(debug-disconnect) PyTmb AI';
    state.aiGenerationServiceStatusBar.tooltip = 'PyTestEmbed AI Generation Service Status';
    state.aiGenerationServiceStatusBar.command = 'pytestembed.toggleAiGenerationService';
    context.subscriptions.push(state.aiGenerationServiceStatusBar);

    // MCP Server status
    state.mcpServerStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 200);
    state.mcpServerStatusBar.text = '$(debug-disconnect) MCP';
    state.mcpServerStatusBar.tooltip = 'PyTestEmbed MCP Server Status (for Agentic Coding)';
    state.mcpServerStatusBar.command = 'pytestembed.toggleMcpServer';
    context.subscriptions.push(state.mcpServerStatusBar);

    // Show status bars
    state.liveTestServerStatusBar.show();
    state.dependencyServiceStatusBar.show();
    state.aiGenerationServiceStatusBar.show();
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
 * Check the status of all servers using health check endpoints
 */
async function checkServerStatus() {
    // Check Live Test Server via WebSocket health check
    await checkWebSocketService('ws://localhost:8765', 'live_test_runner', updateLiveTestServerStatus);

    // Check Dependency Service via WebSocket health check
    await checkWebSocketService('ws://localhost:8769', 'dependency_service', updateDependencyServiceStatus);

    // Check AI Generation Service via WebSocket health check
    await checkWebSocketService('ws://localhost:8771', 'ai_generation_service', updateAiGenerationServiceStatus);

    // Check MCP Server via HTTP (if it has HTTP endpoint)
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const response = await fetch('http://localhost:3001', {
            method: 'GET',
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        updateMcpServerStatus(true);
    } catch (error) {
        updateMcpServerStatus(false);
    }
}

/**
 * Check WebSocket service health without interfering with operations
 */
async function checkWebSocketService(url: string, serviceName: string, updateCallback: (connected: boolean) => void) {
    try {
        const ws = new WebSocket(url);

        const healthCheckPromise = new Promise<boolean>((resolve) => {
            const timeout = setTimeout(() => {
                ws.close();
                resolve(false);
            }, 2000);

            ws.onopen = () => {
                // Send lightweight health check command
                ws.send(JSON.stringify({
                    command: 'health_check',
                    lightweight: true  // Flag to indicate this shouldn't trigger any processing
                }));
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'health_check' && data.status === 'healthy') {
                        clearTimeout(timeout);
                        ws.close();
                        resolve(true);
                    }
                } catch (e) {
                    // Ignore parse errors
                }
            };

            ws.onerror = () => {
                clearTimeout(timeout);
                resolve(false);
            };

            ws.onclose = () => {
                clearTimeout(timeout);
            };
        });

        const isHealthy = await healthCheckPromise;
        updateCallback(isHealthy);
    } catch (error) {
        updateCallback(false);
    }
}

/**
 * Update Live Test Server status indicator
 */
function updateLiveTestServerStatus(connected: boolean) {
    // Update state to match actual connection status
    state.liveTestingEnabled = connected;

    if (connected) {
        state.liveTestServerStatusBar.text = '$(debug-alt) Live';
        state.liveTestServerStatusBar.backgroundColor = undefined;
        state.liveTestServerStatusBar.tooltip = 'Live Test Server: Connected (Click to stop)';
    } else {
        state.liveTestServerStatusBar.text = '$(debug-disconnect) Live';
        state.liveTestServerStatusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        state.liveTestServerStatusBar.tooltip = 'Live Test Server: Disconnected (Click to start)';
    }
}

/**
 * Update Dependency Service status indicator
 */
function updateDependencyServiceStatus(connected: boolean) {
    // Update state to match actual connection status
    state.dependencyServiceEnabled = connected;

    if (connected) {
        state.dependencyServiceStatusBar.text = '$(debug-alt) Deps';
        state.dependencyServiceStatusBar.backgroundColor = undefined;
        state.dependencyServiceStatusBar.tooltip = 'Dependency Service: Connected (Click to stop)';
    } else {
        state.dependencyServiceStatusBar.text = '$(debug-disconnect) Deps';
        state.dependencyServiceStatusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        state.dependencyServiceStatusBar.tooltip = 'Dependency Service: Disconnected (Click to start)';
    }
}

/**
 * Update AI Generation Service status indicator
 */
function updateAiGenerationServiceStatus(connected: boolean) {
    // Update state to match actual connection status
    state.aiGenerationServiceEnabled = connected;

    if (connected) {
        state.aiGenerationServiceStatusBar.text = '$(debug-alt) PyTmb AI';
        state.aiGenerationServiceStatusBar.backgroundColor = undefined;
        state.aiGenerationServiceStatusBar.tooltip = 'AI Generation Service: Connected - Lightbulb quick fixes available (Click to stop)';
    } else {
        state.aiGenerationServiceStatusBar.text = '$(debug-disconnect) PyTmb AI';
        state.aiGenerationServiceStatusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        state.aiGenerationServiceStatusBar.tooltip = 'AI Generation Service: Disconnected - No AI-powered quick fixes (Click to start)';
    }
}

/**
 * Update MCP Server status indicator
 */
function updateMcpServerStatus(connected: boolean) {
    // Update state to match actual connection status
    state.mcpServerEnabled = connected;

    if (connected) {
        state.mcpServerStatusBar.text = '$(debug-alt) MCP';
        state.mcpServerStatusBar.backgroundColor = undefined;
        state.mcpServerStatusBar.tooltip = 'MCP Server: Connected - AI agents can use PyTestEmbed (Click to stop)';
    } else {
        state.mcpServerStatusBar.text = '$(debug-disconnect) MCP';
        state.mcpServerStatusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        state.mcpServerStatusBar.tooltip = 'MCP Server: Disconnected - AI agents cannot use PyTestEmbed (Click to start)';
    }
}
