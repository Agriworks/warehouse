# warehouse

## Design Notes:

Wants:
1. Serverless architecture
    1. Orchestrator (Will need heartbeat service to launch it if we have it on serverless - potential candidate is cronhooks.io)
    2. Base / Data drivers can work naturally on serverless
    3. FastAPI seems to have plugins that would enable serverless (magnum)
2. Data Integrity and Consolidation
    1. Update and finish the features necessary for consolidating time and location
    2. Use panda patches schema to track changes and save on mongodb
    3. Allow for future blockchain storing for data integrity hashes
3. Make Operations addition seemless
    1. The orchestrator should be able to identify and 