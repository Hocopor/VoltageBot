# Checkpoint 02 - execution core

This checkpoint adds the first real trading core on top of checkpoint 01.

Implemented in this checkpoint:
- signed Bybit REST client for authenticated V5 requests;
- live account sync endpoints for wallet, orders and positions;
- paper execution engine;
- mandatory stop-loss + TP1/TP2/TP3 plan generation;
- break-even move after TP1;
- trailing stop activation after TP3;
- orders / trades / positions / PnL API;
- journal entries on closed paper trades;
- frontend execution panel and monitoring tables.

Current intentional limitations:
- historical backtesting is not implemented yet;
- live TP ladder is only partially exchange-managed in this checkpoint;
- AI journal reviews are placeholder text, not DeepSeek-generated yet.
