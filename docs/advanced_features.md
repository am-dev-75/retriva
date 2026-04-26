# Advanced features

- [Advanced features](#advanced-features)
  - [Usage](#usage)
    - [Open WebUI Integration](#open-webui-integration)
      - [File uploading](#file-uploading)
      - [Special-purpose directives](#special-purpose-directives)
      - [Ingestion Tagging](#ingestion-tagging)
        - [What tagging does](#what-tagging-does)
        - [Starting tagging](#starting-tagging)
        - [Replacing tags](#replacing-tags)
        - [Uploading documents with tags](#uploading-documents-with-tags)
        - [Stopping tagging](#stopping-tagging)
        - [Scope and lifetime](#scope-and-lifetime)
        - [Things to know](#things-to-know)
        - [Quick reference](#quick-reference)
  - [Development](#development)
    - [Debugging information](#debugging-information)
      - [Document mappings](#document-mappings)
        - [/internal/mappings/documents](#internalmappingsdocuments)
        - [/internal/mappings/documents/{owui\_file\_id}](#internalmappingsdocumentsowui_file_id)
        - [/internal/mappings/knowledge-bases](#internalmappingsknowledge-bases)

## Usage

### Open WebUI Integration

Retriva supports integration with Open WebUI. This allows you to use Retriva as the backend for Open WebUI.

#### File uploading

Uploading the same file multiple times results in multiple documents, even if the content is identical. Each upload is treated as a distinct document with its own metadata and lifecycle.

For example:

```
$ curl http://localhost:8002/internal/mappings/documents | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  4626  100  4626    0     0  2127k      0 --:--:-- --:--:-- --:--:-- 2258k
[
  {
    "id": 1,
    "owui_file_id": "e2b9176b-a79f-436e-8dcc-6c628af02b9e",
    "filename": "Cyber Resilience Act - Guide.pdf",
    "content_type": "application/pdf",
    "content_hash": "11a05c3a09e27b6681b3b88a8bcd1c7712f7ba8d09644eb4576beee4966f47cc",
    "retriva_doc_id": "owui:e2b9176b-a79f-436e-8dcc-6c628af02b9e",
    "status": "synced",
    "created_at": "2026-04-25T12:48:01.387063+00:00",
    "updated_at": "2026-04-25T12:48:01.387063+00:00"
  },
  {
    "id": 2,
    "owui_file_id": "2739c2b2-1025-45c5-ae8a-c38352f0a8ba",
    "filename": "Cyber Resilience Act - Guide.pdf",
    "content_type": "application/pdf",
    "content_hash": "11a05c3a09e27b6681b3b88a8bcd1c7712f7ba8d09644eb4576beee4966f47cc",
    "retriva_doc_id": "owui:2739c2b2-1025-45c5-ae8a-c38352f0a8ba",
    "status": "synced",
    "created_at": "2026-04-25T13:14:04.390878+00:00",
    "updated_at": "2026-04-25T13:14:04.390878+00:00"
  },
  {
    "id": 3,
    "owui_file_id": "31a6f875-0445-45d4-b530-bebab6b36c57",
    "filename": "4-page.pdf",
    "content_type": "application/pdf",
    "content_hash": "36d70e2bab92b32fbf6eb01078aa0ab9063df7e068c6627960d3e99fa2e6d4a2",
    "retriva_doc_id": "owui:31a6f875-0445-45d4-b530-bebab6b36c57",
    "status": "synced",
    "created_at": "2026-04-25T13:17:04.195280+00:00",
    "updated_at": "2026-04-25T13:17:04.195280+00:00"
  },
  {
    "id": 4,
    "owui_file_id": "f6802d2b-e5ba-458a-8910-cbfd7d94dbfb",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:f6802d2b-e5ba-458a-8910-cbfd7d94dbfb",
    "status": "synced",
    "created_at": "2026-04-25T13:20:04.184685+00:00",
    "updated_at": "2026-04-25T13:20:04.184685+00:00"
  },
  {
    "id": 5,
    "owui_file_id": "85f3bac5-adce-4714-8f40-535971d61ff5",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:85f3bac5-adce-4714-8f40-535971d61ff5",
    "status": "synced",
    "created_at": "2026-04-25T13:27:21.009375+00:00",
    "updated_at": "2026-04-25T13:27:21.009375+00:00"
  },
  {
    "id": 6,
    "owui_file_id": "a0a2af2c-e789-4acf-911b-83aeaff1b582",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:a0a2af2c-e789-4acf-911b-83aeaff1b582",
    "status": "synced",
    "created_at": "2026-04-25T13:27:21.028475+00:00",
    "updated_at": "2026-04-25T13:27:21.028475+00:00"
  },
  {
    "id": 7,
    "owui_file_id": "29ddeb32-96a6-49fc-91bc-024432cf73bf",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:29ddeb32-96a6-49fc-91bc-024432cf73bf",
    "status": "synced",
    "created_at": "2026-04-25T13:33:04.964441+00:00",
    "updated_at": "2026-04-25T13:33:04.964441+00:00"
  },
  {
    "id": 8,
    "owui_file_id": "577bdd91-f774-407b-86bf-574bf32ce4b2",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:577bdd91-f774-407b-86bf-574bf32ce4b2",
    "status": "synced",
    "created_at": "2026-04-25T16:04:03.046563+00:00",
    "updated_at": "2026-04-25T16:04:03.046563+00:00"
  },
  {
    "id": 9,
    "owui_file_id": "e6d6bc81-bc66-44ee-b4d7-0fdf75f72e8b",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:e6d6bc81-bc66-44ee-b4d7-0fdf75f72e8b",
    "status": "synced",
    "created_at": "2026-04-25T16:23:32.041221+00:00",
    "updated_at": "2026-04-25T16:23:32.041221+00:00"
  },
  {
    "id": 10,
    "owui_file_id": "15684346-dbad-49a7-9cd4-6d9efbdcb01b",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:15684346-dbad-49a7-9cd4-6d9efbdcb01b",
    "status": "synced",
    "created_at": "2026-04-25T16:29:02.014021+00:00",
    "updated_at": "2026-04-25T16:29:02.014021+00:00"
  },
  {
    "id": 11,
    "owui_file_id": "400e8b14-4f2c-4d50-b137-6b3d306012c4",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:400e8b14-4f2c-4d50-b137-6b3d306012c4",
    "status": "synced",
    "created_at": "2026-04-25T16:32:20.374483+00:00",
    "updated_at": "2026-04-25T16:32:20.374483+00:00"
  },
  {
    "id": 12,
    "owui_file_id": "503a271f-6f52-4c07-ae1e-4665f164c64d",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:503a271f-6f52-4c07-ae1e-4665f164c64d",
    "status": "synced",
    "created_at": "2026-04-25T16:44:20.370686+00:00",
    "updated_at": "2026-04-25T16:44:20.370686+00:00"
  }
]
```
#### Special-purpose directives

Some functions of Retriva are controlled through chat directives. Directives are special messages you send in the chat. Directives are not interpreted as normal questions/requests and, hence, they do not trigger the AI to answer.

#### Ingestion Tagging

The tagging feature is controlled through chat directives.
This section explains how to attach metadata tags to documents you upload so they can be grouped, filtered, and retrieved more precisely later.

##### What tagging does

When tagging is active:

* Every document you upload is ingested with the specified key–value metadata
* The tags are attached at ingestion time and persist with the document
* Tags apply only to uploads that happen after the directive is issued
* Tagging is especially useful for:
  * Projects, customers, or workstreams
  * Milestones or phases
  * Topics, domains, or document classes

##### Starting tagging

To start (or replace) ingestion tagging, send the start directive followed by one or more `key: value` lines:

```@@ingestion_tag_start
project: Apollo
milestone: M4
```

After this:

* Tagging becomes active
* All subsequent uploads are tagged with `project=Apollo` and `milestone=M4
* You will immediately see a confirmation message such as:

```✅ Ingestion tagging activated.Active metadata:
• project: Apollo
• milestone: M4
```

**Important**: Each `@@ingestion_tag_start` replaces any previously active tags. Tags are not merged.

##### Replacing tags

You can change the active tags at any time by sending another start directive:

```@@ingestion_tag_start
poc: Jupiter
step: S2
customer: ACME
```

From this point on, new uploads receive `poc`, `step`, and `customer`.

Previous tags such as project or milestone are no longer applied.

##### Uploading documents with tags

Once tagging is active, simply upload one or more files.

You do not need to type a message when uploading. The system will not generate an AI answer. You will receive a confirmation instead. Example confirmation:

```✅ Document received and queued for ingestion.Active metadata:
• project: Apollo
• milestone: M4
```

The actual ingestion happens asynchronously in the background.

##### Stopping tagging

To stop applying tags to future uploads, send the stop directive:

```@@ingestion_tag_stop

```

You will see a confirmation:

```✅ Ingestion tagging disabled.Subsequent uploaded documents will not receive user-provided metadata.

```

After this:

Uploads continue to work normally, i.e. no user-defined tags are applied.

##### Scope and lifetime

Tagging is per chat. Tags remain active until you change or stop them. Restarting the system clears the tagging state. Already ingested documents are not modified when tags change.

##### Things to know

Directives are commands, not questions. Uploading files does not trigger an AI response. You may see multiple internal system messages behind the scenes; these are normal and safely ignored. Only documents uploaded after a start directive receive tags.

##### Quick reference


|     | Action                | Directive                |
| --- | --------------------- | ------------------------ |
| 1   | Start or replace tags | `@@ingestion_tag_start`  |
| 2   | Stop tagging          | `@@ingestion_tag_stop`   |
| 3   | Upload with tags      | Upload files after start |

If you are unsure whether tagging is active, just send another @@ingestion_tag_start or @@ingestion_tag_stop—the system will always confirm the current state.

## Development

As mentioned in the [Licensing notes](README.md#licensing-notes), Retriva support extensions that can be added to the core codebase. These extensions allow you to customize and enhance Retriva's functionality without modifying the core code.

### Debugging information

Open WebUI / Retriva Adapter provides some debugging endpoints that can be used to inspect the internal state of Retriva. To enable these endpoints, set the `THIN_ADAPTER_DEBUG_ENDPOINTS` environment variable to `true`.

This can be done in the `.env` file ...
```bash
export THIN_ADAPTER_DEBUG_ENDPOINTS=true
```
... or by setting the environment variable in the shell where you start the adapter:
```bash
(open-webui_retriva-adapter) llandre@vm-ubnt-24-04-4:/mnt/shared/implementation/open-webui_retriva-adapter$ THIN_ADAPTER_DEBUG_ENDPOINTS=true PYTHONPATH=src python -m adapter
```

#### Document mappings
##### /internal/mappings/documents

This endpoint answers the following question: **For each OWUI file, which Retriva document did we create, and what is its ingestion status?**

```bash
curl http://localhost:8002/internal/mappings/documents | jq
```

Output example:

```bash
[
  {
    "id": 1,
    "owui_file_id": "e2b9176b-a79f-436e-8dcc-6c628af02b9e",
    "filename": "Cyber Resilience Act - Guide.pdf",
    "content_type": "application/pdf",
    "content_hash": "11a05c3a09e27b6681b3b88a8bcd1c7712f7ba8d09644eb4576beee4966f47cc",
    "retriva_doc_id": "owui:e2b9176b-a79f-436e-8dcc-6c628af02b9e",
    "status": "synced",
    "created_at": "2026-04-25T12:48:01.387063+00:00",
    "updated_at": "2026-04-25T12:48:01.387063+00:00"
  },
  {
    "id": 2,
    "owui_file_id": "2739c2b2-1025-45c5-ae8a-c38352f0a8ba",
    "filename": "Cyber Resilience Act - Guide.pdf",
    "content_type": "application/pdf",
    "content_hash": "11a05c3a09e27b6681b3b88a8bcd1c7712f7ba8d09644eb4576beee4966f47cc",
    "retriva_doc_id": "owui:2739c2b2-1025-45c5-ae8a-c38352f0a8ba",
    "status": "synced",
    "created_at": "2026-04-25T13:14:04.390878+00:00",
    "updated_at": "2026-04-25T13:14:04.390878+00:00"
  },
  ...
    {
    "id": 12,
    "owui_file_id": "503a271f-6f52-4c07-ae1e-4665f164c64d",
    "filename": "1-page-empty.pdf",
    "content_type": "application/pdf",
    "content_hash": "ac0e9e281666eab9b74ec4ad1f6191fe51704cf9766b3f47770560de463b9186",
    "retriva_doc_id": "owui:503a271f-6f52-4c07-ae1e-4665f164c64d",
    "status": "synced",
    "created_at": "2026-04-25T16:44:20.370686+00:00",
    "updated_at": "2026-04-25T16:44:20.370686+00:00"
  }
]
```
##### /internal/mappings/documents/{owui_file_id}
This endpoint answers the following question: **For a given OWUI file, which Retriva document did we create, and what is its ingestion status?**

```
$ curl http://localhost:8002/internal/mappings/documents/e2b9176b-a79f-436e-8dcc-6c628af02b9e | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   398  100   398    0     0   166k      0 --:--:-- --:--:-- --:--:--  194k
{
  "id": 1,
  "owui_file_id": "e2b9176b-a79f-436e-8dcc-6c628af02b9e",
  "filename": "Cyber Resilience Act - Guide.pdf",
  "content_type": "application/pdf",
  "content_hash": "11a05c3a09e27b6681b3b88a8bcd1c7712f7ba8d09644eb4576beee4966f47cc",
  "retriva_doc_id": "owui:e2b9176b-a79f-436e-8dcc-6c628af02b9e",
  "status": "synced",
  "created_at": "2026-04-25T12:48:01.387063+00:00",
  "updated_at": "2026-04-25T12:48:01.387063+00:00"
}
```

##### /internal/mappings/knowledge-bases

This endpoint answers the following question: **For each OWUI knowledge base, which Retriva knowledge base did we create, and what is its ingestion status?**
