# AGENT-KIT

A curated collection of agent skills, rules, and customizations.

## Skills

### runmyjobs-data-model
Guidance and recipes for interacting with the RunMyJobs (Redwood) Data Model via Java / RedwoodScript, including:
- Querying the data model with ANSI '92 SQL (jcsSession.executeObjectQuery)
- Object lookup and lifecycle (SchedulerSession, JobDefinition, JobChain, Table, Queue)
- UC4 to RunMyJobs mapping using ObjectTag (UC4ExternalBusinessKey)
- Handling Split Objects / siblings and master job definition filtering
- Programmatic job chain creation and step status handlers
