package com.pytestembed.plugin.actions

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.OSProcessHandler
import com.intellij.execution.process.ProcessAdapter
import com.intellij.execution.process.ProcessEvent
import com.intellij.execution.ui.ConsoleViewContentType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileDocumentManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.openapi.wm.ToolWindowManager
import com.pytestembed.plugin.toolwindow.PyTestEmbedToolWindowFactory

/**
 * Enhanced action to run PyTestEmbed tests for the current file.
 * Uses the PyTestEmbed tool window for output display.
 */
class RunTestsAction : AnAction() {

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return

        if (virtualFile.extension != "py") {
            return
        }

        // Save all files first
        FileDocumentManager.getInstance().saveAllDocuments()

        runPyTestEmbedTests(project, virtualFile)
    }

    override fun update(e: AnActionEvent) {
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        val isPythonFile = virtualFile?.extension == "py"
        e.presentation.isEnabledAndVisible = isPythonFile
    }

    /**
     * Run PyTestEmbed tests for the specified file.
     */
    private fun runPyTestEmbedTests(project: Project, file: VirtualFile) {
        try {
            val commandLine = GeneralCommandLine()
                .withExePath("python")
                .withParameters("-m", "pytestembed", "--test", file.path, "--verbose")
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
            consoleView.print("Running PyTestEmbed tests...\n", ConsoleViewContentType.SYSTEM_OUTPUT)
            consoleView.print("Command: python -m pytestembed --test ${file.name}\n", ConsoleViewContentType.SYSTEM_OUTPUT)
            consoleView.print("${"=".repeat(50)}\n", ConsoleViewContentType.SYSTEM_OUTPUT)

            // Attach console to process
            consoleView.attachToProcess(processHandler)

            // Add process listener for completion handling
            processHandler.addProcessListener(object : ProcessAdapter() {
                override fun processTerminated(event: ProcessEvent) {
                    ApplicationManager.getApplication().invokeLater {
                        consoleView.print("\n${"=".repeat(50)}\n", ConsoleViewContentType.SYSTEM_OUTPUT)
                        if (event.exitCode == 0) {
                            consoleView.print("✅ Tests completed successfully\n", ConsoleViewContentType.SYSTEM_OUTPUT)
                        } else {
                            consoleView.print("❌ Tests failed with exit code ${event.exitCode}\n", ConsoleViewContentType.ERROR_OUTPUT)
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

            consoleView.print("❌ Error running PyTestEmbed tests: ${e.message}\n", ConsoleViewContentType.ERROR_OUTPUT)
            toolWindow?.show()
        }
    }
}
