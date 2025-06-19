package com.pytestembed.plugin.services

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.OSProcessHandler
import com.intellij.execution.process.ProcessAdapter
import com.intellij.execution.process.ProcessEvent
import com.intellij.execution.process.ProcessOutputTypes
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.command.WriteCommandAction
import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.editor.Document
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import com.intellij.openapi.util.Key
import com.intellij.openapi.vfs.VirtualFile
import java.util.concurrent.CompletableFuture

data class GeneratedBlocks(
    val test: String? = null,
    val doc: String? = null,
    val error: String? = null
)

@Service(Service.Level.PROJECT)
class SmartGenerationService(private val project: Project) {
    private val logger = Logger.getInstance(SmartGenerationService::class.java)
    
    companion object {
        fun getInstance(project: Project): SmartGenerationService {
            return project.getService(SmartGenerationService::class.java)
        }
    }
    
    fun generateBlocks(
        editor: Editor,
        lineNumber: Int,
        generationType: String = "both",
        useAI: Boolean = true
    ) {
        val virtualFile = editor.virtualFile ?: return
        val filePath = virtualFile.path
        
        ProgressManager.getInstance().run(object : Task.Backgroundable(
            project,
            "Generating PyTestEmbed Blocks",
            true
        ) {
            override fun run(indicator: ProgressIndicator) {
                indicator.text = "Analyzing code..."
                indicator.fraction = 0.2
                
                try {
                    val result = executeGeneration(filePath, lineNumber, generationType, useAI, indicator)
                    
                    ApplicationManager.getApplication().invokeLater {
                        if (result.error != null) {
                            Messages.showErrorDialog(
                                project,
                                "Failed to generate blocks: ${result.error}",
                                "PyTestEmbed Generation Error"
                            )
                        } else {
                            insertGeneratedBlocks(editor, lineNumber, result)
                        }
                    }
                    
                } catch (e: Exception) {
                    logger.error("Smart generation failed", e)
                    ApplicationManager.getApplication().invokeLater {
                        Messages.showErrorDialog(
                            project,
                            "Generation failed: ${e.message}",
                            "PyTestEmbed Error"
                        )
                    }
                }
            }
        })
    }
    
    private fun executeGeneration(
        filePath: String,
        lineNumber: Int,
        generationType: String,
        useAI: Boolean,
        indicator: ProgressIndicator
    ): GeneratedBlocks {
        indicator.text = "Generating content..."
        indicator.fraction = 0.5
        
        val commandLine = GeneralCommandLine()
            .withExePath("python")
            .withParameters("-m", "pytestembed", "generate", filePath, lineNumber.toString())
            .withParameters("--type", generationType)
            .withWorkDirectory(project.basePath)
        
        if (!useAI) {
            commandLine.addParameter("--no-ai")
        }
        
        val processHandler = OSProcessHandler(commandLine)
        val output = StringBuilder()
        val error = StringBuilder()
        
        processHandler.addProcessListener(object : ProcessAdapter() {
            override fun onTextAvailable(event: ProcessEvent, outputType: Key<*>) {
                when (outputType) {
                    ProcessOutputTypes.STDOUT -> output.append(event.text)
                    ProcessOutputTypes.STDERR -> error.append(event.text)
                }
            }
        })
        
        processHandler.startNotify()
        processHandler.waitFor()
        
        indicator.text = "Processing results..."
        indicator.fraction = 0.8
        
        if (processHandler.exitCode != 0) {
            return GeneratedBlocks(error = error.toString().ifEmpty { "Generation process failed" })
        }
        
        return parseGeneratedOutput(output.toString())
    }
    
    private fun parseGeneratedOutput(output: String): GeneratedBlocks {
        val lines = output.split('\n')
        var testBlock: String? = null
        var docBlock: String? = null
        var currentBlock: String? = null
        val blockLines = mutableListOf<String>()
        
        for (line in lines) {
            when {
                line.contains("Generated Test Block:") -> {
                    // Save previous block
                    if (currentBlock == "test" && blockLines.isNotEmpty()) {
                        testBlock = blockLines.joinToString("\n")
                    } else if (currentBlock == "doc" && blockLines.isNotEmpty()) {
                        docBlock = blockLines.joinToString("\n")
                    }
                    
                    currentBlock = "test"
                    blockLines.clear()
                }
                
                line.contains("Generated Documentation Block:") -> {
                    // Save previous block
                    if (currentBlock == "test" && blockLines.isNotEmpty()) {
                        testBlock = blockLines.joinToString("\n")
                    } else if (currentBlock == "doc" && blockLines.isNotEmpty()) {
                        docBlock = blockLines.joinToString("\n")
                    }
                    
                    currentBlock = "doc"
                    blockLines.clear()
                }
                
                currentBlock != null && line.trim().isNotEmpty() && 
                !line.contains("Insert generated blocks") -> {
                    blockLines.add(line)
                }
            }
        }
        
        // Save the last block
        if (currentBlock == "test" && blockLines.isNotEmpty()) {
            testBlock = blockLines.joinToString("\n")
        } else if (currentBlock == "doc" && blockLines.isNotEmpty()) {
            docBlock = blockLines.joinToString("\n")
        }
        
        return GeneratedBlocks(test = testBlock, doc = docBlock)
    }
    
    private fun insertGeneratedBlocks(editor: Editor, lineNumber: Int, blocks: GeneratedBlocks) {
        val document = editor.document
        
        // Find the end of the function to insert blocks
        var insertLine = lineNumber
        for (i in lineNumber until document.lineCount) {
            val line = document.getText(
                com.intellij.openapi.util.TextRange(
                    document.getLineStartOffset(i),
                    document.getLineEndOffset(i)
                )
            )
            
            if (line.trim().isNotEmpty() && 
                !line.startsWith(" ") && 
                !line.startsWith("\t")) {
                insertLine = i
                break
            }
        }
        
        // Prepare the text to insert
        val insertText = buildString {
            blocks.test?.let { test ->
                appendLine(test)
                appendLine() // Empty line
            }
            
            blocks.doc?.let { doc ->
                appendLine(doc)
                appendLine() // Empty line
            }
        }
        
        if (insertText.isNotEmpty()) {
            WriteCommandAction.runWriteCommandAction(project) {
                val insertOffset = document.getLineStartOffset(insertLine)
                document.insertString(insertOffset, insertText)
                
                // Move cursor to the inserted content
                editor.caretModel.moveToOffset(insertOffset + insertText.length)
            }
            
            // Show success message
            val generatedTypes = mutableListOf<String>()
            if (blocks.test != null) generatedTypes.add("test")
            if (blocks.doc != null) generatedTypes.add("documentation")
            
            Messages.showInfoMessage(
                project,
                "Successfully generated ${generatedTypes.joinToString(" and ")} blocks!",
                "PyTestEmbed Generation Complete"
            )
        }
    }
    
    fun generateTestBlocks(editor: Editor, lineNumber: Int, useAI: Boolean = true) {
        generateBlocks(editor, lineNumber, "test", useAI)
    }
    
    fun generateDocBlocks(editor: Editor, lineNumber: Int, useAI: Boolean = true) {
        generateBlocks(editor, lineNumber, "doc", useAI)
    }
    
    fun generateBothBlocks(editor: Editor, lineNumber: Int, useAI: Boolean = true) {
        generateBlocks(editor, lineNumber, "both", useAI)
    }
}
