# Backend Integration Notes

- Copy .env.example to .env and set:
  - SECRET_KEY
  - DATABASE_URL
  - CORS_ALLOW_ORIGINS (include http://localhost:3000 for local React app)
- Ensure the app runs on port 3001 to match the frontend default.
- API endpoints per openapi.json:
  - /auth/register (JSON)
  - /auth/login (x-www-form-urlencoded)
  - /tickets, /tickets/{id}
  - /messages, /messages/ticket/{ticket_id}
