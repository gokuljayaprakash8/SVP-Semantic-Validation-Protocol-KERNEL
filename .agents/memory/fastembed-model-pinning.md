---
name: FastEmbed model pinning
description: Non-obvious model lifecycle constraint for the active FastEmbed integration.
---

FastEmbed 0.8.0 accepts `specific_model_path`, but its `TextEmbedding` path does not reliably expose a Hugging Face revision parameter to the download layer. The active service therefore pins the Qdrant ONNX repository commit with `huggingface_hub.snapshot_download(revision=...)` and passes the returned local snapshot to `TextEmbedding`.

**Why:** Passing only the logical model name allows the model artifact to follow an unbounded repository state, which undermines reproducible governance decisions.

**How to apply:** Keep the logical model name, Qdrant repository, commit revision, artifact allow-list, and cache directory aligned when upgrading FastEmbed or the embedding model.