# Project Map

The user means these three connected projects:

## ARR

Path: `ARR/`

Primary app for the current `/design` legal visualization work.

- Backend: `ARR/backend`
- Frontend: `ARR/frontend`
- Legal/land services: `ARR/backend/land/services`
- Design endpoints: `ARR/backend/design/views.py`
- Design UI: `ARR/frontend/src/design`

For `/design`, ARR is the source of truth. The UI receives legal geometry from ARR Django backend.

## AG-light

Path: `AG-light/`

Cloudflare Worker/lightweight port. It has similar land/regulation logic but does not currently own the `/design` UI flow.

Important gaps compared with ARR:

- No full ARR datum calculator equivalent.
- Simpler sunlight/daylight geometry.
- Used for lightweight API/edge experiments, not the main VWorld design rendering.

## gateway / Hermes

Path: `gateway/`

Agent/tool gateway. Current registered tool is `land_analyst`.

Important distinction:

- Hermes tool path: `gateway land_analyst -> ARR backend /land/analyze/`
- `/design` visual path: `ARR frontend -> ARR backend /design/*`

Do not debug `/design` rendering by starting with Hermes unless the user is asking about the chat/agent interface.
