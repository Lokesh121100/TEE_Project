document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const form = document.getElementById("incident-form");
    const descriptionInput = document.getElementById("description");
    const clearBtn = document.getElementById("clear-btn");
    const submitBtn = document.getElementById("submit-btn");
    const aiStatus = document.getElementById("ai-status");
    const resultContainer = document.getElementById("result-container");
    const reasoningLog = document.getElementById("reasoning-log");
    const agentStatus = document.getElementById("agent-status");
    const progressBar = document.getElementById("progress-bar");
    const statusIndicator = agentStatus.querySelector(".status-indicator");

    const defaultBtnHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2L11 13"></path><path d="M22 2l-7 20-4-9-9-4 20-7z"></path></svg> Process Incident`;

    // ---- Sidebar Navigation ----
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            item.classList.add("active");
            const section = item.dataset.section;
            document.querySelectorAll(".content-section").forEach(s => s.classList.remove("active"));
            const target = document.getElementById("section-" + section);
            if (target) target.classList.add("active");

            // Load section-specific data
            if (section === "analytics") {
                loadConfusionMatrix();
                loadSLADashboard();
            }
            if (section === "dex") {
                loadDeviceHealth();
                loadLockerStatus();
                // Reset VPN panel to idle state when navigating to DEX
                const vpnContainer = document.getElementById("vpn-diagnostics-container");
                if (vpnContainer && vpnContainer.querySelector(".vpn-running")) {
                    vpnContainer.innerHTML = `
                        <div class="vpn-idle">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                            <p style="color: #94a3b8; margin: 10px 0 16px;">Click to run the VPN diagnostic pipeline.</p>
                            <button class="btn-primary" onclick="runVPNDiagnose()">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                                Run VPN Diagnostics
                            </button>
                        </div>`;
                }
            }
        });
    });

    // ---- Quick Scenario Chips ----
    document.querySelectorAll(".scenario-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            descriptionInput.value = chip.dataset.text;
            descriptionInput.focus();
        });
    });

    // ---- Reasoning Log ----
    let stepCount = 0;

    function clearReasoningLog() {
        reasoningLog.innerHTML = "";
        stepCount = 0;
    }

    function addReasoningStep(text, isDone) {
        stepCount++;
        reasoningLog.querySelectorAll(".step-dot.active").forEach(d => {
            d.classList.remove("active");
            d.classList.add("done");
        });

        const step = document.createElement("div");
        step.className = "reasoning-step";
        step.innerHTML = `
            <div class="step-dot ${isDone ? 'done' : 'active'}"></div>
            <div class="step-text">${text}</div>
        `;
        reasoningLog.appendChild(step);
        reasoningLog.scrollTop = reasoningLog.scrollHeight;
    }

    function setAgentState(state, text) {
        aiStatus.textContent = text || "Ready";
        statusIndicator.className = "status-indicator " + state;
    }

    // ---- Escalation State ----
    let currentTicketId = null;
    let conversationTranscript = [];

    const escalationBtn = document.getElementById("escalate-btn");
    const escalationActions = document.getElementById("escalation-actions");
    const modal = document.getElementById("escalation-modal");
    const modalClose = document.getElementById("modal-close");
    const modalCancel = document.getElementById("modal-cancel");
    const modalSubmit = document.getElementById("modal-submit");
    const escalationReason = document.getElementById("escalation-reason");
    const escalationPriority = document.getElementById("escalation-priority");
    const escalationTranscript = document.getElementById("escalation-transcript");

    // Update transcript display in modal
    const updateTranscriptDisplay = () => {
        if (!escalationTranscript) return;
        if (conversationTranscript.length === 0) {
            escalationTranscript.innerHTML = "<p style='color: #6e7681;'>No conversation yet</p>";
        } else {
            escalationTranscript.innerHTML = conversationTranscript
                .map((msg, i) => `<p style="margin: 4px 0; color: #8b949e;"><strong>[${i + 1}]</strong> ${msg}</p>`)
                .join("");
        }
    };

    // Show result and activate escalation button
    const showResult = (html, description, incidentNumber) => {
        resultContainer.innerHTML = html;
        resultContainer.style.display = "block";

        // Show escalation button
        if (escalationActions) {
            escalationActions.style.display = "flex";
        }

        // Set ticket ID
        currentTicketId = incidentNumber || "TICKET-" + Date.now();

        // Add to transcript
        const now = new Date().toLocaleTimeString();
        conversationTranscript.push(`[${now}] User: ${description.substring(0, 80)}...`);
        conversationTranscript.push(`[${now}] IntelSoft AI: Incident processed as ${currentTicketId}`);
        updateTranscriptDisplay();
    };

    // ---- Form Submission with SSE ----
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const description = descriptionInput.value.trim();
        if (!description) return;

        // Reset UI
        submitBtn.disabled = true;
        submitBtn.innerHTML = "Processing...";
        resultContainer.style.display = "none";
        if (escalationActions) escalationActions.style.display = "none";
        progressBar.style.display = "block";
        clearReasoningLog();
        setAgentState("working", "Processing...");
        conversationTranscript = [];
        currentTicketId = null;

        try {
            const response = await fetch("/api/incident/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ description })
            });

            if (!response.ok) {
                const err = await response.json();
                setAgentState("idle", "Error: " + err.error);
                progressBar.style.display = "none";
                submitBtn.disabled = false;
                submitBtn.innerHTML = defaultBtnHTML;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const event = JSON.parse(line.substring(6));
                            if (event.step === "done") {
                                reasoningLog.querySelectorAll(".step-dot.active").forEach(d => {
                                    d.classList.remove("active");
                                    d.classList.add("done");
                                });
                                addReasoningStep("Complete", true);
                                setAgentState("done", "Completed");
                                progressBar.style.display = "none";

                                // Extract incident number from HTML
                                const incMatch = event.data.match(/INC[\w-]+/);
                                const incidentNumber = incMatch ? incMatch[0] : "TICKET-" + Date.now();

                                showResult(event.data, description, incidentNumber);

                                // Check if replacement/locker scenario
                                if (description.toLowerCase().includes("laptop") ||
                                    description.toLowerCase().includes("device") ||
                                    description.toLowerCase().includes("replacement") ||
                                    description.toLowerCase().includes("spill") ||
                                    description.toLowerCase().includes("broken")) {
                                    loadLockerInfo(incidentNumber);
                                }

                                // GAP 5: Refresh metrics and audit trail immediately after incident
                                loadMetrics();
                                loadAuditLogs();

                            } else {
                                addReasoningStep(event.step, false);
                                setAgentState("working", event.step);
                            }
                        } catch (parseErr) {
                            // skip malformed events
                        }
                    }
                }
            }

        } catch (error) {
            setAgentState("idle", "Network error");
            addReasoningStep("Error: " + error.message, true);
            progressBar.style.display = "none";
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = defaultBtnHTML;
        }
    });

    // ---- Clear Button ----
    clearBtn.addEventListener("click", () => {
        descriptionInput.value = "";
        resultContainer.style.display = "none";
        resultContainer.innerHTML = "";
        if (escalationActions) escalationActions.style.display = "none";
        progressBar.style.display = "none";
        setAgentState("idle", "Ready");
        conversationTranscript = [];
        currentTicketId = null;
        reasoningLog.innerHTML = `
            <div class="reasoning-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <p>Submit an incident to see IntelSoft AI's reasoning process in real-time</p>
            </div>`;
    });

    // ---- Modal Controls ----
    const closeModal = () => {
        if (modal) modal.style.display = "none";
        if (escalationReason) escalationReason.value = "";
        if (escalationPriority) escalationPriority.value = "Medium";
    };

    // Open modal
    if (escalationBtn) {
        escalationBtn.addEventListener("click", () => {
            updateTranscriptDisplay();
            modal.style.display = "flex";
            if (escalationReason) escalationReason.focus();
        });
    }

    // Close via X, Cancel, click outside, or ESC
    if (modalClose) modalClose.addEventListener("click", closeModal);
    if (modalCancel) modalCancel.addEventListener("click", closeModal);

    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeModal();
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal && modal.style.display !== "none") {
            closeModal();
        }
    });

    // Submit escalation
    if (modalSubmit) {
        modalSubmit.addEventListener("click", async () => {
            const reason = escalationReason ? escalationReason.value.trim() : "";
            if (!reason) {
                alert("Please provide a reason for escalation");
                return;
            }

            modalSubmit.disabled = true;
            modalSubmit.textContent = "Submitting...";

            try {
                const response = await fetch("/api/escalate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        ticket_id: currentTicketId || "TICKET-001",
                        reason: reason,
                        priority: escalationPriority ? escalationPriority.value : "Medium",
                        transcript: conversationTranscript
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    closeModal();
                    const successHtml = `
                        <div style='background: linear-gradient(135deg, #0d3b66, #0c2d4f); color: #76c893; padding: 24px; border-radius: 12px; border: 1px solid #2a9d8f; text-align: center;'>
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#76c893" stroke-width="2" style="margin-bottom: 12px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                            <h2 style='color: #76c893; margin: 0 0 16px;'>Escalated Successfully</h2>
                            <div style='background: rgba(255,255,255,0.05); border-radius: 8px; padding: 16px; margin-bottom: 16px;'>
                                <p style='margin: 6px 0;'><strong>Reference:</strong> <span style='font-family: monospace; font-size: 1.1em; color: #90e0ef;'>${data.escalation_number}</span></p>
                                <p style='margin: 6px 0;'><strong>Assigned To:</strong> ${data.assigned_team}</p>
                                <p style='margin: 6px 0;'><strong>SLA:</strong> ${data.sla_minutes} minutes response time</p>
                            </div>
                            <p style='margin: 0; color: #90e0ef; font-size: 0.9em;'>${data.message}</p>
                        </div>
                    `;
                    resultContainer.innerHTML = successHtml;
                    if (escalationActions) escalationActions.style.display = "none";
                    conversationTranscript = [];
                    currentTicketId = null;
                } else {
                    alert("Escalation failed: " + (data.error || "Unknown error"));
                }
            } catch (error) {
                alert("Error: " + error.message);
            } finally {
                modalSubmit.disabled = false;
                modalSubmit.textContent = "Submit Escalation";
            }
        });
    }

    // ---- Health Check ----
    const checkHealth = async () => {
        try {
            const res = await fetch("/api/health");
            if (!res.ok) return;
            const data = await res.json();

            const setHealth = (dotId, valId, text) => {
                const dot = document.getElementById(dotId);
                const val = document.getElementById(valId);
                if (!dot || !val) return;
                val.textContent = text.replace(/[^a-zA-Z0-9 .]/g, "").trim();
                if (text.includes("Online") || text.includes("Ready") || text.includes("Reachable")) {
                    dot.className = "health-dot online";
                } else {
                    dot.className = "health-dot error";
                }
            };

            setHealth("dot-ollama", "health-ollama", data.ollama);
            setHealth("dot-model", "health-model", data.model);
            setHealth("dot-snow", "health-snow", data.servicenow);
        } catch (err) {
            // silent
        }
    };

    // ---- Metrics ----
    const loadMetrics = async () => {
        try {
            const res = await fetch("/api/metrics");
            if (!res.ok) return;
            const m = await res.json();
            const set = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val || "--";
            };
            set("metric-mttr", m.mttr);
            set("metric-accuracy", m.accuracy);
            set("metric-satisfaction", m.satisfaction);
            set("metric-total", m.total);
        } catch (err) {
            // silent
        }
    };

    // ---- Audit Logs ----
    const loadAuditLogs = async () => {
        try {
            const res = await fetch("/api/logs");
            if (!res.ok) return;
            const data = await res.json();
            const container = document.getElementById("audit-log-container");
            if (container && data.html) {
                container.innerHTML = data.html;
            }
        } catch (err) {
            // silent
        }
    };

    // ---- Confusion Matrix ----
    const loadConfusionMatrix = async () => {
        const container = document.getElementById("confusion-matrix-container");
        if (!container) return;
        try {
            const res = await fetch("/api/confusion-matrix");
            if (!res.ok) return;
            const data = await res.json();
            const matrix = data.matrix || {};
            const catCounts = data.category_counts || {};
            const subcats = data.subcategories || {};
            const total = (data.metrics && data.metrics.total) || 0;

            const getColor = (val) => {
                if (val >= 88) return "#10b981";
                if (val >= 75) return "#f59e0b";
                return "#ef4444";
            };

            const categories = ["software", "access", "network", "hardware"];

            // Build subcategory breakdown grouped by category
            const subByCategory = {};
            categories.forEach(cat => { subByCategory[cat] = []; });
            Object.entries(subcats).forEach(([key, count]) => {
                const [cat, subcat] = key.split("/");
                if (subByCategory[cat]) subByCategory[cat].push({ subcat, count });
            });
            // Sort subcategories by count desc
            categories.forEach(cat => {
                subByCategory[cat].sort((a, b) => b.count - a.count);
            });

            let html = `<div class="cm-header">AI Classification Accuracy — Live Audit Data</div><div class="cm-grid">`;
            categories.forEach(cat => {
                const val = matrix[cat] || 0;
                const count = catCounts[cat] || 0;
                const color = getColor(val);
                const subs = subByCategory[cat] || [];
                const subsHtml = subs.slice(0, 3).map(s =>
                    `<span class="cm-subcat">${s.subcat} <em>(${s.count})</em></span>`
                ).join("");
                html += `
                    <div class="cm-cell">
                        <div class="cm-category">${cat.charAt(0).toUpperCase() + cat.slice(1)}</div>
                        <div class="cm-value" style="color: ${color};">${val}%</div>
                        <div class="cm-bar-wrap"><div class="cm-bar" style="width: ${val}%; background: ${color};"></div></div>
                        <div class="cm-count">${count} tickets</div>
                        <div class="cm-subcats">${subsHtml}</div>
                    </div>`;
            });
            html += `</div><p class="cm-note">Confidence-weighted accuracy from ${total} audit log entries. Real-time.</p>`;
            container.innerHTML = html;
        } catch (err) {
            if (container) container.innerHTML = "<p class='text-muted'>Confusion matrix will populate after processing incidents.</p>";
        }
    };

    // ---- SLA Dashboard ----
    const loadSLADashboard = async () => {
        const container = document.getElementById("sla-dashboard-container");
        if (!container) return;
        const categories = [
            { name: "Network (VPN/WiFi)", category: "network", priority: "High" },
            { name: "Access (Password)", category: "access", priority: "Medium" },
            { name: "Hardware (Device)", category: "hardware", priority: "High" },
            { name: "Software (VDI/App)", category: "software", priority: "Medium" },
        ];

        try {
            const results = await Promise.all(categories.map(c =>
                fetch("/api/sla-prediction", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ category: c.category, priority: c.priority })
                }).then(r => r.json())
            ));

            let html = '<div class="sla-grid">';
            results.forEach((r, i) => {
                const riskNum = parseInt(r.breach_risk) || 0;
                const riskColor = riskNum >= 70 ? "#ef4444" : riskNum >= 40 ? "#f59e0b" : "#10b981";
                html += `
                    <div class="sla-card">
                        <div class="sla-name">${categories[i].name}</div>
                        <div class="sla-risk" style="color: ${riskColor};">${r.breach_risk}</div>
                        <div class="sla-label">Breach Risk</div>
                        <div class="sla-sla">${r.sla_minutes}min SLA</div>
                        <div class="sla-rec">${r.recommendation}</div>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        } catch (err) {
            if (container) container.innerHTML = "<p class='text-muted'>SLA data loading...</p>";
        }
    };

    // ---- DEX Device Health ----
    const loadDeviceHealth = async () => {
        const container = document.getElementById("dex-devices-container");
        if (!container) return;
        container.innerHTML = "<p class='text-muted'>Loading device health data...</p>";
        try {
            const res = await fetch("/api/device-health");
            if (!res.ok) return;
            const data = await res.json();
            const devices = data.devices || [];

            const getScoreColor = (score) => {
                if (score >= 7) return "#10b981";
                if (score >= 5) return "#f59e0b";
                return "#ef4444";
            };

            const getStatusBadge = (status) => {
                const colors = { Good: "#10b981", Warning: "#f59e0b", Critical: "#ef4444" };
                return `<span style="color: ${colors[status] || '#94a3b8'}; font-weight: 600; font-size: 0.8rem;">${status}</span>`;
            };

            let html = `
                <div class="dex-summary">
                    <span class="dex-sum-item"><strong>${devices.length}</strong> Devices Monitored</span>
                    <span class="dex-sum-item" style="color: #ef4444;"><strong>${data.at_risk}</strong> At Risk</span>
                    <span class="dex-sum-item" style="color: #10b981;"><strong>${devices.length - data.at_risk}</strong> Healthy</span>
                </div>
                <div class="dex-grid">
            `;

            devices.forEach(device => {
                const scoreColor = getScoreColor(device.score);
                html += `
                    <div class="dex-card">
                        <div class="dex-card-header">
                            <div>
                                <div class="dex-device-name">${device.name}</div>
                                <div class="dex-device-type">${device.type}</div>
                            </div>
                            ${getStatusBadge(device.status)}
                        </div>
                        <div class="dex-score" style="color: ${scoreColor};">${device.score}<span style="font-size: 1rem; color: #94a3b8;">/10</span></div>
                        <div class="dex-metrics">
                            <div class="dex-metric-row">
                                <span>CPU</span>
                                <div class="dex-bar-wrap"><div class="dex-bar" style="width: ${device.cpu}%; background: ${device.cpu > 80 ? '#ef4444' : '#2563eb'};"></div></div>
                                <span>${device.cpu}%</span>
                            </div>
                            <div class="dex-metric-row">
                                <span>RAM</span>
                                <div class="dex-bar-wrap"><div class="dex-bar" style="width: ${device.ram}%; background: ${device.ram > 85 ? '#ef4444' : '#7c3aed'};"></div></div>
                                <span>${device.ram}%</span>
                            </div>
                            <div class="dex-metric-row">
                                <span>Disk</span>
                                <div class="dex-bar-wrap"><div class="dex-bar" style="width: ${device.disk}%; background: ${device.disk > 85 ? '#ef4444' : '#10b981'};"></div></div>
                                <span>${device.disk}%</span>
                            </div>
                            ${device.battery !== null ? `
                            <div class="dex-metric-row">
                                <span>Battery</span>
                                <div class="dex-bar-wrap"><div class="dex-bar" style="width: ${device.battery}%; background: ${device.battery < 30 ? '#ef4444' : '#f59e0b'};"></div></div>
                                <span>${device.battery}%</span>
                            </div>` : ''}
                        </div>
                        ${device.score < 5 ? `
                        <button class="btn-remediate" onclick="remediateDevice('${device.name}', this)">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 15l-6 6-6-6m0-8l6-6 6 6"></path></svg>
                            Auto-Remediate
                        </button>` : `<div class="dex-healthy">Device Healthy</div>`}
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        } catch (err) {
            if (container) container.innerHTML = "<p class='text-muted'>Device health data unavailable.</p>";
        }
    };

    // ---- Locker Info (for replacement tickets) ----
    const loadLockerInfo = async (ticketId) => {
        try {
            const res = await fetch("/api/locker/assign", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ticket_id: ticketId, device_type: "laptop" })
            });
            if (!res.ok) return;
            const data = await res.json();

            const lockerDiv = document.createElement("div");
            lockerDiv.className = "locker-banner";
            lockerDiv.innerHTML = `
                <div class="locker-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M9 9h6v6H9z"></path></svg>
                </div>
                <div class="locker-info">
                    <div class="locker-title">Smart Locker Assigned</div>
                    <div class="locker-detail">Locker <strong>${data.locker_number}</strong> — ${data.location}</div>
                    <div class="locker-pin">Collection PIN: <strong style="font-family: monospace; font-size: 1.1em; letter-spacing: 3px;">${data.collection_pin}</strong></div>
                    <div class="locker-expiry">Valid for ${data.expiry_hours} hours</div>
                </div>
            `;
            resultContainer.appendChild(lockerDiv);
            loadLockerStatus(); // update the grid
        } catch (err) {
            // silent - locker not always applicable
        }
    };

    // ---- VPN Auto-Remediation ----
    window.runVPNDiagnose = async () => {
        const container = document.getElementById("vpn-diagnostics-container");
        if (!container) return;

        container.innerHTML = `
            <div class="vpn-running">
                <div class="vpn-spinner"></div>
                <span>IntelSoft AI running VPN diagnostic pipeline...</span>
            </div>`;

        try {
            const res = await fetch("/api/vpn/diagnose", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({})
            });
            if (!res.ok) throw new Error("API error");
            const data = await res.json();

            const statusColor = data.auto_resolved ? "#10b981" : "#ef4444";
            const statusLabel = data.auto_resolved ? "AUTO-RESOLVED" : "NEEDS ATTENTION";

            let html = `
                <div class="vpn-result-header">
                    <div class="vpn-status-badge" style="color: ${statusColor}; border-color: ${statusColor};">${statusLabel}</div>
                    <div class="vpn-meta">
                        <div class="vpn-meta-row"><strong>Issue:</strong> ${data.issue}</div>
                        <div class="vpn-meta-row"><strong>Root Cause:</strong> ${data.root_cause}</div>
                        <div class="vpn-meta-row"><strong>Resolved in:</strong> ${data.time_to_resolve} &nbsp;|&nbsp; <strong>AI Confidence:</strong> ${data.confidence}</div>
                        <div class="vpn-meta-row" style="color: #60a5fa;"><strong>KB Article:</strong> ${data.kb_article}</div>
                    </div>
                </div>
                <div class="vpn-steps-list">`;

            data.steps.forEach(step => {
                const ok = step.status === "ok";
                const stepColor = ok ? "#10b981" : "#ef4444";
                const icon = ok
                    ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${stepColor}" stroke-width="2.5"><path d="M20 6L9 17l-5-5"></path></svg>`
                    : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${stepColor}" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
                html += `
                    <div class="vpn-step-row">
                        <div class="vpn-step-icon">${icon}</div>
                        <div class="vpn-step-body">
                            <div class="vpn-step-title">${step.action}</div>
                            <div class="vpn-step-cmd">${step.command}</div>
                            <div class="vpn-step-detail">${step.detail}</div>
                        </div>
                        <div class="vpn-step-badge" style="color: ${stepColor};">${step.result}</div>
                    </div>`;
            });

            html += `</div>
                <button class="btn-ghost" onclick="runVPNDiagnose()" style="margin-top: 16px;">Re-run Diagnostics</button>`;
            container.innerHTML = html;

        } catch {
            container.innerHTML = `
                <p class="text-muted">VPN diagnostic service unavailable.</p>
                <button class="btn-primary" onclick="runVPNDiagnose()" style="margin-top:10px;">Retry</button>`;
        }
    };

    // ---- Auto-Remediate (DEX) ----
    window.remediateDevice = async (deviceName, btn) => {
        btn.disabled = true;
        btn.textContent = "Remediating...";
        try {
            const res = await fetch("/api/remediate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ device_name: deviceName })
            });
            const data = await res.json();
            btn.textContent = "Remediated!";
            btn.style.background = "#10b981";

            // Reload device health after 2 seconds
            setTimeout(loadDeviceHealth, 2000);
        } catch (err) {
            btn.disabled = false;
            btn.textContent = "Auto-Remediate";
        }
    };

    // ---- Dynamic Locker Status (GAP 6) ----
    const loadLockerStatus = async () => {
        const container = document.getElementById("locker-status-container");
        if (!container) return;
        try {
            const res = await fetch("/api/locker/status");
            if (!res.ok) return;
            const data = await res.json();
            const lockers = data.lockers || [];

            let html = '<div class="locker-status-grid">';
            lockers.forEach(locker => {
                const isAvailable = locker.status === "available";
                html += `
                    <div class="locker-status-card ${isAvailable ? 'available' : 'occupied'}">
                        <div class="locker-num">${locker.number}</div>
                        <div class="locker-type">${locker.type}</div>
                        <div class="locker-floor">${locker.location}</div>
                        <div class="locker-badge ${isAvailable ? 'available-badge' : 'occupied-badge'}">
                            ${isAvailable ? 'Available' : 'In Use'}
                        </div>
                        ${!isAvailable && locker.ticket && locker.ticket !== 'PRE-ASSIGNED'
                        ? `<div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;">Ticket: ${locker.ticket}</div>`
                        : ''}
                    </div>`;
            });
            html += '</div>';
            container.innerHTML = html;
        } catch {
            if (container) container.innerHTML = '<p class="text-muted">Locker status unavailable.</p>';
        }
    };

    // Initial load
    checkHealth();
    loadMetrics();
    loadAuditLogs();
    setInterval(checkHealth, 30000);
    setInterval(loadMetrics, 10000);
    setInterval(loadAuditLogs, 15000);
    setInterval(() => {
        const dexSection = document.getElementById("section-dex");
        if (dexSection && dexSection.classList.contains("active")) {
            loadDeviceHealth();
            loadLockerStatus();
        }
    }, 15000);
});
