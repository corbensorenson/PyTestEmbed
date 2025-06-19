/**
 * PyTestEmbed panel management
 */

import * as vscode from 'vscode';
import { state } from './state';

/**
 * Open PyTestEmbed panel
 */
export function openPyTestEmbedPanel(context: vscode.ExtensionContext) {
    if (state.pyTestEmbedPanel) {
        state.pyTestEmbedPanel.reveal(vscode.ViewColumn.Beside);
        return;
    }

    state.pyTestEmbedPanel = vscode.window.createWebviewPanel(
        'pytestembedPanel',
        'PyTestEmbed Live Server',
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true
        }
    );

    state.pyTestEmbedPanel.webview.html = getPanelWebviewContent();

    // Handle messages from the webview
    state.pyTestEmbedPanel.webview.onDidReceiveMessage(
        message => {
            switch (message.command) {
                case 'clearMessages':
                    import('./state').then(({ clearPanelMessages }) => {
                        clearPanelMessages();
                    });
                    break;
                case 'startLiveTesting':
                    vscode.commands.executeCommand('pytestembed.startLiveTesting');
                    break;
                case 'stopLiveTesting':
                    vscode.commands.executeCommand('pytestembed.stopLiveTesting');
                    break;
                case 'startMcpServer':
                    vscode.commands.executeCommand('pytestembed.startMcpServer');
                    break;
                case 'stopMcpServer':
                    vscode.commands.executeCommand('pytestembed.stopMcpServer');
                    break;
            }
        },
        undefined,
        context.subscriptions
    );

    // Clean up when panel is disposed
    state.pyTestEmbedPanel.onDidDispose(
        () => {
            state.pyTestEmbedPanel = undefined;
        },
        null,
        context.subscriptions
    );

    // Send initial status
    updatePanelStatus();
}

/**
 * Update panel status
 */
export function updatePanelStatus() {
    if (state.pyTestEmbedPanel) {
        state.pyTestEmbedPanel.webview.postMessage({
            type: 'updateStatus',
            liveTestConnected: state.liveTestingEnabled && state.liveTestSocket !== null,
            mcpServerRunning: state.mcpServerEnabled
        });
    }
}

/**
 * Get HTML content for the panel webview
 */
function getPanelWebviewContent(): string {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PyTestEmbed Live Server</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                font-size: var(--vscode-font-size);
                color: var(--vscode-foreground);
                background-color: var(--vscode-editor-background);
                padding: 20px;
                margin: 0;
            }
            .header {
                border-bottom: 1px solid var(--vscode-panel-border);
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .status-section {
                margin-bottom: 20px;
                padding: 10px;
                border: 1px solid var(--vscode-panel-border);
                border-radius: 4px;
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-connected { background-color: #4CAF50; }
            .status-disconnected { background-color: #f44336; }
            .button {
                background-color: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                padding: 8px 16px;
                margin: 4px;
                border-radius: 4px;
                cursor: pointer;
            }
            .button:hover {
                background-color: var(--vscode-button-hoverBackground);
            }
            .messages {
                max-height: 300px;
                overflow-y: auto;
                border: 1px solid var(--vscode-panel-border);
                padding: 10px;
                margin-top: 20px;
                font-family: var(--vscode-editor-font-family);
                font-size: var(--vscode-editor-font-size);
            }
            .message {
                margin-bottom: 5px;
                padding: 2px 0;
            }
            .message.info { color: var(--vscode-foreground); }
            .message.success { color: #4CAF50; }
            .message.warning { color: #FF9800; }
            .message.error { color: #f44336; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🧪 PyTestEmbed Live Server</h2>
            <p>Real-time test execution and AI agent integration</p>
        </div>

        <div class="status-section">
            <h3>Live Test Server</h3>
            <div id="liveTestStatus">
                <span class="status-indicator status-disconnected"></span>
                <span>Disconnected</span>
            </div>
            <button class="button" onclick="toggleLiveTesting()" id="liveTestButton">Start Live Testing</button>
        </div>

        <div class="status-section">
            <h3>MCP Server (AI Agents)</h3>
            <div id="mcpStatus">
                <span class="status-indicator status-disconnected"></span>
                <span>Disconnected</span>
            </div>
            <button class="button" onclick="toggleMcpServer()" id="mcpButton">Start MCP Server</button>
        </div>

        <div class="status-section">
            <h3>Messages</h3>
            <button class="button" onclick="clearMessages()">Clear Messages</button>
            <div class="messages" id="messages">
                <div class="message info">PyTestEmbed panel ready. Start live testing to see real-time test results.</div>
            </div>
        </div>

        <script>
            const vscode = acquireVsCodeApi();
            let liveTestConnected = false;
            let mcpServerRunning = false;

            function toggleLiveTesting() {
                if (liveTestConnected) {
                    vscode.postMessage({ command: 'stopLiveTesting' });
                } else {
                    vscode.postMessage({ command: 'startLiveTesting' });
                }
            }

            function toggleMcpServer() {
                if (mcpServerRunning) {
                    vscode.postMessage({ command: 'stopMcpServer' });
                } else {
                    vscode.postMessage({ command: 'startMcpServer' });
                }
            }

            function clearMessages() {
                vscode.postMessage({ command: 'clearMessages' });
            }

            function updateStatus(status) {
                liveTestConnected = status.liveTestConnected;
                mcpServerRunning = status.mcpServerRunning;

                // Update live test status
                const liveTestStatus = document.getElementById('liveTestStatus');
                const liveTestButton = document.getElementById('liveTestButton');
                if (liveTestConnected) {
                    liveTestStatus.innerHTML = '<span class="status-indicator status-connected"></span><span>Connected</span>';
                    liveTestButton.textContent = 'Stop Live Testing';
                } else {
                    liveTestStatus.innerHTML = '<span class="status-indicator status-disconnected"></span><span>Disconnected</span>';
                    liveTestButton.textContent = 'Start Live Testing';
                }

                // Update MCP status
                const mcpStatus = document.getElementById('mcpStatus');
                const mcpButton = document.getElementById('mcpButton');
                if (mcpServerRunning) {
                    mcpStatus.innerHTML = '<span class="status-indicator status-connected"></span><span>Running</span>';
                    mcpButton.textContent = 'Stop MCP Server';
                } else {
                    mcpStatus.innerHTML = '<span class="status-indicator status-disconnected"></span><span>Stopped</span>';
                    mcpButton.textContent = 'Start MCP Server';
                }
            }

            function addMessage(message, type) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + type;
                messageDiv.textContent = message;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function clearMessagesDisplay() {
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = '<div class="message info">Messages cleared.</div>';
            }

            // Listen for messages from the extension
            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.type) {
                    case 'updateStatus':
                        updateStatus(message);
                        break;
                    case 'addMessage':
                        addMessage(message.message, message.messageType);
                        break;
                    case 'clearMessages':
                        clearMessagesDisplay();
                        break;
                }
            });
        </script>
    </body>
    </html>
    `;
}
