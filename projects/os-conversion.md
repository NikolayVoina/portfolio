# AlmaLinux 10 to CloudLinux 10 conversion

**Problem.** Customers convert existing AlmaLinux servers to CloudLinux in place. The conversion tool did not support version 10 yet.

**What I did.** I adapted the conversion tool for AlmaLinux 10 to CloudLinux 10: version parsing, repositories, packages and registration. I also diagnosed a separate package-order problem that left the Python binary with the wrong group ownership after conversion.

## How a conversion runs

```mermaid
flowchart LR
    A["AlmaLinux 10 server"] --> V["Detect and parse the OS version"]
    V --> Rp["Switch repositories"]
    Rp --> Pk["Replace packages in the right order"]
    Pk --> Rg["Register the server"]
    Rg --> C["CloudLinux 10 server"]
    Pk -.->|"wrong order broke group ownership of the Python binary"| X["Fixed"]
```

## Result

The conversion fixes saved customers an estimated 15% of time per conversion.

**Stack:** Python, Bash, RPM, DNF repositories, test VMs.
