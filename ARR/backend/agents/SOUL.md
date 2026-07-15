# ARR Global A2A Agents Soul

This folder is the global agent infrastructure layer for ARR.

It exists to make agents discoverable, callable, logged, and coordinated across
the application. It should stay domain-neutral. MAAS-specific architectural
reasoning belongs in `ARR/backend/design/maas/agents/`.

The correct output of this layer is reliable agent transport, worker lifecycle,
conversation persistence, and clear A2A cards.
