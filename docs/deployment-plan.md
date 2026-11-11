# Bloom deployment plan

This is a plan for a two-service Render deployment with Neon PostgreSQL. It is not a deployment record.

The ignored `.deploy-env/backend.env` and `.deploy-env/frontend.env` files contain
ready-to-import Render environment values for services named exactly
`mateerixx-bloom-api` and `mateerixx-bloom-web`. In each service's Environment
page, use **Add from .env** with the corresponding file. If Render assigns a
different hostname, update `VITE_API_URL` and `ALLOWED_ORIGINS` to the actual
HTTPS origins before deploying. Never commit either file.

## 1. Prepare the repository

- Keep model weights and local account data out of Git. The two checkpoints are downloaded from `mufasabrownie/glowlytics-skin-models` by `setup_ml.sh`.
- Add the ML runtime packages (`timm`, `torch`, `torchvision`, `ultralytics`, `huggingface_hub`) to the backend's production dependency definition, or keep `setup_ml.sh` in the backend build command. Confirm compatible versions and that the build fits the selected service's memory and disk limits.
- Verify `npm ci && npm run build` in `frontend/` and `python -m pytest tests/ -v --tb=short` in `backend/` before deployment.
- Push the verified source and this plan to GitHub. Keep `.env`, `backend/data/`, and downloaded model files untracked.

## 2. Create the API service

- Create a Render Python web service named `mateerixx-bloom-api` from this GitHub repository, using the repository root as the service root.
- Set build command to `pip install -r backend/requirements.txt && bash setup_ml.sh`. The script downloads both model files into `backend/models/` during the build.
- Set start command to `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Import `.deploy-env/backend.env`. It includes the Neon `DATABASE_URL`, a persistent `AUTH_SECRET`, Python 3.11, and the expected frontend origin. Set the health check path to `/api/health`.
- Neon stores accounts and scan history. A Render persistent disk is not needed for those records. Uploaded photos remain in memory and are not saved.
- Size the service after measuring a real scan with both ML models. The health endpoint reports whether the two checkpoints are installed and whether both lazy-loaded models have loaded; verify a successful scan response separately.

## 3. Create the frontend site

- Create a Render static site named `mateerixx-bloom-web` from the same GitHub repository with root directory `frontend/`, build command `npm ci && npm run build`, and publish directory `dist`.
- Import `.deploy-env/frontend.env` before building. Confirm the API's `ALLOWED_ORIGINS` matches the final static-site URL, then redeploy both services as needed.
- Verify sign-up, sign-in, password visibility toggle, reset flow, image upload, and the ML results panel in a production build.

## 4. Release checks

- Confirm the frontend URL and `/api/health` return HTTP 200.
- Submit a valid face image to `/api/analyse` and confirm `ml.available === true`, four finite signal scores, and an acne detection object. A 422 quality or face response will not include ML results.
- Restart the API and confirm account login and saved history still work, proving Neon persistence.
- Review CORS, logs, model download failures, build size, and response time. Keep the educational disclaimer visible in the UI.
- Enable automatic deployment from `main` only after these checks pass. Record the live URLs and deployment settings in the README.

## References

- [Render FastAPI deployment](https://render.com/docs/deploy-fastapi)
- [Render web services and health checks](https://render.com/docs/web-services)
- [Render static sites](https://render.com/docs/static-sites)
- [Render environment variables](https://render.com/docs/configure-environment-variables)
