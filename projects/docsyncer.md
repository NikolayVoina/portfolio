# DocSyncer: LLM pipeline that keeps public documentation in sync

**Problem.** Product releases changed behaviour faster than the public documentation was updated. Writing documentation by hand for every release lagged behind, and a blocking documentation check slowed developers down.

**What I did.** I designed and built DocSyncer, a GitLab CI pipeline that reads the changes in a release, uses LLMs to update the public documentation and opens a draft pull request for human review.

## How it works

```mermaid
flowchart LR
    T["Release tag"] --> D["Diff against the previous tag of the same line"]
    D --> C["Context: changed code, current docs, read-only neighbouring repositories"]
    C --> W["Author model drafts the docs change"]
    W --> R["Reviewer model scores and comments"]
    R -->|needs work| W
    R -->|good enough or cycle limit| PR["Draft pull request to the public docs repository"]
    PR --> H["Human review, merged with the release"]
```

- **Model per repository.** Each product repository chooses its model and reasoning effort in its own pipeline configuration. I added Anthropic Claude models alongside OpenAI.
- **Never blocks development.** The pipeline runs on release tags, not on merge requests, so it never delays a developer.
- **Safety rule.** Security fixes stay out of the automatic public pull request, because that pull request is public before the release is complete.

## Result

Documentation updates arrive as reviewable draft pull requests with each release. I ran pilots to measure the cost and duration of runs before choosing defaults per repository.

**Stack:** GitLab CI, Python, OpenAI and Anthropic APIs, GitHub pull requests.
