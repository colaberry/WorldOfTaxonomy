# ChatGPT Custom GPT Setup

Turn WorldOfTaxonomy into a ChatGPT Custom GPT via OpenAPI Actions.

## 1. Fetch the OpenAPI spec

The FastAPI backend auto-generates a spec. Download it:

```bash
curl https://worldoftaxonomy.com/api/v1/openapi.json -o openapi.json
```

Or run the bundled export script (writes a trimmed, GPT-optimized spec):

```bash
python skills/openapi/export_openapi.py > worldoftaxonomy_gpt_actions.json
```

## 2. Create the Custom GPT

1. Go to https://chatgpt.com/gpts/editor
2. Click **Create**
3. Fill in the Configure tab:
   - **Name**: WorldOfTaxonomy
   - **Description**: Classify businesses, products, occupations, diseases, and documents under global standard codes. Translate NAICS, ISIC, NACE, HS, ICD, SOC, ISCO across country and system boundaries.
   - **Instructions**: paste the contents of `instructions.md` from this directory
   - **Conversation starters**:
     - "Classify 'organic almond milk manufacturer' under NAICS and ISIC"
     - "Translate NAICS 2022 code 541511 to ISIC Rev 4"
     - "What ICD-10 codes are equivalent across US, Germany, and Australia?"
     - "Show me the hierarchy under NAICS sector 23 (Construction)"

## 3. Add the Action

1. Scroll to **Actions** -> **Create new action**
2. **Authentication**: API Key, header name `Authorization`, value `Bearer wot_<your_api_key>`
   - Get a key at https://worldoftaxonomy.com/dashboard
3. **Schema**: paste the JSON from `worldoftaxonomy_gpt_actions.json`
4. **Privacy policy URL**: `https://worldoftaxonomy.com/privacy`

## 4. Test

Try: "Classify 'small solar panel installation company in Texas' under NAICS 2022."

The GPT should call `POST /classify` and return candidate codes with descriptions.

## Files in this directory

- `export_openapi.py` - fetches the live OpenAPI spec and trims it to the endpoints a Custom GPT needs (search, classify, systems, nodes, equivalences)
- `instructions.md` - system prompt for the Custom GPT
- `worldoftaxonomy_gpt_actions.json` - prebuilt schema (regenerate anytime)
