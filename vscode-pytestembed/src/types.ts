/**
 * Type definitions and interfaces for PyTestEmbed VSCode Extension
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as WebSocket from 'ws';

// Test result tracking
export interface TestResult {
    line: number;
    expression: string;
    status: 'pass' | 'fail' | 'running' | 'error';
    message?: string;
    context?: string; // Code context needed to run this test
}

// Extension state interface
export interface ExtensionState {
    // Block visibility
    testBlocksVisible: boolean;
    docBlocksVisible: boolean;
    
    // Live testing state
    liveTestingEnabled: boolean;
    liveTestSocket: WebSocket | null;
    liveTestProcess: cp.ChildProcess | null;
    
    // MCP server state
    mcpServerEnabled: boolean;
    mcpServerProcess: cp.ChildProcess | null;
    
    // Test results
    testResults: Map<string, TestResult[]>; // file path -> test results
    currentTestProgress: { current: number; total: number };

    // Dependency information cache
    dependencyCache: Map<string, DependencyInfo>; // element_id -> dependency info
    
    // UI components
    outputChannel: vscode.OutputChannel;
    diagnosticCollection: vscode.DiagnosticCollection;
    testProgressStatusBar: vscode.StatusBarItem;
    liveTestServerStatusBar: vscode.StatusBarItem;
    mcpServerStatusBar: vscode.StatusBarItem;
    serverStatusCheckInterval: NodeJS.Timeout | undefined;
    documentChangeTimeout: NodeJS.Timeout | undefined;
    
    // Panel state
    pyTestEmbedPanel: vscode.WebviewPanel | undefined;
    panelMessages: string[];
    
    // Decorations
    testResultDecorations: Map<string, vscode.TextEditorDecorationType>;
    coverageDecorations: Map<string, vscode.TextEditorDecorationType>;
    testResultIconDecorations: vscode.TextEditorDecorationType[];
    hiddenBlockDecorations: Map<string, vscode.TextEditorDecorationType>;
}

// Decoration types
export interface DecorationTypes {
    passIconDecorationType: vscode.TextEditorDecorationType;
    failIconDecorationType: vscode.TextEditorDecorationType;
    runningIconDecorationType: vscode.TextEditorDecorationType;
    errorIconDecorationType: vscode.TextEditorDecorationType;
    blockPassIconDecorationType: vscode.TextEditorDecorationType;
    blockFailIconDecorationType: vscode.TextEditorDecorationType;
    blockRunningIconDecorationType: vscode.TextEditorDecorationType;
    blockErrorIconDecorationType: vscode.TextEditorDecorationType;
}

// Command types
export type BlockType = 'test' | 'doc' | 'both';
export type TestStatus = 'pass' | 'fail' | 'running' | 'error';

// Live test message types
export interface LiveTestMessage {
    type: string;
    data?: any;
    file_path?: string;
    line_number?: number;
    expression?: string;
    status?: TestStatus;
    message?: string;
    error?: string;
    // New message type properties
    tests?: any[];
    test?: any;
    result?: any;
    context?: string;
    timestamp?: number;
}

// Panel message types
export type PanelMessageType = 'info' | 'success' | 'warning' | 'error';

export interface PanelMessage {
    text: string;
    type: PanelMessageType;
    timestamp: number;
}

// Enhanced dependency element information
export interface EnhancedDependencyElement {
    id: string;
    name: string;
    file_path: string;
    line_number: number;
    documentation: string;
    element_type: string;
}

// Dependency information
export interface DependencyInfo {
    element_id: string;
    element_name: string;
    file_path: string;
    line_number: number;
    dependencies: string[];
    dependents: string[];
    enhanced_dependencies?: EnhancedDependencyElement[];
    enhanced_dependents?: EnhancedDependencyElement[];
    is_dead_code: boolean;
    dependency_count: number;
    dependent_count: number;
}
