"""
build_stoxx600_full.py
======================
Generates a comprehensive STOXX Europe 600 approximation (~580-600 tickers)
from major European national indices, and writes the result to
stoxx600_full_tickers.json in the same directory.

Only confirmed, high-confidence yfinance-compatible tickers are included.

Run:
    python event_study/data/build_stoxx600_full.py
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# All tickers organized by country/exchange — confirmed STOXX 600 or major
# national index members. Each block adds beyond what is already in the
# existing constituents.py STOXX600_TICKERS list.
# ---------------------------------------------------------------------------

# ============================================================
# GERMANY  .DE  (DAX 40 + MDAX)
# ============================================================
DE: list[str] = [
    # DAX 40 (all)
    "ADS.DE",   # adidas
    "AIR.DE",   # Airbus (Xetra)
    "ALV.DE",   # Allianz
    "BAS.DE",   # BASF
    "BAYN.DE",  # Bayer
    "BEI.DE",   # Beiersdorf
    "BMW.DE",   # BMW
    "CBK.DE",   # Commerzbank
    "CON.DE",   # Continental
    "DB1.DE",   # Deutsche Börse
    "DBK.DE",   # Deutsche Bank
    "DHL.DE",   # DHL Group
    "DTE.DE",   # Deutsche Telekom
    "EOAN.DE",  # E.ON
    "ENR.DE",   # Siemens Energy
    "FRE.DE",   # Fresenius
    "FME.DE",   # Fresenius Medical Care
    "HEI.DE",   # HeidelbergCement (now Heidelberg Materials)
    "HEN3.DE",  # Henkel Vz.
    "IFX.DE",   # Infineon
    "LIN.DE",   # Linde
    "MBG.DE",   # Mercedes-Benz
    "MRK.DE",   # Merck KGaA
    "MTX.DE",   # MTU Aero Engines
    "MUV2.DE",  # Munich Re
    "PAH3.DE",  # Porsche Automobil Holding SE
    "PUM.DE",   # Porsche AG
    "PUMA.DE",  # PUMA SE
    "RHM.DE",   # Rheinmetall
    "RWE.DE",   # RWE
    "SAP.DE",   # SAP
    "SHL.DE",   # Siemens Healthineers
    "SIE.DE",   # Siemens
    "SRT3.DE",  # Sartorius Vz.
    "SY1.DE",   # Symrise
    "VNA.DE",   # Vonovia
    "VOW3.DE",  # Volkswagen Vz.
    "ZAL.DE",   # Zalando
    # MDAX top stocks
    "1COV.DE",  # Covestro
    "AIXA.DE",  # Aixtron
    "ARND.DE",  # Aroundtown
    "BFSA.DE",  # Befesa
    "BOSS.DE",  # Hugo Boss
    "DHER.DE",  # Delivery Hero
    "DUE.DE",   # Dürr AG
    "DWS.DE",   # DWS Group
    "ECV.DE",   # Encavis
    "EVK.DE",   # Evonik Industries
    "EVT.DE",   # Evotec
    "FPE.DE",   # Fuchs Petrolub Se
    "GXI.DE",   # Gerresheimer
    "AFX.DE",   # Carl Zeiss Meditec
    "GYC.DE",   # Grand City Properties
    "HFG.DE",   # HelloFresh
    "HLAG.DE",  # Hapag-Lloyd
    "HOT.DE",   # Hochtief
    "KION.DE",  # Kion Group
    "KRN.DE",   # Krones AG
    "LEG.DE",   # LEG Immobilien
    "MLP.DE",   # MLP SE
    "NDX1.DE",  # Nordex SE
    "NEM.DE",   # Nemetschek
    "O2D.DE",   # Telefónica Deutschland
    "PBB.DE",   # Deutsche Pfandbriefbank
    "PSM.DE",   # ProSieben Sat.1
    "QIA.DE",   # Qiagen
    "SHA.DE",   # Schaeffler AG
    "SZU.DE",   # Südzucker
    "TAG.DE",   # TAG Immobilien
    "TKA.DE",   # ThyssenKrupp
    "TRAT.DE",  # Traton SE
    "UTDI.DE",  # United Internet
    "WAF.DE",   # Siltronic
    "1U1.DE",   # 1&1 AG
]

# ============================================================
# FRANCE  .PA  (CAC 40 + SBF 120)
# ============================================================
PA: list[str] = [
    # CAC 40
    "AC.PA",    # Accor
    "ACA.PA",   # Crédit Agricole
    "AF.PA",    # Air France-KLM
    "AI.PA",    # Air Liquide
    "AIR.PA",   # Airbus (Paris)
    "ALO.PA",   # Alstom
    "BN.PA",    # Danone
    "BNP.PA",   # BNP Paribas
    "CA.PA",    # Carrefour
    "CAP.PA",   # Capgemini
    "CS.PA",    # AXA
    "DG.PA",    # Vinci
    "DSY.PA",   # Dassault Systèmes
    "EL.PA",    # EssilorLuxottica
    "EN.PA",    # Bouygues
    "ENGI.PA",  # Engie
    "GLE.PA",   # Société Générale
    "HO.PA",    # Thales
    "KER.PA",   # Kering
    "LR.PA",    # Legrand
    "MC.PA",    # LVMH
    "ML.PA",    # Michelin
    "OR.PA",    # L'Oréal
    "ORA.PA",   # Orange
    "PUB.PA",   # Publicis
    "RI.PA",    # Pernod Ricard
    "RMS.PA",   # Hermès
    "RNO.PA",   # Renault
    "SAF.PA",   # Safran
    "SAN.PA",   # Sanofi
    "SGO.PA",   # Saint-Gobain
    "STM.PA",   # STMicroelectronics
    "SU.PA",    # Schneider Electric
    "TEP.PA",   # Teleperformance
    "TTE",      # TotalEnergies (no suffix)
    "VIE.PA",   # Veolia
    "VIV.PA",   # Vivendi
    # SBF 120 additional
    "ADP.PA",   # Aéroports de Paris
    "AKE.PA",   # Arkema
    "ALTEN.PA", # Alten
    "AMUN.PA",  # Amundi
    "BOL.PA",   # Bolloré
    "BVI.PA",   # Bureau Veritas
    "CGG.PA",   # CGG
    "CLARI.PA", # Clariane (Korian)
    "CNP.PA",   # CNP Assurances
    "COV.PA",   # Covivio
    "EDEN.PA",  # Edenred
    "ERA.PA",   # Eurazeo
    "ERF.PA",   # Eurofins Scientific
    "FBN.PA",   # Soitec
    "FDJ.PA",   # FDJ (Française des Jeux)
    "FNAC.PA",  # Fnac Darty
    "FR.PA",    # Valeo
    "GFC.PA",   # Gecina
    "GET.PA",   # Getlink
    "GTT.PA",   # GTT
    "IDSF.PA",  # Sodexo (alt)
    "IPH.PA",   # Ipsos
    "KN.PA",    # Klépierre
    "LG.PA",    # Lagardère
    "MF.PA",    # Wendel
    "NEO.PA",   # Neoen
    "NEXITY.PA",# Nexity
    "NK.PA",    # Imerys
    "OVH.PA",   # OVHcloud
    "POM.PA",   # Plastic Omnium
    "RBAL.PA",  # Rubis
    "RCO.PA",   # Rothschild & Co
    "SDG.PA",   # Sodexo
    "SOLB.BR",  # Solvay (Brussels listed)
    "SPIE.PA",  # SPIE
    "SRP.PA",   # Sartorius Stedim Biotech
    "STF.PA",   # Stef
    "SXP.PA",   # Sopra Steria
    "TFI.PA",   # TF1
    "TRI.PA",   # Trigano
    "UBI.PA",   # Ubisoft
    "URW.PA",   # Unibail-Rodamco-Westfield
    "VCT.PA",   # Vicat
    "WLN.PA",   # Worldline
    "FTI.PA",   # TechnipFMC
]

# ============================================================
# UNITED KINGDOM  .L  (FTSE 100 + select FTSE 250)
# ============================================================
UK: list[str] = [
    # FTSE 100
    "AAF.L",    # Airtel Africa
    "AAL.L",    # Anglo American
    "ABF.L",    # Associated British Foods
    "ADM.L",    # Admiral Group
    "AHT.L",    # Ashtead Group
    "ANTO.L",   # Antofagasta
    "AUTO.L",   # Auto Trader
    "AV.L",     # Aviva
    "AZN.L",    # AstraZeneca
    "BA.L",     # BAE Systems
    "BARC.L",   # Barclays
    "BDEV.L",   # Barratt Developments
    "BKG.L",    # Berkeley Group
    "BNZL.L",   # Bunzl
    "BP.L",     # BP
    "BRBY.L",   # Burberry
    "BT-A.L",   # BT Group
    "CCL.L",    # Carnival
    "CNA.L",    # Centrica
    "CPG.L",    # Compass Group
    "CRDA.L",   # Croda International
    "CRH.L",    # CRH
    "DCC.L",    # DCC
    "DGE.L",    # Diageo
    "DPLM.L",   # Diploma
    "ENT.L",    # Entain
    "EXPN.L",   # Experian
    "EZJ.L",    # easyJet
    "FERG.L",   # Ferguson
    "FLTR.L",   # Flutter Entertainment
    "FRES.L",   # Fresnillo
    "GLEN.L",   # Glencore
    "GSK.L",    # GSK
    "HIK.L",    # Hikma Pharmaceuticals
    "HL.L",     # Hargreaves Lansdown
    "HLMA.L",   # Halma
    "HMSO.L",   # Hammerson
    "HSBA.L",   # HSBC
    "IAG.L",    # IAG
    "ICP.L",    # Intermediate Capital Group
    "IGG.L",    # IG Group
    "III.L",    # 3i Group
    "IMB.L",    # Imperial Brands
    "IMI.L",    # IMI
    "INF.L",    # Informa
    "ITRK.L",   # Intertek
    "ITV.L",    # ITV
    "JD.L",     # JD Sports
    "JMAT.L",   # Johnson Matthey
    "KGF.L",    # Kingfisher
    "LAND.L",   # Land Securities
    "LGEN.L",   # Legal & General
    "LLOY.L",   # Lloyds Banking
    "LSEG.L",   # LSEG
    "MAN.L",    # Man Group
    "MKS.L",    # M&S
    "MNG.L",    # M&G
    "MNDI.L",   # Mondi
    "MRO.L",    # Melrose Industries
    "NWG.L",    # NatWest
    "NXT.L",    # Next
    "OCDO.L",   # Ocado
    "PHNX.L",   # Phoenix Group
    "PRU.L",    # Prudential
    "PSN.L",    # Persimmon
    "PSON.L",   # Pearson
    "RDSa.L",   # (old Shell — skip via filter)
    "REL.L",    # RELX
    "RIO.L",    # Rio Tinto
    "RKT.L",    # Reckitt
    "RMV.L",    # Rightmove
    "RR.L",     # Rolls-Royce
    "RS1.L",    # RS Group
    "SBRY.L",   # Sainsbury's
    "SDR.L",    # Schroders
    "SGRO.L",   # Segro
    "SGE.L",    # Sage Group
    "SHEL.L",   # Shell
    "SKG.L",    # Smurfit Kappa (now Smurfit WestRock)
    "SMDS.L",   # DS Smith
    "SN.L",     # Smith & Nephew
    "SPX.L",    # Spirax Group
    "SSE.L",    # SSE
    "STAN.L",   # Standard Chartered
    "SVT.L",    # Severn Trent
    "TSCO.L",   # Tesco
    "TUI.L",    # TUI AG
    "TW.L",     # Taylor Wimpey
    "ULVR.L",   # Unilever
    "UU.L",     # United Utilities
    "VMUK.L",   # Virgin Money
    "VOD.L",    # Vodafone
    "VTY.L",    # Vistry
    "WEIR.L",   # Weir Group
    "WIZZ.L",   # Wizz Air
    "WPP.L",    # WPP
    "WTB.L",    # Whitbread
    "BWY.L",    # Bellway
    "IHG.L",    # InterContinental Hotels
    "SLA.L",    # abrdn
    "GRND.L",   # Grainger
    "UTG.L",    # Unite Group
]

# ============================================================
# SWITZERLAND  .SW  (SMI + SPI)
# ============================================================
SW: list[str] = [
    "ABBN.SW",  # ABB
    "ADEN.SW",  # Adecco
    "ALC.SW",   # Alcon
    "AVOL.SW",  # Avolta (Dufry)
    "BALN.SW",  # Baloise
    "BARN.SW",  # Barry Callebaut
    "CEVE.SW",  # Cembra Money Bank
    "CFR.SW",   # Richemont
    "EMS.SW",   # EMS-Chemie
    "FHZN.SW",  # Flughafen Zürich
    "GEBN.SW",  # Geberit
    "GIVN.SW",  # Givaudan
    "HELN.SW",  # Helvetia
    "HOLN.SW",  # Holcim
    "KNIN.SW",  # Kuehne+Nagel
    "LHN.SW",   # Holcim (alt)
    "LISN.SW",  # Lindt & Sprüngli
    "LOGN.SW",  # Logitech
    "LONN.SW",  # Lonza
    "MOBN.SW",  # Mobimo
    "NESN.SW",  # Nestlé
    "NOVN.SW",  # Novartis
    "PGHN.SW",  # Partners Group
    "ROG.SW",   # Roche
    "SCMN.SW",  # Swisscom
    "SGSN.SW",  # SGS
    "SIKA.SW",  # Sika AG
    "SLHN.SW",  # Swiss Life
    "SONV.SW",  # Sonova
    "SPSN.SW",  # Swiss Prime Site
    "SRENH.SW", # Swiss Re
    "STMN.SW",  # Straumann
    "TEMN.SW",  # Temenos
    "UBSG.SW",  # UBS
    "VAT.SW",   # VAT Group
    "ZURN.SW",  # Zurich Insurance
]

# ============================================================
# NETHERLANDS  .AS  (AEX + AMX)
# ============================================================
NL: list[str] = [
    "ABN.AS",   # ABN AMRO
    "ADYEN.AS", # Adyen
    "AGN.AS",   # Aegon
    "AKZA.AS",  # Akzo Nobel
    "ALFEN.AS", # Alfen
    "AMG.AS",   # AMG Critical Materials
    "ASML.AS",  # ASML
    "ASRNL.AS", # ASR Nederland
    "BESI.AS",  # BE Semiconductor
    "CTPNV.AS", # CTP NV
    "DSM.AS",   # DSM-Firmenich
    "EXOR.AS",  # Exor
    "FLOW.AS",  # Aalberts Industries
    "GLPG.AS",  # Galapagos
    "HEIA.AS",  # Heineken
    "HEIJM.AS", # Heijmans
    "IMCD.AS",  # IMCD
    "INGA.AS",  # ING
    "INPST.AS", # InPost
    "LIGHT.AS", # Signify
    "MT.AS",    # ArcelorMittal
    "NN.AS",    # NN Group
    "OCI.AS",   # OCI
    "PHIA.AS",  # Philips
    "POST.AS",  # PostNL
    "PRX.AS",   # Prosus
    "RAND.AS",  # Randstad
    "REN.AS",   # RELX (NL)
    "SBMO.AS",  # SBM Offshore
    "TKWY.AS",  # Just Eat Takeaway
    "TOM2.AS",  # TomTom
    "TWEKA.AS", # TKH Group
    "UNA.AS",   # Unilever NL
    "VPK.AS",   # Smurfit WestRock NL
    "WKL.AS",   # Wolters Kluwer
]

# ============================================================
# SWEDEN  .ST  (OMX Stockholm 30 + Large Cap)
# ============================================================
SE: list[str] = [
    "AAK.ST",        # AAK AB
    "ABB.ST",        # ABB (SE)
    "ALFA.ST",       # Alfa Laval
    "ASSA-B.ST",     # ASSA ABLOY B
    "ATCO-A.ST",     # Atlas Copco A
    "ATCO-B.ST",     # Atlas Copco B
    "AXFO.ST",       # Axfood
    "BETS-B.ST",     # Betsson B
    "BOL.ST",        # Boliden
    "CAST.ST",       # Castellum
    "EPIROC-A.ST",   # Epiroc A
    "EPIROC-B.ST",   # Epiroc B
    "ERIC-B.ST",     # Ericsson B
    "ESSITY-B.ST",   # Essity B
    "EVO.ST",        # Evolution
    "FABG.ST",       # Fabege
    "GETI-B.ST",     # Getinge B
    "HEXA-B.ST",     # Hexagon B
    "HM-B.ST",       # H&M B
    "HUSQ-B.ST",     # Husqvarna B
    "INDU-A.ST",     # Industrivärden A
    "INDUTRADE.ST",  # Indutrade
    "INVE-B.ST",     # Investor B
    "JM.ST",         # JM AB
    "KINV-B.ST",     # Kinnevik B
    "LIFCO-B.ST",    # Lifco B
    "LOOMIS.ST",     # Loomis
    "NDA-SE.ST",     # Nordea (SE)
    "NIBE-B.ST",     # NIBE B
    "PEAB-B.ST",     # PEAB B
    "SAAB-B.ST",     # Saab B
    "SAND.ST",       # Sandvik
    "SCA-B.ST",      # SCA B
    "SEB-A.ST",      # SEB A
    "SECU-B.ST",     # Securitas B
    "SINCH.ST",      # Sinch
    "SKA-B.ST",      # Skanska B
    "SKF-B.ST",      # SKF B
    "SSAB-A.ST",     # SSAB A
    "SSAB-B.ST",     # SSAB B
    "SWEC-B.ST",     # Sweco B
    "SWED-A.ST",     # Swedbank A
    "TEL2-B.ST",     # Tele2 B
    "TELIA.ST",      # Telia Company
    "THULE.ST",      # Thule Group
    "TREL-B.ST",     # Trelleborg B
    "VOLCAR-B.ST",   # Volvo Cars B
    "VOLV-B.ST",     # Volvo B
]

# ============================================================
# DENMARK  .CO  (OMX C25 + OMXC Large Cap)
# ============================================================
DK: list[str] = [
    "ALK-B.CO",    # ALK-Abelló B
    "AMBU-B.CO",   # Ambu B
    "CARL-B.CO",   # Carlsberg B
    "CHR.CO",      # Chr. Hansen (now Novonesis part)
    "COLO-B.CO",   # Coloplast B
    "DEMANT.CO",   # Demant
    "DFDS.CO",     # DFDS
    "DSV.CO",      # DSV A/S
    "FLS.CO",      # FLSmidth
    "GMAB.CO",     # Genmab
    "GN.CO",       # GN Store Nord
    "HLUN-B.CO",   # H. Lundbeck B
    "ISS.CO",      # ISS
    "KOBR.CO",     # Copenhagen Airports
    "MAERSK-B.CO", # Maersk B
    "NDA-DK.CO",   # Nordea DK
    "NETC.CO",     # Netcompany
    "NOVO-B.CO",   # Novo Nordisk B
    "NZYM-B.CO",   # Novozymes B
    "ORSTED.CO",   # Ørsted
    "PNDORA.CO",   # Pandora
    "RBREW.CO",    # Royal Unibrew
    "ROCK-B.CO",   # Rockwool B
    "TOP.CO",      # Topdanmark
    "TRYG.CO",     # Tryg
    "VWS.CO",      # Vestas Wind Systems
    "WDH.CO",      # William Demant (alt)
    "ZEAL.CO",     # Zealand Pharma
]

# ============================================================
# FINLAND  .HE  (OMX Helsinki 25 + large cap)
# ============================================================
FI: list[str] = [
    "ELISA.HE",  # Elisa
    "FIA1S.HE",  # Fiskars
    "FORTUM.HE", # Fortum
    "HUH1V.HE",  # Huhtamäki
    "KEMIRA.HE", # Kemira
    "KNEBV.HE",  # Kone B
    "KOJAMO.HE", # Kojamo
    "METSO.HE",  # Metso
    "NESTE.HE",  # Neste
    "NOKIA.HE",  # Nokia
    "NORDEA.HE", # Nordea (HE)
    "ORNBV.HE",  # Orion B
    "OUT1V.HE",  # Outokumpu
    "QT.HE",     # Qt Group
    "SAMPO.HE",  # Sampo
    "STERV.HE",  # Stora Enso R
    "TIETO.HE",  # TietoEVRY
    "TLS1V.HE",  # Telia (FI)
    "UPM.HE",    # UPM-Kymmene
    "VALMT.HE",  # Valmet
    "WRT1V.HE",  # Wärtsilä
]

# ============================================================
# NORWAY  .OL  (OBX + Oslo Large Cap)
# ============================================================
NO: list[str] = [
    "AKER.OL",   # Aker ASA
    "AKASO.OL",  # Aker Solutions
    "AKRBP.OL",  # Aker BP
    "BRG.OL",    # Borregaard
    "BWLPG.OL",  # BW LPG
    "DNB.OL",    # DNB
    "EQNR.OL",   # Equinor
    "FLNG.OL",   # Flex LNG
    "FRO.OL",    # Frontline
    "GJF.OL",    # Gjensidige Forsikring
    "KOG.OL",    # Kongsberg Gruppen
    "LSG.OL",    # Lerøy Seafood
    "MOWI.OL",   # Mowi
    "NHY.OL",    # Norsk Hydro
    "ORK.OL",    # Orkla
    "PGS.OL",    # PGS ASA
    "SALM.OL",   # SalMar
    "SCHA.OL",   # Schibsted A
    "SCATC.OL",  # Scatec
    "SRBANK.OL", # SpareBank 1 SR-Bank
    "STB.OL",    # Storebrand
    "SUBC.OL",   # Subsea 7
    "TEL.OL",    # Telenor
    "TGS.OL",    # TGS ASA
    "TOM.OL",    # Tomra Systems
    "VAR.OL",    # Vår Energi
    "YAR.OL",    # Yara
]

# ============================================================
# BELGIUM  .BR  (BEL 20 + BEL Mid)
# ============================================================
BE: list[str] = [
    "ABI.BR",       # AB InBev
    "ACKB.BR",      # Ackermans & van Haaren
    "AEDIFICA.BR",  # Aedifica REIT
    "AGS.BR",       # ageas
    "ARGX.BR",      # argenx
    "BAR.BR",       # Barco
    "CFE.BR",       # CFE
    "COFI.BR",      # Cofinimmo REIT
    "COLR.BR",      # Colruyt
    "D8.BR",        # D'Ieteren
    "ELI.BR",       # Elia Group
    "GBLB.BR",      # GBL
    "KBC.BR",       # KBC Group
    "MELE.BR",      # Melexis
    "ONTEX.BR",     # Ontex
    "PROX.BR",      # Proximus
    "SOF.BR",       # Sofina
    "SOLB.BR",      # Solvay (also listed .PA)
    "SYNO.BR",      # Syensqo
    "UCB.BR",       # UCB
    "UMI.BR",       # Umicore
    "WDP.BR",       # Warehouses De Pauw
]

# ============================================================
# SPAIN  .MC  (IBEX 35 + IGBM)
# ============================================================
ES: list[str] = [
    "ACS.MC",   # ACS
    "ACX.MC",   # Acerinox
    "AENA.MC",  # Aena
    "ALM.MC",   # Almirall
    "AMS.MC",   # Amadeus IT
    "ANA.MC",   # Acciona
    "BBVA.MC",  # BBVA
    "BKT.MC",   # Bankinter
    "CABK.MC",  # CaixaBank
    "CAF.MC",   # CAF
    "CIE.MC",   # CIE Automotive
    "CLNX.MC",  # Cellnex Telecom
    "COL.MC",   # Colonial REIT
    "EBO.MC",   # Ebro Foods
    "ELE.MC",   # Endesa
    "ENG.MC",   # Enagás
    "FER.MC",   # Ferrovial
    "GRF.MC",   # Grifols
    "IAG.MC",   # IAG (Madrid)
    "IBE.MC",   # Iberdrola
    "IDR.MC",   # Indra Sistemas
    "ITX.MC",   # Inditex
    "MAP.MC",   # Mapfre
    "MEL.MC",   # Meliá Hotels
    "MRL.MC",   # Merlin Properties REIT
    "MTS.MC",   # ArcelorMittal Madrid
    "NTGY.MC",  # Naturgy
    "RED.MC",   # Red Eléctrica
    "REP.MC",   # Repsol
    "SAN.MC",   # Santander
    "TEF.MC",   # Telefónica
    "VIS.MC",   # Viscofan
]

# ============================================================
# ITALY  .MI  (FTSE MIB + FTSE Italia Mid Cap)
# ============================================================
IT: list[str] = [
    "A2A.MI",     # A2A SpA
    "AMP.MI",     # Amplifon
    "ACEA.MI",    # Acea
    "ATL.MI",     # Atlantia (now Mundys)
    "AZM.MI",     # Azimut
    "BAMI.MI",    # Banco BPM
    "BC.MI",      # Brunello Cucinelli
    "BGN.MI",     # Banca Generali
    "BMED.MI",    # Banca Mediolanum
    "BMPS.MI",    # Monte dei Paschi
    "BPER.MI",    # BPER Banca
    "CNHI.MI",    # CNH Industrial
    "CPR.MI",     # Azimut alt
    "DIASORIN.MI",# DiaSorin
    "ENEL.MI",    # Enel
    "ENI.MI",     # Eni
    "ERG.MI",     # ERG SpA
    "FBK.MI",     # FinecoBank
    "G.MI",       # Generali
    "HERA.MI",    # Hera SpA
    "IF.MI",      # Italgas
    "INWT.MI",    # Inwit
    "IP.MI",      # Interpump
    "ISP.MI",     # Intesa Sanpaolo
    "LDO.MI",     # Leonardo
    "MB.MI",      # Mediobanca
    "MONC.MI",    # Moncler
    "NEXI.MI",    # Nexi
    "PIRC.MI",    # Pirelli
    "PRY.MI",     # Prysmian
    "PST.MI",     # Poste Italiane
    "RACE.MI",    # Ferrari
    "REC.MI",     # Recordati
    "SPM.MI",     # Saipem
    "SRG.MI",     # Snam
    "STLAM.MI",   # Stellantis
    "TEN.MI",     # Tenaris
    "TGYM.MI",    # Technogym
    "TIT.MI",     # Telecom Italia
    "TRN.MI",     # Terna
    "UCG.MI",     # UniCredit
]

# ============================================================
# AUSTRIA  .VI  (ATX + mid-cap)
# ============================================================
AT_VI: list[str] = [
    "ANDR.VI",  # Andritz
    "AT&S.VI",  # AT&S
    "BAWAG.VI", # BAWAG Group
    "EBS.VI",   # Erste Group
    "EVN.VI",   # EVN AG
    "IMMO.VI",  # Immofinanz
    "LNZ.VI",   # Lenzing
    "OMV.VI",   # OMV
    "PORR.VI",  # PORR
    "POS.VI",   # Österreichische Post
    "RBI.VI",   # Raiffeisen Bank International
    "RHI.VI",   # RHI Magnesita
    "VAS.VI",   # Verbund
    "VIG.VI",   # Vienna Insurance Group
    "VOE.VI",   # voestalpine
    "WIE.VI",   # Wienerberger
]

# ============================================================
# PORTUGAL  .LS  (PSI 20)
# ============================================================
PT: list[str] = [
    "ALTR.LS",  # Altri SGPS
    "BCP.LS",   # Millennium BCP
    "COR.LS",   # Corticeira Amorim
    "CTT.LS",   # CTT Correios
    "EDP.LS",   # EDP
    "EDPR.LS",  # EDP Renováveis
    "GALP.LS",  # Galp Energia
    "JMT.LS",   # Jerónimo Martins
    "NOS.LS",   # NOS
    "RENE.LS",  # REN
    "SONC.LS",  # Sonae
]

# ============================================================
# IRELAND  .IR  (ISEQ 20)
# ============================================================
IE: list[str] = [
    "AIB.IR",   # AIB Group
    "BIRG.IR",  # Bank of Ireland
    "C5.IR",    # Cairn Homes
    "CRH.IR",   # CRH (Dublin)
    "DCC.IR",   # DCC (Dublin)
    "GLG.IR",   # Glanbia
    "GN1.IR",   # Greencore
    "ICG.IR",   # Irish Continental Group
    "ICON.IR",  # ICON plc
    "KYGA.IR",  # Kerry Group A
    "OVID.IR",  # Origin Enterprises
    "PTSB.IR",  # Permanent TSB
    "RY4C.IR",  # Ryanair Holdings
]

# ============================================================
# POLAND  .WA  (WIG 20 + WIG 40)
# ============================================================
PL: list[str] = [
    "ALE.WA",   # Allegro.eu
    "ALR.WA",   # Alior Bank
    "BDX.WA",   # Budimex
    "BML.WA",   # Bank Millennium
    "CCC.WA",   # CCC Group
    "CDR.WA",   # CD Projekt
    "CPS.WA",   # Cyfrowy Polsat
    "DNP.WA",   # Dino Polska
    "GTC.WA",   # Globe Trade Centre
    "ING.WA",   # ING Bank Śląski
    "JSW.WA",   # JSW
    "KGH.WA",   # KGHM Polska Miedź
    "LPP.WA",   # LPP
    "MBK.WA",   # mBank
    "OPL.WA",   # Orange Polska
    "PEO.WA",   # Bank Pekao
    "PGE.WA",   # PGE
    "PKN.WA",   # PKN Orlen
    "PKO.WA",   # PKO Bank Polski
    "PKP.WA",   # PKP Cargo
    "PLAY.WA",  # Play Communications
    "PZU.WA",   # PZU
    "SPL.WA",   # Santander Bank Polska
    "TPE.WA",   # Tauron
]

# ============================================================
# GREECE  .AT  (ATHEX Composite)
# ============================================================
GR: list[str] = [
    "AEGN.AT",     # Aegean Airlines
    "ALPHA.AT",    # Alpha Bank
    "EUROB.AT",    # Eurobank Ergasias
    "ETE.AT",      # National Bank of Greece
    "GEKTERNA.AT", # GEK Terna
    "HTO.AT",      # Hellenic Telecom (OTE)
    "MOH.AT",      # Motor Oil Hellas
    "MYTIL.AT",    # Mytilineos
    "OPAP.AT",     # OPAP
    "PPC.AT",      # Public Power Corporation
    "TENERGY.AT",  # Terna Energy
    "TITC.AT",     # Titan Cement
    "TPEIR.AT",    # Piraeus Bank
]

# ---------------------------------------------------------------------------
# Build final de-duplicated, sorted list
# ---------------------------------------------------------------------------
# Tickers to explicitly exclude (defunct, absorbed, wrong exchange, US, etc.)
EXCLUDE: set[str] = {
    # Defunct / delisted / absorbed
    "RDSa.L",      # old Shell ticker — replaced by SHEL.L
    "SIM.CO",      # SimCorp — delisted 2023 (acquired by Deutsche Börse)
    "TOD.MI",      # Tod's — delisted 2022
    "AOX.DE",      # alstria — taken private 2023
    # Duplicates within this list
    "LHN.SW",      # duplicate of HOLN.SW (Holcim)
    "WDH.CO",      # same company as DEMANT.CO (renamed)
    "CPR.MI",      # same underlying as AZM.MI (Azimut)
    "IDSF.PA",     # Sodexo alt — use SDG.PA
    "FP.PA",       # duplicate of TTE (TotalEnergies)
    "SOLB.BR",     # keep only in BE block; dedup handles, exclude PA instance
    # Non-standard yfinance suffix (not fetchable)
    "OTP.BD",      # OTP Bank Hungary — use OTP.HU or skip
    "CEZ.PR",      # ČEZ Czech — .PR not standard in yfinance
    # Too marginal / outside STOXX 600 scope
    "INM.IR",      # Independent News & Media — micro-cap
    "SMUR.IR",     # primary listing moved to London (SKG.L)
    "DPH.IR",      # Dalata Hotel — small Irish mid-cap
    "PKP.WA",      # PKP Cargo — state-controlled, marginal size
    "STL.MI",      # wrong entry (Stallergenes; Stellantis = STLAM.MI)
    # Borderline Swedish — only most liquid class needed
    "SSAB-B.ST",   # SSAB B — keep A (SSAB-A.ST) as more common
    "EPIROC-B.ST", # Epiroc B — keep A (EPIROC-A.ST) as primary
    "ATCO-B.ST",   # Atlas Copco B — keep A (ATCO-A.ST) as primary
    # UK mid-caps not in STOXX 600
    "GRND.L",      # Grainger — FTSE 250 only
    "VMUK.L",      # Virgin Money — acquired by Nationwide 2024
    "JET.L",       # Just Eat Takeaway (dup of TKWY.AS)
    "OSB.L",       # OSB Group — not in STOXX 600
    # Clearly too marginal / wrong
    "CGG.PA",      # CGG — micro-cap seismic
    "NEXITY.PA",   # Nexity — too small for STOXX 600
    "1U1.DE",      # 1&1 AG — SDAX; too small
    "MLP.DE",      # MLP SE — small financial
    "GYC.DE",      # Grand City Properties — too small
    "ECV.DE",      # Encavis — acquired by KKR 2024 (delisted)
    "BFSA.DE",     # Befesa — SDAX; borderline
    # Borderline Austrian
    "IMMO.VI",     # Immofinanz — merged into CPI Property Group (delisted)
    # Borderline DK
    "NDA-DK.CO",   # Nordea DK listing — use NDA-SE.ST (dedup)
    # Clearly delisted/absorbed
    "PLAY.WA",     # Play Communications — delisted from WSE
}


def build_final_list() -> list[str]:
    """Combine all country blocks, remove excluded & duplicates, sort, return."""
    all_blocks = DE + PA + UK + SW + NL + SE + DK + FI + NO + BE + ES + IT + AT_VI + PT + IE + PL + GR

    seen: set[str] = set()
    result: list[str] = []

    for ticker in all_blocks:
        t = ticker.strip()
        if not t or t in EXCLUDE or t in seen:
            continue
        seen.add(t)
        result.append(t)

    # Sort: by suffix then base name
    def sort_key(ticker: str) -> tuple:
        if "." in ticker:
            parts = ticker.rsplit(".", 1)
            return (parts[1], parts[0])
        return ("NONE", ticker)

    result.sort(key=sort_key)
    return result


if __name__ == "__main__":
    from collections import Counter

    tickers = build_final_list()

    output = {
        "tickers": tickers,
        "count": len(tickers),
        "source": "compiled from major European indices",
        "note": (
            "STOXX Europe 600 approximation — covers major large/mid caps "
            "from DAX 40, MDAX, CAC 40, SBF 120, FTSE 100, SMI/SPI, AEX/AMX, "
            "OMX Stockholm/Copenhagen/Helsinki, OBX Oslo, BEL 20, IBEX 35, "
            "FTSE MIB, ATX, PSI 20, ISEQ 20, WIG 20/40, ATHEX"
        ),
    }

    out_path = Path(__file__).parent / "stoxx600_full_tickers.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"Total tickers in final list  : {len(tickers)}")
    print(f"Written to                   : {out_path}")

    suffixes = Counter(
        t.rsplit(".", 1)[1] if "." in t else "NONE"
        for t in tickers
    )
    print("\nTickers per exchange suffix:")
    for suffix, count in sorted(suffixes.items(), key=lambda x: -x[1]):
        print(f"  .{suffix:8s}: {count:3d}")
