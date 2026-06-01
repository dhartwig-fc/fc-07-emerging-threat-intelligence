# ET002 – Synthetic Identity Networks

## Threat Description

Synthetic Identity Networks involve the creation and use of fictitious or partially fabricated identities to establish financial relationships, obtain financial products and facilitate money laundering, fraud and sanctions evasion.

Unlike traditional identity theft, synthetic identities are often created using a combination of genuine and fabricated information, making them difficult to detect through conventional KYC controls.

These networks may operate across multiple institutions and jurisdictions, creating interconnected clusters of synthetic customers, accounts and counterparties.

---

## Source References

- FinCEN
- FATF
- FCA
- Europol
- Industry Fraud Intelligence Reports

---

## Jurisdictions

- Global
- United States
- United Kingdom
- European Union

---

## Threat Indicators

### Customer Indicators

- Recently established identity
- Limited digital footprint
- Inconsistent customer information
- Unusual document combinations
- Multiple applications using similar attributes

### Behavioural Indicators

- Rapid account activity following onboarding
- Multiple linked accounts
- Common contact details across customers
- Shared devices or IP addresses
- Coordinated transaction activity

### Network Indicators

- Shared telephone numbers
- Shared email addresses
- Shared physical addresses
- Common beneficial owners
- Repeated counterparty relationships

---

## Data Sources

| Source | Purpose |
|----------|----------|
| Customer KYC Records | Identity verification |
| Customer Due Diligence Files | Risk assessment |
| Device Data | Device sharing analysis |
| IP Address Data | Network analysis |
| Transaction Data | Behavioural analysis |
| Corporate Registry Data | Entity validation |
| Adverse Media Sources | External intelligence |
| Network Analytics Platforms | Relationship discovery |

---

## Detection Opportunities

- Entity Resolution
- Identity Matching
- Device Intelligence
- Shared Attribute Analysis
- Behavioural Analytics
- Network Graph Analytics
- Peer Group Analysis

---

## Network Analytics Opportunities

### Shared Attributes

- Telephone numbers
- Email addresses
- Residential addresses
- Device identifiers
- IP addresses

### Relationship Analysis

- Shared counterparties
- Circular transaction flows
- Common onboarding patterns
- Network clustering

### Risk Propagation

- Connected high-risk entities
- Shared fraud indicators
- Network-based risk scoring

---

## Investigation Considerations

Investigators should:

- Validate identity attributes
- Review onboarding evidence
- Assess linked entities
- Review network relationships
- Analyse transaction behaviour
- Assess fraud indicators
- Review sanctions exposure

---

## Potential Future Controls

- AI-assisted identity validation
- Synthetic identity scoring models
- Network-based onboarding controls
- Shared device analytics
- Cross-institution intelligence sharing
- Graph-based entity resolution

---

## Threat Assessment

| Category | Assessment |
|----------|------------|
| Likelihood | High |
| Impact | High |
| Detection Readiness | Medium |
| Regulatory Interest | High |
| Future Priority | Critical |

---

## Research Status

Current Status: Active Research

This threat has been identified by multiple regulators and industry bodies as an increasing risk area requiring enhanced identity analytics, network intelligence and behavioural monitoring capabilities.

---

## Related Repositories

- FC-03 Network Intelligence Library
- FC-04 TBML Analytics Toolkit
- FC-06 AI-Enabled Investigator Copilot

---

Emerging Threat Intelligence Library

Threat ID: ET002  
Threat Category: Synthetic Identity Networks
