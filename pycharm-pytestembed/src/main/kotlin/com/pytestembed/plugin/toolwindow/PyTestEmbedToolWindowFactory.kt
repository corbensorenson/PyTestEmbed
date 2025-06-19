package com.pytestembed.plugin.toolwindow

import com.intellij.execution.impl.ConsoleViewImpl
import com.intellij.execution.ui.ConsoleView
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.treeStructure.Tree
import java.awt.BorderLayout
import java.awt.GridLayout
import javax.swing.*
import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.DefaultTreeModel

/**
 * Factory for creating the PyTestEmbed tool window.
 * Provides a console view and control panel for PyTestEmbed operations.
 */
class PyTestEmbedToolWindowFactory : ToolWindowFactory {
    
    companion object {
        private val consoleViews = mutableMapOf<Project, ConsoleView>()
        
        fun getConsoleView(project: Project): ConsoleView {
            return consoleViews.getOrPut(project) {
                ConsoleViewImpl(project, true)
            }
        }
    }
    
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val contentFactory = ContentFactory.getInstance()
        
        // Create main panel with tabs
        val tabbedPane = JTabbedPane()
        
        // Console tab
        val consoleView = getConsoleView(project)
        val consolePanel = JPanel(BorderLayout())
        consolePanel.add(consoleView.component, BorderLayout.CENTER)
        tabbedPane.addTab("Console", consolePanel)
        
        // Controls tab
        val controlsPanel = createControlsPanel(project)
        tabbedPane.addTab("Controls", controlsPanel)
        
        // File explorer tab
        val explorerPanel = createExplorerPanel(project)
        tabbedPane.addTab("Files", explorerPanel)
        
        // Create content and add to tool window
        val content = contentFactory.createContent(tabbedPane, "", false)
        toolWindow.contentManager.addContent(content)
    }
    
    private fun createControlsPanel(project: Project): JPanel {
        val panel = JPanel(BorderLayout())
        
        // Title
        val titleLabel = JLabel("PyTestEmbed Controls", SwingConstants.CENTER)
        titleLabel.font = titleLabel.font.deriveFont(16f)
        panel.add(titleLabel, BorderLayout.NORTH)
        
        // Button panel
        val buttonPanel = JPanel(GridLayout(0, 2, 5, 5))
        buttonPanel.border = BorderFactory.createEmptyBorder(10, 10, 10, 10)
        
        // Visibility buttons
        val toggleTestsBtn = JButton("Toggle Test Blocks")
        toggleTestsBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.ToggleTestBlocks")
                ?.actionPerformed(createActionEvent(project))
        }
        
        val toggleDocsBtn = JButton("Toggle Doc Blocks")
        toggleDocsBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.ToggleDocBlocks")
                ?.actionPerformed(createActionEvent(project))
        }
        
        val showAllBtn = JButton("Show All Blocks")
        showAllBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.ShowAllBlocks")
                ?.actionPerformed(createActionEvent(project))
        }
        
        val hideAllBtn = JButton("Hide All Blocks")
        hideAllBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.HideAllBlocks")
                ?.actionPerformed(createActionEvent(project))
        }
        
        // Execution buttons
        val runTestsBtn = JButton("Run Tests")
        runTestsBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.RunTests")
                ?.actionPerformed(createActionEvent(project))
        }
        
        val generateDocsBtn = JButton("Generate Docs")
        generateDocsBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.GenerateDocs")
                ?.actionPerformed(createActionEvent(project))
        }
        
        val runWithoutBlocksBtn = JButton("Run Without Blocks")
        runWithoutBlocksBtn.addActionListener {
            com.intellij.openapi.actionSystem.ActionManager.getInstance()
                .getAction("PyTestEmbed.RunWithoutBlocks")
                ?.actionPerformed(createActionEvent(project))
        }
        
        // Add buttons to panel
        buttonPanel.add(toggleTestsBtn)
        buttonPanel.add(toggleDocsBtn)
        buttonPanel.add(showAllBtn)
        buttonPanel.add(hideAllBtn)
        buttonPanel.add(runTestsBtn)
        buttonPanel.add(generateDocsBtn)
        buttonPanel.add(runWithoutBlocksBtn)
        
        panel.add(buttonPanel, BorderLayout.CENTER)
        
        // Status panel
        val statusPanel = JPanel(BorderLayout())
        val statusLabel = JLabel("Ready", SwingConstants.CENTER)
        statusPanel.add(statusLabel, BorderLayout.CENTER)
        statusPanel.border = BorderFactory.createTitledBorder("Status")
        panel.add(statusPanel, BorderLayout.SOUTH)
        
        return panel
    }
    
    private fun createExplorerPanel(project: Project): JPanel {
        val panel = JPanel(BorderLayout())
        
        // Create tree for PyTestEmbed files
        val root = DefaultMutableTreeNode("PyTestEmbed Files")
        val treeModel = DefaultTreeModel(root)
        val tree = Tree(treeModel)
        
        // TODO: Populate tree with actual PyTestEmbed files from project
        // For now, add placeholder nodes
        val exampleNode = DefaultMutableTreeNode("example.py")
        root.add(exampleNode)
        
        val scrollPane = JBScrollPane(tree)
        panel.add(scrollPane, BorderLayout.CENTER)
        
        return panel
    }
    
    private fun createActionEvent(project: Project): com.intellij.openapi.actionSystem.AnActionEvent {
        // Create a minimal action event for triggering actions
        val dataContext = com.intellij.openapi.actionSystem.impl.SimpleDataContext.getProjectContext(project)
        return com.intellij.openapi.actionSystem.AnActionEvent.createFromDataContext(
            "PyTestEmbedToolWindow",
            null,
            dataContext
        )
    }
}
