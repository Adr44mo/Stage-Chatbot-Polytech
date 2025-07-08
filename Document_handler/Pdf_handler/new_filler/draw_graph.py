from .graph.build_graph import build_graph
from pathlib import Path

if __name__ == "__main__":
    graph = build_graph()
    output_path = Path(__file__).parent / "rag_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph.get_graph().draw_png())
    print(f"Graph PNG généré : {output_path}")