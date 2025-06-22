/**
 * Code Actions implementation for PyTestEmbed test: and doc: blocks
 * Communicates with Python AI generation services
 */

import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import { state } from './state';

/**
 * Base function to communicate with Python AI generation service
 */
async function callAIGenerationService(
    filePath: string,
    lineNumber: number,
    action: string,
    blockType: 'test' | 'doc'
): Promise<void> {

    // Check if AI generation service is running
    if (!state.aiGenerationServiceEnabled) {
        vscode.window.showWarningMessage('AI generation service must be running for AI-powered quick fixes. Click "PyTmb AI" in status bar to start.');
        return;
    }

    try {
        const ws = new WebSocket('ws://localhost:8771');
        
        const requestPromise = new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                ws.close();
                reject(new Error('Request timeout'));
            }, 30000); // 30 second timeout for AI generation

            ws.onopen = () => {
                console.log(`🤖 Requesting ${action} for ${blockType} block at ${filePath}:${lineNumber}`);
                
                const request = {
                    command: 'ai_generation',
                    action: action,
                    block_type: blockType,
                    file_path: filePath,
                    line_number: lineNumber
                };
                
                ws.send(JSON.stringify(request));
            };

            ws.onmessage = (event) => {
                try {
                    const response = JSON.parse(event.data.toString());
                    
                    if (response.type === 'ai_generation_result') {
                        clearTimeout(timeout);
                        ws.close();
                        
                        if (response.success) {
                            vscode.window.showInformationMessage(
                                `✅ ${action} completed successfully`
                            );
                            
                            // Refresh the file to show changes
                            vscode.commands.executeCommand('workbench.action.files.revert');
                        } else {
                            vscode.window.showErrorMessage(
                                `❌ ${action} failed: ${response.error || 'Unknown error'}`
                            );
                        }
                        
                        resolve();
                    } else if (response.type === 'ai_generation_progress') {
                        // Show progress to user
                        state.outputChannel.appendLine(`[AI Generation] ${response.message}`);
                    }
                } catch (e) {
                    console.error('Error parsing AI generation response:', e);
                }
            };

            ws.onerror = (error) => {
                clearTimeout(timeout);
                console.error('WebSocket error:', error);
                reject(error);
            };

            ws.onclose = () => {
                clearTimeout(timeout);
            };
        });

        await requestPromise;

    } catch (error) {
        console.error(`Error in ${action}:`, error);
        vscode.window.showErrorMessage(`Failed to ${action}: ${error}`);
    }
}

// Test block actions
export async function rewriteTestBlock(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'rewrite_test_block', 'test');
}

export async function addAnotherTest(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'add_another_test', 'test');
}

export async function generateEdgeCaseTests(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'generate_edge_case_tests', 'test');
}

export async function improveTestCoverage(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'improve_test_coverage', 'test');
}

// Doc block actions
export async function rewriteDocBlock(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'rewrite_doc_block', 'doc');
}

export async function addMoreDetail(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'add_more_detail', 'doc');
}

export async function addExamples(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'add_examples', 'doc');
}

export async function improveClarityDoc(filePath: string, lineNumber: number): Promise<void> {
    await callAIGenerationService(filePath, lineNumber, 'improve_clarity', 'doc');
}

/**
 * Show AI generation progress in status bar
 */
function showAIGenerationProgress(action: string) {
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.text = `$(sync~spin) ${action}...`;
    statusBarItem.show();
    
    // Hide after 30 seconds (timeout)
    setTimeout(() => {
        statusBarItem.dispose();
    }, 30000);
    
    return statusBarItem;
}
