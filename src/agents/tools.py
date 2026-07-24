"""Tool schemas and their (stubbed) executors.

Each specialist gets at most six tools, plus the shared handoff tool. The
executor bodies here return canned data so the repo runs end to end; replace
them with calls to your real billing / identity / knowledge-base systems.
"""
from __future__ import annotations

import json

HANDOFF_TO_ROUTER = {
    "name": "handoff_to_router",
    "description": "Give the conversation back to the router when it has drifted "
    "outside your specialty. Provide a one-sentence note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "note": {"type": "string"},
            "target": {"type": "string", "description": "Optional suggested agent."},
        },
        "required": ["note"],
    },
}


def _tool(name, desc, props, required):
    return {
        "name": name,
        "description": desc,
        "input_schema": {"type": "object", "properties": props, "required": required},
    }


TOOLS_BY_AGENT = {
    "billing": [
        _tool("get_invoice", "Fetch a customer's most recent invoices.",
              {"customer_id": {"type": "string"}}, ["customer_id"]),
        _tool("list_charges", "List charges in a date window.",
              {"customer_id": {"type": "string"}, "days": {"type": "integer"}}, ["customer_id"]),
        _tool("issue_refund", "Refund a charge.",
              {"charge_id": {"type": "string"}, "amount": {"type": "number"},
               "reason": {"type": "string"}}, ["charge_id", "amount"]),
    ],
    "technical": [
        _tool("search_kb", "Search the knowledge base.",
              {"query": {"type": "string"}}, ["query"]),
        _tool("get_system_status", "Current status of a subsystem.",
              {"component": {"type": "string"}}, ["component"]),
        _tool("run_diagnostic", "Run a diagnostic against the customer's account.",
              {"customer_id": {"type": "string"}, "check": {"type": "string"}},
              ["customer_id", "check"]),
    ],
    "account": [
        _tool("get_profile", "Fetch account profile.",
              {"customer_id": {"type": "string"}}, ["customer_id"]),
        _tool("update_profile", "Update a profile field.",
              {"customer_id": {"type": "string"}, "field": {"type": "string"},
               "value": {"type": "string"}}, ["customer_id", "field", "value"]),
        _tool("send_password_reset", "Trigger a password reset email.",
              {"customer_id": {"type": "string"}}, ["customer_id"]),
    ],
    "escalation": [
        _tool("create_ticket", "Open a human support ticket.",
              {"customer_id": {"type": "string"}, "summary": {"type": "string"},
               "priority": {"type": "string"}}, ["summary"]),
    ],
}


# ---- stubbed backends: swap these for real integrations ----

def _impl_get_invoice(a):
    return {"customer_id": a["customer_id"],
            "invoices": [{"id": "inv_1042", "amount": 49.0, "status": "paid"}]}


def _impl_list_charges(a):
    return {"charges": [
        {"id": "ch_9a", "amount": 49.0, "at": "2026-07-01T10:00:00Z"},
        {"id": "ch_9b", "amount": 49.0, "at": "2026-07-01T10:01:30Z"},
    ]}


def _impl_issue_refund(a):
    return {"refund_id": "re_5521", "charge_id": a["charge_id"],
            "amount": a["amount"], "status": "succeeded"}


def _impl_search_kb(a):
    return {"results": [{"title": "Resolving 401 errors", "url": "kb/401"}]}


def _impl_get_system_status(a):
    return {"component": a["component"], "status": "operational"}


def _impl_run_diagnostic(a):
    return {"check": a["check"], "result": "no anomalies detected"}


def _impl_get_profile(a):
    return {"customer_id": a["customer_id"], "email": "user@example.com",
            "plan": "pro", "mfa": True}


def _impl_update_profile(a):
    return {"updated": a["field"], "value": a["value"], "status": "ok"}


def _impl_send_password_reset(a):
    return {"status": "sent", "channel": "email"}


def _impl_create_ticket(a):
    return {"ticket_id": "TKT-3391", "priority": a.get("priority", "normal"),
            "status": "queued"}


IMPL = {
    "get_invoice": _impl_get_invoice,
    "list_charges": _impl_list_charges,
    "issue_refund": _impl_issue_refund,
    "search_kb": _impl_search_kb,
    "get_system_status": _impl_get_system_status,
    "run_diagnostic": _impl_run_diagnostic,
    "get_profile": _impl_get_profile,
    "update_profile": _impl_update_profile,
    "send_password_reset": _impl_send_password_reset,
    "create_ticket": _impl_create_ticket,
}


def tools_for(agent: str) -> list[dict]:
    return TOOLS_BY_AGENT.get(agent, []) + [HANDOFF_TO_ROUTER]


def find_handoff(content) -> dict | None:
    for block in content:
        if getattr(block, "type", None) == "tool_use" and block.name == "handoff_to_router":
            return block.input
    return None


async def execute_tools(content, agent: str) -> list[dict]:
    """Run every non-handoff tool call and return tool_result blocks."""
    from shared.human_handoff import enqueue

    results = []
    for block in content:
        if getattr(block, "type", None) != "tool_use" or block.name == "handoff_to_router":
            continue
        impl = IMPL.get(block.name)
        payload = impl(block.input) if impl else {"error": f"unknown tool {block.name}"}
        # Opening a human ticket also queues an async handoff for the human agents.
        if block.name == "create_ticket":
            await enqueue({"agent": agent, "input": block.input, "ticket": payload})
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": json.dumps(payload),
        })
    return results
