# User guide

## First launch

1. Install and start Ollama
2. Pull models:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

3. Launch Local AI
4. Open **Models** and confirm “Connected”
5. Set chat and embedding models if needed

## Chatting

- Create a conversation with **New**
- Type a message and press **Send**
- Use **Stop** to cancel generation
- Toggle **Use documents** / **Use memory** per conversation

## Documents & RAG

1. Open **Documents** → **Import files…**
2. Wait until status becomes `ready`
3. Ask questions in Chat with **Use documents** enabled
4. Citations appear under assistant replies

Supported types: `.pdf`, `.docx`, `.txt`, `.md`

## Memory

Add short facts or preferences in **Memory**. They are embedded locally and retrieved when relevant. Disable globally in Settings or per chat.

## Themes

Settings → Theme → System / Light / Dark.

## Data location

Local AI stores data in your OS user data/config/log directories for the app id `local-ai`. Uninstalling the packaged app does not always delete this data — remove it manually if desired.
