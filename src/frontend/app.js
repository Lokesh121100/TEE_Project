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
        // Remove active class from previous dots
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

    // ---- Form Submission with SSE ----
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const description = descriptionInput.value.trim();
        if (!description) return;

        // Reset UI
        submitBtn.disabled = true;
        submitBtn.innerHTML = "Processing...";
        resultContainer.style.display = "none";
        progressBar.style.display = "block";
        clearReasoningLog();
        setAgentState("working", "Processing...");

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
                                // Mark all dots as done
                                reasoningLog.querySelectorAll(".step-dot.active").forEach(d => {
                                    d.classList.remove("active");
                                    d.classList.add("done");
                                });
                                addReasoningStep("Complete", true);
                                setAgentState("done", "Completed");
                                progressBar.style.display = "none";
                                resultContainer.innerHTML = event.data;
                                resultContainer.style.display = "block";
                            } else {
                                addReasoningStep(event.step, false);
                                setAgentState("working", event.step);
                            }
                        } catch (parseErr) {
                            // skip
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
        progressBar.style.display = "none";
        setAgentState("idle", "Ready");
        reasoningLog.innerHTML = `
            <div class="reasoning-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <p>Submit an incident to see ARIA's reasoning process in real-time</p>
            </div>`;
    });

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

    // ---- Escalation to Human ----
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

    // Show escalation option when result is displayed
    const originalShowResult = (html, title, ticket) => {
        resultContainer.innerHTML = html;
        resultContainer.style.display = "block";
        if (escalationActions) {
            escalationActions.style.display = "flex";
        }
        currentTicketId = ticket || "TICKET-001";
        conversationTranscript.push(`User inquiry processed. Result: ${title}`);
        updateTranscriptDisplay();
    };

    // Update transcript display in modal
    const updateTranscriptDisplay = () => {
        if (!escalationTranscript) return;
        if (conversationTranscript.length === 0) {
            escalationTranscript.innerHTML = "<p style='color: #6e7681;'>No conversation yet</p>";
        } else {
            escalationTranscript.innerHTML = conversationTranscript
                .map((msg, i) => `<p style="margin: 4px 0; color: #8b949e;"><strong>[${i+1}]</strong> ${msg}</p>`)
                .join("");
        }
    };

    // Modal open
    if (escalationBtn) {
        escalationBtn.addEventListener("click", () => {
            modal.style.display = "flex";
            escalationReason.focus();
        });
    }

    // Modal close
    const closeModal = () => {
        if (modal) modal.style.display = "none";
        if (escalationReason) escalationReason.value = "";
        if (escalationPriority) escalationPriority.value = "Medium";
    };

    if (modalClose) modalClose.addEventListener("click", closeModal);
    if (modalCancel) modalCancel.addEventListener("click", closeModal);

    // Modal submit
    if (modalSubmit) {
        modalSubmit.addEventListener("click", async () => {
            const reason = escalationReason.value.trim();
            if (!reason) {
                alert("Please provide a reason for escalation");
                return;
            }

            // Disable submit button
            modalSubmit.disabled = true;
            modalSubmit.textContent = "Submitting...";

            try {
                const response = await fetch("/api/escalate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        ticket_id: currentTicketId,
                        reason: reason,
                        priority: escalationPriority.value,
                        transcript: conversationTranscript
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Show success message
                    closeModal();
                    const successHtml = `
                        <div style='background: #0d3b66; color: #76c893; padding: 20px; border-radius: 12px; border: 1px solid #2a9d8f; text-align: center;'>
                            <h2 style='color: #76c893; margin-bottom: 10px;'>✓ Escalated Successfully</h2>
                            <p><strong>Reference Number:</strong> <span style='font-family: monospace; font-size: 1.1em;'>${data.escalation_number}</span></p>
                            <p><strong>Assigned Team:</strong> ${data.assigned_team}</p>
                            <p><strong>SLA:</strong> ${data.sla_minutes} minutes response time</p>
                            <p style='margin-top: 15px; color: #90e0ef;'>${data.message}</p>
                        </div>
                    `;
                    resultContainer.innerHTML = successHtml;
                    escalationActions.style.display = "none";

                    // Reset conversation
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

    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // Initial load
    checkHealth();
    loadMetrics();
    loadAuditLogs();
    setInterval(checkHealth, 30000);
    setInterval(loadMetrics, 60000);
});
