package com.pytestembed.plugin.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.Project
import com.pytestembed.plugin.services.LiveTestService

class StopLiveTestingAction : AnAction("Stop Live Testing", "Stop PyTestEmbed live testing", null) {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val liveTestService = LiveTestService.getInstance(project)
        liveTestService.stopLiveTesting()
    }
    
    override fun update(e: AnActionEvent) {
        val project = e.project
        if (project == null) {
            e.presentation.isEnabledAndVisible = false
            return
        }
        
        val liveTestService = LiveTestService.getInstance(project)
        e.presentation.isEnabled = liveTestService.isLiveTestingEnabled()
    }
}
