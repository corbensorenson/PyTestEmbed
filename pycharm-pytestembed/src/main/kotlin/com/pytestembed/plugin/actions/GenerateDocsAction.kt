package com.pytestembed.plugin.actions

import com.intellij.execution.ExecutionManager
import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.OSProcessHandler
import com.intellij.execution.process.ProcessAdapter
import com.intellij.execution.process.ProcessEvent
import com.intellij.execution.ui.ConsoleView
import com.intellij.execution.ui.ConsoleViewContentType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileDocumentManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowManager
import com.pytestembed.plugin.toolwindow.PyTestEmbedToolWindowFactory

/**
 * Action to generate PyTestEmbed documentation for the current file.
 */
class GenerateDocsAction : AnAction() {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
        
        if (virtualFile.extension != "py") {
            return
        }
        
        // Save all files first
        FileDocumentManager.getInstance().saveAllDocuments()
        
        runPyTestEmbedCommand(project, virtualFile, "--doc")
    }
    
    override fun update(e: AnActionEvent) {
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        val isPythonFile = virtualFile?.extension == "py"
        e.presentation.isEnabledAndVisible = isPythonFile
    }
    
    private fun runPyTestEmbedCommand(project: Project, file: VirtualFile, command: String) {
        try {
            val commandLine = GeneralCommandLine()
                .withExePath("python")
                .withParameters("-m", "pytestembed", command, file.path, "--verbose")
                .withWorkDirectory(project.basePath)
            
            val processHandler = OSProcessHandler(commandLine)
            
            // Get or create the tool window
            val toolWindowManager = ToolWindowManager.getInstance(project)
            val toolWindow = toolWindowManager.getToolWindow("PyTestEmbed")
                ?: toolWindowManager.registerToolWindow("PyTestEmbed", true, true)
            
            // Get the console view from the tool window
            val consoleView = PyTestEmbedToolWindowFactory.getConsoleView(project)
            
            // Clear previous output
            consoleView.clear()
            
            // Show the tool window
            toolWindow.show()
            
            // Print command being executed
            consoleView.print("Generating documentation...\n", ConsoleViewContentType.SYSTEM_OUTPUT)
            consoleView.print("Command: python -m pytestembed $command ${file.name}\n", ConsoleViewContentType.SYSTEM_OUTPUT)
            consoleView.print("${"=".repeat(50)}\n", ConsoleViewContentType.SYSTEM_OUTPUT)
            
            // Attach console to process
            consoleView.attachToProcess(processHandler)
            
            // Add process listener for completion handling
            processHandler.addProcessListener(object : ProcessAdapter() {
                override fun processTerminated(event: ProcessEvent) {
                    ApplicationManager.getApplication().invokeLater {
                        consoleView.print("\n${"=".repeat(50)}\n", ConsoleViewContentType.SYSTEM_OUTPUT)
                        if (event.exitCode == 0) {
                            consoleView.print("✅ Documentation generation completed successfully\n", ConsoleViewContentType.SYSTEM_OUTPUT)
                        } else {
                            consoleView.print("❌ Documentation generation failed with exit code ${event.exitCode}\n", ConsoleViewContentType.ERROR_OUTPUT)
                        }
                    }
                }
            })
            
            // Start the process
            processHandler.startNotify()
            
        } catch (e: Exception) {
            // Handle errors
            val toolWindowManager = ToolWindowManager.getInstance(project)
            val toolWindow = toolWindowManager.getToolWindow("PyTestEmbed")
            val consoleView = PyTestEmbedToolWindowFactory.getConsoleView(project)
            
            consoleView.print("❌ Error running PyTestEmbed: ${e.message}\n", ConsoleViewContentType.ERROR_OUTPUT)
            toolWindow?.show()
        }
    }
}
