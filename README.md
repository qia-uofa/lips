# LLM-driven Iterative Project Synthesizer (LIPS)
  
## Installation
```bash
python3 -m pip install --force-reinstall git+https://github.com/mandelbroetchen/lips.git
```

## Usage

1. Create the root directory of your project

```
mkdir ./my-project/
mv ./my-project/
```

2. Create `.env` and `api-config.json` to configure your LLM API. 
### `.env`
```
API_KEY=YOUR_API_KEY
```
### `api-config.json`
```
{
    "model": "mistral/mistral-large-latest",
    "max_tokens": 20000,
    "temperature": 0
}
```

3. Create 


