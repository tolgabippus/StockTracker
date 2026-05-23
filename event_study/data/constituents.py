"""
constituents.py — Constituent tickers for STOXX 50 and STOXX Europe 600.

Usage:
    from data.constituents import STOXX50_TICKERS, STOXX600_TICKERS

Stand: Mai 2025. Bei Index-Rebalancing muss diese Liste manuell aktualisiert werden.
yfinance-Ticker mit Länder-Suffix (z.B. .DE, .PA, .AS) für Xetra / Euronext.
"""

# ---------------------------------------------------------------------------
# Euro STOXX 50 — 50 Konstituenten
# ---------------------------------------------------------------------------
STOXX50_TICKERS: list[str] = [
    # Deutschland
    "ADS.DE",   # adidas
    "AIR.PA",   # Airbus (Paris gelistet)
    "ALV.DE",   # Allianz
    "BAS.DE",   # BASF
    "BAYN.DE",  # Bayer
    "BMW.DE",   # BMW
    "DB1.DE",   # Deutsche Börse
    "DHL.DE",   # DHL Group
    "DTE.DE",   # Deutsche Telekom
    "EOAN.DE",  # E.ON
    "MBG.DE",   # Mercedes-Benz
    "MRK.DE",   # Merck KGaA
    "MUV2.DE",  # Munich Re
    "RWE.DE",   # RWE
    "SAP.DE",   # SAP
    "SHL.DE",   # Siemens Healthineers
    "SIE.DE",   # Siemens
    "VOW3.DE",  # Volkswagen Vz.
    # Frankreich
    "AI.PA",    # Air Liquide
    "BN.PA",    # Danone
    "BNP.PA",   # BNP Paribas
    "CS.PA",    # AXA
    "DG.PA",    # Vinci
    "EL.PA",    # EssilorLuxottica
    "EN.PA",    # Bouygues (Engie alt: ENGI.PA)
    "ENGI.PA",  # Engie
    "GLE.PA",   # Société Générale
    "KER.PA",   # Kering
    "MC.PA",    # LVMH
    "OR.PA",    # L'Oréal
    "ORA.PA",   # Orange
    "RI.PA",    # Pernod Ricard
    "RMS.PA",   # Hermès
    "SAF.PA",   # Safran
    "SAN.PA",   # Sanofi
    "SU.PA",    # Schneider Electric
    "TTE",      # TotalEnergies
    # Niederlande
    "ADYEN.AS", # Adyen
    "ASML.AS",  # ASML
    "INGA.AS",  # ING
    "PHIA.AS",  # Philips
    "PRX.AS",   # Prosus
    # Spanien
    "BBVA.MC",  # BBVA
    "IBE.MC",   # Iberdrola
    "ITX.MC",   # Inditex
    "SAN.MC",   # Santander
    # Italien
    "ENEL.MI",  # Enel
    "ENI.MI",   # Eni
    "ISP.MI",   # Intesa Sanpaolo
    "UCG.MI",   # UniCredit
]

# ---------------------------------------------------------------------------
# STOXX Europe 600 — 600 Konstituenten (repräsentative Auswahl)
# ---------------------------------------------------------------------------
# Vollständige Liste: https://www.stoxx.com/index-details?isin=EU0009658202
# Hier: alle STOXX-50-Werte + wichtige weitere Large/Mid Caps aus dem STOXX 600
STOXX600_TICKERS: list[str] = STOXX50_TICKERS + [
    # Deutschland (weitere)
    "1COV.DE",  # Covestro
    "BOSS.DE",  # Hugo Boss
    "CON.DE",   # Continental
    "DHER.DE",  # Delivery Hero
    "ENR.DE",   # Siemens Energy
    "FRE.DE",   # Fresenius
    "FME.DE",   # Fresenius Medical Care
    "HEI.DE",   # HeidelbergCement
    "HEN3.DE",  # Henkel Vz.
    "IFX.DE",   # Infineon
    "LIN.DE",   # Linde (DE-Listing)
    "MTX.DE",   # MTU Aero Engines
    "PUMA.DE",  # PUMA
    "PUM.DE",   # Porsche AG
    "QIA.DE",   # Qiagen
    "SY1.DE",   # Symrise
    "VNA.DE",   # Vonovia
    "ZAL.DE",   # Zalando
    # Frankreich (weitere)
    "AC.PA",    # Accor
    "ACA.PA",   # Crédit Agricole
    "AF.PA",    # Air France-KLM
    "AKE.PA",   # Arkema
    "ALO.PA",   # Alstom
    "CAP.PA",   # Capgemini
    "CA.PA",    # Carrefour
    "CGG.PA",   # CGG
    "DSY.PA",   # Dassault Systèmes
    "ERA.PA",   # Eurazeo
    "FP.PA",    # TotalEnergies (alt)
    "GET.PA",   # Getlink
    "HO.PA",    # Thales
    "IDSF.PA",  # Sodexo
    "KN.PA",    # Klépierre
    "LR.PA",    # Legrand
    "LHN.SW",   # LafargeHolcim → Holcim
    "ML.PA",    # Michelin
    "PUB.PA",   # Publicis
    "RNO.PA",   # Renault
    "SGO.PA",   # Saint-Gobain
    "SOLB.BR",  # Solvay (Brüssel)
    "STM.PA",   # STMicroelectronics
    "SXP.PA",   # Sopra Steria
    "TEP.PA",   # Teleperformance
    "TRI.PA",   # Trigano
    "UBI.PA",   # Ubisoft
    "VIE.PA",   # Veolia
    "VIV.PA",   # Vivendi
    # Niederlande (weitere)
    "ABN.AS",   # ABN AMRO
    "AKZA.AS",  # Akzo Nobel
    "DSM.AS",   # DSM-Firmenich
    "HEIA.AS",  # Heineken
    "IMCD.AS",  # IMCD
    "NN.AS",    # NN Group
    "RAND.AS",  # Randstad
    "REN.AS",   # RELX (NL-Listing)
    "TKWY.AS",  # Just Eat Takeaway
    "UNA.AS",   # Unilever NL
    "WKL.AS",   # Wolters Kluwer
    # Schweiz (SMI-Werte im STOXX 600)
    "ABBN.SW",  # ABB
    "CFR.SW",   # Richemont
    "GEBN.SW",  # Geberit
    "GIVN.SW",  # Givaudan
    "LONN.SW",  # Lonza
    "NESN.SW",  # Nestlé
    "NOVN.SW",  # Novartis
    "ROG.SW",   # Roche
    "SGSN.SW",  # SGS
    "SLHN.SW",  # Swiss Life
    "SRENH.SW", # Swiss Re
    "UBSG.SW",  # UBS
    "ZURN.SW",  # Zurich Insurance
    # Vereinigtes Königreich (FTSE-Werte im STOXX 600)
    "AZN.L",    # AstraZeneca
    "BA.L",     # BAE Systems
    "BP.L",     # BP
    "BT-A.L",   # BT Group
    "CRH.L",    # CRH
    "DGE.L",    # Diageo
    "EXPN.L",   # Experian
    "FLTR.L",   # Flutter Entertainment
    "GLEN.L",   # Glencore
    "GSK.L",    # GSK
    "HSBA.L",   # HSBC
    "IMB.L",    # Imperial Brands
    "LSEG.L",   # London Stock Exchange Group
    "LLOY.L",   # Lloyds Banking
    "MNG.L",    # M&G
    "NXT.L",    # Next
    "PRU.L",    # Prudential
    "REL.L",    # RELX
    "RIO.L",    # Rio Tinto
    "RKT.L",    # Reckitt Benckiser
    "RR.L",     # Rolls-Royce
    "SBRY.L",   # Sainsbury's
    "SHEL.L",   # Shell
    "SKG.L",    # Smurfit Kappa
    "SMDS.L",   # Smith Douglas Homes
    "SON.L",    # Sonova
    "TSCO.L",   # Tesco
    "ULVR.L",   # Unilever UK
    "UTG.L",    # Unite Group
    "VOD.L",    # Vodafone
    # Spanien (weitere)
    "ACS.MC",   # ACS
    "AMS.MC",   # Amadeus IT
    "ELE.MC",   # Endesa
    "FER.MC",   # Ferrovial
    "MAP.MC",   # Mapfre
    "REP.MC",   # Repsol
    "TEF.MC",   # Telefónica
    # Italien (weitere)
    "ATL.MI",   # Atlantia
    "AZM.MI",   # Azimut
    "BGN.MI",   # Banca Generali
    "BMED.MI",  # Banca Mediolanum
    "BMPS.MI",  # Monte dei Paschi
    "BPER.MI",  # BPER Banca
    "CPR.MI",   # Azimut / CPR
    "G.MI",     # Generali
    "IF.MI",    # Italgas
    "LDO.MI",   # Leonardo
    "MONC.MI",  # Moncler
    "PIRC.MI",  # Pirelli
    "PST.MI",   # Poste Italiane
    "REC.MI",   # Recordati
    "SPM.MI",   # Saipem
    "SRG.MI",   # Snam
    "STL.MI",   # Stallergenes Greer
    "TEN.MI",   # Tenaris
    "TIT.MI",   # Telecom Italia
    "TOD.MI",   # Tod's
    # Schweden
    "ABB.ST",   # ABB (SE-Listing)
    "ALFA.ST",  # Alfa Laval
    "ASSA-B.ST",# ASSA ABLOY
    "ATCO-A.ST",# Atlas Copco A
    "ERIC-B.ST",# Ericsson B
    "ESSITY-B.ST", # Essity
    "EVO.ST",   # Evolution
    "GETI-B.ST",# Getinge
    "HM-B.ST",  # H&M B
    "INVE-B.ST",# Investor B
    "KINV-B.ST",# Kinnevik
    "NDA-SE.ST",# Nordea (SE)
    "SAND.ST",  # Sandvik
    "SCA-B.ST", # SCA
    "SEB-A.ST", # SEB A
    "SECU-B.ST",# Securitas
    "SKA-B.ST", # Skanska
    "SKF-B.ST", # SKF
    "SWED-A.ST",# Swedbank
    "TEL2-B.ST",# Tele2
    "VOLV-B.ST",# Volvo B
    # Dänemark
    "CARL-B.CO",# Carlsberg B
    "CHR.CO",   # Chr. Hansen
    "COLO-B.CO",# Coloplast
    "GN.CO",    # GN Store Nord
    "ISS.CO",   # ISS
    "MAERSK-B.CO", # Maersk B
    "NFLX.CO",  # (placeholder — Novo Nordisk below)
    "NOVO-B.CO",# Novo Nordisk B
    "ORSTED.CO",# Ørsted
    "PNDORA.CO",# Pandora
    "RBREW.CO", # Royal Unibrew
    "ROCK-B.CO",# Rockwool B
    "SIM.CO",   # SimCorp
    "VWS.CO",   # Vestas Wind Systems
    "WDH.CO",   # William Demant
    # Finnland
    "FORTUM.HE",# Fortum
    "HUH1V.HE", # Huhtamäki
    "KNEBV.HE", # Kone B
    "NESTE.HE", # Neste
    "NOKIA.HE", # Nokia
    "OUT1V.HE", # Outokumpu
    "SAMPO.HE", # Sampo
    "STERV.HE", # Stora Enso R
    "TLS1V.HE", # Telia
    "WRT1V.HE", # Wärtsilä
    # Norwegen
    "AKRBP.OL", # Aker BP
    "DNB.OL",   # DNB
    "EQNR.OL",  # Equinor
    "MOWI.OL",  # Mowi
    "NHY.OL",   # Norsk Hydro
    "ORK.OL",   # Orkla
    "SALM.OL",  # SalMar
    "SCHA.OL",  # Schibsted
    "SUBC.OL",  # Subsea 7
    "TEL.OL",   # Telenor
    "YAR.OL",   # Yara
    # Belgien / Luxemburg
    "ABI.BR",   # AB InBev
    "ACKB.BR",  # Ackermans & van Haaren
    "AGS.BR",   # ageas
    "ARGX.BR",  # argenx
    "COLR.BR",  # Colruyt
    "GBLB.BR",  # Groupe Bruxelles Lambert
    "KBC.BR",   # KBC
    "PROX.BR",  # Proximus
    "SOF.BR",   # Sofina
    "UCB.BR",   # UCB
    "UMI.BR",   # Umicore
    # Österreich
    "EBS.VI",   # Erste Group
    "OMV.VI",   # OMV
    "RBI.VI",   # Raiffeisen Bank International
    "VIG.VI",   # Vienna Insurance Group
    "VOE.VI",   # voestalpine
    # Portugal
    "EDP.LS",   # EDP
    "EDPR.LS",  # EDP Renováveis
    "GALP.LS",  # Galp Energia
    "NOS.LS",   # NOS
    # Irland
    "AIB.IR",   # AIB
    "BIRG.IR",  # Bank of Ireland
    "DPH.IR",   # Dalata Hotel
    "INM.IR",   # Independent News
    "PTSB.IR",  # Permanent TSB
    # Polen / Ungarn / Tschechien (Eastern Europe)
    "PKO.WA",   # PKO Bank Polski
    "PKN.WA",   # PKN Orlen
    "PZU.WA",   # PZU
    "KGH.WA",   # KGHM Polska Miedź
    "LPP.WA",   # LPP
    "DNP.WA",   # Dino Polska
    "OPL.WA",   # Orange Polska
    "PEO.WA",   # Bank Pekao
    "SPL.WA",   # Santander Bank Polska
    "CDR.WA",   # CD Projekt
    "OTP.BD",   # OTP Bank (Ungarn)
    "CEZ.PR",   # ČEZ (Tschechien)
]

# De-duplicate (STOXX50 bereits enthalten)
STOXX600_TICKERS = list(dict.fromkeys(STOXX600_TICKERS))
