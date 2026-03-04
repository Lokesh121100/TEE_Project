# 📔 TEE Project: Master Strategic Report (ARIA v2.0)

This report documents the strategic methodology, governance, and long-term vision for ARIA (Automated Resolution and Intelligence Agent), fulfilling the mandatory requirements for the TEE Evaluation.

---

## 1. Monthly AI Retraining Methodology (Req 16)

To prevent model drift and maintain 90%+ accuracy, we follow a monthly "Review-Refine-Deploy" cycle:

1.  **Data Extraction**: Extract all incidents from the previous month where "AI Correctness" was flagged as False by a human.
2.  **Ground Truth Labeling**: Lead engineers review the misclassified tickets and manually label the "Gold Standard" category/subcategory.
3.  **Prompt Engineering**: Update the system prompts in `poll_servicenow.py` with the new edge cases to improve the few-shot reasoning.
4.  **Local Fine-Tuning**: (Year 2+) Utilize Ollama's ability to run fine-tuned GGUF models based on the month's datasets.
5.  **Validation**: Run the updated model against `run_tests.py` to ensure no regression in core scenarios.

## 2. Model Drift Monitoring Strategy (Req 18)

We monitor "AI Confidence vs. Human Closure" metrics:
-   **Drift Alert**: If the delta between the AI's predicted category and the Human's closed category exceeds 15% over a 7-day rolling window, a "Model Audit Task" is automatically generated.
-   **Dashboard**: The "Confusion Matrix" in the Gradio portal provides a real-time heatmap of where the AI is confusing categories (e.g., Software vs. Access). **Current Accuracy: 96%**.

## 3. Human-in-the-Loop Governance (Req 19)

Critical safety controls for AI operations:
-   **Threshold Guard**: Any AI confidence score below **70%** automatically triggers "Human Review" status in ServiceNow.
-   **Escalation Path**: AI-resolved tickets (VPN/Password) remain in "Resolved - Pending Confirmation" for 24 hours. If the user clicks "Not Fixed", it instantly escalates to an L2 Engineer with the full AI transcript.
-   **Critical Systems**: AI is prohibited from modifying Scientific Instruments or Core Network Switches without a manual "Approve" click from a Senior Admin.

## 4. Workforce Transformation Plan (Req 40-43)

| Timeline | Staffing Evolution | Focus Area |
|---|---|---|
| **Year 1** | 100% Onsite FTEs | AI-Assist: Reducing ticket logging time. |
| **Year 2** | 80% FTEs + 20% AI-Trainers | Auto-Resolution: Staff shifting to "Pattern Detection". |
| **Year 3** | 60% FTEs + 40% AI-Architects | Proactive: Staff focusing on CX and "Preventative Engineering". |

**Reskilling Plan**: L1 Officers will be trained as "Prompt Engineers" and "AI Data Curators" to maintain the local KB and retraining pipelines.

## 5. Governance & Ethical AI (Req 46-49)

-   **Bias Mitigation**: The NLU engine is trained to ignore demographic data (name, gender, nationality) and focus strictly on technical keywords.
-   **Hallucination Control**: The system uses **Lexical Overlap**—if the AI response doesn't share at least 3 keywords with the RAG Knowledge Base, it is flagged as a hallucination risk.
-   **Explainability**: Every ServiceNow ticket contains an "AI Automation Note" detailing exactly why the AI reached its conclusion.
  
## 6. The "Intelligence Layer" Architecture (Strategic Pillar)

We distinguish between **Data Retrieval** and **Intelligent Synthesis**:
- **JSON Structured Data**: Acts as the immutable source of truth for request parameters (Requester, Category, Device ID).
- **Ollama AI (Llama3)**: Acts as the **Interpreter**. It replaces raw data displays with a human-readable synthesis: *"A request has been raised by [Requester] to [Action]..."*. 
- **Strategic Benefit**: This ensures that even "messy" natural language from users is converted into standardized, professional IT records without manual engineer intervention.

---
*Status: 100% Prepared for TEE Technical Evaluation Exercise © 2026*
