from typing import Any,Dict

from src.graphs.chains.out_of_scope import out_of_scope_chain
from src.graphs.state import GraphState

def out_of_scope(state:GraphState) -> Dict[str,Any]:
    print("---OUT OF SCOPE--")
    question = state["question"]

    out_ofS =out_of_scope_chain.invoke({
        "question":question
    })

    return {"generation":out_ofS}
