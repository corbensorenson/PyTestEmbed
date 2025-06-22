/**
 * Test result decorations and visual indicators
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { decorationTypes, state, getTestResults } from './state';
import { TestResult } from './types';

/**
 * Initialize test result decoration types
 */
export function initializeTestResultDecorations() {
    // Pass icon (green checkmark) - only gutter icon, no right-side indicators
    decorationTypes.passIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'pass.svg')),
        gutterIconSize: 'contain'
    });

    // Fail icon (red X) - only gutter icon
    decorationTypes.failIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'fail.svg')),
        gutterIconSize: 'contain'
    });

    // Running icon (spinning loader) - only gutter icon
    decorationTypes.runningIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'running.svg')),
        gutterIconSize: 'contain'
    });

    // Error icon (warning triangle) - only gutter icon
    decorationTypes.errorIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'error.svg')),
        gutterIconSize: 'contain'
    });

    // Block status decorations (for test: lines when collapsed) - only gutter icons
    decorationTypes.blockPassIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'pass.svg')),
        gutterIconSize: 'contain'
    });

    decorationTypes.blockFailIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'fail.svg')),
        gutterIconSize: 'contain'
    });

    decorationTypes.blockRunningIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'running.svg')),
        gutterIconSize: 'contain'
    });

    decorationTypes.blockErrorIconDecorationType = vscode.window.createTextEditorDecorationType({
        gutterIconPath: vscode.Uri.file(path.join(__dirname, '..', 'resources', 'error.svg')),
        gutterIconSize: 'contain'
    });
}

/**
 * Dispose test result decorations
 */
export function disposeTestResultDecorations() {
    Object.values(decorationTypes).forEach(decoration => {
        if (decoration) {
            decoration.dispose();
        }
    });
}

/**
 * Refresh test result decorations for a file
 */
export function refreshTestResultDecorations(filePath: string) {
    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);
    if (!editor) return;

    const fileResults = getTestResults(filePath);

    // Clear individual test decorations - we only want block-level decorations
    editor.setDecorations(decorationTypes.passIconDecorationType, []);
    editor.setDecorations(decorationTypes.failIconDecorationType, []);
    editor.setDecorations(decorationTypes.runningIconDecorationType, []);
    editor.setDecorations(decorationTypes.errorIconDecorationType, []);

    // Update collapsed block status indicators instead
    updateCollapsedBlockStatusIndicators(editor, fileResults);
}

/**
 * Update status indicators for collapsed test blocks
 */
export function updateCollapsedBlockStatusIndicators(editor: vscode.TextEditor, fileResults: TestResult[]) {
    const document = editor.document;
    const testBlockStatusRanges: { [key: string]: vscode.DecorationOptions[] } = {
        pass: [],
        fail: [],
        running: [],
        error: []
    };

    // Find all test: blocks
    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        if (line.text.trim() === 'test:') {
            // Always show status for test: blocks
            // Find all tests in this block
            const blockTests = findTestsInBlock(document, i, fileResults);

            if (blockTests.length === 0) {
                // No tests run yet - show as fail (untested)
                const range = new vscode.Range(i, 0, i, 0);
                const decorationOptions: vscode.DecorationOptions = {
                    range,
                    hoverMessage: 'Tests not run yet'
                };
                testBlockStatusRanges.fail.push(decorationOptions);
            } else {
                // Determine block status based on tests
                const hasFailures = blockTests.some(t => t.status === 'fail' || t.status === 'error');
                const hasRunning = blockTests.some(t => t.status === 'running');

                const range = new vscode.Range(i, 0, i, 0);
                let status: string;
                let hoverMessage: string;

                if (hasRunning) {
                    status = 'running';
                    hoverMessage = 'Tests running...';
                } else if (hasFailures) {
                    status = 'fail';
                    const failCount = blockTests.filter(t => t.status === 'fail' || t.status === 'error').length;
                    hoverMessage = `${failCount} test(s) failing`;
                } else {
                    status = 'pass';
                    hoverMessage = `All ${blockTests.length} tests passing`;
                }

                const decorationOptions: vscode.DecorationOptions = {
                    range,
                    hoverMessage
                };
                testBlockStatusRanges[status].push(decorationOptions);
            }
        }
    }

    // Apply decorations
    editor.setDecorations(decorationTypes.blockPassIconDecorationType, testBlockStatusRanges.pass);
    editor.setDecorations(decorationTypes.blockFailIconDecorationType, testBlockStatusRanges.fail);
    editor.setDecorations(decorationTypes.blockRunningIconDecorationType, testBlockStatusRanges.running);
    editor.setDecorations(decorationTypes.blockErrorIconDecorationType, testBlockStatusRanges.error);
}

/**
 * Check if a test block is collapsed
 */
function isTestBlockCollapsed(editor: vscode.TextEditor, testBlockLine: number): boolean {
    const document = editor.document;

    // Check if the test: block content is visible
    // If the lines immediately after test: are not in the visible ranges, it's likely folded

    // Find the first non-empty line after test:
    let nextContentLine = -1;
    for (let i = testBlockLine + 1; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        if (line.text.trim() !== '') {
            nextContentLine = i;
            break;
        }
    }

    if (nextContentLine === -1) {
        return false; // No content to fold
    }

    // Check if this content line is visible in any visible range
    const isContentVisible = editor.visibleRanges.some(range =>
        nextContentLine >= range.start.line && nextContentLine <= range.end.line
    );

    // If content is not visible but the test: line is visible, it's likely folded
    const isTestLineVisible = editor.visibleRanges.some(range =>
        testBlockLine >= range.start.line && testBlockLine <= range.end.line
    );

    return isTestLineVisible && !isContentVisible;
}

/**
 * Find all tests within a test block
 */
function findTestsInBlock(document: vscode.TextDocument, testBlockLine: number, fileResults: TestResult[]): TestResult[] {
    const blockTests: TestResult[] = [];
    const baseIndent = document.lineAt(testBlockLine).firstNonWhitespaceCharacterIndex;

    // Find the end of the test block
    let endLine = testBlockLine;
    for (let i = testBlockLine + 1; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const trimmedText = line.text.trim();

        if (trimmedText === '') {
            continue; // Skip empty lines
        }

        const currentIndent = line.firstNonWhitespaceCharacterIndex;

        // If we hit something at same or lower indentation, we've reached the end
        if (currentIndent <= baseIndent) {
            break;
        }

        endLine = i;
    }

    // Find tests in this range
    for (const testResult of fileResults) {
        if (testResult.line > testBlockLine && testResult.line <= endLine) {
            blockTests.push(testResult);
        }
    }

    return blockTests;
}

/**
 * Clear all decorations
 */
export function clearAllDecorations() {
    state.testResultDecorations.forEach(decoration => decoration.dispose());
    state.testResultDecorations.clear();

    state.coverageDecorations.forEach(decoration => decoration.dispose());
    state.coverageDecorations.clear();
}

/**
 * Clear decorations for a specific file
 */
export function clearDecorationsForFile(filePath: string) {
    const keys = Array.from(state.testResultDecorations.keys()).filter(key => key.startsWith(filePath));
    keys.forEach(key => {
        const decoration = state.testResultDecorations.get(key);
        if (decoration) {
            decoration.dispose();
            state.testResultDecorations.delete(key);
        }
    });
}
