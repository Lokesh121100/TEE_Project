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

    // Initial load
    checkHealth();
    loadMetrics();
    loadAuditLogs();
    setInterval(checkHealth, 30000);
    setInterval(loadMetrics, 60000);
});
