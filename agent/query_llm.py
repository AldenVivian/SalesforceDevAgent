# agent/query_llm.py
import json
import os
from typing import Any, Dict, List, Tuple

from openai import OpenAI
from context.mcp_tools import (
    get_apex_class,
    search_metadata,
    get_object_schema,
)

# Map tool names to callables
TOOL_FUNCS = {
    "get_apex_class": lambda args: get_apex_class(type("X", (), args)),
    "search_metadata": lambda args: search_metadata(type("X", (), args)),
    "get_object_schema": lambda args: get_object_schema(type("X", (), args)),
}

# JSON schema tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_apex_class",
            "description": "Retrieve full source code for a specific Apex class by exact Name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Exact Apex class name"}
                },
                "required": ["name"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_metadata",
            "description": "Search code metadata by name across ApexClass and ApexTrigger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Substring to search"},
                    "types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of types to restrict search",
                    },
                },
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_object_schema",
            "description": "Return the full sObject describe for a Salesforce object API name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_api_name": {
                        "type": "string",
                        "description": "API name like Account, Contact, CustomObject__c",
                    }
                },
                "required": ["object_api_name"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]

SYSTEM_PROMPT = (
    "You are a Salesforce engineering agent that answers questions using tools only when needed. "
    "Prefer the smallest set of tool calls to answer accurately. "
    "If code or schema is requested, call the appropriate tool by exact name."
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _execute_tool_calls(message) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Execute any tool calls the model proposed and return (tool_results_msgs, log_entries)."""
    tool_results_msgs: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []
    tool_calls = getattr(message, "tool_calls", None) or []
    for call in tool_calls:
        fn = call.function
        name = fn.name
        args = json.loads(fn.arguments or "{}")
        func = TOOL_FUNCS.get(name)
        try:
            result = func(args) if func else {"error": f"Unknown tool {name}"}
        except Exception as e:
            result = {"error": str(e)}
        tool_results_msgs.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": json.dumps(result),
            }
        )
        logs.append({"name": name, "args": args, "ok": "error" not in result})
    return tool_results_msgs, logs


def run_agent(question: str, max_iterations: int = 5) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_log: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = resp.choices[0].message
        if msg.tool_calls:
            tool_msgs, logs = _execute_tool_calls(msg)
            tool_log.extend(logs)
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                }
            )
            messages.extend(tool_msgs)
            continue
        # Final answer
        return {
            "answer": msg.content or "",
            "tool_calls": tool_log,
            "total_tokens": getattr(resp.usage, "total_tokens", None),
            "duration_ms": None,
        }
    # Safety net if the model keeps calling tools
    return {
        "answer": "Stopped after max tool iterations.",
        "tool_calls": tool_log,
        "total_tokens": None,
        "duration_ms": None,
    }
