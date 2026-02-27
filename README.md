# xeroml-sdk

Official Python SDK for the XeroML API.

## Install

```bash
pip install xeroml-sdk
```

## Usage

```python
from xeroml import XeroML

client = XeroML(api_key="xml_...")

result = client.classify(text="I want to cancel my subscription")
```

## Development

```bash
uv sync
uv run ruff check .    # lint
uv run pytest           # test
```
