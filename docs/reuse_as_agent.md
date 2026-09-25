# Reuse as a bounded domain agent

Expose procurement as a structured domain capability rather than a free-form chatbot.

Example:

{
  "name": "procurement.analyze",
  "input": {"product_codes": ["P0001"]}
}

Return structured proposals containing demand, inventory position, expiry exposure, supplier, quantity, rationale, assumptions and human-review state.

A future supervisor can call this agent alongside inventory, sales, finance and supplier-risk agents.
