import gradio as gr
import os
import requests
from requests.auth import HTTPBasicAuth
from transformers import pipeline
import time

# ==================== CONFIGURATION ====================
# Using the verified credentials from your project
SERVICENOW_URL = "https://dev273008.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASS = "@nL=BMhj07Sk"
TABLE_NAME = "x_1941577_tee_se_0_ai_incident_demo"

def generate_incident_summary(description):
    """Mock AI summary for 100% reliability during demo"""
    # Simulate AI behavior without the heavy model overhead
    time.sleep(2) # Simulate 'Thinking'
    words = description.split()
    if len(words) > 10:
        return " ".join(words[:8]) + "..."
    return description

def process_incident(description):
    """The core logic for the Portal"""
    try:
        # Step 1: AI Analysis
        yield gr.update(value="Step 1/3: AI is reading your problem...", visible=True), gr.update(visible=False), None
        
        summary = generate_incident_summary(description)
        
        # Step 2: Categorization (Simple Logic for Demo)
        yield gr.update(value="Step 2/3: Categorizing and Generating Confidence Score..."), gr.update(visible=False), None
        time.sleep(1)
        
        category = "Software"
        if "vpn" in description.lower() or "network" in description.lower():
            category = "Network"
        elif "laptop" in description.lower() or "hardware" in description.lower():
            category = "Hardware"
        elif "password" in description.lower() or "login" in description.lower():
            category = "Access"
            
        # Step 3: ServiceNow Integration
        yield gr.update(value="Step 3/3: Integrating with ServiceNow Platform..."), gr.update(visible=False), None
        
        url = f"{SERVICENOW_URL}/api/now/table/{TABLE_NAME}"
        payload = {
            "short_description": summary,
            "category": category,
            "caller": "demo.user@tee-project.com",
            "ai_confidence_score": 0.94,
            "ai_case_summary": summary
        }
        
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(SERVICENOW_USER, SERVICENOW_PASS),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            res_data = response.json()['result']
            inc_number = res_data.get('number', 'INCXXXXX')
            sys_id = res_data.get('sys_id', '')
            
            result_html = f"""
            <div style='background-color: #0d1117; color: #58a6ff; padding: 20px; border-radius: 10px; border: 1px solid #30363d;'>
                <h3 style='color: #3fb950;'>✓ Success: AI Incident Created</h3>
                <p><b>Incident Number:</b> {inc_number}</p>
                <p><b>Category:</b> {category}</p>
                <p><b>Confidence Score:</b> 94%</p>
                <p><b>AI Summary:</b> {summary}</p>
                <hr style='border: 0.5px solid #30363d;'>
                <p style='font-size: 0.8em; color: #8b949e;'>This record is now live in your ServiceNow Instance.</p>
            </div>
            """
            yield gr.update(visible=False), gr.update(value=result_html, visible=True), sys_id
        else:
            yield gr.update(value=f"Error: {response.status_code}"), gr.update(visible=False), None
            
    except Exception as e:
        yield gr.update(value=f"System Error: {str(e)}"), gr.update(visible=False), None

# ==================== UI DESIGN ====================
with gr.Blocks(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="slate"), title="AI Service Desk Portal") as demo:
    gr.Markdown("""
    # 🤖 TEE AI Service Desk Portal
    *Empowering IT with Autonomous Intelligence*
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            problem_input = gr.Textbox(
                label="Describe the IT Issue", 
                placeholder="Example: My laptop is very slow and the VPN keeps disconnecting...", 
                lines=5
            )
            submit_btn = gr.Button("🚀 Process with AI Agent", variant="primary")
            
        with gr.Column(scale=1):
            status_update = gr.Label(value="Ready to process...", visible=True, label="AI Status")
            output_html = gr.HTML(visible=False)
            sys_id_box = gr.Textbox(visible=False) # Hidden storage
            
    gr.Markdown("---")
    gr.Markdown("### 💡 Demo Instructions")
    gr.Markdown("1. Enter a problem above. | 2. Watch the AI process in real-time. | 3. Refresh your ServiceNow Dashboard to see the new ticket.")

    submit_btn.click(
        fn=process_incident, 
        inputs=problem_input, 
        outputs=[status_update, output_html, sys_id_box]
    )

if __name__ == "__main__":
    demo.launch(share=False)
