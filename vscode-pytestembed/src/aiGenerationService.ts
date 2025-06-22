/**
 * AI Generation Service management for PyTestEmbed extension
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import { state } from './state';

/**
 * Start the AI generation service
 */
export function startAiGenerationService() {
    if (state.aiGenerationServiceEnabled) {
        vscode.window.showInformationMessage('AI generation service is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    try {
        // Start AI generation service process
        const process = cp.spawn('python', [
            '-m', 'pytestembed.ai_generation_service',
            workspaceFolder.uri.fsPath,
            '8771'
        ], {
            cwd: workspaceFolder.uri.fsPath,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        process.stdout?.on('data', (data) => {
            const output = data.toString();
            console.log('AI Generation Service:', output);
            state.outputChannel.appendLine(`[AI Generation] ${output}`);
        });

        process.stderr?.on('data', (data) => {
            const output = data.toString();
            console.error('AI Generation Service Error:', output);
            state.outputChannel.appendLine(`[AI Generation Error] ${output}`);
        });

        process.on('close', (code) => {
            console.log(`AI generation service exited with code ${code}`);
            state.outputChannel.appendLine(`[AI Generation] Process exited with code ${code}`);
            state.aiGenerationServiceEnabled = false;
            state.aiGenerationServiceProcess = null;
        });

        process.on('error', (error) => {
            console.error('Failed to start AI generation service:', error);
            vscode.window.showErrorMessage(`Failed to start AI generation service: ${error.message}`);
            state.aiGenerationServiceEnabled = false;
            state.aiGenerationServiceProcess = null;
        });

        state.aiGenerationServiceProcess = process;
        state.aiGenerationServiceEnabled = true;

        vscode.window.showInformationMessage('AI generation service started successfully');
        state.outputChannel.appendLine('[AI Generation] Started successfully');

    } catch (error) {
        console.error('Error starting AI generation service:', error);
        vscode.window.showErrorMessage(`Error starting AI generation service: ${error}`);
    }
}

/**
 * Stop the AI generation service
 */
export function stopAiGenerationService() {
    if (!state.aiGenerationServiceEnabled || !state.aiGenerationServiceProcess) {
        vscode.window.showInformationMessage('AI generation service is not running');
        return;
    }

    try {
        // Kill the process
        state.aiGenerationServiceProcess.kill('SIGTERM');
        
        // Force kill after 5 seconds if it doesn't stop gracefully
        setTimeout(() => {
            if (state.aiGenerationServiceProcess && !state.aiGenerationServiceProcess.killed) {
                state.aiGenerationServiceProcess.kill('SIGKILL');
            }
        }, 5000);

        state.aiGenerationServiceEnabled = false;
        state.aiGenerationServiceProcess = null;

        vscode.window.showInformationMessage('AI generation service stopped');
        state.outputChannel.appendLine('[AI Generation] Stopped');

    } catch (error) {
        console.error('Error stopping AI generation service:', error);
        vscode.window.showErrorMessage(`Error stopping AI generation service: ${error}`);
    }
}

/**
 * Check if AI generation service is running
 */
export function isAiGenerationServiceRunning(): boolean {
    return state.aiGenerationServiceEnabled && state.aiGenerationServiceProcess !== null;
}

/**
 * Restart the AI generation service
 */
export function restartAiGenerationService() {
    if (isAiGenerationServiceRunning()) {
        stopAiGenerationService();
        // Wait a bit before restarting
        setTimeout(() => {
            startAiGenerationService();
        }, 2000);
    } else {
        startAiGenerationService();
    }
}
