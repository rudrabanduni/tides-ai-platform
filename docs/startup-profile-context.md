# Startup Profile Context Contract

The startup profile context builder produces a single structured object that downstream AI agents can consume as prompt input.

## Builder

`StartupProfileContextBuilder.build()` in `app/modules/startup_profiles/context.py`

## Input

| Input | Required | Missing behavior |
|-------|----------|----------------|
| `StartupApplication` | Yes | Must be provided |
| `Founder` records | No | `founders` becomes `[]` |
| `StartupProfile` | No | `current_profile` becomes `null` |
| `CompanyProfile` | No | `company_profile` becomes `null` |
| `Document` records | No | `documents` becomes `[]` |

The builder does not query the database. Callers load records through existing services or repositories and pass them in.

## Output

Top-level object: `StartupProfileContext`

```json
{
  "startup": {},
  "founders": [],
  "company_profile": null,
  "documents": [],
  "current_profile": null
}
```

Use `StartupProfileContext.to_prompt_dict()` to produce JSON-safe data for prompts.

## Section contracts

### `startup`

Application-level facts from `StartupApplication`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Startup application ID |
| `startup_name` | string | Required |
| `sector` | string or null | |
| `stage` | string or null | |
| `current_status` | string | Enum value, e.g. `Submitted` |
| `problem_statement` | string or null | |
| `solution_summary` | string or null | |
| `business_model` | string or null | |
| `target_market` | string or null | |
| `traction_summary` | string or null | |
| `funding_status` | string or null | |
| `submitted_at` | ISO datetime or null | |

### `founders`

Ordered list of founder records. Empty list when no founders are supplied.

| Field | Type |
|-------|------|
| `id` | UUID |
| `name` | string |
| `email` | string or null |
| `phone` | string or null |
| `education` | string or null |
| `experience_summary` | string or null |
| `linkedin_url` | string or null |
| `role_in_startup` | string or null |

### `company_profile`

`null` when no company profile exists.

| Field | Type |
|-------|------|
| `id` | UUID |
| `website` | string or null |
| `incorporation_status` | string or null |
| `registration_number` | string or null |
| `location` | string or null |
| `team_size` | integer or null |
| `revenue_status` | string or null |
| `ip_status` | string or null |
| `market_category` | string or null |

### `documents`

Ordered list of uploaded documents. Empty list when no documents are supplied.

Internal storage paths are intentionally excluded.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | |
| `document_type` | string | Enum value |
| `original_filename` | string | |
| `processing_status` | string | Enum value |
| `parsed_text` | string or null | Included only when `processing_status` is `parsed` |
| `content_type` | string or null | |
| `file_size` | integer | Bytes |

### `current_profile`

`null` when no startup profile exists.

Canonical profile fields from `StartupProfile`.

| Field | Type |
|-------|------|
| `id` | UUID |
| `startup_id` | UUID |
| `problem_statement` | string or null |
| `solution_summary` | string or null |
| `target_market` | string or null |
| `business_model` | string or null |
| `technology_summary` | string or null |
| `traction_summary` | string or null |
| `funding_summary` | string or null |
| `ip_summary` | string or null |
| `generated_at` | ISO datetime |
| `updated_at` | ISO datetime |

## Missing data rules

1. Optional singleton inputs (`profile`, `company_profile`) serialize as `null`, not empty objects.
2. Optional list inputs (`founders`, `documents`) serialize as empty arrays.
3. Nullable fields inside populated sections remain `null` when source data is absent.
4. Document `parsed_text` is omitted unless the document status is `parsed`.

## Example

```python
from app.modules.startup_profiles.context import StartupProfileContextBuilder

context = StartupProfileContextBuilder().build(
    startup=startup,
    founders=founders,
    profile=profile,
    company_profile=company_profile,
    documents=documents,
)
prompt_payload = context.to_prompt_dict()
```
