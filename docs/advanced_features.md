# Advanced features

- [Advanced features](#advanced-features)
  - [Usage](#usage)
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

## Usage

### Special-purpose directives

Some functions of Retriva are controlled through chat directives. Directives are special messages you send in the chat. Directives are not interpreted as normal questions/requests and, hence, they do not trigger the AI to answer.

### Ingestion Tagging

The tagging feature is controlled through chat directives.
This section explains how to attach metadata tags to documents you upload so they can be grouped, filtered, and retrieved more precisely later.

#### What tagging does

When tagging is active:

* Every document you upload is ingested with the specified key–value metadata
* The tags are attached at ingestion time and persist with the document
* Tags apply only to uploads that happen after the directive is issued
* Tagging is especially useful for:
  * Projects, customers, or workstreams
  * Milestones or phases
  * Topics, domains, or document classes

#### Starting tagging

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

#### Replacing tags

You can change the active tags at any time by sending another start directive:

```@@ingestion_tag_start
poc: Jupiter
step: S2
customer: ACME
```

From this point on, new uploads receive `poc`, `step`, and `customer`.

Previous tags such as project or milestone are no longer applied.

#### Uploading documents with tags

Once tagging is active, simply upload one or more files.

You do not need to type a message when uploading. The system will not generate an AI answer. You will receive a confirmation instead. Example confirmation:

```✅ Document received and queued for ingestion.Active metadata:
• project: Apollo
• milestone: M4
```

The actual ingestion happens asynchronously in the background.

#### Stopping tagging

To stop applying tags to future uploads, send the stop directive:

```@@ingestion_tag_stop

```

You will see a confirmation:

```✅ Ingestion tagging disabled.Subsequent uploaded documents will not receive user-provided metadata.

```

After this:

Uploads continue to work normally, i.e. no user-defined tags are applied.

#### Scope and lifetime

Tagging is per chat. Tags remain active until you change or stop them. Restarting the system clears the tagging state. Already ingested documents are not modified when tags change.

#### Things to know

Directives are commands, not questions. Uploading files does not trigger an AI response. You may see multiple internal system messages behind the scenes; these are normal and safely ignored. Only documents uploaded after a start directive receive tags.

#### Quick reference


|     | Action                | Directive                |
| --- | --------------------- | ------------------------ |
| 1   | Start or replace tags | `@@ingestion_tag_start`  |
| 2   | Stop tagging          | `@@ingestion_tag_stop`   |
| 3   | Upload with tags      | Upload files after start |

	
	
	

If you are unsure whether tagging is active, just send another @@ingestion_tag_start or @@ingestion_tag_stop—the system will always confirm the current state.

## Development

As mentioned in the [Licensing notes](README.md#licensing-notes), Retriva support extensions that can be added to the core codebase. These extensions allow you to customize and enhance Retriva's functionality without modifying the core code.
