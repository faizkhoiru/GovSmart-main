# GovSmart Backend

Backend service for GovSmart E-Governance & Pengaduan AI.
Built with FastAPI, MySQL, and Poetry.

## Deploy frontend and backend on Render

Deploy the backend as a Docker Web Service using the `backend` root directory.
Deploy the frontend as a Static Site using the `frontend` root directory, build
command `npm run build`, and publish directory `dist`.

Set `VITE_API_BASE_URL` on the frontend service to the backend URL, for example
`https://govsmart-main.onrender.com`. Set `CORS_ORIGINS` on the backend service
to the exact frontend URL assigned by Render, for example
`https://govsmart-frontend.onrender.com`. If the frontend uses a custom domain,
include that exact origin as well (comma-separated).

Redeploy both services after changing these values. The backend's chatbot
connection remains configured separately through `CHATBOT_URL` and
`CHATBOT_INTERNAL_TOKEN`.
