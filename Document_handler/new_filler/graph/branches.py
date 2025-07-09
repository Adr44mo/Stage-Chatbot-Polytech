def validation_branch(state):
    return "correction" if not state.get("is_valid") else "save"