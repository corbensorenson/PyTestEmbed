/**
 * Status bar indicators for PyTestEmbed services
 */

import * as vscode from 'vscode';
import { state } from './state';

let liveTestStatusItem: vscode.StatusBarItem;
let dependencyStatusItem: vscode.StatusBarItem;
let mcpStatusItem: vscode.StatusBarItem;

/**
 * Create status bar indicators for all services
 */
export function createStatusBarIndicators(context: vscode.ExtensionContext) {
    // Live Test Service Status
    liveTestStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    liveTestStatusItem.command = 'pytestembed.toggleLiveTesting';
    liveTestStatusItem.tooltip = 'Click to toggle Live Testing';
    updateLiveTestStatus(false);
    liveTestStatusItem.show();
    context.subscriptions.push(liveTestStatusItem);

    // Dependency Graph Service Status  
    dependencyStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    dependencyStatusItem.command = 'pytestembed.toggleDependencyService';
    dependencyStatusItem.tooltip = 'Click to toggle Dependency Graph Service';
    updateDependencyStatus(false);
    dependencyStatusItem.show();
    context.subscriptions.push(dependencyStatusItem);

    // MCP Service Status
    mcpStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 98);
    mcpStatusItem.command = 'pytestembed.toggleMcpService';
    mcpStatusItem.tooltip = 'Click to toggle MCP Service';
    updateMcpStatus(false);
    mcpStatusItem.show();
    context.subscriptions.push(mcpStatusItem);
}

/**
 * Update live test service status
 */
export function updateLiveTestStatus(running: boolean) {
    if (liveTestStatusItem) {
        if (running) {
            liveTestStatusItem.text = '$(check-all) Live Test';
            liveTestStatusItem.backgroundColor = undefined;
            liveTestStatusItem.color = '#4CAF50'; // Green
        } else {
            liveTestStatusItem.text = '$(circle-slash) Live Test';
            liveTestStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            liveTestStatusItem.color = undefined;
        }
    }
}

/**
 * Update dependency service status
 */
export function updateDependencyStatus(running: boolean) {
    if (dependencyStatusItem) {
        if (running) {
            dependencyStatusItem.text = '$(references) Dependencies';
            dependencyStatusItem.backgroundColor = undefined;
            dependencyStatusItem.color = '#2196F3'; // Blue
        } else {
            dependencyStatusItem.text = '$(circle-slash) Dependencies';
            dependencyStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            dependencyStatusItem.color = undefined;
        }
    }
}

/**
 * Update MCP service status
 */
export function updateMcpStatus(running: boolean) {
    if (mcpStatusItem) {
        if (running) {
            mcpStatusItem.text = '$(robot) MCP';
            mcpStatusItem.backgroundColor = undefined;
            mcpStatusItem.color = '#FF9800'; // Orange
        } else {
            mcpStatusItem.text = '$(circle-slash) MCP';
            mcpStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            mcpStatusItem.color = undefined;
        }
    }
}

/**
 * Dispose status bar items
 */
export function disposeStatusBar() {
    liveTestStatusItem?.dispose();
    dependencyStatusItem?.dispose();
    mcpStatusItem?.dispose();
}
