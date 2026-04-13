"""
model_trainer.py — Handles fine-tuning LLMs on historical assessment data.

Reads `training_data.jsonl` from all assessment logs and prepares the data
for model fine-tuning (local HuggingFace or remote API like OpenAI/Groq).
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from app.core.log_store import LOGS_ROOT

logger = logging.getLogger("app_reader.model_trainer")

def discover_training_data() -> list[dict]:
    """Finds all `training_data.jsonl` files across all logs."""
    training_records = []
    
    if not LOGS_ROOT.exists():
        return training_records

    for subdir in LOGS_ROOT.iterdir():
        if not subdir.is_dir():
            continue
            
        data_path = subdir / "training_data.jsonl"
        if data_path.exists():
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            training_records.append(json.loads(line))
            except Exception as e:
                logger.error(f"Failed to read training data from {data_path}: {e}")
                
    return training_records


def build_huggingface_dataset(export_path: str = "hf_dataset.jsonl") -> int:
    """
    Transforms historical reports into instructional fine-tuning data:
    Input: "Here is the code summary..."
    Output: "Here is the detailed architecture assessment and category breakdowns..."
    """
    records = discover_training_data()
    if not records:
        logger.warning("No training data found.")
        return 0

    hf_records = []
    
    for record in records:
        try:
            # Construct the Instruction
            instruction = "Analyze the provided codebase summary and evaluate it across the 9 dimensions for AI readiness."
            
            # Construct the Input (What the model sees)
            # In a real scenario, this would be the raw file code. For now, we use the source origin.
            repo_source = record.get("input_source", "Unknown")
            input_text = f"Codebase Source: {repo_source}\nLocal Pattern Engine Flags: {json.dumps(record.get('report1_static', {}).get('layer_scores', {}))}"
            
            # Construct the Output (What the model should predict)
            # We want the model to predict the merged report (Report 3)
            expected_output = json.dumps(record.get("final_merged", {}), indent=2)
            
            hf_records.append({
                "messages": [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": input_text},
                    {"role": "assistant", "content": expected_output}
                ]
            })
        except Exception as e:
            logger.warning(f"Skipping a record due to formatting error: {e}")

    try:
        with open(export_path, "w", encoding="utf-8") as f:
            for rec in hf_records:
                f.write(json.dumps(rec) + "\n")
        logger.info(f"Exported {len(hf_records)} records to {export_path}")
    except Exception as e:
        logger.error(f"Failed to export huggingface dataset: {e}")

    return len(hf_records)

def simulate_fine_tuning_job():
    """Entry point to trigger fine-tuning using the exported data."""
    export_path = LOGS_ROOT / f"finetune_export_{int(datetime.now(timezone.utc).timestamp())}.jsonl"
    count = build_huggingface_dataset(str(export_path))
    
    if count == 0:
        return {"status": "failed", "message": "No training data available. Run more assessments to build history."}
        
    # In a fully integrated system, you would upload `export_path` to OpenAI/Groq here
    # e.g. client.files.create(file=open(export_path, "rb"), purpose="fine-tune")
    # e.g. client.fine_tuning.jobs.create(training_file=file_id, model="llama3-8b")
    
    return {
        "status": "success",
        "message": f"Prepared {count} assessments for fine-tuning. Saved to {export_path.name}",
        "export_path": str(export_path)
    }
