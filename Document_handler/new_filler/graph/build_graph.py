from langgraph.graph import StateGraph, END
from .nodes import (
    load_json_node, detect_type_node,
    fill_tags_node, fill_type_specific_node,
    validate_node, save_node, check_type_of_input_node, normalize_json_file_node,
    load_pdf_to_data_manual_node, load_pdf_to_data_scraped_node,
    fill_metadata_scraped_node, fill_metadata_manual_node, save_to_error_node,
    syllabus_extract_node, end_node
)
from typing import TypedDict, Any

class FillerState(TypedDict):
    file_path: str
    data: Any
    output_data: Any
    is_valid: bool
    web_page: bool 
    pdf_scraped: bool
    processed: bool
    is_syllabus: bool
    hash: str
    error: str
    traceback: str

def build_graph():
    graph = StateGraph(FillerState)
    # Define nodes
    graph.add_node("detect_type", detect_type_node)
    graph.add_node("fill_metadata_manual", fill_metadata_manual_node)
    graph.add_node("fill_metadata_scraped", fill_metadata_scraped_node)
    graph.add_node("fill_tags", fill_tags_node)
    graph.add_node("fill_type_specific", fill_type_specific_node)
    graph.add_node("validate", validate_node)
    graph.add_node("save", save_node)
    # Add dummy nodes before each main node if needed
    graph.add_node("save_to_error_node", save_to_error_node)
    graph.add_node("dummy_end", end_node)
    graph.add_node("check_type_of_input", check_type_of_input_node)
    graph.add_node("normalize_json_file", normalize_json_file_node)
    graph.add_node("load_pdf_to_data_manual", load_pdf_to_data_manual_node)
    graph.add_node("load_pdf_to_data_scraped", load_pdf_to_data_scraped_node)
    graph.add_node("syllabus_extract_node", syllabus_extract_node)

    graph.set_entry_point("check_type_of_input")

    graph.add_conditional_edges(
        "check_type_of_input",
        lambda state: (
            "normalize_json_file" if state.get("web_page") and not state.get("pdf_scraped")
            else "load_pdf_to_data_scraped" if state.get("pdf_scraped") 
            else "syllabus_extract_node" if state.get("is_syllabus")
            else "load_pdf_to_data_manual"
        ),
        {
            "syllabus_extract_node": "syllabus_extract_node",
            "load_pdf_to_data_manual": "load_pdf_to_data_manual",
            "normalize_json_file": "normalize_json_file",
            "load_pdf_to_data_scraped": "load_pdf_to_data_scraped"
        }
    )
    # graph.add_edge("normalize_json_file", "detect_type")
    graph.add_edge("normalize_json_file", "fill_tags")

    # graph.add_edge("detect_type", "fill_type_specific")
    # graph.add_edge("fill_metadata_manual", "detect_type")
    # graph.add_edge("fill_type_specific", "fill_tags")

    graph.add_edge("load_pdf_to_data_manual", "fill_metadata_manual")

    graph.add_edge("load_pdf_to_data_scraped", "fill_metadata_scraped")

    graph.add_edge("fill_metadata_manual", "fill_tags")
    graph.add_edge("fill_metadata_scraped", "fill_tags")
    graph.add_edge("fill_tags", "validate")
    graph.add_conditional_edges(
        "validate",
        lambda state: "save_to_error_node" if not state.get("is_valid") else "save",
        {"save_to_error_node": "save_to_error_node", "save": "save"}
    )
    graph.add_edge("save", "dummy_end")
    graph.add_edge("save_to_error_node", "dummy_end")
    graph.set_finish_point("dummy_end")

    graph.add_edge("syllabus_extract_node", "validate")

    return graph.compile()

