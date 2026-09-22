---
layout: default
title: AgentWeave — Pre-Inference Routing for Tool-Rich LLMs
description: Open-source pre-inference routing for tool-rich LLM and multi-agent systems with MCP, A2A, LangGraph, AutoGen, policy-aware routing, recovery, and reproducible evaluation.
permalink: /
---

# AgentWeave — Pre-Inference Routing for Tool-Rich LLMs

**AgentWeave** is an open-source pre-inference routing and reliability layer for **tool-rich LLM applications and multi-agent systems**. It reduces the tools or agents exposed to the model before inference while keeping policy, provenance, recovery, execution, and evaluation explicit.

AgentWeave is maintained by [Saurav Singla](https://github.com/sauravsingla) and is designed for systems using **MCP (Model Context Protocol), A2A, LangGraph, AutoGen, function calling, tool routing, agent routing, and multi-agent orchestration**.

## Start here

- [AgentWeave repository](https://github.com/sauravsingla/agentweave)
- [30-second start](https://github.com/sauravsingla/agentweave#30-second-start)
- [MCP integration](MCP_INTEGRATION.html)
- [A2A interoperability](A2A_COMPATIBILITY.html)
- [LangGraph integration](LANGGRAPH_INTEGRATION.html)
- [AutoGen integration](AUTOGEN_INTEGRATION.html)
- [BFCL reproduction](BFCL_REPRODUCE.html)
- [API compatibility](API_COMPATIBILITY.html)
- [Research paper](https://arxiv.org/abs/2608.23078)

## What problem does AgentWeave solve?

LLM and agent applications can expose hundreds or thousands of tools, APIs, or specialist agents. Sending the entire action catalog to the model increases the decision space, prompt size, and routing difficulty. AgentWeave performs **routing before reasoning**: it applies policy and capability constraints, selects a smaller relevant candidate set, and then hands that reduced action space to the downstream model or agent framework.

## Core use cases

- **MCP tool routing** for large Model Context Protocol tool catalogs
- **LLM tool selection** and function-calling systems with many candidate tools
- **Multi-agent routing** and specialist-agent selection
- **LangGraph** workflows requiring explicit routing before model execution
- **AutoGen** teams with task-aware participant selection
- **A2A agent interoperability** with explicit selection and execution boundaries
- Policy-aware routing, recovery, provenance, and reproducible evaluation

## Research

AgentWeave accompanies the paper **“AgentWeave: Routing Before Reasoning for Efficient Function Calling in Tool-Rich Language Models.”**

- [Read the paper on arXiv](https://arxiv.org/abs/2608.23078)
- [Citation metadata](https://github.com/sauravsingla/agentweave/blob/main/CITATION.cff)
- [Reproducible evaluation](https://github.com/sauravsingla/agentweave#results-at-a-glance)

## Project identity

Canonical source repository: [github.com/sauravsingla/agentweave](https://github.com/sauravsingla/agentweave)

Author and maintainer: [Saurav Singla](https://github.com/sauravsingla)
