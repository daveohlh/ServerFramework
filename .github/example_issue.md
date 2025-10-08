### **As a(n) *Auditor* I want *robust logging* so that *I can see who violated privacy laws*.**

## Executive Summary

We need to create an interface to a time-series database (InfluxDB) to efficiently store audit logs separate from our relational database.

## Acceptance Criteria

- [ ] `database` extension implemented and connects to InfluxDB
- [ ] `Root InfluxDB` provider seeded at boot based on environment variables - updated if environment variables change
- [ ] `meta_logging` extension implemented, links to all flows with hooks

## In-Scope Files / Directories / Systems

- `extensions/database/`
- `extensions/meta_logging/`

## Out-of-Scope Files / Directories / Systems

Except to update hooks logic if necessary - no changes specific to this ticket: 
- `database/`
- `logic/`
- `endpoints/`

### Issue Dependencies

- https://github.com/JamesonRGrieve/ServerFramework/issue/116
- https://github.com/JamesonRGrieve/OtherRepository/issue/35

### Other Dependencies

- InfluxDB Server must be set up for testing.
