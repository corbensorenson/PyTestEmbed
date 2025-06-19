package com.pytestembed.plugin.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.project.Project
import com.pytestembed.plugin.services.LiveTestService

class StartLiveTestingAction : AnAction("Start Live Testing", "Start PyTestEmbed live testing", null) {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val liveTestService = LiveTestService.getInstance(project)
        liveTestService.startLiveTesting()
    }
    
    override fun update(e: AnActionEvent) {
        val project = e.project
        if (project == null) {
            e.presentation.isEnabledAndVisible = false
            return
        }
        
        val liveTestService = LiveTestService.getInstance(project)
        e.presentation.isEnabled = !liveTestService.isLiveTestingEnabled()
        e.presentation.text = if (liveTestService.isLiveTestingEnabled()) {
            "Live Testing Running"
        } else {
            "Start Live Testing"
        }
    }
}
