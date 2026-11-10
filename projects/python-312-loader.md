# Loading hosted Python applications on Python 3.12+

**Problem.** Hosting customers run Python web applications through the platform's application selector. Its loader used the `imp` module, which Python 3.12 removed, so applications on new Python versions could not start.

**What I did.** I replaced the imp-based loader with `importlib` and adapted how application configuration is generated and parsed. Hosted applications now load through ASGI on Python 3.12+ on CloudLinux and Ubuntu.

## Simplified flow

```mermaid
flowchart LR
    Cfg["Application settings chosen by the user"] --> Gen["Generated configuration"]
    Gen --> Ld["Loader"]
    Ld -->|"before: imp, removed in 3.12"| Old["Fails on 3.12+"]
    Ld -->|"now: importlib"| App["Application module"]
    App --> Srv["ASGI application served to visitors"]
```

**Stack:** Python, importlib, ASGI, CloudLinux, Ubuntu.
