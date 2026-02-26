# Deploying nanobot to the Cloud

nanobot is designed to be easily deployable to any cloud platform that supports Docker. This guide covers deployment on popular platforms and how to configure nanobot using environment variables.

## Environment Variables Configuration

When deploying to the cloud, you often cannot mount a local config file (`~/.nanobot/config.json`). Instead, nanobot supports configuration via environment variables.

### Method 1: Full Config JSON (Recommended for complex setups)

You can provide the entire configuration as a JSON string in the `NANOBOT_CONFIG_JSON` environment variable.

**Example:**

```bash
NANOBOT_CONFIG_JSON='{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-..."
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123456:ABC-..."
    }
  }
}'
```

### Method 2: Individual Environment Variables

You can also set individual configuration values using environment variables. The format is `NANOBOT_<SECTION>__<SUBSECTION>__<KEY>`. Note the double underscore (`__`) for nesting.

**Examples:**

- `NANOBOT_PROVIDERS__OPENROUTER__API_KEY` -> `providers.openrouter.apiKey`
- `NANOBOT_CHANNELS__TELEGRAM__TOKEN` -> `channels.telegram.token`
- `NANOBOT_AGENTS__DEFAULTS__MODEL` -> `agents.defaults.model`

## Docker Deployment

You can run nanobot anywhere with Docker.

```bash
docker run -d \
  -e NANOBOT_PROVIDERS__OPENROUTER__API_KEY="sk-or-..." \
  -e NANOBOT_CHANNELS__TELEGRAM__ENABLED="true" \
  -e NANOBOT_CHANNELS__TELEGRAM__TOKEN="123456:..." \
  -p 18790:18790 \
  nanobot gateway
```

## Platform-Specific Guides

### Railway

[Railway](https://railway.app) is a modern cloud platform that makes it easy to deploy Docker containers.

1.  Fork this repository or create a new repo with your nanobot code.
2.  Login to Railway and create a **New Project**.
3.  Select **Deploy from GitHub repo** and choose your repository.
4.  Railway will automatically detect the `Dockerfile` and start building.
5.  Go to the **Variables** tab and add your configuration:
    -   Add `NANOBOT_CONFIG_JSON` with your full config JSON.
    -   OR add individual variables like `NANOBOT_PROVIDERS__OPENROUTER__API_KEY`.
6.  The deployment will restart automatically.

> **Note:** A `railway.json` is included in the repo to ensure correct deployment settings.

### Render

[Render](https://render.com) offers a simple way to deploy web services.

1.  Fork this repository.
2.  Login to Render and create a new **Web Service**.
3.  Connect your GitHub repository.
4.  Render should detect the `Dockerfile` environment.
5.  Under **Environment Variables**, add:
    -   Key: `NANOBOT_CONFIG_JSON`
    -   Value: Your configuration JSON string.
6.  Click **Create Web Service**.

> **Note:** You can also use the "Blueprints" feature with the included `render.yaml` file.

### Heroku

1.  Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
2.  Login: `heroku login`
3.  Create an app: `heroku create my-nanobot`
4.  Set the stack to container: `heroku stack:set container`
5.  Set config vars:
    ```bash
    heroku config:set NANOBOT_PROVIDERS__OPENROUTER__API_KEY="sk-or-..."
    ```
6.  Push and deploy:
    ```bash
    git push heroku main
    ```

### DigitalOcean App Platform

1.  Create a new **App**.
2.  Select your GitHub repository.
3.  Select the **Dockerfile** resource type.
4.  Edit **Environment Variables** to add your keys.
5.  Deploy!

## Persistence

By default, the Docker container's filesystem is ephemeral. If you need persistent memory (sessions, workspace files) across restarts:

1.  **Railway:** Add a [Volume](https://docs.railway.app/reference/volumes) and mount it to `/root/.nanobot`.
2.  **Render:** Add a [Disk](https://render.com/docs/disks) and mount it to `/root/.nanobot`.
3.  **Docker:** Use `-v my-volume:/root/.nanobot`.
