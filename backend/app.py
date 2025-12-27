"""
Search API Server

Flask-based REST API for the search system.
"""

import os
import json
from typing import Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import queue
import threading

from backend.core.orchestrator import SearchOrchestrator, SearchConfig, ProgressUpdate


app = Flask(__name__)
CORS(app)

# Global orchestrator
orchestrator: Optional[SearchOrchestrator] = None


def get_orchestrator() -> SearchOrchestrator:
    """Get or create orchestrator."""
    global orchestrator
    
    if orchestrator is None:
        orchestrator = SearchOrchestrator(
            pubmed_key=os.environ.get("NCBI_API_KEY"),
            semantic_scholar_key=os.environ.get("SEMANTIC_SCHOLAR_KEY"),
            email=os.environ.get("SEARCH_EMAIL", "user@example.com")
        )
    
    return orchestrator


@app.route("/api/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({"status": "ok"})


@app.route("/api/search", methods=["POST"])
def search():
    """
    Search for papers.
    
    Request:
    {
        "query": "search query",
        "maxPerSource": 100,
        "expandCitations": true,
        "includePreprints": true,
        "minReliability": 0.0,
        "yearStart": null,
        "yearEnd": null
    }
    """
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No request body"}), 400
    
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "Empty query"}), 400
    
    config = SearchConfig(
        max_per_source=data.get("maxPerSource", 100),
        expand_citations=data.get("expandCitations", True),
        include_preprints=data.get("includePreprints", True),
        min_reliability=data.get("minReliability", 0.0),
        year_start=data.get("yearStart"),
        year_end=data.get("yearEnd")
    )
    
    orch = get_orchestrator()
    result = orch.search(query, config)
    
    if result.is_err:
        return jsonify({"error": result.error}), 500
    
    return jsonify(result.unwrap().to_dict())


@app.route("/api/search/stream", methods=["POST"])
def search_stream():
    """Search with streaming progress (SSE)."""
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No request body"}), 400
    
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "Empty query"}), 400
    
    config = SearchConfig(
        max_per_source=data.get("maxPerSource", 100),
        expand_citations=data.get("expandCitations", True),
        include_preprints=data.get("includePreprints", True),
        min_reliability=data.get("minReliability", 0.0),
        year_start=data.get("yearStart"),
        year_end=data.get("yearEnd")
    )
    
    progress_queue = queue.Queue()
    
    def generate():
        orch = get_orchestrator()
        
        def on_progress(update: ProgressUpdate):
            progress_queue.put({
                "type": "progress",
                "phase": update.phase,
                "source": update.source,
                "status": update.status,
                "count": update.count,
                "message": update.message
            })
        
        orch.set_progress_callback(on_progress)
        
        result_holder = [None]
        error_holder = [None]
        
        def run_search():
            result = orch.search(query, config)
            if result.is_ok:
                result_holder[0] = result.unwrap()
            else:
                error_holder[0] = result.error
            progress_queue.put(None)
        
        thread = threading.Thread(target=run_search)
        thread.start()
        
        while True:
            item = progress_queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
        
        thread.join()
        
        if result_holder[0]:
            yield f"data: {json.dumps({'type': 'result', 'data': result_holder[0].to_dict()})}\n\n"
        elif error_holder[0]:
            yield f"data: {json.dumps({'type': 'error', 'error': error_holder[0]})}\n\n"
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/api/paper/<paper_id>", methods=["GET"])
def get_paper(paper_id: str):
    """Get paper by ID."""
    
    orch = get_orchestrator()
    
    if paper_id.startswith("pubmed_"):
        adapter = orch.adapters.get("pubmed")
    elif paper_id.startswith("s2_"):
        adapter = orch.adapters.get("semantic_scholar")
    elif paper_id.startswith("arxiv_"):
        adapter = orch.adapters.get("arxiv")
    elif paper_id.startswith("openalex_"):
        adapter = orch.adapters.get("openalex")
    elif paper_id.startswith("10."):
        adapter = orch.adapters.get("openalex")
    else:
        return jsonify({"error": "Unknown ID format"}), 400
    
    if not adapter:
        return jsonify({"error": "Adapter not found"}), 500
    
    result = adapter.get_by_id(paper_id)
    
    if result.is_err:
        return jsonify({"error": result.error}), 500
    
    paper = result.unwrap()
    
    if not paper:
        return jsonify({"error": "Not found"}), 404
    
    return jsonify(paper.to_dict())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    print(f"Starting Search API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
