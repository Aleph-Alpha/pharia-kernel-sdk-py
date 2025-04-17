# Skill templates

Skill code can be generated declaratively from templates:

```sh
uv run pharia-skill generate chat
Skill name (skill): 
Output file (skill.py): 
Template config (template_config.json): 
Model (llama-3.1-8b-instruct): 
System prompt (You are a helpful assistant.): 
```

The input values can also be provided non-interactively:

```sh
uv run pharia-skill generate chat --name skill --system_prompt: "You are a helpful assistant." --no-interactive
```