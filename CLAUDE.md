# CLAUDE.md - WorldOfTaxonomy

## What this project is

WorldOfTaxonomy is a unified global industry classification knowledge graph. It connects 1000 classification systems as equal peers through equivalence mappings (crosswalk edges).

**1000 systems, 1,212,173+ nodes, 321,937+ crosswalk edges.**

| System | Region | Codes |
|--------|--------|-------|
| NAICS 2022 | North America | 2,125 |
| NIC 2008 | India | 2,070 |
| SIC 1987 | USA/UK | 1,176 |
| NACE Rev 2 | EU (27 countries) | 996 |
| WZ 2008 | Germany | 996 |
| ONACE 2008 | Austria | 996 |
| NOGA 2008 | Switzerland | 996 |
| ANZSIC 2006 | Australia/NZ | 825 |
| ISIC Rev 4 | Global (UN) | 766 |
| JSIC 2013 | Japan | 20 |
| ISO 3166-1 | Global | 271 |
| ISO 3166-2 | Global | 5,246 |
| UN M.49 | Global | 272 |
| HS 2022 | Global (WCO) | 6,960 |
| CPC v2.1 | Global (UN) | 4,596 |
| UNSPSC v24 | Global (GS1 US) | 77,337 |
| SOC 2018 | United States | 1,447 |
| ISCO-08 | Global (ILO) | 619 |
| CIP 2020 | United States | 2,848 |
| ISCED 2011 | Global (UNESCO) | 20 |
| ISCED-F 2013 | Global (UNESCO) | 122 |
| ATC WHO 2021 | Global (WHO) | 6,440 |
| COFOG | Global (UN) | 188 |
| GICS Bridge | Global (MSCI/S&P) | 11 |
| GHG Protocol | Global (WRI/WBCSD) | 20 |
| ESCO Occupations | Europe / Global (EU Commission) | 3,045 |
| ESCO Skills | Europe / Global (EU Commission) | 14,247 |
| O*NET-SOC | United States (DOL) | 867 |
| Patent CPC | Global (EPO/USPTO) | 254,249 |
| CFR Title 49 | United States | 104 |
| FMCSA Regulations | United States | 80 |
| GDPR Articles | European Union | 110 |
| ISO 31000 | Global (ISO) | 47 |
| Domain: Truck Freight Types | United States | 44 |
| Domain: Truck Vehicle Classes | United States | 23 |
| Domain: Truck Cargo Classification | United States | 46 |
| Domain: Truck Carrier Operations | United States | 27 |
| Domain: NAICS 484 -> Truck Domain crosswalk | United States | ~200 edges |
| Domain: Agricultural Crop Types | United States | 46 |
| Domain: Agricultural Livestock Categories | United States | 27 |
| Domain: Agricultural Farming Methods | United States | 28 |
| Domain: Agricultural Commodity Grades | United States | 30 |
| Domain: NAICS 11 -> Agriculture Domain crosswalk | United States | ~48 edges |
| Domain: Mining Mineral Types | Global | 25 |
| Domain: Mining Extraction Methods | Global | 20 |
| Domain: Mining Reserve Classification | Global | 12 |
| Domain: NAICS 21 -> Mining Domain crosswalk | United States | ~31 edges |
| Domain: Utility Energy Sources | United States | 17 |
| Domain: Utility Grid Regions | United States | 15 |
| Domain: NAICS 22 -> Utility Domain crosswalk | United States | ~20 edges |
| Domain: Construction Trade Types | United States | 20 |
| Domain: Construction Building Types | United States | 17 |
| Domain: NAICS 23 -> Construction Domain crosswalk | United States | ~27 edges |
| Domain: Manufacturing Process Types | Global | 20 |
| Domain: Retail Channel Types | United States | 19 |
| Domain: Finance Instrument Types | Global | 24 |
| Domain: Health Care Settings | United States | 23 |
| Domain: Transportation Modes | United States | 21 |
| Domain: Information and Media Types | United States | 20 |
| Domain: Real Estate Property Types | United States | 20 |
| Domain: Food Service and Accommodation | United States | 23 |
| Domain: Wholesale Trade Channels | United States | 20 |
| Domain: Professional Services Types | United States | 21 |
| Domain: Education Program Types | United States | 22 |
| Domain: Arts and Entertainment Content Types | United States | 22 |
| Domain: Other Services Types | United States | 20 |
| Domain: Public Administration Types | United States | 22 |
| Domain: Supply Chain and Trade Terms | Global | 23 |
| Domain: Workforce Safety and Health | United States | 24 |
| ANZSCO 2022 | Australia / New Zealand | 1,590 |
| ICD-11 MMS | Global (WHO) | 37,052 |
| LOINC | Global (Regenstrief) | 102,751 |
| Domain: Chemical Industry Types | Global | 29 |
| Domain: Defence and Security Types | Global | 23 |
| Domain: Water and Environment Types | Global | 28 |
| Domain: AI and Data Types | Global | 25 |
| Domain: Biotechnology and Genomics Types | Global | 26 |
| Domain: Space and Satellite Economy Types | Global | 24 |
| Domain: Climate Technology Types | Global | 30 |
| Domain: Advanced Materials Types | Global | 27 |
| Domain: Quantum Computing Types | Global | 23 |
| Domain: Digital Assets and Web3 Types | Global | 25 |
| Domain: Autonomous Systems and Robotics Types | Global | 27 |
| Domain: New Energy Storage Types | Global | 25 |
| Domain: Next-Generation Semiconductor Types | Global | 31 |
| Domain: Synthetic Biology Types | Global | 28 |
| Domain: Extended Reality and Metaverse Types | Global | 27 |
| Nation-Sector Geographic Synergy Crosswalk | Global | 98 edges |
| Domain: Truck Pricing and Rate Structures | United States | 27 |
| Domain: Truck Regulatory Compliance | United States | 25 |
| Domain: Truck Technology Adoption | United States | 22 |
| Domain: Truck Lane and Geography | United States | 23 |
| Domain: Agricultural Equipment and Machinery | United States | 35 |
| Domain: Agricultural Input Supply Types | United States | 30 |
| Domain: Agricultural Business Structure | United States | 27 |
| Domain: Agricultural Market Channel Types | United States | 26 |
| Domain: Agricultural Regulatory Framework | United States | 30 |
| Domain: Agricultural Land and Soil Classification | United States | 35 |
| Domain: Agricultural Post-Harvest and Value Chain | United States | 37 |
| Domain: Mining Equipment Types | Global | 30 |
| Domain: Mining Project Lifecycle Phases | Global | 26 |
| Domain: Mining Safety and Regulatory Compliance | Global | 25 |
| Domain: Utility Tariff and Rate Structure Types | United States | 26 |
| Domain: Utility Infrastructure Asset Types | United States | 25 |
| Domain: Utility Regulatory Ownership Types | United States | 25 |
| Domain: Construction Project Delivery Methods | United States | 22 |
| Domain: Construction Material System Types | United States | 24 |
| Domain: Construction Sustainability and Green Building Types | United States | 24 |
| Domain: Manufacturing Industry Vertical | Global | 26 |
| Domain: Manufacturing Quality and Compliance | Global | 18 |
| Domain: Manufacturing Operations Model Types | Global | 18 |
| Domain: Retail Merchandise Category Types | United States | 20 |
| Domain: Retail Fulfillment and Last-Mile Delivery | United States | 18 |
| Domain: Finance Market Structure Types | Global | 18 |
| Domain: Finance Regulatory Framework Types | Global | 18 |
| Domain: Health Care Specialty Service Lines | United States | 20 |
| Domain: Health Care Payer Types | United States | 18 |
| Domain: Transportation Service Class Types | United States | 19 |
| Domain: Transportation Infrastructure Types | United States | 19 |
| Domain: Information and Media Revenue Model Types | United States | 18 |
| Domain: Information Platform and Distribution Types | United States | 18 |
| Domain: Real Estate Transaction Types | United States | 16 |
| Domain: Real Estate Capital Structure Types | United States | 15 |
| Domain: Food Service Revenue Mix Types | United States | 15 |
| Domain: Food Service Ownership and Business Model Types | United States | 16 |
| Domain: Education Funding Source and Governance | United States | 18 |
| Domain: Education Learner Segment Types | United States | 18 |
| Domain: Arts and Entertainment Monetization Types | United States | 19 |
| Domain: Arts and Entertainment Creator Structure Types | United States | 15 |
| Domain: Other Services Pricing and Delivery Types | United States | 15 |
| Domain: Public Administration Funding Source Types | United States | 19 |
| Domain: Supply Chain Technology Platform Types | Global | 19 |
| Domain: Supply Chain Risk Category Types | Global | 18 |
| Domain: Workforce Training and Development Types | United States | 18 |
| Domain: Workforce Safety Management System Types | United States | 15 |
| GB/T 4754-2017 | China | 118 |
| KSIC 2017 | South Korea | 108 |
| SSIC 2020 | Singapore | 21 |
| MSIC 2008 | Malaysia | 21 |
| TSIC 2009 | Thailand | 21 |
| PSIC 2009 | Philippines | 21 |
| SITC Rev 4 | Global (UN) | 77 |
| BEC Rev 5 | Global (UN) | 29 |
| NOC 2021 | Canada | 51 |
| UK SOC 2020 | United Kingdom | 43 |
| KldB 2010 | Germany | 54 |
| ROME v4 | France | 93 |
| NUCC HCPT | United States | 94 |
| MS-DRG | United States | 50 |
| HCPCS Level II | United States | 59 |
| SASB SICS | Global | 86 |
| EU Taxonomy | European Union | 60 |
| EU NUTS 2021 | European Union | 124 |
| US FIPS | United States | 86 |
| HTS (US) | United States | 120 |
| ICD-10-CM | United States | 97,606 |
| MeSH | Global | 31,124 |
| PRODCOM | European Union | 38 |
| CPV 2008 | European Union | 96 |
| ACM CCS 2012 | Global | 67 |
| JEL Codes | Global | 98 |
| Domain: Chemical Hazard Classification | Global | 21 |
| Domain: Chemical Regulatory Framework Types | Global | 20 |
| Domain: Defence Acquisition Programme Types | Global | 21 |
| Domain: Defence Technology Readiness Levels | Global | 15 |
| Domain: Water and Environment Regulatory Framework Types | Global | 19 |
| Domain: Water Ecosystem Service Types | Global | 18 |
| Domain: AI Deployment Infrastructure Types | Global | 22 |
| Domain: AI Ethics and Governance Framework Types | Global | 21 |
| Domain: Biotechnology Regulatory Pathway Types | Global | 19 |
| Domain: Biotechnology Business Model Types | Global | 20 |
| Domain: Space Orbital Classification Types | Global | 20 |
| Domain: Space Regulatory and Licensing Framework Types | Global | 17 |
| Domain: Climate Finance Instrument Types | Global | 20 |
| Domain: Climate Policy Mechanism Types | Global | 20 |
| Domain: Advanced Materials Application Sector Types | Global | 20 |
| Domain: Advanced Materials Manufacturing Process Types | Global | 20 |
| Domain: Quantum Computing Application Domain Types | Global | 16 |
| Domain: Quantum Technology Commercialization Stage Types | Global | 13 |
| Domain: Digital Assets Regulatory Framework Types | Global | 18 |
| Domain: Digital Assets Infrastructure Layer Types | Global | 17 |
| Domain: Robotics Application Domain Types | Global | 20 |
| Domain: Robotics Sensing and Perception Technology Types | Global | 17 |
| Domain: Energy Storage Application Use Case Types | Global | 20 |
| Domain: Energy Storage Performance and Specification Types | Global | 16 |
| Domain: Semiconductor Application End-Market Types | Global | 20 |
| Domain: Semiconductor IP and Business Model Types | Global | 17 |
| Domain: Synthetic Biology Application Sector Types | Global | 19 |
| Domain: Synthetic Biology Biosafety and Containment Level Types | Global | 16 |
| Domain: Extended Reality Application Domain Types | Global | 21 |
| Domain: Extended Reality Business Model Types | Global | 17 |
| Domain: Manufacturing Supply Chain Integration Model Types | Global | 19 |
| Domain: Manufacturing Facility and Production Configuration Types | Global | 17 |
| Domain: Retail Pricing Strategy Types | United States | 20 |
| Domain: Retail Store Format and Size Types | United States | 20 |
| Domain: Finance Client and Investor Segment Types | Global | 19 |
| Domain: Health Care Delivery and Payment Model Types | United States | 18 |
| Domain: Health Information Technology System Types | United States | 21 |
| Domain: Transportation Fare and Pricing Model Types | United States | 18 |
| Domain: Transportation Fleet Ownership and Operating Model Types | United States | 17 |
| Domain: Information and Media Content Format Types | United States | 20 |
| Domain: Real Estate Property Class and Grade Types | United States | 16 |
| Domain: Real Estate Leasing Structure Types | United States | 17 |
| Domain: Food Service Cuisine and Menu Category Types | United States | 22 |
| Domain: Education Delivery Format and Modality Types | United States | 18 |
| Domain: Education Credential and Award Types | United States | 19 |
| Domain: Professional Services Billing and Fee Arrangement Types | United States | 19 |
| Domain: Arts and Entertainment Venue and Distribution Platform Types | United States | 19 |
| Domain: Public Administration Procurement Method Types | United States | 19 |
| Domain: Supply Chain Logistics Service Model Types | Global | 19 |
| Domain: Workforce Safety Incident Classification Types | United States | 18 |
| Domain: Personal Protective Equipment (PPE) Category Types | United States | 24 |
| Domain: Wholesale Distribution Strategy and Model Types | United States | 19 |
| ATECO 2007 | Italy | 996 |
| NAF Rev 2 | France | 996 |
| PKD 2007 | Poland | 996 |
| SBI 2008 | Netherlands | 996 |
| SNI 2007 | Sweden | 996 |
| DB07 | Denmark | 996 |
| TOL 2008 | Finland | 996 |
| CIIU Rev 4 AC (Colombia) | Colombia | 766 |
| CLANAE Rev 4 (Argentina) | Argentina | 766 |
| CIIU Rev 4 (Chile) | Chile | 766 |
| arXiv Taxonomy | Global | 110 |
| SDG 2030 | Global (UN) | 82 |
| OECD DAC | Global (OECD) | 62 |
| GRI Standards | Global | 38 |
| ICB | Global | 32 |
| Basel Exposure | Global | 36 |
| WB Income Groups | Global | 27 |
| ADB Sector | Asia-Pacific | 46 |
| TNFD | Global | 34 |
| SFDR | European Union | 30 |
| MSC 2020 | Global | 92 |
| PACS | Global | 70 |
| LCC | Global | 111 |
| ECCN | United States | 58 |
| Schedule B | United States | 119 |
| ICD-10-PCS | United States | 79,987 |
| ICD-O-3 | Global (WHO) | 115 |
| ICF | Global (WHO) | 34 |
| CAE Rev 3 | Portugal | 996 |
| CZ-NACE | Czech Republic | 996 |
| TEAOR 2008 | Hungary | 996 |
| CAEN Rev 2 | Romania | 996 |
| NKD 2007 | Croatia | 996 |
| SK NACE Rev 2 | Slovakia | 996 |
| NKID | Bulgaria | 996 |
| EMTAK | Estonia | 996 |
| EVRK (NACE-LT) | Lithuania | 996 |
| NK (NACE-LV) | Latvia | 996 |
| NACE Rev 2 (Turkey) | Turkey | 996 |
| CIIU Rev 4 (Peru) | Peru | 766 |
| CIIU Rev 4 (Ecuador) | Ecuador | 766 |
| CAEB (Bolivia) | Bolivia | 766 |
| CIIU Rev 4 (Venezuela) | Venezuela | 766 |
| CIIU Rev 4 (Costa Rica) | Costa Rica | 766 |
| CIIU Rev 4 (Guatemala) | Guatemala | 766 |
| CIIU Rev 4 (Panama) | Panama | 766 |
| VSIC 2018 | Vietnam | 766 |
| BSIC | Bangladesh | 766 |
| PSIC (Pakistan) | Pakistan | 766 |
| ISIC Rev 4 (Nigeria) | Nigeria | 766 |
| ISIC Rev 4 (Kenya) | Kenya | 766 |
| ISIC Rev 4 (Egypt) | Egypt | 766 |
| ISIC Rev 4 (Saudi Arabia) | Saudi Arabia | 766 |
| ISIC Rev 4 (UAE) | United Arab Emirates | 766 |
| COICOP 2018 | Global (UN) | 62 |
| CFI ISO 10962 | Global (ISO) | 63 |
| FORD Frascati 2015 | Global (OECD) | 48 |
| CN 2024 | European Union | 118 |
| ANZSRC FOR 2020 | Australia / New Zealand | 166 |
| ICD-10-GM | Germany | 51 |
| ICD-10-AM | Australia / New Zealand | 52 |
| SEEA | Global (UN) | 47 |
| CNAE 2009 | Spain | 996 |
| NACE-BEL 2008 | Belgium | 996 |
| NACE-LU 2008 | Luxembourg | 996 |
| NACE Rev 2 (Ireland) | Ireland | 996 |
| STAKOD 08 | Greece | 996 |
| NACE Rev 2 (Cyprus) | Cyprus | 996 |
| NACE Rev 2 (Malta) | Malta | 996 |
| SKD 2008 | Slovenia | 996 |
| SN 2007 | Norway | 996 |
| ISAT 2008 | Iceland | 996 |
| KD 2010 (Serbia) | Serbia | 996 |
| NKD Rev 2 (North Macedonia) | North Macedonia | 996 |
| KD BiH 2010 | Bosnia and Herzegovina | 996 |
| KD 2010 (Montenegro) | Montenegro | 996 |
| NVE Rev 2 (Albania) | Albania | 996 |
| KD 2010 (Kosovo) | Kosovo | 996 |
| CAEM Rev 2 (Moldova) | Moldova | 996 |
| KVED 2010 (Ukraine) | Ukraine | 996 |
| NACE Rev 2 (Georgia) | Georgia | 996 |
| NACE Rev 2 (Armenia) | Armenia | 996 |
| KBLI 2020 (Indonesia) | Indonesia | 766 |
| SLSIC (Sri Lanka) | Sri Lanka | 766 |
| ISIC Rev 4 (Myanmar) | Myanmar | 766 |
| ISIC Rev 4 (Cambodia) | Cambodia | 766 |
| ISIC Rev 4 (Laos) | Laos | 766 |
| ISIC Rev 4 (Nepal) | Nepal | 766 |
| ISIC Rev 4 (Ethiopia) | Ethiopia | 766 |
| ISIC Rev 4 (Tanzania) | Tanzania | 766 |
| ISIC Rev 4 (Ghana) | Ghana | 766 |
| ISIC Rev 4 (Morocco) | Morocco | 766 |
| ISIC Rev 4 (Tunisia) | Tunisia | 766 |
| ISIC Rev 4 (Algeria) | Algeria | 766 |
| ISIC Rev 4 (Senegal) | Senegal | 766 |
| ISIC Rev 4 (Cameroon) | Cameroon | 766 |
| ISIC Rev 4 (Uganda) | Uganda | 766 |
| ISIC Rev 4 (Mozambique) | Mozambique | 766 |
| ISIC Rev 4 (Iraq) | Iraq | 766 |
| ISIC Rev 4 (Jordan) | Jordan | 766 |
| CIIU Rev 4 (Paraguay) | Paraguay | 766 |
| CIIU Rev 4 (Uruguay) | Uruguay | 766 |
| CIIU Rev 4 (Dominican Republic) | Dominican Republic | 766 |
| ISIC Rev 4 (Honduras) | Honduras | 766 |
| ISIC Rev 4 (El Salvador) | El Salvador | 766 |
| ISIC Rev 4 (Nicaragua) | Nicaragua | 766 |
| ISIC Rev 4 (Zimbabwe) | Zimbabwe | 766 |
| ISIC Rev 4 (Trinidad and Tobago) | Trinidad and Tobago | 766 |
| ISIC Rev 4 (Jamaica) | Jamaica | 766 |
| ISIC Rev 4 (Haiti) | Haiti | 766 |
| ISIC Rev 4 (Fiji) | Fiji | 766 |
| ISIC Rev 4 (Papua New Guinea) | Papua New Guinea | 766 |
| ISIC Rev 4 (Mongolia) | Mongolia | 766 |
| ISIC Rev 4 (Kazakhstan) | Kazakhstan | 766 |
| ISIC Rev 4 (Uzbekistan) | Uzbekistan | 766 |
| ISIC Rev 4 (Azerbaijan) | Azerbaijan | 766 |
| ISIC Rev 4 (Ivory Coast) | Ivory Coast | 766 |
| ISIC Rev 4 (Rwanda) | Rwanda | 766 |
| ISIC Rev 4 (Zambia) | Zambia | 766 |
| ISIC Rev 4 (Botswana) | Botswana | 766 |
| ISIC Rev 4 (Namibia) | Namibia | 766 |
| ISIC Rev 4 (Madagascar) | Madagascar | 766 |
| ISIC Rev 4 (Mauritius) | Mauritius | 766 |
| ISIC Rev 4 (Burkina Faso) | Burkina Faso | 766 |
| ISIC Rev 4 (Mali) | Mali | 766 |
| ISIC Rev 4 (Malawi) | Malawi | 766 |
| ISIC Rev 4 (Afghanistan) | Afghanistan | 766 |
| ISIC Rev 4 (Lebanon) | Lebanon | 766 |
| ISIC Rev 4 (Oman) | Oman | 766 |
| ISIC Rev 4 (Qatar) | Qatar | 766 |
| ISIC Rev 4 (Bahrain) | Bahrain | 766 |
| ISIC Rev 4 (Kuwait) | Kuwait | 766 |
| ISIC Rev 4 (Yemen) | Yemen | 766 |
| ISIC Rev 4 (Iran) | Iran | 766 |
| ISIC Rev 4 (Libya) | Libya | 766 |
| ISIC Rev 4 (Israel) | Israel | 766 |
| ISIC Rev 4 (Palestine) | Palestine | 766 |
| ISIC Rev 4 (Syria) | Syria | 766 |
| ISIC Rev 4 (Kyrgyzstan) | Kyrgyzstan | 766 |
| ISIC Rev 4 (Tajikistan) | Tajikistan | 766 |
| ISIC Rev 4 (Turkmenistan) | Turkmenistan | 766 |
| ISIC Rev 4 (Cuba) | Cuba | 766 |
| ISIC Rev 4 (Barbados) | Barbados | 766 |
| ISIC Rev 4 (Bahamas) | Bahamas | 766 |
| ISIC Rev 4 (Guyana) | Guyana | 766 |
| ISIC Rev 4 (Suriname) | Suriname | 766 |
| ISIC Rev 4 (Belize) | Belize | 766 |
| ISIC Rev 4 (Antigua and Barbuda) | Antigua and Barbuda | 766 |
| ISIC Rev 4 (Saint Lucia) | Saint Lucia | 766 |
| ISIC Rev 4 (Grenada) | Grenada | 766 |
| ISIC Rev 4 (Saint Vincent) | Saint Vincent and the Grenadines | 766 |
| ISIC Rev 4 (Dominica) | Dominica | 766 |
| ISIC Rev 4 (Saint Kitts) | Saint Kitts and Nevis | 766 |
| ISIC Rev 4 (South Sudan) | South Sudan | 766 |
| ISIC Rev 4 (Somalia) | Somalia | 766 |
| ISIC Rev 4 (Guinea) | Guinea | 766 |
| ISIC Rev 4 (Sierra Leone) | Sierra Leone | 766 |
| ISIC Rev 4 (Liberia) | Liberia | 766 |
| ISIC Rev 4 (Togo) | Togo | 766 |
| ISIC Rev 4 (Benin) | Benin | 766 |
| ISIC Rev 4 (Niger) | Niger | 766 |
| ISIC Rev 4 (Chad) | Chad | 766 |
| ISIC Rev 4 (DRC) | Democratic Republic of the Congo | 766 |
| ISIC Rev 4 (Angola) | Angola | 766 |
| ISIC Rev 4 (Gabon) | Gabon | 766 |
| ISIC Rev 4 (Equatorial Guinea) | Equatorial Guinea | 766 |
| ISIC Rev 4 (Congo Republic) | Republic of the Congo | 766 |
| ISIC Rev 4 (Comoros) | Comoros | 766 |
| ISIC Rev 4 (Djibouti) | Djibouti | 766 |
| ISIC Rev 4 (Cabo Verde) | Cabo Verde | 766 |
| ISIC Rev 4 (Gambia) | Gambia | 766 |
| ISIC Rev 4 (Guinea-Bissau) | Guinea-Bissau | 766 |
| ISIC Rev 4 (Mauritania) | Mauritania | 766 |
| ISIC Rev 4 (Eswatini) | Eswatini | 766 |
| ISIC Rev 4 (Lesotho) | Lesotho | 766 |
| ISIC Rev 4 (Burundi) | Burundi | 766 |
| ISIC Rev 4 (Eritrea) | Eritrea | 766 |
| ISIC Rev 4 (Seychelles) | Seychelles | 766 |
| ISIC Rev 4 (Samoa) | Samoa | 766 |
| ISIC Rev 4 (Tonga) | Tonga | 766 |
| ISIC Rev 4 (Vanuatu) | Vanuatu | 766 |
| ISIC Rev 4 (Solomon Islands) | Solomon Islands | 766 |
| ISIC Rev 4 (Brunei) | Brunei | 766 |
| ISIC Rev 4 (East Timor) | East Timor | 766 |
| ISIC Rev 4 (Bhutan) | Bhutan | 766 |
| ISIC Rev 4 (Maldives) | Maldives | 766 |
| Domain: Insurance Product Types | Global | 25 |
| Domain: Insurance Risk Classification | Global | 25 |
| Domain: Legal Practice Area Types | United States | 26 |
| Domain: Telecom Service Types | Global | 25 |
| Domain: Telecom Network Technology Types | Global | 25 |
| Domain: Cybersecurity Threat Types | Global | 27 |
| Domain: Cybersecurity Framework Types | Global | 22 |
| Domain: Gaming and Esports Types | Global | 27 |
| Domain: Waste Management Types | Global | 27 |
| Domain: Textile and Fashion Types | Global | 27 |
| Domain: Tourism and Travel Types | Global | 27 |
| Domain: Maritime Shipping Types | Global | 27 |
| Domain: Aviation Service Types | Global | 27 |
| Domain: Forestry Management Types | Global | 27 |
| Domain: Fishing and Aquaculture Types | Global | 25 |
| Domain: Wine and Spirits Types | Global | 27 |
| Domain: Nuclear Energy Types | Global | 26 |
| Domain: Hydrogen Economy Types | Global | 27 |
| Domain: Pet and Animal Care Types | United States | 26 |
| Domain: Sports and Recreation Types | United States | 27 |
| Domain: Nonprofit and Social Impact Types | United States | 27 |
| Domain: Childcare and Early Education Types | United States | 26 |
| Domain: Senior Care Types | United States | 26 |
| Domain: Advertising and Marketing Types | United States | 28 |
| Domain: Datacenter and Cloud Infrastructure | Global | 26 |
| Domain: E-Commerce Platform Types | Global | 26 |
| Domain: Fintech Service Types | Global | 27 |
| Domain: EdTech Platform Types | Global | 27 |
| Domain: PropTech Types | Global | 27 |
| Domain: AgriTech Types | Global | 27 |
| Domain: HealthTech Types | Global | 27 |
| Domain: CleanTech Types | Global | 27 |
| Domain: LegalTech Types | Global | 27 |
| Domain: InsurTech Types | Global | 27 |
| Domain: RegTech Types | Global | 27 |
| HIPAA | United States | 36 |
| SOX (Sarbanes-Oxley) | United States | 56 |
| GLBA (Gramm-Leach-Bliley) | United States | 28 |
| FERPA | United States | 30 |
| COPPA | United States | 23 |
| FCRA (Fair Credit Reporting) | United States | 28 |
| ADA (Americans with Disabilities) | United States | 31 |
| OSHA 29 CFR 1910 (General Industry) | United States | 47 |
| OSHA 29 CFR 1926 (Construction) | United States | 49 |
| NERC CIP | United States | 49 |
| FISMA | United States | 26 |
| FedRAMP | United States | 37 |
| CCPA/CPRA | United States | 34 |
| CFPB Regulations | United States | 22 |
| SEC Regulations | United States | 28 |
| FINRA Rules | United States | 27 |
| FAR (Federal Acquisition) | United States | 32 |
| DFARS | United States | 25 |
| ITAR | United States | 32 |
| EAR (Export Administration) | United States | 31 |
| Clean Air Act | United States | 28 |
| Clean Water Act | United States | 22 |
| CERCLA (Superfund) | United States | 25 |
| RCRA | United States | 29 |
| TSCA | United States | 22 |
| PCI DSS v4.0 | Global | 29 |
| SOC 2 Trust Criteria | United States | 37 |
| HITRUST CSF | United States | 27 |
| CMMC 2.0 | United States | 24 |
| NIST CSF 2.0 | United States | 28 |
| NIST SP 800-53 Rev 5 | United States | 36 |
| NIST SP 800-171 Rev 3 | United States | 28 |
| CIS Controls v8 | Global | 29 |
| COBIT 2019 | Global | 44 |
| COSO Framework | Global | 22 |
| FFIEC IT Handbook | United States | 25 |
| FTC Safeguards Rule | United States | 22 |
| NAIC Model Laws | United States | 21 |
| US GAAP (ASC) | United States | 33 |
| FASB Standards | United States | 19 |
| PCAOB Standards | United States | 23 |
| AICPA Professional Standards | United States | 21 |
| Joint Commission Standards | United States | 30 |
| CAP Accreditation | United States | 21 |
| CLIA Regulations | United States | 20 |
| FDA 21 CFR Parts | United States | 24 |
| DEA Schedules | United States | 25 |
| USP Chapters | United States | 21 |
| ASHRAE Standards | United States | 21 |
| ANSI/ASME Standards | United States | 24 |
| DORA (EU) 2022/2554 | European Union | 27 |
| NIS2 Directive | European Union | 24 |
| EU AI Act | European Union | 27 |
| ePrivacy Directive | European Union | 15 |
| MiFID II | European Union | 24 |
| Solvency II | European Union | 22 |
| PSD2 | European Union | 19 |
| REACH | European Union | 19 |
| RoHS Directive | European Union | 22 |
| MDR (Medical Device Regulation) | European Union | 22 |
| IVDR | European Union | 17 |
| EU Whistleblower Directive | European Union | 17 |
| CSRD | European Union | 25 |
| CBAM | European Union | 18 |
| WEEE Directive | European Union | 21 |
| EU Packaging Regulation | European Union | 19 |
| EU Batteries Regulation | European Union | 18 |
| SFDR (Detailed) | European Union | 22 |
| EU Deforestation Regulation | European Union | 20 |
| Digital Services Act | European Union | 21 |
| Digital Markets Act | European Union | 19 |
| EU Cyber Resilience Act | European Union | 20 |
| EU Data Act | European Union | 20 |
| EU Machinery Regulation | European Union | 20 |
| EMAS | European Union | 25 |
| ISO 9001:2015 (Quality) | Global | 35 |
| ISO 14001:2015 (Environmental) | Global | 29 |
| ISO/IEC 27001:2022 (Info Security) | Global | 30 |
| ISO 22000:2018 (Food Safety) | Global | 31 |
| ISO 45001:2018 (OH&S) | Global | 30 |
| ISO 50001:2018 (Energy) | Global | 26 |
| ISO 13485:2016 (Medical Devices QMS) | Global | 28 |
| ISO 22301:2019 (Business Continuity) | Global | 26 |
| ISO/IEC 20000-1:2018 (IT Service Mgmt) | Global | 23 |
| ISO 26000:2010 (Social Responsibility) | Global | 22 |
| ISO 37001:2016 (Anti-Bribery) | Global | 29 |
| ISO/IEC 42001:2023 (AI Management) | Global | 32 |
| ISO 28000:2022 (Supply Chain Security) | Global | 24 |
| ISO 55001:2014 (Asset Management) | Global | 25 |
| ISO 41001:2018 (Facility Management) | Global | 23 |
| ISO 30401:2018 (Knowledge Management) | Global | 22 |
| ISO 21001:2018 (Education) | Global | 31 |
| ISO 39001:2012 (Road Traffic Safety) | Global | 24 |
| ISO 37101:2016 (Sustainable Communities) | Global | 23 |
| ISO 14064 (Greenhouse Gas) | Global | 20 |
| ISO 14040 (Life Cycle Assessment) | Global | 25 |
| ISO 19011:2018 (Auditing) | Global | 30 |
| ISO 31010:2019 (Risk Assessment) | Global | 26 |
| ISO 22313:2020 (BC Guidance) | Global | 24 |
| ISO/IEC 27701:2019 (Privacy) | Global | 27 |
| Basel III/IV | Global | 24 |
| FATF 40 Recommendations | Global | 29 |
| ILO Core Conventions | Global | 16 |
| UN Guiding Principles (Business & HR) | Global | 22 |
| OECD MNE Guidelines | Global | 22 |
| WTO SPS Agreement | Global | 19 |
| WTO TBT Agreement | Global | 17 |
| Codex Alimentarius | Global | 22 |
| WHO FCTC | Global | 18 |
| UNCITRAL Model Laws | Global | 20 |
| UNCLOS | Global | 25 |
| Montreal Protocol | Global | 19 |
| Paris Agreement | Global | 20 |
| Kimberley Process | Global | 17 |
| Equator Principles | Global | 18 |
| IFC Performance Standards | Global | 21 |
| ICAO Annexes | Global | 26 |
| IMO MARPOL | Global | 20 |
| IMO SOLAS | Global | 21 |
| Berne Convention | Global | 18 |
| Domain: Pharma Drug Classification | Global | 26 |
| Domain: Medical Device Classification | Global | 19 |
| Domain: Clinical Trial Classification | Global | 22 |
| Domain: Mental Health Service Types | Global | 22 |
| Domain: Dental Service Types | United States | 18 |
| Domain: Veterinary Service Types | Global | 19 |
| Domain: Credit Rating Scale Types | Global | 21 |
| Domain: Derivatives Instrument Types | Global | 22 |
| Domain: Private Equity Stage Types | Global | 20 |
| Domain: Digital Banking Service Types | Global | 21 |
| Domain: Payment Processing Types | Global | 21 |
| Domain: Trade Finance Instrument Types | Global | 18 |
| Domain: Reinsurance Types | Global | 18 |
| Domain: Microfinance Types | Global | 18 |
| Domain: Autonomous Vehicle Level Types | Global | 17 |
| Domain: EV Charging Infrastructure Types | Global | 18 |
| Domain: Fleet Management Types | Global | 18 |
| Domain: Rail Service Classification Types | Global | 17 |
| Domain: Last-Mile Delivery Types | Global | 17 |
| Domain: Solar Energy Types | Global | 19 |
| Domain: Wind Energy Types | Global | 17 |
| Domain: Battery Technology Types | Global | 19 |
| Domain: Smart Grid Types | Global | 18 |
| Domain: Carbon Credit Types | Global | 18 |
| Domain: Cloud Service Model Types | Global | 19 |
| Domain: DevOps Practice Types | Global | 20 |
| Domain: SaaS Category Types | Global | 18 |
| Domain: IoT Device Classification Types | Global | 17 |
| Domain: Organic Certification Types | Global | 16 |
| Domain: Crop Protection Types | Global | 17 |
| Domain: Soil Management Types | Global | 17 |
| Domain: Precision Agriculture Types | Global | 17 |
| Domain: Digital Twin Application Types | Global | 19 |
| Domain: Edge Computing Types | Global | 17 |
| Domain: Coworking Space Types | Global | 17 |
| Domain: Event Management Types | Global | 18 |
| Domain: Franchise Model Types | Global | 17 |
| Domain: Subscription Model Types | Global | 19 |
| Domain: Circular Economy Types | Global | 18 |
| Domain: Sharing Economy Types | Global | 17 |
| Domain: HR Technology Types | Global | 18 |
| Domain: Talent Marketplace Types | Global | 18 |
| Domain: Insurance Underwriting Types | Global | 15 |
| Domain: Insurance Claims Types | Global | 17 |
| Domain: Actuarial Method Types | Global | 16 |
| Domain: Commercial Lending Types | Global | 16 |
| Domain: Mortgage Types | Global | 16 |
| Domain: Wealth Management Types | Global | 17 |
| Domain: Hedge Fund Strategy Types | Global | 18 |
| Domain: Commodity Trading Types | Global | 16 |
| Domain: Forex Instrument Types | Global | 15 |
| Domain: Bond Rating Types | Global | 18 |
| Domain: Municipal Bond Types | Global | 15 |
| Domain: Asset Securitization Types | Global | 17 |
| Domain: REIT Types | Global | 17 |
| Domain: Property Valuation Types | Global | 16 |
| Domain: Zoning Classification Types | United States | 19 |
| Domain: Construction Permit Types | United States | 16 |
| Domain: Building Code Types | United States | 16 |
| Domain: Fire Protection Types | United States | 16 |
| Domain: Elevator Inspection Types | United States | 14 |
| Domain: Plumbing Code Types | United States | 16 |
| Domain: Electrical Code Types | United States | 16 |
| Domain: HVAC System Types | Global | 17 |
| Domain: Roofing Types | United States | 16 |
| Domain: Foundation Types | United States | 15 |
| Domain: Structural System Types | Global | 17 |
| Domain: Facade System Types | Global | 16 |
| Domain: Landscape Types | United States | 17 |
| Domain: Parking Types | United States | 16 |
| Domain: Signage Types | United States | 16 |
| Domain: Accessibility Feature Types | United States | 16 |
| Domain: Environmental Remediation Types | Global | 17 |
| Domain: Brownfield Types | United States | 16 |
| Domain: Green Building Material Types | Global | 17 |
| Domain: Modular Construction Types | Global | 16 |
| Domain: Prefab Types | Global | 14 |
| Domain: Smart Building Types | Global | 17 |
| Domain: Building Automation Types | Global | 16 |
| Domain: Energy Audit Types | Global | 16 |
| Domain: Commissioning Types | Global | 18 |
| Domain: Retro-Commissioning Types | Global | 16 |
| Domain: Facilities Benchmarking Types | Global | 16 |
| Domain: Lease Abstraction Types | Global | 17 |
| Domain: API Architecture Types | Global | 17 |
| Domain: Database Type Classification | Global | 17 |
| Domain: Programming Paradigm Types | Global | 16 |
| Domain: Software License Types | Global | 17 |
| Domain: Open Source Governance Types | Global | 16 |
| Domain: Version Control Types | Global | 15 |
| Domain: CI/CD Pipeline Types | Global | 17 |
| Domain: Container Orchestration Types | Global | 16 |
| Domain: Serverless Pattern Types | Global | 15 |
| Domain: Microservices Pattern Types | Global | 17 |
| Domain: Event-Driven Architecture Types | Global | 16 |
| Domain: Data Mesh Types | Global | 15 |
| Domain: Data Lakehouse Types | Global | 15 |
| Domain: MLOps Types | Global | 17 |
| Domain: Feature Store Types | Global | 15 |
| Domain: Model Registry Types | Global | 14 |
| Domain: Data Catalog Types | Global | 15 |
| Domain: Data Quality Types | Global | 16 |
| Domain: Data Governance Types | Global | 16 |
| Domain: Data Lineage Types | Global | 14 |
| Domain: Master Data Management Types | Global | 16 |
| Domain: Reference Data Management Types | Global | 15 |
| Domain: Synthetic Data Types | Global | 15 |
| Domain: Privacy Enhancing Technology Types | Global | 16 |
| Domain: Zero Trust Architecture Types | Global | 16 |
| Domain: Identity Governance Types | Global | 16 |
| Domain: SIEM Types | Global | 15 |
| Domain: SOAR Platform Types | Global | 15 |
| Domain: Threat Intelligence Types | Global | 16 |
| Domain: Vulnerability Management Types | Global | 16 |
| Domain: Penetration Testing Types | Global | 15 |
| Domain: Incident Response Types | Global | 16 |
| Domain: Disaster Recovery Types | Global | 15 |
| Domain: Backup Strategy Types | Global | 15 |
| Domain: Encryption Standard Types | Global | 16 |
| Domain: Key Management Types | Global | 15 |
| Domain: Certificate Authority Types | Global | 15 |
| Domain: PKI Component Types | Global | 15 |
| Domain: Hardware Security Module Types | Global | 15 |
| Domain: Red Team Types | Global | 15 |
| Domain: Blue Team Types | Global | 16 |
| Domain: Purple Team Types | Global | 14 |
| Domain: Hospital Department Types | United States | 18 |
| Domain: Nursing Specialty Types | United States | 17 |
| Domain: Allied Health Profession Types | United States | 16 |
| Domain: Lab Test Category Types | Global | 17 |
| Domain: Imaging Modality Types | Global | 16 |
| Domain: Surgical Specialty Types | Global | 17 |
| Domain: Anesthesia Types | Global | 16 |
| Domain: Pathology Subspecialty Types | Global | 15 |
| Domain: Pharmacy Practice Types | United States | 16 |
| Domain: Formulary Tier Types | United States | 15 |
| Domain: Drug Interaction Types | Global | 15 |
| Domain: Adverse Event Classification Types | Global | 15 |
| Domain: Clinical Endpoint Types | Global | 15 |
| Domain: Biomarker Types | Global | 16 |
| Domain: Companion Diagnostic Types | Global | 15 |
| Domain: Orphan Drug Types | Global | 14 |
| Domain: Biosimilar Types | Global | 14 |
| Domain: Gene Therapy Types | Global | 15 |
| Domain: Cell Therapy Types | Global | 15 |
| Domain: Radiopharmaceutical Types | Global | 14 |
| Domain: Medical Gas Types | Global | 14 |
| Domain: Surgical Instrument Types | Global | 16 |
| Domain: Implant Classification Types | Global | 15 |
| Domain: Wound Care Types | Global | 15 |
| Domain: Infection Control Types | Global | 15 |
| Domain: Sterilization Method Types | Global | 15 |
| Domain: Clean Room Classification Types | Global | 15 |
| Domain: Biobank Types | Global | 14 |
| Domain: Clinical Registry Types | Global | 14 |
| Domain: Patient-Reported Outcome Types | Global | 15 |
| Domain: Telemedicine Modality Types | Global | 15 |
| Domain: Remote Monitoring Types | Global | 15 |
| Domain: Clinical Decision Support Types | United States | 15 |
| Domain: Social Determinant of Health Types | Global | 15 |
| Domain: Population Health Types | Global | 14 |
| Domain: Value-Based Care Model Types | United States | 15 |
| Domain: Bundled Payment Types | United States | 15 |
| Domain: Capitation Model Types | United States | 14 |
| Domain: Global Budget Types | United States | 14 |
| Domain: Prosthetic Types | Global | 15 |
| Domain: Orthotic Types | Global | 15 |
| Domain: Health Literacy Types | Global | 14 |
| Domain: Oil Grade Types | Global | 14 |
| Domain: Natural Gas Types | Global | 14 |
| Domain: LNG Terminal Types | Global | 14 |
| Domain: Pipeline Types | Global | 14 |
| Domain: Refinery Process Types | Global | 14 |
| Domain: Petrochemical Types | Global | 15 |
| Domain: Biofuel Generation Types | Global | 14 |
| Domain: Geothermal System Types | Global | 14 |
| Domain: Tidal Energy Types | Global | 13 |
| Domain: Wave Energy Types | Global | 13 |
| Domain: District Heating Types | Global | 14 |
| Domain: Cogeneration Types | Global | 13 |
| Domain: Microgrid Types | Global | 14 |
| Domain: Virtual Power Plant Types | Global | 14 |
| Domain: Demand Response Types | Global | 14 |
| Domain: Ancillary Service Types | Global | 14 |
| Domain: Capacity Market Types | Global | 13 |
| Domain: Renewable Energy Certificate Types | Global | 14 |
| Domain: Carbon Offset Protocol Types | Global | 14 |
| Domain: Emission Factor Types | Global | 14 |
| Domain: Air Quality Index Types | Global | 14 |
| Domain: Water Quality Index Types | Global | 14 |
| Domain: Soil Contamination Types | Global | 14 |
| Domain: Biodiversity Offset Types | Global | 13 |
| Domain: Wetland Types | Global | 14 |
| Domain: Seed Variety Types | Global | 14 |
| Domain: Irrigation Method Types | Global | 14 |
| Domain: Greenhouse Types | Global | 13 |
| Domain: Aquaponics Types | Global | 13 |
| Domain: Vertical Farming Types | Global | 13 |
| Domain: Cold Chain Types | Global | 14 |
| Domain: Warehouse Types | Global | 14 |
| Domain: Cross-Dock Types | Global | 13 |
| Domain: Freight Class Types | United States | 19 |
| Domain: Incoterm Detailed Types | Global | 14 |
| Domain: Customs Procedure Types | Global | 14 |
| Domain: Free Trade Zone Types | Global | 13 |
| Domain: Noise Pollution Types | Global | 13 |
| Domain: Light Pollution Types | Global | 13 |
| Domain: Invasive Species Types | Global | 14 |
| Domain: Coral Reef Types | Global | 14 |
| Domain: Mangrove Types | Global | 13 |
| Domain: University Ranking Types | Global | 14 |
| Domain: Accreditation Body Types | Global | 14 |
| Domain: Student Assessment Types | Global | 15 |
| Domain: Curriculum Standard Types | Global | 14 |
| Domain: Learning Outcome Types | Global | 14 |
| Domain: Competency Framework Types | Global | 14 |
| Domain: Micro-Credential Types | Global | 14 |
| Domain: Apprenticeship Types | Global | 14 |
| Domain: Gig Worker Types | Global | 14 |
| Domain: Employee Benefit Types | United States | 15 |
| Domain: Compensation Structure Types | United States | 14 |
| Domain: Labor Union Types | Global | 13 |
| Domain: EEO Category Types | United States | 14 |
| Domain: Diversity Metric Types | Global | 14 |
| Domain: Government Contract Types | United States | 15 |
| Domain: Grant Types | United States | 14 |
| Domain: Municipal Service Types | United States | 14 |
| Domain: Emergency Service Types | United States | 14 |
| Domain: Court Types | United States | 15 |
| Domain: Alternative Dispute Resolution Types | Global | 14 |
| Domain: Trademark Classification Types | Global | 14 |
| Domain: Patent Types | Global | 14 |
| Domain: Copyright Category Types | Global | 14 |
| Domain: Trade Secret Types | Global | 14 |
| Domain: Antitrust Types | Global | 14 |
| Domain: Consumer Protection Types | United States | 14 |
| Domain: Sanctions Types | Global | 14 |
| Domain: Export Control Types | Global | 14 |
| Domain: Customs Classification Types | Global | 14 |
| Domain: Internship Model Types | Global | 13 |
| Domain: Workplace Mediation Types | Global | 13 |
| Domain: Collective Bargaining Types | Global | 13 |
| Domain: Product Liability Types | Global | 14 |
| Domain: Law Enforcement Types | United States | 14 |
| Domain: Corrections Types | United States | 15 |
| Domain: Notary Types | Global | 13 |
| Domain: Class Action Types | United States | 14 |
| Domain: Freelance Platform Types | Global | 14 |
| Domain: Digital Badge Types | Global | 14 |
| Domain: Arbitration Types | Global | 14 |
| ICD-10-CA | Canada | 23 |
| SNOMED CT (Skeleton) | Global | 20 |
| CPT (AMA Skeleton) | United States | 18 |
| G-DRG (Germany) | Germany | 26 |
| RxNorm (Skeleton) | United States | 16 |
| NDC (National Drug Code) | United States | 112,077 |
| DSM-5 (Skeleton) | Global | 21 |
| ICPC-2 (Primary Care) | Global | 18 |
| ICHI (Health Interventions) | Global | 15 |
| GBD Cause List | Global | 23 |
| GMDN (Medical Devices) | Global | 17 |
| WHO Essential Medicines | Global | 27 |
| CDC Vaccine Schedule | United States | 18 |
| NCI Thesaurus | Global | 211,072 |
| CTCAE (Adverse Events) | Global | 27 |
| IFRS Standards | Global | 34 |
| Bloomberg BICS | Global | 13 |
| Refinitiv TRBC | Global | 13 |
| SFIA v8 | Global | 14 |
| DigComp 2.2 | European Union | 27 |
| e-CF v4 | European Union | 35 |
| Scopus ASJC | Global | 28 |
| Web of Science Categories | Global | 25 |
| EQF Levels | European Union | 13 |
| AQF (Australia) | Australia | 14 |
| O*NET Knowledge Areas | United States | 14 |
| O*NET Abilities | United States | 17 |
| IUCN Red List Categories | Global | 15 |
| CITES Appendices | Global | 16 |
| EU Waste Catalogue | European Union | 21 |
| Stockholm Convention POPs | Global | 19 |
| Rotterdam Convention PIC | Global | 17 |
| Minamata Convention | Global | 15 |
| IATA Aircraft Type Codes | Global | 14 |
| IMO Vessel Type Codes | Global | 17 |
| IETF RFC Categories | Global | 15 |
| W3C Standards | Global | 16 |
| IEEE Standards (Skeleton) | Global | 14 |
| USB-IF Classes | Global | 23 |
| Bluetooth SIG Profiles | Global | 17 |
| ESCO Qualifications | European Union | 15 |
| WorldSkills Categories | Global | 14 |
| O*NET Work Activities | United States | 16 |
| O*NET Work Context | United States | 15 |
| O*NET Interests (RIASEC) | United States | 13 |
| O*NET Work Values | United States | 14 |
| LinkedIn Skills Taxonomy | Global | 17 |
| NQF (UK) | United Kingdom | 14 |
| NAICS 2017 (Historical) | North America | 21 |
| NAICS 2012 (Historical) | North America | 21 |
| ISIC Rev 3.1 | Global | 18 |
| EU TARIC | European Union | 22 |
| UK Trade Tariff | United Kingdom | 22 |
| ASEAN Tariff (AHTN) | Southeast Asia | 19 |
| MERCOSUR Tariff (NCM) | South America | 18 |
| AfCFTA Tariff | Africa | 15 |
| GCC Common Customs Tariff | Gulf States | 17 |
| ECOWAS CET | West Africa | 14 |
| Dewey Decimal (Skeleton) | Global | 11 |
| UDC (Skeleton) | Global | 11 |
| LCSH (Skeleton) | Global | 20 |
| ERA Fields of Research | Australia | 24 |
| UNESCO Thesaurus (Skeleton) | Global | 15 |
| Getty AAT (Skeleton) | Global | 14 |
| AACSB Standards | Global | 14 |
| ABET Criteria | Global | 14 |
| EPA RCRA Hazardous Waste | United States | 15 |
| Ramsar Wetland Classification | Global | 21 |
| CBD Global Biodiversity Targets | Global | 24 |
| UNEP Chemicals | Global | 15 |
| NATO Codification (Skeleton) | Global | 19 |
| FAA Aircraft Categories | United States | 16 |
| UIC Railway Codes | Global | 15 |
| ICAO Airport Code Regions | Global | 21 |
| US DoD MIL-STD Categories | United States | 15 |
| ITU-T Recommendations | Global | 19 |
| 3GPP Specifications | Global | 18 |
| PCI-SIG Specifications | Global | 14 |
| JEDEC Standards | Global | 14 |
| SEMI Standards | Global | 14 |
| VESA Standards | Global | 13 |
| HCPCS Level III | United States | 13 |
| ICN Nursing (ICNP) | Global | 14 |
| EDQM Dosage Forms | European Union | 17 |
| OMIM (Skeleton) | Global | 14 |
| Orphanet (Skeleton) | Global | 16 |
| FTSE Russell ICB (Detailed) | Global | 12 |
| CBD Aichi Targets | Global | 21 |
| UN Ammunition (IATG) | Global | 14 |
| STANAG Categories | Global | 16 |
| ANZSRC SEO | Australia / New Zealand | 17 |
| O*NET Work Styles | United States | 17 |
| IBC 2021 | Global | 26 |
| NFPA Codes | United States | 17 |
| NUTS Candidate Extensions | Europe | 11 |
| OPEC Reference Basket | Global | 14 |
| LME Metals | Global | 15 |
| NMFC | United States | 19 |
| STCC | United States | 26 |
| NAIC Lines of Business | United States | 30 |
| NGSS | United States | 14 |
| Common Core State Standards | United States | 18 |
| Bloom's Taxonomy | Global | 14 |
| GDPR Legal Bases | European Union | 16 |
| Data Retention Period Categories | Global | 16 |
| Codex Alimentarius Committees | Global | 19 |
| HEDIS | United States | 15 |
| CMS Star Ratings | United States | 13 |
| MITRE ATT&CK | Global | 15 |
| CVE/CWE Types | Global | 16 |
| OWASP Top 10 | Global | 11 |
| TCFD Recommendations | Global | 14 |
| ISSB S1/S2 | Global | 16 |
| SBTi Categories | Global | 14 |
| CFR Title Index | United States | 19 |
| USC Title Index | United States | 23 |
| SWIFT MT Messages | Global | 13 |
| ISO 20022 Messages | Global | 17 |
| Payment Card Schemes | Global | 15 |
| GS1 Standards | Global | 14 |
| EDI Standards | Global | 14 |
| SCOR Model | Global | 17 |
| SHRM Competency | United States | 16 |
| Job Family Model | Global | 19 |
| RICS Valuation | Global | 14 |
| BREEAM | Global | 17 |
| LEED v4.1 | Global | 14 |
| FAO AQUASTAT | Global | 14 |
| FAOSTAT Domains | Global | 17 |
| IEA Energy Balance | Global | 19 |
| IRENA RE Technologies | Global | 17 |
| HL7 FHIR Resources | Global | 15 |
| DICOM Modalities | Global | 16 |
| ITU-R Radio Bands | Global | 16 |
| SI Units | Global | 19 |
| Board Committees | Global | 14 |
| Corporate Actions (ISO 15022) | Global | 19 |
| PMBOK 7th Ed | Global | 21 |
| PRINCE2 | Global | 15 |
| ITIL 4 | Global | 26 |
| ISA Standards (Auditing) | Global | 12 |
| WCO SAFE Framework | Global | 14 |
| SKOS | Global | 17 |
| XBRL Taxonomy | Global | 14 |
| Token Standards (Blockchain) | Global | 15 |
| DeFi Protocol Types | Global | 15 |
| IAB Content Taxonomy | Global | 21 |
| TOGAF ADM | Global | 14 |
| ArchiMate | Global | 14 |
| IRS Form Types | United States | 15 |
| VAT Rate Types | Global | 14 |
| GDPR Data Subject Rights | European Union | 13 |
| Contract Types | Global | 16 |
| IMO Ship Type Classification | Global | 17 |
| ISO Container Types (ISO 6346) | Global | 14 |
| NANDA-I Nursing Diagnoses | Global | 14 |
| NIC Nursing Interventions | Global | 14 |
| MIME Types (IANA) | Global | 16 |
| HTTP Status Codes | Global | 17 |
| SPDX Licenses | Global | 17 |
| Periodic Table (Element Groups) | Global | 18 |
| Geological Timescale (ICS) | Global | 20 |
| Beaufort Wind Scale | Global | 14 |
| Mohs Hardness Scale | Global | 11 |
| Pantone Color Families | Global | 12 |
| RAL Colors | Global | 13 |
| ISRC (Recording Codes) | Global | 13 |
| ISBN Groups | Global | 13 |
| USDA Soil Taxonomy | United States | 13 |
| Koppen Climate Classification | Global | 17 |
| ICAO Flight Rules/Airspace | Global | 15 |
| Olympic Sports (IOC) | Global | 16 |
| FIFA Confederations | Global | 14 |
| HACCP Principles | Global | 13 |
| EU 14 Major Allergens | European Union | 15 |
| WCAG 2.2 | Global | 17 |
| Six Sigma DMAIC/DMADV | Global | 16 |
| Lean Manufacturing Tools | Global | 15 |
| AI/ML Model Types | Global | 17 |
| CNCF Cloud Native Landscape | Global | 15 |
| SDG Global Indicators | Global | 20 |
| Unicode Emoji Categories | Global | 13 |
| Blood Types (ABO/Rh) | Global | 14 |
| Richter/Earthquake Magnitude | Global | 13 |
| Saffir-Simpson Hurricane Scale | Global | 12 |
| Enhanced Fujita Tornado Scale | United States | 10 |
| UV Index | Global | 11 |
| APGAR Score | Global | 12 |
| Bristol Stool Scale | Global | 11 |
| Numeric Pain Rating Scale | Global | 12 |
| WHO BMI Categories | Global | 11 |
| ASA Physical Status | Global | 11 |

Three surfaces: **Web App** (Next.js), **REST API** (FastAPI), **MCP Server** (stdio).

## Architecture

```
WorldOfTaxonomy/
├── world_of_taxonomy/           # Python backend
│   ├── api/                     # FastAPI REST API
│   │   ├── app.py               # App factory with lifespan (pool management)
│   │   ├── deps.py              # DI: get_conn, get_current_user, validate_api_key
│   │   ├── schemas.py           # Pydantic models (system, node, auth, etc.)
│   │   ├── middleware.py        # Rate limiting (slowapi)
│   │   └── routers/
│   │       ├── systems.py       # GET /api/v1/systems, /api/v1/systems/{id}
│   │       ├── nodes.py         # GET .../nodes/{code}, /children, /ancestors
│   │       ├── search.py        # GET /api/v1/search?q=
│   │       ├── equivalences.py  # GET .../equivalences, /stats
│   │       └── auth.py          # POST register, login; GET /me; CRUD /keys
│   ├── mcp/                     # MCP server (stdio transport)
│   │   └── server.py
│   ├── ingest/                  # One ingester per classification system
│   │   ├── naics.py             # NAICS 2022 (Census Bureau CSV)
│   │   ├── isic.py              # ISIC Rev 4 (UN CSV)
│   │   ├── nace.py              # NACE Rev 2 (Eurostat XLSX)
│   │   ├── sic.py               # SIC 1987 (OSHA HTML + GitHub CSV fallback)
│   │   ├── anzsic.py            # ANZSIC 2006 (ABS XLS via xlrd)
│   │   ├── nic.py               # NIC 2008 (Indian govt PDF/CSV)
│   │   ├── jsic.py              # JSIC 2013 (skeleton: 20 divisions)
│   │   ├── nace_derived.py      # WZ 2008, ÖNACE 2008, NOGA 2008 (copy NACE nodes)
│   │   └── crosswalk.py         # ISIC↔NAICS concordance
│   ├── query.py                 # Core query functions (get_system, search, etc.)
│   ├── db.py                    # asyncpg pool (Neon PostgreSQL, statement_cache_size=0)
│   ├── schema.sql               # Core tables: classification_system, classification_node, equivalence
│   ├── schema_auth.sql          # Auth tables: app_user, api_key, usage_log
│   └── __main__.py              # CLI: serve, mcp, ingest, init-auth
├── frontend/                    # Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Home: Industry Map + Galaxy View
│       │   ├── explore/page.tsx # Full-text search with ?q= param support
│       │   ├── system/[id]/page.tsx # System detail with sectors + crosswalks
│       │   ├── dashboard/page.tsx   # Stats overview + crosswalk matrix
│       │   ├── layout.tsx       # Root layout (Geist fonts, Providers)
│       │   └── globals.css      # shadcn/ui theme tokens (oklch), dark + light
│       ├── components/
│       │   ├── IndustryMap.tsx   # 22 industry sectors with icons → /explore?q=
│       │   ├── ThemeToggle.tsx   # Dark/light mode toggle (next-themes)
│       │   ├── Providers.tsx     # ThemeProvider + React Query
│       │   ├── visualizations/GalaxyView.tsx  # D3.js force simulation, animated
│       │   ├── layout/Header.tsx # Nav with systems dropdown
│       │   ├── layout/Footer.tsx
│       │   └── ui/              # shadcn/ui components
│       └── lib/
│           ├── api.ts           # Typed API client (all endpoints)
│           ├── types.ts         # TypeScript interfaces matching Pydantic models
│           └── colors.ts        # System tint colors + sector colors
├── tests/                       # pytest suite (18 files)
│   ├── conftest.py              # test_wot schema isolation, seed data, session pool
│   ├── test_api_*.py            # API contract tests (systems, nodes, search, equivalences)
│   ├── test_auth.py             # hashing, JWT, registration, API keys, usage log
│   ├── test_node_detail_contract.py  # node detail page API contract
│   ├── test_mcp_*.py            # MCP protocol + tool handlers
│   ├── test_ingest_*.py         # per-system ingester tests
│   └── test_cli.py              # CLI argument parsing
├── .env                         # DATABASE_URL, JWT_SECRET (not committed)
└── requirements.txt             # asyncpg, fastapi, uvicorn, bcrypt, PyJWT, slowapi, etc.
```

## Tech stack

**Backend**: Python 3.9 · FastAPI · asyncpg · PostgreSQL on Neon (pgbouncer → `statement_cache_size=0`) · bcrypt · PyJWT · slowapi · MCP SDK

**Frontend**: Next.js 15 (App Router) · TypeScript · Tailwind CSS v4 · shadcn/ui · D3.js · React Query · next-themes · lucide-react

**Database**: Neon PostgreSQL. Three core tables (`classification_system`, `classification_node`, `equivalence`) plus three auth tables (`app_user`, `api_key`, `usage_log`).

## How to run

```bash
# Backend
source .env
python3 -m uvicorn world_of_taxonomy.api.app:create_app --factory --port 8000

# Frontend (requires Node.js - use nvm if npx not found)
cd frontend && npx next dev --port 3000
```

Frontend proxies `/api/*` to `:8000` via `next.config.ts` rewrites.

## How to test

```bash
# All tests (uses test_wot schema, never touches production)
python3 -m pytest tests/ -v

# Specific area
python3 -m pytest tests/test_auth.py -v
python3 -m pytest tests/test_ingest_naics.py -v
```

Test isolation: `conftest.py` creates a `test_wot` PostgreSQL schema, seeds NAICS/ISIC/SIC test data, and tears down after each test. Production data in `public` schema is never touched.

## Development practices

- **TDD - Red → Green → Refactor, strictly enforced**:
  1. **Red**: Write the test first. Run it. Confirm it fails for the right reason before writing any implementation code.
  2. **Green**: Write the minimum code to make the test pass. Nothing more.
  3. **Refactor**: Clean up implementation and tests while keeping all tests green.
  - Never write implementation before a failing test exists.
  - Never skip the "run it red" step - a test that was never red proves nothing.
  - Never refactor while tests are red.
- **No em-dashes**: Never use the em-dash character (U+2014) anywhere in the project - code, comments, docstrings, markdown, or configuration. Use a hyphen `-` instead. The CI pipeline enforces this with a grep check.
- **No speculative code**: Don't add features, abstractions, or error handling beyond what's asked.
- **Type safety**: All frontend code is TypeScript. All backend models are Pydantic. Keep types.ts in sync with schemas.py.
- **Theme support**: Both dark and light modes must work. Galaxy View text uses SVG shadow filters for contrast in both themes.
- **Test schema isolation**: Tests MUST use the `test_wot` schema. Never run test queries against `public`.

## Auth system

- Registration: POST `/api/v1/auth/register` → bcrypt password hash → JWT token
- Login: POST `/api/v1/auth/login` → JWT (15 min expiry)
- API keys: `wot_` + 32 hex chars, bcrypt-hashed, prefix-indexed
- Rate limits: anonymous 30 req/min, authenticated 1000 req/min
- JWT secret: `JWT_SECRET` env var (must be ≥32 chars in production)

## Key patterns

- **Lifespan handler** in `app.py` manages the asyncpg pool lifecycle
- **NACE-derived systems** (WZ, ÖNACE, NOGA) copy all NACE nodes and create 1:1 equivalence edges
- **Next.js API proxy**: client-side `api.ts` uses relative paths (`/api/v1/...`), `next.config.ts` rewrites them to the FastAPI backend
- **Galaxy View**: D3 force simulation in a React `useEffect`, with `useTheme()` for theme-aware rendering. Cleanup properly (stop simulation, cancel animation frame)
- **IndustryMap**: Links to `/explore?q=<term>`, Explore page reads `useSearchParams()` wrapped in `<Suspense>`

## What's NOT done yet

- ~~Node detail page~~ ✓ done - `/system/[id]/node/[code]/page.tsx` with breadcrumb, typographic depth, children panel, cross-system equivalences, inline API endpoint
- Auth frontend pages (login, register, API key dashboard) - backend is complete
- Production deployment (Vercel for frontend, Fly.io/Railway for backend)
- CI/CD pipeline
- Domain-specific taxonomy extensions (ICD codes, crop taxonomies, etc.)
