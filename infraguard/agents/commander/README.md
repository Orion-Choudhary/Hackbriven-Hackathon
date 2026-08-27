# Commander

Commander creates the incident plan, obtains the parent intent token, and delegates narrow authority to sub-agents.

Local dry run:

```powershell
python -m infraguard.agents.commander.main
```

ArmorIQ probe:

```powershell
python -m infraguard.agents.commander.main --armoriq --config infraguard/armoriq/armoriq.yaml
```
