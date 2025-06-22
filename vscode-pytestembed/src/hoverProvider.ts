import * as vscode from 'vscode';
import { requestDependencyInfo, getCachedDependencyInfo } from './liveClient';
import { state } from './state';
import { DependencyInfo } from './types';
import * as WebSocket from 'ws';

export class PyTestEmbedHoverProvider implements vscode.HoverProvider {
    
    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | undefined> {

        // Get the word at the current position
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return undefined;
        }

        const word = document.getText(wordRange);

        // Only provide hover for function/method names (simple heuristic)
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(word)) {
            return undefined;
        }

        // Skip common keywords and built-ins
        const skipWords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally',
                          'import', 'from', 'return', 'yield', 'pass', 'break', 'continue', 'self', 'cls',
                          'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'with', 'as'];
        if (skipWords.includes(word)) {
            return undefined;
        }

        // Get the current line to determine context
        const currentLine = document.lineAt(position.line);
        const lineText = currentLine.text;

        // Check if we're hovering over a function/class definition
        const isDefinition = lineText.trim().startsWith('def ') || lineText.trim().startsWith('class ');

        // Check if we're hovering over a method call (e.g., obj.method())
        const beforeWord = lineText.substring(0, wordRange.start.character);
        const afterWord = lineText.substring(wordRange.end.character);
        const isMethodCall = beforeWord.includes('.') || afterWord.startsWith('(');

        // Check if this is a method being called on an object (e.g., "add" in "calc.add()")
        const isMethodInCall = /\w+\s*\.\s*$/.test(beforeWord) && afterWord.startsWith('(');

        // Check if we're hovering over a variable that might be an instance
        const isVariableInstance = /^\s*\w+\s*=.*\w+\(\)/.test(lineText) && lineText.includes(word);

        // Check if we're hovering over an object in a method call (e.g., "obj" in "obj.method()")
        const isObjectInMethodCall = afterWord.startsWith('.') || /\.\w+\(/.test(lineText.substring(wordRange.end.character));

        // Additional check for method calls using a broader pattern
        const isLikelyMethodCall = /\w+\s*\.\s*\w+\s*\(/.test(lineText) && lineText.includes(word);

        // Debug logging
        console.log(`🔍 Hover debug for "${word}":`, {
            beforeWord: `"${beforeWord}"`,
            afterWord: `"${afterWord}"`,
            isMethodCall,
            isMethodInCall,
            isVariableInstance,
            isObjectInMethodCall,
            isLikelyMethodCall,
            lineText: `"${lineText}"`
        });

        // Skip single-letter variables but allow class names (usually capitalized)
        if (!isDefinition && word.length === 1) {
            return undefined;
        }

        // Allow any word that looks like it could be a function/method/class
        // Only skip very short words that are likely variables
        if (!isDefinition && !isMethodCall && !isVariableInstance && !isObjectInMethodCall && !isMethodInCall && !isLikelyMethodCall) {
            // Skip single letters and very common short words that are unlikely to be functions
            if (word.length === 1 || ['a', 'b', 'c', 'x', 'y', 'z', 'i', 'j', 'k', 'n', 'm'].includes(word)) {
                return undefined;
            }
        }

        // Get workspace folder
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!workspaceFolder) {
            return undefined;
        }

        const relativePath = require('path').relative(workspaceFolder.uri.fsPath, document.uri.fsPath);
        const lineNumber = position.line + 1; // Convert to 1-based

        try {
            if (isDefinition) {
                // For function/class definitions, show dependencies
                const elementId = `${relativePath}:${word}:${lineNumber}`;
                let dependencyInfo = getCachedDependencyInfo(elementId);

                if (!dependencyInfo && state.liveTestingEnabled) {
                    // Request dependency info from live client
                    requestDependencyInfo(relativePath, word, lineNumber);
                    // Return a loading hover for now
                    return new vscode.Hover(new vscode.MarkdownString(`🔍 Loading dependencies for **${word}**...`));
                }

                if (dependencyInfo) {
                    return await this.createDependencyHover(dependencyInfo);
                }
            } else {
                // For function calls, method calls, and instances, show documentation
                let targetElement = word;

                // If it's a variable instance, try to find what class it's an instance of
                if (isVariableInstance) {
                    const classMatch = lineText.match(/(\w+)\s*=.*?(\w+)\(\)/);
                    if (classMatch && classMatch[1] === word) {
                        targetElement = classMatch[2]; // Use the class name instead
                        console.log(`🔍 Variable ${word} is instance of ${targetElement}`);
                    }
                }

                // If it's an object in a method call, try to find the class type
                if (isObjectInMethodCall) {
                    // Look for variable assignment in the file to determine type
                    const text = document.getText();
                    const assignmentPattern = new RegExp(`${word}\\s*=.*?(\\w+)\\(\\)`, 'g');
                    const match = assignmentPattern.exec(text);
                    if (match) {
                        targetElement = match[1]; // Use the class name
                        console.log(`🔍 Object ${word} is instance of ${targetElement}`);
                    }
                }

                // If it's a method being called on an object (e.g., "add" in "calc.add()")
                if (isMethodInCall) {
                    // Find the object name before the dot
                    const objectMatch = beforeWord.match(/(\w+)\s*\.\s*$/);
                    if (objectMatch) {
                        const objectName = objectMatch[1];
                        console.log(`🔍 Method ${word} called on object ${objectName}`);
                        // Just use the method name - the dependency service will find it
                        targetElement = word;
                    }
                } else {
                    // Additional check: look for method calls in a different pattern
                    // Handle cases like "calc.add(" where we might be hovering over "add"
                    const methodCallPattern = /(\w+)\s*\.\s*(\w+)\s*\(/;
                    const methodMatch = lineText.match(methodCallPattern);
                    if (methodMatch && methodMatch[2] === word) {
                        console.log(`🔍 Alternative method detection: ${word} called on ${methodMatch[1]}`);
                        targetElement = word;
                    }
                }

                console.log(`🔍 Requesting documentation for targetElement: "${targetElement}" in file: "${relativePath}"`);
                const docInfo = await this.getDocumentationInfo(relativePath, targetElement);
                if (docInfo) {
                    console.log(`✅ Got documentation for ${targetElement}`);
                    return await this.createDocumentationHover(targetElement, docInfo.documentation, docInfo.sourceFile);
                } else {
                    console.log(`❌ No documentation found for ${targetElement}, creating fallback hover`);
                    // Create a fallback hover with just the element name and navigation
                    return await this.createDocumentationHover(targetElement, `No documentation available for ${targetElement}`, relativePath);
                }
            }
        } catch (error) {
            console.error('Error getting hover info:', error);
        }

        return undefined;
    }
    
    private async getDependencyInfo(filePath: string, elementName: string, lineNumber: number): Promise<DependencyInfo | null> {
        return new Promise((resolve, reject) => {
            // Connect to dedicated dependency service
            const ws = new WebSocket('ws://localhost:8770');

            const timeout = setTimeout(() => {
                ws.close();
                console.log(`⏰ Timeout getting dependency info for ${elementName}`);
                resolve(null);
            }, 5000); // Increased timeout

            ws.on('open', () => {
                const request = {
                    command: 'get_dependencies',
                    file_path: filePath,
                    element_name: elementName,
                    line_number: lineNumber
                };
                console.log(`🔍 Requesting dependency info for ${elementName} at ${filePath}:${lineNumber}`);
                ws.send(JSON.stringify(request));
            });

            ws.on('message', (data: WebSocket.Data) => {
                clearTimeout(timeout);
                try {
                    const response = JSON.parse(data.toString());
                    console.log(`📨 Received response type: ${response.type}`);

                    if (response.type === 'dependency_info') {
                        ws.close();
                        console.log(`✅ Got dependency info for ${elementName}: ${response.dependency_count} deps, ${response.dependent_count} dependents`);
                        resolve(response as DependencyInfo);
                    } else if (response.type === 'error') {
                        ws.close();
                        console.log(`❌ Error from dependency service: ${response.message}`);
                        resolve(null);
                    } else {
                        // Unexpected response type, keep waiting
                        console.log(`⚠️ Unexpected response type: ${response.type}`);
                    }
                } catch (error) {
                    ws.close();
                    console.log(`❌ Error parsing response: ${error}`);
                    reject(error);
                }
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                console.log(`❌ WebSocket error: ${error}`);
                reject(error);
            });

            ws.on('close', () => {
                clearTimeout(timeout);
            });
        });
    }
    
    private async getDocumentationInfo(filePath: string, elementName: string): Promise<{documentation: string, sourceFile: string} | null> {
        // Always use dependency service for consistency
        return new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://localhost:8770');

            const timeout = setTimeout(() => {
                ws.close();
                console.log(`⏰ Timeout getting documentation for ${elementName}`);
                resolve(null);
            }, 3000);

            ws.on('open', () => {
                const request = {
                    command: 'get_element_documentation',
                    file_path: filePath,
                    element_name: elementName
                };
                console.log(`📖 Requesting documentation for ${elementName} from dependency service`);
                ws.send(JSON.stringify(request));
            });

            ws.on('message', (data: WebSocket.Data) => {
                clearTimeout(timeout);
                try {
                    const response = JSON.parse(data.toString());
                    console.log(`📨 Documentation response: ${response.type}`);

                    if (response.type === 'element_documentation') {
                        ws.close();
                        console.log(`✅ Got documentation for ${elementName}: ${response.documentation ? 'found' : 'not found'}`);

                        // Find the actual source file for this element
                        const sourceFile = response.source_file || filePath;
                        resolve(response.documentation ? {documentation: response.documentation, sourceFile} : null);
                    } else if (response.type === 'error') {
                        ws.close();
                        console.log(`❌ Error getting documentation: ${response.message}`);
                        resolve(null);
                    }
                } catch (error) {
                    ws.close();
                    console.log(`❌ Error parsing documentation response: ${error}`);
                    reject(error);
                }
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                console.log(`❌ WebSocket error getting documentation: ${error}`);
                reject(error);
            });
        });
    }

    private isLikelyImportedElement(word: string, document: vscode.TextDocument): boolean {
        const text = document.getText();
        const lines = text.split('\n');

        for (const line of lines) {
            const trimmed = line.trim();

            // Check for "from module import word" patterns
            if (trimmed.includes('import') && trimmed.includes(word)) {
                const fromImportMatch = trimmed.match(/^from\s+[\w.]+\s+import\s+(.+)$/);
                if (fromImportMatch) {
                    const imports = fromImportMatch[1].split(',').map(imp => imp.trim());
                    for (const imp of imports) {
                        const cleanImport = imp.split(' as ')[0].trim();
                        if (cleanImport === word) {
                            return true;
                        }
                    }
                }

                // Check for "import module" then "module.word" usage
                if (trimmed.startsWith('import ') && text.includes(`.${word}`)) {
                    return true;
                }
            }
        }

        // Also check if the word appears in variable assignments that might be imported classes
        // e.g., "derp_instance = Derp()" where Derp is imported
        const assignmentPattern = new RegExp(`\\b${word}\\s*=\\s*\\w+\\(`, 'g');
        if (assignmentPattern.test(text)) {
            return true;
        }

        // Check if word appears in method calls that suggest it's an instance
        // e.g., "derp_instance.foo()"
        const methodCallPattern = new RegExp(`\\b${word}\\.\\w+\\(`, 'g');
        if (methodCallPattern.test(text)) {
            return true;
        }

        return false;
    }

    public async findElementAcrossFiles(elementName: string): Promise<{file_path: string, line_number: number} | null> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return null;
            }

            // Search for Python files in the workspace
            const pythonFiles = await vscode.workspace.findFiles('**/*.py', '**/node_modules/**');

            for (const fileUri of pythonFiles) {
                try {
                    const document = await vscode.workspace.openTextDocument(fileUri);
                    const text = document.getText();
                    const lines = text.split('\n');

                    // Search for function or class definition
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();

                        if (line.startsWith(`def ${elementName}(`) ||
                            line.startsWith(`class ${elementName}(`) ||
                            line.startsWith(`class ${elementName}:`)) {

                            const relativePath = require('path').relative(workspaceFolder.uri.fsPath, fileUri.fsPath);
                            console.log(`✅ Found ${elementName} in ${relativePath} at line ${i + 1}`);
                            return {
                                file_path: relativePath,
                                line_number: i + 1
                            };
                        }
                    }
                } catch (error) {
                    // Skip files that can't be read
                    continue;
                }
            }

            console.log(`❌ Could not find ${elementName} in any workspace files`);
            return null;

        } catch (error) {
            console.log(`❌ Error searching across files for ${elementName}:`, error);
            return null;
        }
    }

    public async getElementLocation(filePath: string, elementName: string, lineNumber?: number): Promise<{file_path: string, line_number: number} | null> {
        // First try to find the definition by searching the file directly
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return null;
            }

            const fullPath = require('path').join(workspaceFolder.uri.fsPath, filePath);
            const document = await vscode.workspace.openTextDocument(vscode.Uri.file(fullPath));
            const text = document.getText();
            const lines = text.split('\n');

            console.log(`🔍 Searching for definition of ${elementName} in ${filePath}`);

            // Search for function or class definition
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();

                // Look for exact matches for function/class definitions
                if (line.startsWith(`def ${elementName}(`) ||
                    line.startsWith(`class ${elementName}(`) ||
                    line.startsWith(`class ${elementName}:`)) {
                    const location = {
                        file_path: filePath,
                        line_number: i + 1  // Convert to 1-based
                    };
                    console.log(`✅ Found ${elementName} definition at line ${i + 1}`);
                    return location;
                }
            }

            console.log(`❌ Could not find definition of ${elementName} in file`);
            return null;

        } catch (error) {
            console.log(`❌ Error searching for ${elementName} definition:`, error);

            // Fallback to dependency service
            return new Promise((resolve, reject) => {
                const ws = new WebSocket('ws://localhost:8770');

                const timeout = setTimeout(() => {
                    ws.close();
                    resolve(null);
                }, 3000);

                ws.on('open', () => {
                    const request = {
                        command: 'get_dependencies',
                        file_path: filePath,
                        element_name: elementName,
                        line_number: lineNumber || 1
                    };
                    console.log(`🔍 Fallback: Getting element location for ${elementName} via dependency service`);
                    ws.send(JSON.stringify(request));
                });

                ws.on('message', (data: WebSocket.Data) => {
                    clearTimeout(timeout);
                    try {
                        const response = JSON.parse(data.toString());

                        if (response.type === 'dependency_info') {
                            ws.close();
                            const location = {
                                file_path: response.file_path || filePath,
                                line_number: response.line_number || lineNumber || 1
                            };
                            console.log(`✅ Fallback found location for ${elementName}:`, location);
                            resolve(location);
                        } else {
                            ws.close();
                            resolve(null);
                        }
                    } catch (error) {
                        ws.close();
                        resolve(null);
                    }
                });

                ws.on('error', (error) => {
                    clearTimeout(timeout);
                    resolve(null);
                });
            });
        }
    }

    private async createDocumentationHover(elementName: string, documentation: string, filePath: string): Promise<vscode.Hover> {
        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;

        // Try to get the element location for navigation - first in current file, then across files
        let elementInfo = await this.getElementLocation(filePath, elementName);

        // If not found in current file, search across workspace
        if (!elementInfo) {
            elementInfo = await this.findElementAcrossFiles(elementName);
        }

        if (elementInfo) {
            // Create both navigation links
            const navigateUri = vscode.Uri.parse(`command:pytestembed.navigateToElement?${encodeURIComponent(JSON.stringify(elementInfo))}`);
            const navigateSplitUri = vscode.Uri.parse(`command:pytestembed.navigateToElementSplit?${encodeURIComponent(JSON.stringify(elementInfo))}`);
            markdown.appendMarkdown(`**📖 [${elementName}](${navigateUri}) 🔗 | [📱 Split](${navigateSplitUri})**\n\n`);
            console.log(`🔗 Created navigation links for ${elementName}:`, elementInfo);
        } else {
            markdown.appendMarkdown(`**📖 ${elementName}**\n\n`);
            console.log(`❌ No navigation link for ${elementName} - element not found`);
        }

        markdown.appendMarkdown(`${documentation}\n`);
        return new vscode.Hover(markdown);
    }

    private async createDependencyHover(info: DependencyInfo): Promise<vscode.Hover> {
        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;

        // Header
        markdown.appendMarkdown(`**🔗 ${info.element_name}**\n\n`);
        
        // Dependencies section
        if (info.enhanced_dependencies && info.enhanced_dependencies.length > 0) {
            markdown.appendMarkdown(`**📥 Dependencies (${info.dependency_count}):**\n\n`);

            for (const dep of info.enhanced_dependencies) {
                // Find the correct location using our file search method
                let depLocation = await this.getElementLocation(dep.file_path, dep.name);

                // If not found in the specified file, search across workspace for cross-file elements
                if (!depLocation) {
                    depLocation = await this.findElementAcrossFiles(dep.name);
                }

                // Fallback to original location
                depLocation = depLocation || {file_path: dep.file_path, line_number: dep.line_number};

                const navigateUri = vscode.Uri.parse(`command:pytestembed.navigateToElement?${encodeURIComponent(JSON.stringify(depLocation))}`);
                const navigateSplitUri = vscode.Uri.parse(`command:pytestembed.navigateToElementSplit?${encodeURIComponent(JSON.stringify(depLocation))}`);
                console.log(`🔗 Creating dependency link for ${dep.name}:`, depLocation);

                // Get documentation for cross-file elements
                let documentation = dep.documentation;
                if (!documentation) {
                    const crossFileDoc = await this.getDocumentationInfo(depLocation.file_path, dep.name);
                    documentation = crossFileDoc?.documentation || '';
                }

                markdown.appendMarkdown(`• [**${dep.name}**](${navigateUri}) (${dep.element_type}) 🔗 | [📱 Split](${navigateSplitUri})`);

                if (documentation) {
                    markdown.appendMarkdown(`  \n  📝 ${documentation}`);
                }

                markdown.appendMarkdown(`\n\n`);
            }
        }
        
        // Dependents section
        if (info.enhanced_dependents && info.enhanced_dependents.length > 0) {
            markdown.appendMarkdown(`**📤 Used by (${info.dependent_count}):**\n\n`);

            for (const dep of info.enhanced_dependents) {
                // Find the correct location using our file search method
                let depLocation = await this.getElementLocation(dep.file_path, dep.name);

                // If not found in the specified file, search across workspace for cross-file elements
                if (!depLocation) {
                    depLocation = await this.findElementAcrossFiles(dep.name);
                }

                // Fallback to original location
                depLocation = depLocation || {file_path: dep.file_path, line_number: dep.line_number};

                const navigateUri = vscode.Uri.parse(`command:pytestembed.navigateToElement?${encodeURIComponent(JSON.stringify(depLocation))}`);
                const navigateSplitUri = vscode.Uri.parse(`command:pytestembed.navigateToElementSplit?${encodeURIComponent(JSON.stringify(depLocation))}`);
                console.log(`🔗 Creating dependent link for ${dep.name}:`, depLocation);

                // Get documentation for cross-file elements
                let documentation = dep.documentation;
                if (!documentation) {
                    const crossFileDoc = await this.getDocumentationInfo(depLocation.file_path, dep.name);
                    documentation = crossFileDoc?.documentation || '';
                }

                markdown.appendMarkdown(`• [**${dep.name}**](${navigateUri}) (${dep.element_type}) 🔗 | [📱 Split](${navigateSplitUri})`);

                if (documentation) {
                    markdown.appendMarkdown(`  \n  📝 ${documentation}`);
                }

                markdown.appendMarkdown(`\n\n`);
            }
        }

        // If no dependencies or dependents
        if ((!info.enhanced_dependencies || info.enhanced_dependencies.length === 0) &&
            (!info.enhanced_dependents || info.enhanced_dependents.length === 0)) {
            markdown.appendMarkdown(`*No dependencies or dependents found.*`);
        }

        return new vscode.Hover(markdown);
    }
}

export function registerHoverProvider(context: vscode.ExtensionContext) {
    const hoverProvider = new PyTestEmbedHoverProvider();
    
    const disposable = vscode.languages.registerHoverProvider(
        { scheme: 'file', language: 'python' },
        hoverProvider
    );
    
    context.subscriptions.push(disposable);
}
