package com.pytestembed.plugin.services

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.process.OSProcessHandler
import com.intellij.execution.process.ProcessAdapter
import com.intellij.execution.process.ProcessEvent
import com.intellij.execution.process.ProcessOutputTypes
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.editor.markup.HighlighterLayer
import com.intellij.openapi.editor.markup.HighlighterTargetArea
import com.intellij.openapi.editor.markup.RangeHighlighter
import com.intellij.openapi.editor.markup.TextAttributes
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Key
import com.intellij.ui.JBColor
import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.awt.Color
import java.awt.Font
import java.io.IOException
import java.net.URI
import java.net.http.HttpClient
import java.net.http.WebSocket
import java.util.concurrent.CompletableFuture
import java.util.concurrent.ConcurrentHashMap

@Serializable
data class TestResult(
    val test_name: String,
    val status: String,
    val message: String,
    val duration: Double,
    val line_number: Int,
    val file_path: String,
    val assertion: String
)

@Serializable
data class FileTestResults(
    val file_path: String,
    val status: String,
    val tests: List<TestResult>,
    val coverage: Map<String, String>,
    val duration: Double,
    val timestamp: Double
)

@Serializable
data class LiveTestMessage(
    val type: String,
    val data: FileTestResults? = null,
    val file_path: String? = null,
    val error: String? = null,
    val timestamp: Double? = null
)

@Service(Service.Level.PROJECT)
class LiveTestService(private val project: Project) {
    private val logger = Logger.getInstance(LiveTestService::class.java)
    private var liveTestProcess: OSProcessHandler? = null
    private var webSocket: WebSocket? = null
    private var isRunning = false
    private val testResultHighlighters = ConcurrentHashMap<String, List<RangeHighlighter>>()
    private val json = Json { ignoreUnknownKeys = true }
    
    companion object {
        fun getInstance(project: Project): LiveTestService {
            return project.getService(LiveTestService::class.java)
        }
    }
    
    fun startLiveTesting() {
        if (isRunning) {
            logger.info("Live testing is already running")
            return
        }
        
        logger.info("Starting PyTestEmbed Live Testing...")
        
        try {
            // Start the live test server
            val commandLine = GeneralCommandLine()
                .withExePath("python")
                .withParameters("-m", "pytestembed", "live", "--port", "8765")
                .withWorkDirectory(project.basePath)
            
            liveTestProcess = OSProcessHandler(commandLine)
            
            liveTestProcess?.addProcessListener(object : ProcessAdapter() {
                override fun processTerminated(event: ProcessEvent) {
                    logger.info("Live test server terminated with exit code: ${event.exitCode}")
                    isRunning = false
                    disconnectWebSocket()
                }
                
                override fun onTextAvailable(event: ProcessEvent, outputType: Key<*>) {
                    if (outputType == ProcessOutputTypes.STDOUT) {
                        logger.info("Live server: ${event.text}")
                    } else if (outputType == ProcessOutputTypes.STDERR) {
                        logger.warn("Live server error: ${event.text}")
                    }
                }
            })
            
            liveTestProcess?.startNotify()
            
            // Wait a moment for server to start, then connect
            ApplicationManager.getApplication().executeOnPooledThread {
                Thread.sleep(2000)
                connectWebSocket()
            }
            
        } catch (e: Exception) {
            logger.error("Failed to start live testing", e)
        }
    }
    
    fun stopLiveTesting() {
        if (!isRunning) {
            logger.info("Live testing is not running")
            return
        }
        
        logger.info("Stopping PyTestEmbed Live Testing...")
        
        disconnectWebSocket()
        
        liveTestProcess?.let { process ->
            if (!process.isProcessTerminated) {
                process.destroyProcess()
            }
        }
        
        clearAllHighlighters()
        isRunning = false
    }
    
    fun isLiveTestingEnabled(): Boolean = isRunning
    
    fun runTestAtCursor(editor: Editor, lineNumber: Int) {
        if (!isRunning || webSocket == null) {
            return
        }
        
        val filePath = editor.virtualFile?.path ?: return
        val relativePath = project.basePath?.let { basePath ->
            filePath.removePrefix(basePath).removePrefix("/")
        } ?: filePath
        
        val message = mapOf(
            "command" to "run_test",
            "file_path" to relativePath,
            "line_number" to lineNumber
        )
        
        sendWebSocketMessage(message)
    }
    
    private fun connectWebSocket() {
        try {
            val client = HttpClient.newHttpClient()
            val builder = client.newWebSocketBuilder()
            
            webSocket = builder.buildAsync(
                URI.create("ws://localhost:8765"),
                object : WebSocket.Listener {
                    override fun onOpen(webSocket: WebSocket) {
                        logger.info("Connected to live test server")
                        isRunning = true
                        webSocket.request(1)
                    }
                    
                    override fun onText(webSocket: WebSocket, data: CharSequence, last: Boolean): CompletableFuture<*>? {
                        handleWebSocketMessage(data.toString())
                        webSocket.request(1)
                        return null
                    }
                    
                    override fun onClose(webSocket: WebSocket, statusCode: Int, reason: String): CompletableFuture<*>? {
                        logger.info("Disconnected from live test server: $reason")
                        isRunning = false
                        return null
                    }
                    
                    override fun onError(webSocket: WebSocket, error: Throwable) {
                        logger.error("Live test WebSocket error", error)
                        isRunning = false
                    }
                }
            ).get()
            
        } catch (e: Exception) {
            logger.error("Failed to connect to live test server", e)
        }
    }
    
    private fun disconnectWebSocket() {
        webSocket?.sendClose(WebSocket.NORMAL_CLOSURE, "Stopping live testing")
        webSocket = null
    }
    
    private fun sendWebSocketMessage(message: Map<String, Any>) {
        webSocket?.let { ws ->
            try {
                val jsonMessage = json.encodeToString(
                    kotlinx.serialization.serializer<Map<String, Any>>(),
                    message
                )
                ws.sendText(jsonMessage, true)
            } catch (e: Exception) {
                logger.error("Failed to send WebSocket message", e)
            }
        }
    }
    
    private fun handleWebSocketMessage(message: String) {
        try {
            val liveMessage = json.decodeFromString<LiveTestMessage>(message)
            
            when (liveMessage.type) {
                "test_results" -> liveMessage.data?.let { handleTestResults(it) }
                "test_start" -> handleTestStart(liveMessage)
                "test_error" -> handleTestError(liveMessage)
                "coverage" -> handleCoverage(liveMessage)
            }
            
        } catch (e: Exception) {
            logger.error("Failed to parse live test message: $message", e)
        }
    }
    
    private fun handleTestResults(results: FileTestResults) {
        ApplicationManager.getApplication().invokeLater {
            val filePath = results.file_path
            
            // Clear existing highlighters for this file
            clearHighlightersForFile(filePath)
            
            // Find the editor for this file
            val editor = findEditorForFile(filePath) ?: return@invokeLater
            
            val highlighters = mutableListOf<RangeHighlighter>()
            
            // Create highlighters for test results
            results.tests.forEach { test ->
                val lineNumber = test.line_number - 1 // Convert to 0-based
                if (lineNumber >= 0 && lineNumber < editor.document.lineCount) {
                    val startOffset = editor.document.getLineStartOffset(lineNumber)
                    val endOffset = editor.document.getLineEndOffset(lineNumber)
                    
                    val attributes = when (test.status) {
                        "pass" -> createPassAttributes()
                        "fail" -> createFailAttributes()
                        "error" -> createErrorAttributes()
                        else -> null
                    }
                    
                    attributes?.let { attrs ->
                        val highlighter = editor.markupModel.addRangeHighlighter(
                            startOffset,
                            endOffset,
                            HighlighterLayer.LAST + 1,
                            attrs,
                            HighlighterTargetArea.LINES_IN_RANGE
                        )
                        highlighters.add(highlighter)
                    }
                }
            }
            
            testResultHighlighters[filePath] = highlighters
        }
    }
    
    private fun handleTestStart(message: LiveTestMessage) {
        logger.info("Tests starting for: ${message.file_path}")
    }
    
    private fun handleTestError(message: LiveTestMessage) {
        logger.error("Test error in ${message.file_path}: ${message.error}")
    }
    
    private fun handleCoverage(message: LiveTestMessage) {
        // Implementation for coverage visualization
        logger.info("Coverage data received for: ${message.file_path}")
    }
    
    private fun findEditorForFile(filePath: String): Editor? {
        // Implementation to find the editor for the given file path
        // This would involve using IntelliJ's FileEditorManager
        return null // Simplified for now
    }
    
    private fun createPassAttributes(): TextAttributes {
        return TextAttributes().apply {
            backgroundColor = JBColor(Color(0, 255, 0, 25), Color(0, 255, 0, 25))
            effectColor = JBColor.GREEN
        }
    }
    
    private fun createFailAttributes(): TextAttributes {
        return TextAttributes().apply {
            backgroundColor = JBColor(Color(255, 0, 0, 25), Color(255, 0, 0, 25))
            effectColor = JBColor.RED
        }
    }
    
    private fun createErrorAttributes(): TextAttributes {
        return TextAttributes().apply {
            backgroundColor = JBColor(Color(255, 165, 0, 25), Color(255, 165, 0, 25))
            effectColor = JBColor.ORANGE
        }
    }
    
    private fun clearHighlightersForFile(filePath: String) {
        testResultHighlighters[filePath]?.forEach { highlighter ->
            highlighter.dispose()
        }
        testResultHighlighters.remove(filePath)
    }
    
    private fun clearAllHighlighters() {
        testResultHighlighters.values.forEach { highlighters ->
            highlighters.forEach { it.dispose() }
        }
        testResultHighlighters.clear()
    }
}
