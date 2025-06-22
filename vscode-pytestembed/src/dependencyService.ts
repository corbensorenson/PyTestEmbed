/**
 * Dependency Service management for PyTestEmbed extension
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import { state } from './state';

/**
 * Start the dependency service
 */
export function startDependencyService() {
    if (state.dependencyServiceEnabled) {
        vscode.window.showInformationMessage('Dependency service is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    try {
        // Start dependency service process
        const process = cp.spawn('python', [
            '-m', 'pytestembed.dependency_service',
            workspaceFolder.uri.fsPath,
            '8769'
        ], {
            cwd: workspaceFolder.uri.fsPath,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        process.stdout?.on('data', (data) => {
            const output = data.toString();
            console.log('Dependency Service:', output);
            state.outputChannel.appendLine(`[Dependency Service] ${output}`);
        });

        process.stderr?.on('data', (data) => {
            const output = data.toString();
            console.error('Dependency Service Error:', output);
            state.outputChannel.appendLine(`[Dependency Service Error] ${output}`);
        });

        process.on('close', (code) => {
            console.log(`Dependency service exited with code ${code}`);
            state.outputChannel.appendLine(`[Dependency Service] Process exited with code ${code}`);
            state.dependencyServiceEnabled = false;
            state.dependencyServiceProcess = null;
        });

        process.on('error', (error) => {
            console.error('Failed to start dependency service:', error);
            vscode.window.showErrorMessage(`Failed to start dependency service: ${error.message}`);
            state.dependencyServiceEnabled = false;
            state.dependencyServiceProcess = null;
        });

        state.dependencyServiceProcess = process;
        state.dependencyServiceEnabled = true;

        vscode.window.showInformationMessage('Dependency service started successfully');
        state.outputChannel.appendLine('[Dependency Service] Started successfully');

    } catch (error) {
        console.error('Error starting dependency service:', error);
        vscode.window.showErrorMessage(`Error starting dependency service: ${error}`);
    }
}

/**
 * Stop the dependency service
 */
export function stopDependencyService() {
    if (!state.dependencyServiceEnabled || !state.dependencyServiceProcess) {
        vscode.window.showInformationMessage('Dependency service is not running');
        return;
    }

    try {
        // Kill the process
        state.dependencyServiceProcess.kill('SIGTERM');
        
        // Force kill after 5 seconds if it doesn't stop gracefully
        setTimeout(() => {
            if (state.dependencyServiceProcess && !state.dependencyServiceProcess.killed) {
                state.dependencyServiceProcess.kill('SIGKILL');
            }
        }, 5000);

        state.dependencyServiceEnabled = false;
        state.dependencyServiceProcess = null;

        vscode.window.showInformationMessage('Dependency service stopped');
        state.outputChannel.appendLine('[Dependency Service] Stopped');

    } catch (error) {
        console.error('Error stopping dependency service:', error);
        vscode.window.showErrorMessage(`Error stopping dependency service: ${error}`);
    }
}

/**
 * Check if dependency service is running
 */
export function isDependencyServiceRunning(): boolean {
    return state.dependencyServiceEnabled && state.dependencyServiceProcess !== null;
}

/**
 * Restart the dependency service
 */
export function restartDependencyService() {
    if (isDependencyServiceRunning()) {
        stopDependencyService();
        // Wait a bit before restarting
        setTimeout(() => {
            startDependencyService();
        }, 2000);
    } else {
        startDependencyService();
    }
}
