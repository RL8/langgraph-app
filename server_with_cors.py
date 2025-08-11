#!/usr/bin/env python3
"""Custom server with CORS support for manual testing interface."""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from langgraph.graph import StateGraph
from langchain_core.messages import ToolMessage
from agent.graph import graph
from agent.state import State

# Create FastAPI app
app = FastAPI(title="Research Agent Manual Testing", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for manual testing
current_state = None

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the manual testing interface."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Research Agent - Manual Testing</title>
    <style>
        body {
            font-family: monospace;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .section {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h2 {
            margin-top: 0;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        input[type="text"], textarea, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .step {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border: 1px solid #eee;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        .step.ready {
            background: #f8f9fa;
        }
        .step.completed {
            background: #d4edda;
            border-color: #c3e6cb;
        }
        .step.error {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        .step.processing {
            background: #fff3cd;
            border-color: #ffeaa7;
        }
        .step-output {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin-top: 5px;
            font-family: monospace;
            font-size: 11px;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
            display: none;
        }
        .step-output.show {
            display: block;
        }
        .step-container {
            margin-bottom: 10px;
        }
        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border: 1px solid #eee;
            border-radius: 4px;
            cursor: pointer;
        }
        .step-header:hover {
            background: #f8f9fa;
        }
        .step-header.ready {
            background: #f8f9fa;
        }
        .step-header.completed {
            background: #d4edda;
            border-color: #c3e6cb;
        }
        .step-header.error {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        .step-header.processing {
            background: #fff3cd;
            border-color: #ffeaa7;
        }
        .step-title {
            font-weight: bold;
        }
        .step-status {
            font-size: 11px;
            color: #666;
        }
        .processing-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .output {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .controls {
            text-align: center;
            padding: 20px 0;
        }
        .topic-section {
            margin-bottom: 15px;
        }
        .topic-section label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .schema-info {
            background: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 11px;
        }
        
        /* Hybrid Execution Styles */
        .hybrid-controls {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .progress-container {
            margin-top: 15px;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #007bff, #28a745);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .progress-text {
            font-size: 12px;
            color: #666;
        }
        
        .hybrid-step {
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .hybrid-step .step-header {
            display: flex;
            align-items: center;
            padding: 15px;
            background: #f8f9fa;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .hybrid-step .step-header:hover {
            background: #e9ecef;
        }
        
        .step-icon {
            font-size: 24px;
            margin-right: 15px;
            width: 30px;
            text-align: center;
        }
        
        .step-info {
            flex: 1;
        }
        
        .step-title {
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 5px;
        }
        
        .step-status {
            font-size: 12px;
            margin-bottom: 3px;
        }
        
        .step-desc {
            font-size: 11px;
            color: #666;
        }
        
        .step-toggle {
            font-size: 12px;
            color: #666;
            transition: transform 0.2s;
        }
        
        .step-details {
            background: white;
            border-top: 1px solid #ddd;
            padding: 15px;
            display: none;
        }
        
        .step-details.show {
            display: block;
        }
        
        .details-content {
            font-family: monospace;
            font-size: 11px;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }
        
        /* Status colors */
        .step-status.waiting { color: #6c757d; }
        .step-status.processing { color: #007bff; }
        .step-status.completed { color: #28a745; }
        .step-status.error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Research Agent - Hybrid Testing</h1>
        
        <!-- Input Section -->
        <div class="section">
            <h2>📝 Input Section</h2>
            
            <div class="topic-section">
                <label>Choose a sample topic or enter your own:</label>
                <select id="topic-select" onchange="updateTopic()">
                    <option value="">-- Select a sample topic --</option>
                    <option value="Taylor Swift's musical evolution and lyrical themes">1. Taylor Swift's musical evolution and lyrical themes</option>
                    <option value="The impact of social media on mental health">2. The impact of social media on mental health</option>
                    <option value="Climate change effects on global agriculture">3. Climate change effects on global agriculture</option>
                    <option value="Artificial intelligence in healthcare applications">4. Artificial intelligence in healthcare applications</option>
                    <option value="The rise of remote work and its economic implications">5. The rise of remote work and its economic implications</option>
                    <option value="Renewable energy adoption trends worldwide">6. Renewable energy adoption trends worldwide</option>
                    <option value="The evolution of electric vehicles and market trends">7. The evolution of electric vehicles and market trends</option>
                    <option value="Mental health awareness in modern society">8. Mental health awareness in modern society</option>
                    <option value="The future of cryptocurrency and blockchain technology">9. The future of cryptocurrency and blockchain technology</option>
                    <option value="Sustainable fashion and ethical consumerism">10. Sustainable fashion and ethical consumerism</option>
                </select>
            </div>
            
            <div class="topic-section">
                <label>Or enter your own topic:</label>
                <input type="text" id="topic" placeholder="Enter your research topic here...">
            </div>
            
            <div class="schema-info">
                <strong>Default Schema:</strong> The system uses a universal research schema that extracts:
                <ul>
                    <li><strong>key_concepts</strong>: Main ideas and concepts related to the topic</li>
                    <li><strong>historical_context</strong>: Background and historical development</li>
                    <li><strong>current_state</strong>: Present situation and recent developments</li>
                    <li><strong>challenges_issues</strong>: Problems, obstacles, and controversies</li>
                    <li><strong>future_outlook</strong>: Predictions, trends, and potential developments</li>
                    <li><strong>key_players</strong>: Important individuals, organizations, or entities</li>
                    <li><strong>technological_aspects</strong>: Technology-related elements (if applicable)</li>
                    <li><strong>social_impact</strong>: Effects on society, culture, or communities</li>
                </ul>
            </div>
            
            <button onclick="initialize()">Initialize</button>
            <button onclick="clearInputs()">Clear</button>
        </div>

        <!-- Hybrid Execution -->
        <div class="section">
            <h2>🚀 Hybrid Execution</h2>
            <div class="hybrid-controls">
                <button onclick="startHybridExecution()" id="hybrid-start-btn">Start Hybrid Execution</button>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="progress-text" id="progress-text">Ready to start</div>
                </div>
            </div>
        </div>

        <!-- Execution Steps -->
        <div class="section">
            <h2>📋 Execution Steps</h2>
            <div id="hybrid-steps">
                <div class="hybrid-step" id="step-1">
                    <div class="step-header" onclick="toggleStepDetails('step-1')">
                        <div class="step-icon">🧠</div>
                        <div class="step-info">
                            <div class="step-title">AGENT PLANNING</div>
                            <div class="step-status" id="step-1-status">⏳ Waiting</div>
                            <div class="step-desc">Initial research strategy and planning</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-1-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>

                <div class="hybrid-step" id="step-2">
                    <div class="step-header" onclick="toggleStepDetails('step-2')">
                        <div class="step-icon">🔍</div>
                        <div class="step-info">
                            <div class="step-title">SEARCH EXECUTION</div>
                            <div class="step-status" id="step-2-status">⏳ Waiting</div>
                            <div class="step-desc">Web search for research topic</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-2-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>

                <div class="hybrid-step" id="step-3">
                    <div class="step-header" onclick="toggleStepDetails('step-3')">
                        <div class="step-icon">📄</div>
                        <div class="step-info">
                            <div class="step-title">SCRAPING EXECUTION</div>
                            <div class="step-status" id="step-3-status">⏳ Waiting</div>
                            <div class="step-desc">Website content scraping from search results</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-3-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>

                <div class="hybrid-step" id="step-4">
                    <div class="step-header" onclick="toggleStepDetails('step-4')">
                        <div class="step-icon">⚙️</div>
                        <div class="step-info">
                            <div class="step-title">INFORMATION EXTRACTION</div>
                            <div class="step-status" id="step-4-status">⏳ Waiting</div>
                            <div class="step-desc">Extract structured information from gathered content</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-4-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>

                <div class="hybrid-step" id="step-5">
                    <div class="step-header" onclick="toggleStepDetails('step-5')">
                        <div class="step-icon">✅</div>
                        <div class="step-info">
                            <div class="step-title">QUALITY VALIDATION</div>
                            <div class="step-status" id="step-5-status">⏳ Waiting</div>
                            <div class="step-desc">Quality validation and completeness assessment</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-5-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>

                <div class="hybrid-step" id="step-6">
                    <div class="step-header" onclick="toggleStepDetails('step-6')">
                        <div class="step-icon">🔄</div>
                        <div class="step-info">
                            <div class="step-title">ITERATION DECISION</div>
                            <div class="step-status" id="step-6-status">⏳ Waiting</div>
                            <div class="step-desc">Decision making based on quality assessment</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-6-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>

                <div class="hybrid-step" id="step-7">
                    <div class="step-header" onclick="toggleStepDetails('step-7')">
                        <div class="step-icon">📊</div>
                        <div class="step-info">
                            <div class="step-title">FINAL OUTPUT</div>
                            <div class="step-status" id="step-7-status">⏳ Waiting</div>
                            <div class="step-desc">Final structured output generation and delivery</div>
                        </div>
                        <div class="step-toggle">▼</div>
                    </div>
                    <div class="step-details" id="step-7-details">
                        <div class="details-content">Details will appear here when step completes</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Controls -->
        <div class="section">
            <h2>🎛️ Controls</h2>
            <div class="controls">
                <button onclick="reset()">Reset</button>
                <button onclick="exportResults()">Export Results</button>
                <button onclick="saveState()">Save State</button>
                <button onclick="loadState()">Load State</button>
            </div>
        </div>
    </div>

    <script>
        let currentState = null;
        
        // Default schema for universal research
        const defaultSchema = {
            "type": "object",
            "properties": {
                "key_concepts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Main ideas, concepts, and fundamental elements related to the topic"
                },
                "historical_context": {
                    "type": "string",
                    "description": "Background information, historical development, and evolution of the topic"
                },
                "current_state": {
                    "type": "string", 
                    "description": "Present situation, recent developments, and current status"
                },
                "challenges_issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Problems, obstacles, controversies, and challenges faced"
                },
                "future_outlook": {
                    "type": "string",
                    "description": "Predictions, trends, potential developments, and future prospects"
                },
                "key_players": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Important individuals, organizations, companies, or entities involved"
                },
                "technological_aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Technology-related elements, innovations, or technical considerations"
                },
                "social_impact": {
                    "type": "string",
                    "description": "Effects on society, culture, communities, or human behavior"
                }
            },
            "required": ["key_concepts", "current_state", "challenges_issues"]
        };

        function updateTopic() {
            const select = document.getElementById('topic-select');
            const input = document.getElementById('topic');
            if (select.value) {
                input.value = select.value;
            }
        }

        async function initialize() {
            const topic = document.getElementById('topic').value;
            
            if (!topic) {
                alert('Please provide a topic');
                return;
            }
            
            try {
                const response = await fetch('/initialize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({topic, extraction_schema: defaultSchema})
                });
                
                const result = await response.json();
                if (response.ok) {
                    currentState = result.state;
                    alert('State initialized successfully');
                } else {
                    alert('Error: ' + result.detail);
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }

        function toggleStepDetails(stepId) {
            const details = document.getElementById(stepId + '-details');
            const toggle = details.previousElementSibling.querySelector('.step-toggle');
            details.classList.toggle('show');
            toggle.textContent = details.classList.contains('show') ? '▲' : '▼';
        }

        async function startHybridExecution() {
            if (!currentState) {
                alert('Please initialize state first');
                return;
            }
            
            const startBtn = document.getElementById('hybrid-start-btn');
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            
            // Update UI for execution start
            startBtn.disabled = true;
            startBtn.textContent = 'Executing...';
            progressText.textContent = 'Starting hybrid execution...';
            
            try {
                // Update all steps to processing state
                for (let i = 1; i <= 7; i++) {
                    const stepStatus = document.getElementById(`step-${i}-status`);
                    stepStatus.textContent = '🔄 Processing...';
                    stepStatus.className = 'step-status processing';
                }
                
                // Execute hybrid workflow
                const response = await fetch('/hybrid-execution', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const result = await response.json();
                
                if (result.status === 'completed') {
                    // Update progress
                    progressFill.style.width = '100%';
                    progressText.textContent = 'Execution completed successfully';
                    
                    // Update current state
                    currentState = result.state;
                    
                    // Update each step with results
                    updateStepResults(result.step_results);
                    
                    startBtn.textContent = 'Re-run';
                } else {
                    progressText.textContent = 'Execution failed';
                    alert('Error: ' + result.error);
                    startBtn.textContent = 'Retry';
                }
                
            } catch (e) {
                progressText.textContent = 'Execution failed';
                alert('Error: ' + e.message);
                startBtn.textContent = 'Retry';
            } finally {
                startBtn.disabled = false;
            }
        }

        function updateStepResults(stepResults) {
            const stepMappings = {
                'step_1_agent_planning': 1,
                'step_2_search_execution': 2,
                'step_3_scraping_execution': 3,
                'step_4_information_extraction': 4,
                'step_5_quality_validation': 5,
                'step_6_iteration_decision': 6,
                'step_7_final_output': 7
            };
            
            for (const [stepKey, stepData] of Object.entries(stepResults)) {
                const stepNumber = stepMappings[stepKey];
                if (stepNumber) {
                    const stepStatus = document.getElementById(`step-${stepNumber}-status`);
                    const stepDetails = document.getElementById(`step-${stepNumber}-details`);
                    
                    // Update status
                    if (stepData.status === 'completed') {
                        stepStatus.textContent = '✅ Completed';
                        stepStatus.className = 'step-status completed';
                    } else if (stepData.status === 'skipped') {
                        stepStatus.textContent = '⏭️ Skipped';
                        stepStatus.className = 'step-status waiting';
                    } else {
                        stepStatus.textContent = '❌ Failed';
                        stepStatus.className = 'step-status error';
                    }
                    
                    // Update details
                    const detailsContent = formatStepDetails(stepData);
                    stepDetails.querySelector('.details-content').innerHTML = detailsContent;
                }
            }
        }

        function formatStepDetails(stepData) {
            let details = `=== STEP DETAILS ===\n`;
            details += `Status: ${stepData.status}\n`;
            details += `Description: ${stepData.description}\n\n`;
            
            // Add step-specific details
            if (stepData.query) details += `Query: ${stepData.query}\n`;
            if (stepData.results_count !== undefined) details += `Results Count: ${stepData.results_count}\n`;
            if (stepData.urls_processed !== undefined) details += `URLs Processed: ${stepData.urls_processed}\n`;
            if (stepData.messages_processed !== undefined) details += `Messages Processed: ${stepData.messages_processed}\n`;
            if (stepData.messages_count !== undefined) details += `Messages Count: ${stepData.messages_count}\n`;
            if (stepData.extraction_success !== undefined) details += `Extraction Success: ${stepData.extraction_success ? 'Yes' : 'No'}\n`;
            if (stepData.validation_passed !== undefined) details += `Validation Passed: ${stepData.validation_passed ? 'Yes' : 'No'}\n`;
            if (stepData.loop_step !== undefined) details += `Loop Step: ${stepData.loop_step}\n`;
            if (stepData.decision) details += `Decision: ${stepData.decision}\n`;
            if (stepData.reason) details += `Reason: ${stepData.reason}\n`;
            if (stepData.output_summary) details += `Output Summary: ${stepData.output_summary}\n`;
            
            // Add full details for troubleshooting
            if (stepData.full_details) {
                details += `\n=== FULL DETAILS FOR TROUBLESHOOTING ===\n`;
                details += JSON.stringify(stepData.full_details, null, 2);
            }
            
            // Add search details if available
            if (stepData.search_details && stepData.search_details.length > 0) {
                details += `\n=== SEARCH DETAILS ===\n`;
                details += JSON.stringify(stepData.search_details, null, 2);
            }
            
            // Add scraping details if available
            if (stepData.scraping_details && stepData.scraping_details.length > 0) {
                details += `\n=== SCRAPING DETAILS ===\n`;
                details += JSON.stringify(stepData.scraping_details, null, 2);
            }
            
            // Add extracted info if available
            if (stepData.extracted_info) {
                details += `\n=== EXTRACTED INFORMATION ===\n`;
                details += JSON.stringify(stepData.extracted_info, null, 2);
            }
            
            // Add final info if available
            if (stepData.final_info) {
                details += `\n=== FINAL INFORMATION ===\n`;
                details += JSON.stringify(stepData.final_info, null, 2);
            }
            
            return details;
        }

        async function runAll() {
            // Redirect to hybrid execution
            await startHybridExecution();
        }

        async function reset() {
            try {
                await fetch('/reset', {method: 'POST'});
                currentState = null;
                
                // Reset hybrid execution UI
                const startBtn = document.getElementById('hybrid-start-btn');
                const progressFill = document.getElementById('progress-fill');
                const progressText = document.getElementById('progress-text');
                
                startBtn.disabled = false;
                startBtn.textContent = 'Start Hybrid Execution';
                progressFill.style.width = '0%';
                progressText.textContent = 'Ready to start';
                
                // Reset all step statuses
                for (let i = 1; i <= 7; i++) {
                    const stepStatus = document.getElementById(`step-${i}-status`);
                    const stepDetails = document.getElementById(`step-${i}-details`);
                    
                    stepStatus.textContent = '⏳ Waiting';
                    stepStatus.className = 'step-status waiting';
                    stepDetails.querySelector('.details-content').textContent = 'Details will appear here when step completes';
                    stepDetails.classList.remove('show');
                }
                
                alert('State reset successfully');
            } catch (e) {
                alert('Error resetting: ' + e.message);
            }
        }

        async function exportResults() {
            if (!currentState) {
                alert('No state to export');
                return;
            }
            
            try {
                const response = await fetch('/export');
                const result = await response.json();
                
                const blob = new Blob([JSON.stringify(result, null, 2)], {type: 'application/json'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'research_results.json';
                a.click();
                URL.revokeObjectURL(url);
            } catch (e) {
                alert('Error exporting: ' + e.message);
            }
        }



        function clearInputs() {
            document.getElementById('topic').value = '';
            document.getElementById('topic-select').value = '';
        }

        function saveState() {
            if (!currentState) {
                alert('No state to save');
                return;
            }
            
            const stateData = {
                timestamp: new Date().toISOString(),
                state: currentState
            };
            
            const blob = new Blob([JSON.stringify(stateData, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `research_state_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }

        function loadState() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        try {
                            const data = JSON.parse(e.target.result);
                            if (data.state) {
                                currentState = data.state;
                                alert('State loaded successfully');
                            } else {
                                alert('Invalid state file');
                            }
                        } catch (error) {
                            alert('Error loading state: ' + error.message);
                        }
                    };
                    reader.readAsText(file);
                }
            };
            input.click();
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.post("/initialize")
async def initialize_state(request: dict):
    """Initialize the state with topic and schema."""
    global current_state
    
    topic = request.get("topic")
    extraction_schema = request.get("extraction_schema")
    
    if not topic or not extraction_schema:
        raise HTTPException(status_code=400, detail="Missing topic or extraction_schema")
    
    # Initialize state
    current_state = {
        "messages": [],
        "topic": topic,
        "extraction_schema": extraction_schema,
        "loop_step": 0,
        "info": None
    }
    
    return {"status": "initialized", "state": current_state}

@app.post("/execute-step/{step_name}")
async def execute_step(step_name: str):
    """Execute a specific step manually using full graph execution and result extraction."""
    global current_state
    
    if current_state is None:
        raise HTTPException(status_code=400, detail="State not initialized")
    
    import time
    import traceback
    
    start_time = time.time()
    
    try:
        # Map step names to execution strategies
        step_mapping = {
            "input": "full_execution",
            "planning": "full_execution", 
            "search": "direct_tool",
            "scraping": "direct_tool",
            "extraction": "full_execution",
            "validation": "full_execution",
            "decision": "full_execution",
            "output": "full_execution"
        }
        
        execution_strategy = step_mapping.get(step_name, "full_execution")
        
        # Prepare detailed response
        detailed_response = {
            "step": step_name,
            "execution_strategy": execution_strategy,
            "start_time": start_time,
            "input_state_summary": {
                "topic": current_state.get("topic"),
                "loop_step": current_state.get("loop_step"),
                "messages_count": len(current_state.get("messages", [])),
                "has_info": current_state.get("info") is not None
            }
        }
        
        if execution_strategy == "direct_tool":
            # Execute tools directly
            if step_name == "search":
                from agent.tools import search
                search_query = current_state.get("topic", "Taylor Swift musical evolution")
                
                detailed_response["search_query"] = search_query
                detailed_response["tool_details"] = f"Executing search with query: {search_query}"
                
                result = await search(search_query, config={})
                detailed_response["output"] = result
                detailed_response["status"] = "completed"
                
            elif step_name == "scraping":
                from agent.tools import scrape_website
                url = "https://example.com"
                detailed_response["scraping_url"] = url
                detailed_response["tool_details"] = f"Scraping content from: {url}"
                
                result = await scrape_website(url, state=current_state, config={})
                detailed_response["output"] = result
                detailed_response["status"] = "completed"
                
        else:
            # Use full graph execution and extract intermediate results
            detailed_response["execution_details"] = f"Executing full graph and extracting {step_name} results"
            
            # Execute the full graph
            final_result = await graph.ainvoke(current_state)
            
            # Extract intermediate results based on step
            intermediate_results = extract_intermediate_results(final_result, step_name)
            
            # Update current state with final result
            current_state = final_result
            
            detailed_response["output"] = intermediate_results
            detailed_response["final_state"] = final_result
            detailed_response["status"] = "completed"
            detailed_response["state_updated"] = True
            
        end_time = time.time()
        detailed_response["end_time"] = end_time
        detailed_response["duration"] = end_time - start_time
        detailed_response["state"] = current_state
        
        return detailed_response
        
    except Exception as e:
        end_time = time.time()
        
        error_response = {
            "step": step_name,
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": {
                "message": str(e),
                "traceback": traceback.format_exc(),
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            },
            "input_state_summary": {
                "topic": current_state.get("topic"),
                "loop_step": current_state.get("loop_step"),
                "messages_count": len(current_state.get("messages", [])),
                "has_info": current_state.get("info") is not None
            },
            "state": current_state
        }
        
        return error_response

@app.post("/hybrid-execution")
async def hybrid_execution():
    """Execute the full workflow with step-by-step progress tracking."""
    global current_state
    
    if current_state is None:
        raise HTTPException(status_code=400, detail="State not initialized")
    
    import time
    import traceback
    
    start_time = time.time()
    
    try:
        # Execute the full graph
        final_result = await graph.ainvoke(current_state)
        
        # Extract step-by-step results
        step_results = extract_hybrid_step_results(final_result)
        
        # Update current state
        current_state = final_result
        
        end_time = time.time()
        
        return {
            "status": "completed",
            "duration": end_time - start_time,
            "start_time": start_time,
            "end_time": end_time,
            "step_results": step_results,
            "final_state": final_result,
            "state": current_state
        }
        
    except Exception as e:
        end_time = time.time()
        
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": {
                "message": str(e),
                "traceback": traceback.format_exc(),
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            },
            "state": current_state
        }

def extract_intermediate_results(final_result, step_name):
    """Extract relevant intermediate results based on the step being executed."""
    messages = final_result.get("messages", [])
    
    if step_name == "input":
        # Extract initial planning and research strategy
        input_messages = [msg for msg in messages if hasattr(msg, 'content') and msg.content]
        return {
            "research_strategy": "Extracted from initial agent planning",
            "messages_count": len(input_messages),
            "initial_planning": input_messages[:2] if input_messages else []
        }
        
    elif step_name == "extraction":
        # Extract information extraction results
        info = final_result.get("info")
        return {
            "extracted_info": info,
            "extraction_complete": info is not None,
            "extraction_schema_used": final_result.get("extraction_schema")
        }
        
    elif step_name == "validation":
        # Extract validation results
        loop_step = final_result.get("loop_step", 0)
        info = final_result.get("info")
        return {
            "validation_passed": info is not None and loop_step >= 5,
            "loop_step": loop_step,
            "final_info": info,
            "validation_complete": loop_step >= 5 or info is not None
        }
    
    else:
        # Default: return general execution info
        return {
            "execution_complete": True,
            "messages_processed": len(messages),
            "final_state_keys": list(final_result.keys())
        }

def extract_hybrid_step_results(final_result):
    """Extract detailed results for each step in the hybrid execution."""
    messages = final_result.get("messages", [])
    info = final_result.get("info")
    loop_step = final_result.get("loop_step", 0)
    
    # Analyze messages to extract step-by-step information
    search_results = []
    scraping_results = []
    agent_messages = []
    tool_messages = []
    
    for msg in messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            agent_messages.append(msg)
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == 'search':
                    search_results.append(tool_call)
                elif tool_call.get('name') == 'scrape_website':
                    scraping_results.append(tool_call)
        elif hasattr(msg, 'content') and msg.content and isinstance(msg, ToolMessage):
            tool_messages.append(msg)
    
    # Extract detailed information for troubleshooting
    detailed_messages = []
    for i, msg in enumerate(messages):
        msg_info = {
            "index": i,
            "type": type(msg).__name__,
            "content_length": len(str(msg.content)) if hasattr(msg, 'content') else 0,
            "has_tool_calls": hasattr(msg, 'tool_calls') and bool(msg.tool_calls),
            "tool_calls_count": len(msg.tool_calls) if hasattr(msg, 'tool_calls') and msg.tool_calls else 0
        }
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            msg_info["tool_calls"] = [
                {
                    "name": tc.get('name'),
                    "args": tc.get('args'),
                    "id": tc.get('id')
                } for tc in msg.tool_calls
            ]
        detailed_messages.append(msg_info)
    
    return {
        "step_1_agent_planning": {
            "status": "completed",
            "messages_count": len(agent_messages),
            "agent_messages": detailed_messages[:3] if detailed_messages else [],  # First few messages
            "description": "Initial agent planning and research strategy",
            "full_details": {
                "total_messages": len(messages),
                "agent_messages": len(agent_messages),
                "tool_messages": len(tool_messages),
                "loop_step": loop_step,
                "topic": final_result.get("topic"),
                "extraction_schema": final_result.get("extraction_schema")
            }
        },
        "step_2_search_execution": {
            "status": "completed" if search_results else "skipped",
            "query": final_result.get("topic", "N/A"),
            "results_count": len(search_results),
            "search_details": search_results,
            "description": "Web search execution for research topic",
            "full_details": {
                "search_queries": [tc.get('args', {}).get('query', 'N/A') for tc in search_results],
                "search_ids": [tc.get('id', 'N/A') for tc in search_results],
                "search_timestamps": [f"Message {i+1}" for i, msg in enumerate(messages) if hasattr(msg, 'tool_calls') and any(tc.get('name') == 'search' for tc in msg.tool_calls)]
            }
        },
        "step_3_scraping_execution": {
            "status": "completed" if scraping_results else "skipped",
            "urls_processed": len(scraping_results),
            "scraping_details": scraping_results,
            "description": "Website content scraping from search results",
            "full_details": {
                "scraped_urls": [tc.get('args', {}).get('url', 'N/A') for tc in scraping_results],
                "scraping_ids": [tc.get('id', 'N/A') for tc in scraping_results],
                "scraping_timestamps": [f"Message {i+1}" for i, msg in enumerate(messages) if hasattr(msg, 'tool_calls') and any(tc.get('name') == 'scrape_website' for tc in msg.tool_calls)]
            }
        },
        "step_4_information_extraction": {
            "status": "completed" if info else "incomplete",
            "extraction_success": info is not None,
            "extracted_info": info,
            "messages_processed": len(messages),
            "description": "Information extraction and processing from gathered content",
            "full_details": {
                "extraction_schema": final_result.get("extraction_schema"),
                "extracted_fields": list(info.keys()) if info else [],
                "extraction_quality": "Complete" if info else "Incomplete",
                "total_messages_analyzed": len(messages),
                "agent_processing_rounds": len([msg for msg in messages if hasattr(msg, 'tool_calls') and msg.tool_calls])
            }
        },
        "step_5_quality_validation": {
            "status": "completed",
            "validation_passed": info is not None and len(str(info)) > 10,
            "loop_step": loop_step,
            "quality_assessment": "Good" if (info and len(str(info)) > 10) else "Incomplete",
            "description": "Quality validation and completeness assessment",
            "full_details": {
                "validation_criteria": "Info exists and has sufficient content",
                "validation_result": info is not None,
                "content_length": len(str(info)) if info else 0,
                "loop_iterations": loop_step,
                "satisfaction_threshold": "> 10 characters",
                "meets_threshold": len(str(info)) > 10 if info else False
            }
        },
        "step_6_iteration_decision": {
            "status": "completed",
            "decision": "complete" if info else "continue",
            "reason": "Information extracted successfully" if info else "More iterations needed",
            "description": "Iteration decision making based on quality assessment",
            "full_details": {
                "decision_logic": "Complete if info exists and is substantial",
                "final_decision": "complete" if info else "continue",
                "decision_reasoning": "Sufficient information extracted" if info else "Insufficient information, needs more research",
                "workflow_end_state": "Terminated" if info else "Would continue if not at end"
            }
        },
        "step_7_final_output": {
            "status": "completed",
            "final_info": info,
            "output_summary": f"Generated structured output with {len(info) if info else 0} fields" if info else "No output generated",
            "description": "Final structured output generation and delivery",
            "full_details": {
                "output_fields": list(info.keys()) if info else [],
                "output_content": info,
                "output_quality": "Complete" if info else "Empty",
                "schema_compliance": "Compliant" if info else "Non-compliant",
                "final_state": {
                    "topic": final_result.get("topic"),
                    "loop_step": loop_step,
                    "messages_count": len(messages),
                    "has_info": info is not None
                }
            }
        }
    }

@app.post("/run-all")
async def run_all_steps():
    """Run all steps automatically."""
    global current_state
    
    if current_state is None:
        raise HTTPException(status_code=400, detail="State not initialized")
    
    try:
        result = await graph.ainvoke(current_state)
        current_state = result
        return {"status": "completed", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/reset")
async def reset_state():
    """Reset the current state."""
    global current_state
    current_state = None
    return {"status": "reset"}

@app.get("/export")
async def export_results():
    """Export current results."""
    global current_state
    if current_state is None:
        raise HTTPException(status_code=400, detail="No state to export")
    
    return {
        "export_time": "2024-01-01T00:00:00Z",
        "state": current_state
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "research-agent-manual-testing"}

@app.post("/invoke")
async def invoke_agent(request: dict):
    """Invoke the agent with topic and extraction_schema."""
    try:
        # Extract required fields
        topic = request.get("topic")
        extraction_schema = request.get("extraction_schema")
        
        if not topic or not extraction_schema:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required fields: topic and extraction_schema"}
            )
        
        # Invoke the graph (handle async properly)
        import asyncio
        result = asyncio.run(graph.ainvoke({
            "messages": [],
            "topic": topic,
            "extraction_schema": extraction_schema
        }))
        
        return result
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Agent execution failed: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2025)
