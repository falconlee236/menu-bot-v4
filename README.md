# menu-bot-v4

## quickstart
```bash
docker build -t freshmeal-bot .
```

```bash
docker run -d -p 7753:7753 --name my-bot \
  -e MicrosoftAppId="본인의_APP_ID" \
  -e MicrosoftAppPassword="본인의_PASSWORD" \
  -e GROQ_API_KEY="본인의_GROQ_API_KEY" \
  freshmeal-bot
```