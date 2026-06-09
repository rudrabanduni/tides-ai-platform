# Excel Intake Workflow

The startup intake pipeline imports Accubate `.xlsx` exports into the platform.

## Endpoint

`POST /api/v1/intake/upload-applications`

The endpoint is protected by the same RBAC layer as startup creation. Admin and evaluator users may upload files.

## Expected Columns

- `Startup Name`
- `Founder Name`
- `Founder Email`
- `Problem Statement`
- `Solution`
- `Target Market`
- `Startup Stage`

Header matching is case-insensitive and ignores extra whitespace.

## Processing Flow

```text
XLSX upload
  |
Validate file extension and workbook headers
  |
Read rows with openpyxl in read-only mode
  |
Skip fully empty rows
  |
Validate each non-empty row
  |
Create StartupApplication, Founder, StartupProfile, StartupProfileVersion
  |
Write audit logs with filename and row number
  |
Return summary with row-level errors
```

## Validation

Rows are rejected when:

- `Startup Name` is missing
- `Founder Name` is missing
- `Founder Email` is missing
- `Founder Email` is invalid
- `Founder Email` appears more than once in the uploaded file
- `Founder Email` already exists in the platform

One failed row does not stop the rest of the import.

## Response

```json
{
  "total_rows": 0,
  "successful_rows": 0,
  "failed_rows": 0,
  "errors": []
}
```

`total_rows` counts non-empty data rows below the header. Fully empty rows are ignored.
