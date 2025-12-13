from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from .storage import DATA_DIR


def check_llamaindex_available() -> bool:
    """Check if LlamaIndex is installed and available."""
    try:
        import llama_index
        return True
    except ImportError:
        return False


def _get_llm_model():
    """Get LLM model for LlamaIndex - uses HuggingFace or Ollama."""
    import os
    
    # Try HuggingFace first (for local models or inference API)
    try:
        from llama_index.llms.huggingface import HuggingFaceLLM
        
        # Try to get HuggingFace token for inference API
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            # Try reading from cache
            try:
                token_path = Path.home() / ".cache" / "huggingface" / "token"
                if token_path.exists():
                    hf_token = token_path.read_text().strip()
            except Exception:
                pass
        
        # For now, use a simple local model (requires PyTorch)
        # Note: HuggingFaceLLM loads models locally, which can be slow
        # For inference API, we'd need a different approach
        try:
            # Use a small, fast model
            return HuggingFaceLLM(
                model_name="gpt2",  # Small model for testing
                device_map="cpu",
                max_new_tokens=512,
            )
        except Exception as e:
            print(f"Failed to initialize HuggingFace LLM: {e}")
            print("Note: Local models require PyTorch and can be slow.")
        
    except ImportError:
        pass
    
    # Fallback: use Ollama if available (better for local inference)
    try:
        from llama_index.llms.ollama import Ollama
        
        # Check if Ollama is available
        import subprocess
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            return Ollama(model="llama3.2", request_timeout=120.0)
    except (ImportError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        pass
    
    return None


def call_llamaindex(prompt: str) -> Optional[str]:
    """Call LLM using LlamaIndex framework."""
    if not check_llamaindex_available():
        print("Error: LlamaIndex is not installed.")
        print("Install it with: pip install llama-index")
        return None
    
    try:
        llm = _get_llm_model()
        if not llm:
            print("Error: No LLM backend available.")
            print("Options:")
            print("1. Install Ollama for local inference: https://ollama.ai/")
            print("2. Ensure PyTorch is installed for HuggingFace models")
            return None
        
        print("Using LlamaIndex to generate analysis...")
        
        # Use complete() method (standard for LlamaIndex LLMs)
        try:
            response = llm.complete(prompt)
            if hasattr(response, 'text'):
                return response.text.strip()
            elif hasattr(response, 'content'):
                return str(response.content).strip()
            else:
                return str(response).strip()
        except Exception as e:
            print(f"Error during text generation: {e}")
            return None
                
    except Exception as e:
        print(f"Error calling LlamaIndex LLM: {e}")
        import traceback
        traceback.print_exc()
        return None


def read_query_data_from_csv(csv_path: Path) -> List[str]:
    """Extract query column data from browser_history.csv."""
    queries = []
    if not csv_path.exists():
        return queries
    
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                query = row.get("query", "").strip()
                if query:
                    queries.append(query)
    except Exception as e:
        print(f"Error reading CSV queries: {e}")
    
    return queries


def read_graph_data(json_path: Path) -> Optional[Dict]:
    """Read graph data from JSON file."""
    if not json_path.exists():
        return None
    
    try:
        with json_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as e:
        print(f"Error reading graph data: {e}")
        return None


def format_analysis_prompt(query_data: List[str], graph_data: Optional[Dict]) -> str:
    """Format the prompt for LLM analysis."""
    
    # Format query data
    query_section = "## Search Query Data:\n"
    if query_data:
        unique_queries = list(set(query_data))[:100]  # Limit to top 100 unique queries
        query_section += "\n".join(f"- {q}" for q in unique_queries[:50])  # Show first 50
        if len(unique_queries) > 50:
            query_section += f"\n... and {len(unique_queries) - 50} more unique queries.\n"
    else:
        query_section += "No search queries found in the data.\n"
    
    # Format graph data
    graph_section = "\n## Selected Subdomains by Day of Week:\n"
    if graph_data and "selected_subdomains_by_day_of_week" in graph_data:
        dow_data = graph_data["selected_subdomains_by_day_of_week"]
        dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for subdomain, data in list(dow_data.items())[:20]:  # Top 20 subdomains
            graph_section += f"\n### {subdomain} (Total: {data['total_visits']} visits):\n"
            dow_counts = data["day_of_week"]
            graph_section += "  " + " | ".join(
                f"{day}: {dow_counts.get(day, 0)}" for day in dow_labels
            ) + "\n"
        
        if "day_of_week_totals" in graph_data:
            totals = graph_data["day_of_week_totals"]
            graph_section += "\n### Overall Day-of-Week Totals:\n"
            graph_section += "  " + " | ".join(
                f"{day}: {totals.get(day, 0)}" for day in dow_labels
            ) + "\n"
    else:
        graph_section += "No graph data available.\n"
    
    # Main analysis prompt
    prompt = f"""You are analyzing browser history data to understand user behavior patterns. Based on the following data, provide a brief, insightful analysis.

{query_section}

{graph_section}

Please provide a structured analysis with the following sections:

1. **Learning Direction**: What topics, technologies, or domains is the user exploring based on their search queries and visited domains?

2. **Working Patterns**: What patterns can you observe in their day-of-week usage? When do they seem most active? What does this suggest about their work schedule?

3. **Mental Model Evolution**: How might their interests or focus areas be evolving over time? Are there shifts in domain preferences or topic clusters?

4. **Research Interest Spikes**: Identify any notable spikes or concentrated interests in specific domains or topics. What might have triggered these?

5. **Job Personality (Based on All Attached Data)**: Based on all the data provided (search queries, domain patterns, day-of-week activity), what can you infer about their professional role, work style, and personality traits? Consider:
   - Primary professional focus
   - Work habits and schedule
   - Learning style and interests
   - Problem-solving approach
   - Communication and collaboration patterns

Keep the analysis concise but insightful. Focus on patterns and insights rather than just restating the data.
"""
    
    return prompt


def analyze_with_llamaindex(
    csv_path: Path, graph_json_path: Path
) -> Optional[str]:
    """Main function to analyze browser history data using LlamaIndex."""
    
    if not check_llamaindex_available():
        print("Error: LlamaIndex is not installed.")
        print("Install it with: pip install llama-index")
        return None
    
    print("Extracting data for analysis...")
    query_data = read_query_data_from_csv(csv_path)
    graph_data = read_graph_data(graph_json_path)
    
    if not query_data and not graph_data:
        print("No data available for analysis.")
        return None
    
    print(f"Found {len(query_data)} search queries and graph data.")
    print("Sending data to LlamaIndex for analysis...")
    
    prompt = format_analysis_prompt(query_data, graph_data)
    result = call_llamaindex(prompt)
    
    return result
