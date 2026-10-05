"""Backend: serves the page and runs the AI (minimax + alpha-beta) in engine.py."""
import random
import time

from flask import Flask, jsonify, request, send_from_directory

import engine

app = Flask(__name__, static_folder="static")


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/api/new")
def new_game():
    """Start a game: backend picks the fixed rockfall schedule."""
    return jsonify(schedule=engine.make_schedule(random.randint(0, 10**6)))


@app.post("/api/ai-move")
def ai_move():
    """Receive the board state, return the AI's best move."""
    d = request.get_json(force=True)
    board, sch = d["board"], d["schedule"]
    ply = int(d["ply"])
    depth = max(1, min(int(d.get("depth", 4)), 6))
    start = time.time()
    m = engine.ai_move(board, ply, depth, sch)
    return jsonify(move=list(m) if m else None,
                   seconds=round(time.time() - start, 3))


if __name__ == "__main__":
    app.run(debug=True)