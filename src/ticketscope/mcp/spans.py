"""The attribute keys of the `tools/call {tool}` span (R5, R-010).

The span itself is the MCP SDK's `OpenTelemetryMiddleware` span (SERVER, on the global
provider); this module pins the keys it carries so epic 7's `spanmetrics` dimensions and the
tests read one list. The keys come from the OpenTelemetry MCP and GenAI semantic conventions
(experimental), as emitted by `mcp` 2.3.0 with `opentelemetry-semantic-conventions` 0.66b2
(semconv schema 1.44.0). `ticketscope.query.text` is ours and appears only on opt-in.
"""

MCP_METHOD_NAME = "mcp.method.name"
MCP_PROTOCOL_VERSION = "mcp.protocol.version"
JSONRPC_REQUEST_ID = "jsonrpc.request.id"
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"
ERROR_TYPE = "error.type"
QUERY_TEXT = "ticketscope.query.text"

# On every successful `tools/call` span.
TOOL_SPAN_KEYS = frozenset(
    {
        MCP_METHOD_NAME,
        MCP_PROTOCOL_VERSION,
        JSONRPC_REQUEST_ID,
        GEN_AI_OPERATION_NAME,
        GEN_AI_TOOL_NAME,
    }
)
# Added when the call fails (`is_error` result or an exception).
TOOL_SPAN_ERROR_KEYS = TOOL_SPAN_KEYS | {ERROR_TYPE}
# Added when `trace_query_text` is on.
TOOL_SPAN_QUERY_KEYS = TOOL_SPAN_KEYS | {QUERY_TEXT}
