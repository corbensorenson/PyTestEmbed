package com.pytestembed.plugin.services

import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.project.Project

/**
 * Service to manage PyTestEmbed plugin state across the project.
 * Tracks visibility state of test and doc blocks.
 */
@Service(Service.Level.PROJECT)
@State(
    name = "PyTestEmbedState",
    storages = [Storage("pytestembed.xml")]
)
class PyTestEmbedStateService : PersistentStateComponent<PyTestEmbedStateService.State> {
    
    data class State(
        var testBlocksVisible: Boolean = true,
        var docBlocksVisible: Boolean = true,
        var autoFoldOnOpen: Boolean = false,
        var showToolbarButtons: Boolean = true,
        var showStatusBarWidget: Boolean = true
    )
    
    private var myState = State()
    
    override fun getState(): State = myState
    
    override fun loadState(state: State) {
        myState = state
    }
    
    // Test blocks visibility
    fun areTestBlocksVisible(): Boolean = myState.testBlocksVisible
    
    fun setTestBlocksVisible(visible: Boolean) {
        myState.testBlocksVisible = visible
    }
    
    // Doc blocks visibility
    fun areDocBlocksVisible(): Boolean = myState.docBlocksVisible
    
    fun setDocBlocksVisible(visible: Boolean) {
        myState.docBlocksVisible = visible
    }
    
    // Auto-fold settings
    fun isAutoFoldOnOpen(): Boolean = myState.autoFoldOnOpen
    
    fun setAutoFoldOnOpen(autoFold: Boolean) {
        myState.autoFoldOnOpen = autoFold
    }
    
    // UI settings
    fun shouldShowToolbarButtons(): Boolean = myState.showToolbarButtons
    
    fun setShowToolbarButtons(show: Boolean) {
        myState.showToolbarButtons = show
    }
    
    fun shouldShowStatusBarWidget(): Boolean = myState.showStatusBarWidget
    
    fun setShowStatusBarWidget(show: Boolean) {
        myState.showStatusBarWidget = show
    }
    
    // Convenience methods
    fun toggleTestBlocks(): Boolean {
        myState.testBlocksVisible = !myState.testBlocksVisible
        return myState.testBlocksVisible
    }
    
    fun toggleDocBlocks(): Boolean {
        myState.docBlocksVisible = !myState.docBlocksVisible
        return myState.docBlocksVisible
    }
    
    fun showAllBlocks() {
        myState.testBlocksVisible = true
        myState.docBlocksVisible = true
    }
    
    fun hideAllBlocks() {
        myState.testBlocksVisible = false
        myState.docBlocksVisible = false
    }
    
    companion object {
        fun getInstance(project: Project): PyTestEmbedStateService {
            return project.getService(PyTestEmbedStateService::class.java)
        }
    }
}
