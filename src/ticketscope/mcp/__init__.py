"""The MCP server: a stateless Streamable HTTP front for `/v1` (AD-2, AD-4).

It reaches `api` only through `ticketscope.apiclient`; it never imports `core`, `adapters`,
`http`, `jobs`, `psycopg` or `fastembed`.
"""
