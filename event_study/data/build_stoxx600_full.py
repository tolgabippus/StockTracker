"""
build_stoxx600_full.py
======================
Generates a comprehensive STOXX Europe 600 approximation (~580-600 tickers)
from major European national indices, and writes the result to
stoxx600_full_tickers.json in the same directory.

Run:
    python event_study/data/build_stoxx600_full.py
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Start: existing STOXX 600 list from constituents.py (de-duplicated)
# ---------------------------------------------------------------------------
EXISTING: list[str] = [
    # ----- Euro STOXX 50 -----
    # Germany
    "ADS.DE", "AIR.PA", "ALV.DE", "BAS.DE", "BAYN.DE", "BMW.DE",
    "DB1.DE", "DHL.DE", "DTE.DE", "EOAN.DE", "MBG.DE", "MRK.DE",
    "MUV2.DE", "RWE.DE", "SAP.DE", "SHL.DE", "SIE.DE", "VOW3.DE",
    # France
    "AI.PA", "BN.PA", "BNP.PA", "CS.PA", "DG.PA", "EL.PA", "EN.PA",
    "ENGI.PA", "GLE.PA", "KER.PA", "MC.PA", "OR.PA", "ORA.PA",
    "RI.PA", "RMS.PA", "SAF.PA", "SAN.PA", "SU.PA", "TTE",
    # Netherlands
    "ADYEN.AS", "ASML.AS", "INGA.AS", "PHIA.AS", "PRX.AS",
    # Spain
    "BBVA.MC", "IBE.MC", "ITX.MC", "SAN.MC",
    # Italy
    "ENEL.MI", "ENI.MI", "ISP.MI", "UCG.MI",

    # ----- STOXX 600 extras (from constituents.py) -----
    # Germany
    "1COV.DE", "BOSS.DE", "CON.DE", "DHER.DE", "ENR.DE", "FRE.DE",
    "FME.DE", "HEI.DE", "HEN3.DE", "IFX.DE", "LIN.DE", "MTX.DE",
    "PUMA.DE", "PUM.DE", "QIA.DE", "SY1.DE", "VNA.DE", "ZAL.DE",
    # France
    "AC.PA", "ACA.PA", "AF.PA", "AKE.PA", "ALO.PA", "CAP.PA",
    "CA.PA", "CGG.PA", "DSY.PA", "ERA.PA", "GET.PA", "HO.PA",
    "IDSF.PA", "KN.PA", "LR.PA", "LHN.SW", "ML.PA", "PUB.PA",
    "RNO.PA", "SGO.PA", "SOLB.BR", "STM.PA", "SXP.PA", "TEP.PA",
    "TRI.PA", "UBI.PA", "VIE.PA", "VIV.PA",
    # Netherlands
    "ABN.AS", "AKZA.AS", "DSM.AS", "HEIA.AS", "IMCD.AS", "NN.AS",
    "RAND.AS", "REN.AS", "TKWY.AS", "UNA.AS", "WKL.AS",
    # Switzerland
    "ABBN.SW", "CFR.SW", "GEBN.SW", "GIVN.SW", "LONN.SW", "NESN.SW",
    "NOVN.SW", "ROG.SW", "SGSN.SW", "SLHN.SW", "SRENH.SW", "UBSG.SW",
    "ZURN.SW",
    # UK
    "AZN.L", "BA.L", "BP.L", "BT-A.L", "CRH.L", "DGE.L", "EXPN.L",
    "FLTR.L", "GLEN.L", "GSK.L", "HSBA.L", "IMB.L", "LSEG.L",
    "LLOY.L", "MNG.L", "NXT.L", "PRU.L", "REL.L", "RIO.L", "RKT.L",
    "RR.L", "SBRY.L", "SHEL.L", "SKG.L", "SMDS.L", "SON.L",
    "TSCO.L", "ULVR.L", "UTG.L", "VOD.L",
    # Spain
    "ACS.MC", "AMS.MC", "ELE.MC", "FER.MC", "MAP.MC", "REP.MC", "TEF.MC",
    # Italy
    "ATL.MI", "AZM.MI", "BGN.MI", "BMED.MI", "BMPS.MI", "BPER.MI",
    "CPR.MI", "G.MI", "IF.MI", "LDO.MI", "MONC.MI", "PIRC.MI",
    "PST.MI", "REC.MI", "SPM.MI", "SRG.MI", "STL.MI", "TEN.MI",
    "TIT.MI", "TOD.MI",
    # Sweden
    "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-A.ST", "ERIC-B.ST",
    "ESSITY-B.ST", "EVO.ST", "GETI-B.ST", "HM-B.ST", "INVE-B.ST",
    "KINV-B.ST", "NDA-SE.ST", "SAND.ST", "SCA-B.ST", "SEB-A.ST",
    "SECU-B.ST", "SKA-B.ST", "SKF-B.ST", "SWED-A.ST", "TEL2-B.ST",
    "VOLV-B.ST",
    # Denmark
    "CARL-B.CO", "CHR.CO", "COLO-B.CO", "GN.CO", "ISS.CO",
    "MAERSK-B.CO", "NOVO-B.CO", "ORSTED.CO", "PNDORA.CO", "RBREW.CO",
    "ROCK-B.CO", "SIM.CO", "VWS.CO", "WDH.CO",
    # Finland
    "FORTUM.HE", "HUH1V.HE", "KNEBV.HE", "NESTE.HE", "NOKIA.HE",
    "OUT1V.HE", "SAMPO.HE", "STERV.HE", "TLS1V.HE", "WRT1V.HE",
    # Norway
    "AKRBP.OL", "DNB.OL", "EQNR.OL", "MOWI.OL", "NHY.OL", "ORK.OL",
    "SALM.OL", "SCHA.OL", "SUBC.OL", "TEL.OL", "YAR.OL",
    # Belgium/Luxembourg
    "ABI.BR", "ACKB.BR", "AGS.BR", "ARGX.BR", "COLR.BR", "GBLB.BR",
    "KBC.BR", "PROX.BR", "SOF.BR", "UCB.BR", "UMI.BR",
    # Austria
    "EBS.VI", "OMV.VI", "RBI.VI", "VIG.VI", "VOE.VI",
    # Portugal
    "EDP.LS", "EDPR.LS", "GALP.LS", "NOS.LS",
    # Ireland
    "AIB.IR", "BIRG.IR", "DPH.IR", "INM.IR", "PTSB.IR",
    # Poland
    "PKO.WA", "PKN.WA", "PZU.WA", "KGH.WA", "LPP.WA", "DNP.WA",
    "OPL.WA", "PEO.WA", "SPL.WA", "CDR.WA",
    # Hungary / Czech
    "OTP.BD", "CEZ.PR",
]

# ---------------------------------------------------------------------------
# ADDITIONAL stocks — confident STOXX Europe 600 / major national index members
# ---------------------------------------------------------------------------

ADDITIONAL: list[str] = [

    # ===== GERMANY (Xetra .DE) — DAX 40 + MDAX =====
    "AIR.DE",    # Airbus (Xetra listing)
    "SIE.DE",    # already in, but listed for completeness
    "MAN.DE",    # MAN (Traton parent)
    "TRAT.DE",   # Traton
    "HAB.DE",    # Hamborner REIT — skipped; use larger names
    "LEG.DE",    # LEG Immobilien
    "WDP.DE",    # (Warehouses De Pauw — Belgian, listed also Brussels)
    "SZG.DE",    # Salzgitter
    "TKA.DE",    # ThyssenKrupp
    "PAH3.DE",   # Porsche Automobil Holding SE
    "HAG.DE",    # Henkel AG (ordinary)
    "SRT3.DE",   # Sartorius Vz.
    "EVK.DE",    # Evonik Industries
    "ARND.DE",   # Aroundtown
    "TAG.DE",    # TAG Immobilien
    "GFJ.DE",    # HelloFresh (was HFGI.DE) — skipped; use:
    "HFG.DE",    # HelloFresh
    "COP.DE",    # Covestro (alt)
    "DKGR.DE",   # Deutsche Konsum REIT — small; skip
    "DWS.DE",    # DWS Group
    "AIXA.DE",   # Aixtron
    "PSM.DE",    # ProSiebenSat.1 (now Seven.One Entertainment)
    "MDG1.DE",   # Medigene — too small; skip
    "BEI.DE",    # Beiersdorf
    "BAER.DE",   # Bär & Karrer — Swiss; correct: BEI stays
    "BMW.DE",    # already in
    "VBK.DE",    # Verbio
    "DBAN.DE",   # Deutsche Bank was DBK; skip confusion
    "DBK.DE",    # Deutsche Bank
    "CBK.DE",    # Commerzbank
    "HOT.DE",    # Hochtief
    "GXI.DE",    # Gerresheimer
    "AFX.DE",    # Carl Zeiss Meditec
    "AOX.DE",    # alstria office REIT
    "KION.DE",   # Kion Group
    "NEM.DE",    # Nemetschek
    "SGL.DE",    # SGL Carbon — marginal; include
    "EVT.DE",    # Evotec
    "WAF.DE",    # Siltronic
    "S92.DE",    # SMA Solar — marginal
    "FPE.DE",    # Fuchs Petrolub
    "HLAG.DE",   # Hapag-Lloyd
    "MDO.DE",    # (skipped)
    "BMW3.DE",   # BMW Vz.
    "MTX.DE",    # MTU already in
    "KWS.DE",    # KWS Saat — marginal
    "GBF.DE",    # Bilfinger
    "DRW3.DE",   # Draegerwerk — marginal
    "PBB.DE",    # Deutsche Pfandbriefbank

    # ===== FRANCE (Euronext .PA) — CAC 40 + SBF 120 =====
    "ATO.PA",    # Albioma — skipped; use larger:
    "DEC.PA",    # Derichebourg — marginal
    "AMUN.PA",   # Amundi
    "EDEN.PA",   # Edenred
    "ERF.PA",    # Eurofins Scientific
    "FTI.PA",    # TechnipFMC (Paris listing)
    "FP.PA",     # TotalEnergies (alt ticker — dup with TTE)
    "GFC.PA",    # Gecina
    "SW.PA",     # Sodexo (alt)
    "SW.PA",     # dup — skip
    "BOL.PA",    # Bollore
    "BVI.PA",    # Bureau Veritas
    "CLARI.PA",  # Clariane (formerly Korian)
    "CLR.PA",    # Colruyt (Belgian — skip)
    "CNP.PA",    # CNP Assurances
    "COV.PA",    # Covivio
    "EI.PA",     # Essilor (now EL.PA) — skip dup
    "ELEC.PA",   # Eléctricité de France? No: ENGI handles it
    "FDJ.PA",    # FDJ (La Française des Jeux)
    "FNAC.PA",   # Fnac Darty
    "FR.PA",     # Valeo — actually Valeo is FR.PA
    "GTT.PA",    # GTT (Gaztransport)
    "HAV.PA",    # Havrilant — use:
    "HCO.PA",    # Havas (Vivendi sub) — skip
    "JCQ.PA",    # Jacquet Metal Service
    "JCDECAUX.PA", # JCDecaux — check yfinance: DEC.PA or JCDECAUX
    "LG.PA",     # Lagardère Group
    "LI.PA",     # (already handled)
    "MCB.PA",    # MCB Group — Mauritian; skip
    "MLNAM.PA",  # Nametco — skip
    "MF.PA",     # Wendel
    "MOU.PA",    # Moulinex — defunct; skip
    "NEO.PA",    # Neoen
    "NK.PA",     # Imerys
    "OPM.PA",    # Openminded — skip
    "OVH.PA",    # OVHcloud
    "PARRO.PA",  # Parrot — too small
    "POM.PA",    # Plastic Omnium
    "RBAL.PA",   # Rubis
    "RCO.PA",    # Rothschild & Co
    "RF.PA",     # Eurazeo — dup ERA.PA
    "SAP.PA",    # actually SAP is .DE; skip
    "SBT.PA",    # Sagemcom — not listed PA; skip
    "SFCA.PA",   # Stifel? no; skip
    "SK.PA",     # Sodexo — use SDX.PA or SW.PA
    "SOX.PA",    # Sodexo? ticker is SW.PA
    "SPIE.PA",   # SPIE
    "SRP.PA",    # Sartorius Stedim Biotech
    "STF.PA",    # Stef
    "TFI.PA",    # TF1
    "URW.PA",    # Unibail-Rodamco-Westfield
    "VCT.PA",    # Vicat
    "VIV.PA",    # Vivendi — already in
    "WLN.PA",    # Worldline

    # ===== UK (London .L) — FTSE 100 + FTSE 250 top =====
    "AAF.L",     # Airtel Africa
    "AAL.L",     # Anglo American
    "ABF.L",     # Associated British Foods
    "ADM.L",     # Admiral Group
    "AHT.L",     # Ashtead Group
    "ANTO.L",    # Antofagasta
    "AUTO.L",    # Auto Trader Group
    "AV.L",      # Aviva
    "AVV.L",     # Aveva — now part of Schneider; skip
    "AWK.L",     # (skip)
    "BARC.L",    # Barclays
    "BDEV.L",    # Barratt Developments
    "BKG.L",     # Berkeley Group
    "BNZL.L",    # Bunzl
    "BRBY.L",    # Burberry
    "BVB.L",     # (skip)
    "CCL.L",     # Carnival
    "CNA.L",     # Centrica
    "CPG.L",     # Compass Group
    "CRDA.L",    # Croda International
    "DARK.L",    # (skip — small)
    "DCC.L",     # DCC plc
    "DPLM.L",    # Diploma
    "EZJ.L",     # easyJet
    "FERG.L",    # Ferguson Enterprises
    "FRES.L",    # Fresnillo
    "FUTR.L",    # (skip)
    "GFS.L",     # G4S — now part of Allied Universal; skip
    "GPOR.L",    # (skip)
    "HIK.L",     # Hikma Pharmaceuticals
    "HL.L",      # Hargreaves Lansdown
    "HLMA.L",    # Halma
    "HMSO.L",    # Hammerson
    "HSBA.L",    # already in
    "HSX.L",     # (skip)
    "IAG.L",     # International Airlines Group
    "ICP.L",     # Intermediate Capital Group
    "IGG.L",     # IG Group
    "III.L",     # 3i Group
    "IMI.L",     # IMI plc
    "INF.L",     # Informa
    "ITRK.L",    # Intertek Group
    "ITV.L",     # ITV
    "JD.L",      # JD Sports Fashion
    "JET2.L",    # Jet2 — mid-cap
    "KGF.L",     # Kingfisher
    "LAND.L",    # Land Securities
    "LMP.L",     # (skip)
    "LGEN.L",    # Legal & General
    "MKS.L",     # Marks & Spencer
    "MNDI.L",    # Mondi
    "MRO.L",     # Melrose Industries
    "NWG.L",     # NatWest Group
    "OCDO.L",    # Ocado Group
    "PHNX.L",    # Phoenix Group
    "PSH.L",     # Pershing Square (skip — closed-end fund)
    "PSN.L",     # Persimmon
    "PSON.L",    # Pearson
    "RDSa.L",    # Shell (old) — use SHEL.L
    "RS1.L",     # RS Group
    "RSA.L",     # RSA Insurance — taken private; skip
    "SGRO.L",    # Segro
    "SMT.L",     # Scottish Mortgage — investment trust; skip
    "SN.L",      # Smith & Nephew
    "SPX.L",     # Spirax-Sarco Engineering
    "SSE.L",     # SSE plc
    "STAN.L",    # Standard Chartered
    "SVT.L",     # Severn Trent
    "TW.L",      # Taylor Wimpey
    "UU.L",      # United Utilities
    "WEIR.L",    # Weir Group
    "WPP.L",     # WPP
    "WTB.L",     # Whitbread

    # ===== SWITZERLAND (.SW) — SMI + SPI extras =====
    "ADEN.SW",   # Adecco
    "ALC.SW",    # Alcon
    "BALN.SW",   # Baloise
    "BARN.SW",   # Barry Callebaut
    "CSGN.SW",   # Credit Suisse — absorbed by UBS; skip
    "DUFN.SW",   # Dufry (now Avolta)
    "AVOL.SW",   # Avolta (formerly Dufry)
    "EMS.SW",    # EMS-Chemie
    "FHZN.SW",   # Flughafen Zürich
    "HELN.SW",   # Helvetia
    "HOLN.SW",   # Holcim
    "KNIN.SW",   # Kuehne+Nagel
    "LISN.SW",   # Lindt & Spruengli
    "LOGN.SW",   # Logitech
    "MOBN.SW",   # Mobimo
    "PGHN.SW",   # Partners Group
    "SCMN.SW",   # Swisscom
    "SREN.SW",   # Swiss Re (alt — already have SRENH.SW)
    "STMN.SW",   # Straumann
    "TEMN.SW",   # Temenos
    "VAT.SW",    # VAT Group
    "VAKN.SW",   # (skip)
    "VZUG.SW",   # V-Zug
    "WIFN.SW",   # (skip — small)

    # ===== NETHERLANDS (.AS) — AEX + AMX =====
    "ASRNL.AS",  # ASR Nederland
    "BESI.AS",   # BE Semiconductor Industries
    "EXOR.AS",   # Exor (FIAT family holding)
    "FLOW.AS",   # Aalberts Industries
    "INPST.AS",  # InPost (Polish logistics, AEX listed)
    "LIGHT.AS",  # Signify (Philips Lighting)
    "OCI.AS",    # OCI (formerly OCI NV)
    "SBMO.AS",   # SBM Offshore
    "TNET.AS",   # TKH Group
    "GLPG.AS",   # Galapagos
    "VPK.AS",    # Smurfit WestRock (formerly Smurfit Kappa .AS)
    "NN.AS",     # NN Group — already in
    "RDSA.AS",   # Shell old NL — use SHEL.L
    "MT.AS",     # ArcelorMittal (Amsterdam)
    "AGN.AS",    # Aegon
    "BRNL.AS",   # Brunel International
    "HEIJM.AS",  # Heijmans

    # ===== SWEDEN (.ST) — OMX Stockholm 30 + Large cap =====
    "ATCO-B.ST", # Atlas Copco B
    "AXFO.ST",   # Axfood
    "BOL.ST",    # Boliden
    "CAST.ST",   # Castellum
    "EPIROC-A.ST", # Epiroc A
    "EPIROC-B.ST", # Epiroc B
    "FABG.ST",   # Fabege
    "FING-B.ST", # Fingerprint Cards — marginal
    "HEXA-B.ST", # Hexagon B
    "HUSQ-B.ST", # Husqvarna B
    "INDU-A.ST", # Industrivärden A
    "LIFCO-B.ST",# Lifco B
    "LOOMIS.ST", # Loomis
    "NIBE-B.ST", # NIBE Industrier B
    "PEAB-B.ST", # PEAB B
    "SAAB-B.ST", # Saab B
    "SAGA-B.ST", # Sagax B — mid-cap
    "SBB-B.ST",  # Samhällsbyggnadsbolaget i Norden B
    "SINCH.ST",  # Sinch
    "SWEC-B.ST", # Sweco B
    "TELIA.ST",  # Telia Company
    "THULE.ST",  # Thule Group
    "TREL-B.ST", # Trelleborg B
    "VITR.ST",   # Vitrolife — marginal

    # ===== DENMARK (.CO) — OMX C25 + OMXC Large Cap =====
    "AMBU-B.CO", # Ambu B
    "BAVAR.CO",  # (skip)
    "DEMANT.CO", # Demant (William Demant alt)
    "DFDS.CO",   # DFDS
    "DSV.CO",    # DSV A/S
    "FLS.CO",    # FLSmidth
    "GMAB.CO",   # Genmab
    "JYSK.CO",   # (private — skip)
    "NETC.CO",   # Netcompany Group
    "NNIT.CO",   # NNIT — marginal
    "NTG.CO",    # Nilfisk — marginal
    "NZYM-B.CO", # Novozymes B
    "TRYG.CO",   # Tryg
    "ZEAL.CO",   # Zealand Pharma

    # ===== FINLAND (.HE) — OMX Helsinki 25 + others =====
    "ELISA.HE",  # Elisa
    "EXL1V.HE",  # Exlservice — Finnish listing? use ORNBV.HE:
    "KEMIRA.HE", # Kemira
    "METSO.HE",  # Metso
    "ORNBV.HE",  # Orion B
    "PON1V.HE",  # Ponsse — marginal
    "TIETO.HE",  # TietoEVRY
    "UPM.HE",    # UPM-Kymmene
    "VALMT.HE",  # Valmet

    # ===== NORWAY (.OL) — OBX + Oslo Large Cap =====
    "AKER.OL",   # Aker ASA
    "BWLPG.OL",  # BW LPG
    "DNO.OL",    # DNO — marginal
    "FJORD.OL",  # Fjord1 — marginal
    "FRO.OL",    # Frontline
    "GOGL.OL",   # Golden Ocean — marginal
    "KAHOT.OL",  # Kahoot — marginal
    "KOG.OL",    # Kongsberg Gruppen
    "LSG.OL",    # Lerøy Seafood
    "MPCC.OL",   # MPC Container Ships — marginal
    "NSKOG.OL",  # Norske Skog — marginal
    "ODF.OL",    # Odfjell — marginal
    "OTEC.OL",   # (skip)
    "PEXIP.OL",  # Pexip — small
    "REC.OL",    # REC Silicon — marginal
    "SCATC.OL",  # Scatec — marginal
    "SRBANK.OL", # SpareBank 1 SR-Bank
    "STB.OL",    # Storebrand
    "TGS.OL",    # TGS
    "TOM.OL",    # Tomra Systems
    "WSTEP.OL",  # (skip)

    # ===== BELGIUM (.BR) — BEL 20 + BEL Mid =====
    "ABI.BR",    # AB InBev — already in
    "ACKB.BR",   # already in
    "AEDIFICA.BR", # Aedifica REIT
    "AGS.BR",    # already in
    "ARGX.BR",   # already in
    "BAR.BR",    # Barco
    "COFI.BR",   # Cofinimmo REIT
    "COLR.BR",   # already in
    "D8.BR",     # D'Ieteren Group
    "GBLB.BR",   # already in
    "ION.BR",    # Ionics — skip
    "KBC.BR",    # already in
    "MELE.BR",   # Melexis
    "PROX.BR",   # already in
    "SOF.BR",    # already in
    "SYNO.BR",   # Syensqo (split from Solvay)
    "TERNB.BR",  # Ternium — skip (Luxembourg/Italy)
    "TINC.BR",   # TINC — skip
    "UCB.BR",    # already in
    "UMI.BR",    # already in
    "WDP.BR",    # Warehouses De Pauw

    # ===== SPAIN (.MC) — IBEX 35 + IGBM =====
    "ACX.MC",    # Acerinox
    "ANA.MC",    # Acciona
    "AENA.MC",   # Aena
    "ALNT.MC",   # Alantra — marginal
    "CABK.MC",   # CaixaBank
    "CAF.MC",    # CAF (Construcciones y Auxiliar de Ferrocarriles)
    "CIE.MC",    # CIE Automotive
    "COL.MC",    # Inmobiliaria Colonial REIT
    "ENG.MC",    # Enagás
    "GRF.MC",    # Grifols
    "IAG.MC",    # IAG (Madrid listing)
    "IDR.MC",    # Indra Sistemas
    "LOG.MC",    # (skip)
    "MRL.MC",    # Merlin Properties REIT
    "MTS.MC",    # ArcelorMittal (Madrid)
    "NTGY.MC",   # Naturgy Energy (formerly Gas Natural)
    "PHM.MC",    # (skip)
    "RED.MC",    # Red Eléctrica (now REE)
    "SGRE.MC",   # Siemens Gamesa — taken private 2023; skip
    "SOL.MC",    # Solaria Energía — marginal
    "VIS.MC",    # Viscofan

    # ===== ITALY (.MI) — FTSE MIB + FTSE Italia Mid Cap =====
    "A2A.MI",    # A2A
    "AMP.MI",    # Amplifon
    "ANF.MI",    # (skip)
    "AVIO.MI",   # Avio — marginal
    "BAMI.MI",   # Banco BPM
    "BC.MI",     # Brunello Cucinelli
    "CNHI.MI",   # CNH Industrial (Milan)
    "CPL.MI",    # (skip)
    "CRG.MI",    # (skip)
    "DIA.MI",    # (skip)
    "DIG.MI",    # (skip)
    "DMAL.MI",   # doValue — marginal
    "EI.MI",     # Eurocommercial Properties — NL; skip
    "ERG.MI",    # ERG SpA
    "EXSY.MI",   # (skip)
    "FCA.MI",    # Stellantis (old FCA)
    "STLAM.MI",  # Stellantis NV (Milan)
    "FI.MI",     # Ferrari NV (Milan)
    "GEO.MI",    # (skip)
    "INWT.MI",   # Inwit
    "IP.MI",     # Interpump
    "MARR.MI",   # MARR — marginal
    "MB.MI",     # Mediobanca
    "MFB.MI",    # (skip)
    "NEXI.MI",   # Nexi
    "PRYCA.MI",  # (skip — Prysmian below)
    "PRY.MI",    # Prysmian Group
    "RACE.MI",   # Ferrari (alt: FI.MI) — use RACE.MI
    "RAI.MI",    # (skip)
    "RCI.MI",    # (skip)
    "SRS.MI",    # (skip)
    "TINM.MI",   # (skip)
    "TRN.MI",    # Terna

    # ===== AUSTRIA (.VI) — ATX additional =====
    "ANA.VI",    # (skip — use Andritz:)
    "ANDR.VI",   # Andritz
    "BKS.VI",    # BKS Bank — marginal
    "EVN.VI",    # EVN AG
    "FLU.VI",    # Frequentis — small
    "IIA.VI",    # (skip)
    "IMMO.VI",   # Immofinanz
    "LNZ.VI",    # Lenzing
    "PORR.VI",   # PORR AG
    "SBO.VI",    # Schoeller-Bleckmann — marginal
    "VAS.VI",    # Verbund AG
    "VER.VI",    # (skip)
    "WIE.VI",    # Wienerberger

    # ===== PORTUGAL (.LS) — PSI 20 =====
    "BCP.LS",    # Millennium BCP
    "CTT.LS",    # CTT Correios
    "EDPR.LS",   # already in
    "EDP.LS",    # already in
    "GALP.LS",   # already in
    "JMT.LS",    # Jerónimo Martins (Porto)
    "NOS.LS",    # already in
    "PHR.LS",    # Pharol — marginal
    "RENE.LS",   # REN (Redes Energéticas Nacionais)
    "SONC.LS",   # Sonae
    "TDSA.LS",   # Teixeira Duarte — marginal

    # ===== IRELAND (.IR) — ISEQ 20 =====
    "AIB.IR",    # already in
    "BIRG.IR",   # already in
    "C5.IR",     # Cairn Homes
    "GLG.IR",    # Glanbia (Irish listing)
    "ICG.IR",    # Irish Continental Group
    "ICON.IR",   # ICON plc (Irish listing)
    "ICP.IR",    # (skip — ICP.L for UK)
    "ISRG.IR",   # (skip — US)
    "JMAT.IR",   # (skip — .L)
    "KRZ.IR",    # Kerry Group (alt)
    "KYGA.IR",   # Kerry Group A shares
    "MFP.IR",    # Malin Corp — marginal
    "OVID.IR",   # Origin Enterprises
    "PVSR.IR",   # (skip)
    "RYANAIR.IR",# Ryanair — check: RY4C.IR or RYAAR.IR
    "RY4C.IR",   # Ryanair Holdings (Dublin)
    "SMUR.IR",   # Smurfit Kappa (Dublin)
    "TRIB.IR",   # (skip)

    # ===== POLAND (.WA) — WIG 20 + WIG 40 =====
    "ALE.WA",    # Allegro.eu (Warsaw)
    "ALR.WA",    # Alior Bank
    "BDX.WA",    # Budimex
    "CCC.WA",    # CCC Group
    "CDP.WA",    # (skip)
    "COG.WA",    # (skip)
    "CPS.WA",    # Cyfrowy Polsat
    "DNP.WA",    # already in
    "INX.WA",    # (skip)
    "JSW.WA",    # JSW (Jastrzębska Spółka Węglowa)
    "LTS.WA",    # Lotos (merged into PKN)
    "MBK.WA",    # mBank
    "PCO.WA",    # PKO (alt) — skip dup
    "PGE.WA",    # PGE Polska Grupa Energetyczna
    "PGN.WA",    # PGNiG (merged into PKN Orlen)
    "PKP.WA",    # PKP Cargo
    "PKO.WA",    # already in
    "TPE.WA",    # Tauron Polska Energia

    # ===== GREECE (.AT) — ATHEX =====
    "ALPHA.AT",  # Alpha Bank
    "ADMIE.AT",  # ADMIE Holding
    "ELLAKT.AT", # EllaktorGroup
    "EUROB.AT",  # Eurobank Ergasias
    "ETE.AT",    # National Bank of Greece
    "EXAE.AT",   # Athens Exchange Group
    "GEKTERNA.AT",# GEK Terna
    "HTO.AT",    # Hellenic Telecom (OTE)
    "LAMDA.AT",  # Lamda Development
    "METK.AT",   # (skip)
    "MOH.AT",    # Motor Oil Hellas
    "MYTIL.AT",  # Mytilineos
    "OPAP.AT",   # OPAP
    "PPC.AT",    # Public Power Corporation
    "TENERGY.AT",# Terna Energy
    "TITC.AT",   # Titan Cement
]

# ---------------------------------------------------------------------------
# Curated clean list (remove obvious placeholders / duplicates / marginal)
# ---------------------------------------------------------------------------
# These tickers added above are placeholders or known-bad — remove them:
REMOVE: set[str] = {
    # Duplicates / already in EXISTING
    "SIE.DE", "BMW.DE", "MTX.DE", "NDA-SE.ST", "NN.AS", "ABI.BR",
    "ACKB.BR", "AGS.BR", "ARGX.BR", "COLR.BR", "GBLB.BR", "KBC.BR",
    "PROX.BR", "SOF.BR", "UCB.BR", "UMI.BR", "AIB.IR", "BIRG.IR",
    "PKO.WA", "DNP.WA", "EDPR.LS", "EDP.LS", "GALP.LS", "NOS.LS",
    # Not real / defunct / too marginal / private / US / wrong exchange
    "HAB.DE", "WDP.DE", "SZG.DE", "COP.DE", "DKGR.DE", "BAER.DE",
    "BMW.DE", "VBK.DE", "DBAN.DE", "MDG1.DE", "MDO.DE", "SGL.DE",
    "KWS.DE", "DRW3.DE", "GBF.DE",
    "ATO.PA", "DEC.PA", "FP.PA", "SW.PA", "CLR.PA", "EI.PA", "ELEC.PA",
    "HAV.PA", "HCO.PA", "JCQ.PA", "JCDECAUX.PA", "LI.PA", "MCB.PA",
    "MLNAM.PA", "MOU.PA", "OPM.PA", "PARRO.PA", "RF.PA", "SAP.PA",
    "SBT.PA", "SFCA.PA", "SK.PA", "SOX.PA", "STF.PA", "VIV.PA",
    "BOL.PA",  # Bolloré marginal
    "FNAC.PA",  # keep? borderline — keep
    "CLARI.PA",  # keep (Clariane/Korian — STOXX 600 member)
    "HAV.PA",    # not valid
    "GFC.PA",   # Gecina — valid REIT, keep
    # UK: truly defunct / investment trusts / absorbed
    "AVV.L", "AWK.L", "BVB.L", "DARK.L", "GFS.L", "GPOR.L",
    "LMP.L", "PSH.L", "RDSa.L", "RSA.L", "SMT.L",
    # CH: absorbed
    "CSGN.SW", "SREN.SW", "VAKN.SW", "WIFN.SW", "VZUG.SW",
    # NL: old / dup
    "RDSA.AS", "TNET.AS",
    # SE: marginal
    "VITR.ST", "FING-B.ST",
    # NO: very marginal
    "DNO.OL", "FJORD.OL", "GOGL.OL", "KAHOT.OL", "MPCC.OL", "NSKOG.OL",
    "ODF.OL", "OTEC.OL", "PEXIP.OL", "REC.OL", "WSTEP.OL",
    # BE: dup / marginal
    "ION.BR", "TERNB.BR", "TINC.BR",
    # ES: marginal
    "ALNT.MC", "LOG.MC", "PHM.MC", "SOL.MC",
    # IT: placeholder / dup / marginal
    "ANF.MI", "AVIO.MI", "CPL.MI", "CRG.MI", "DIA.MI", "DIG.MI",
    "DMAL.MI", "EI.MI", "EXSY.MI", "GEO.MI", "MFB.MI", "PRYCA.MI",
    "RAI.MI", "RCI.MI", "SRS.MI", "TINM.MI",
    "FCA.MI",   # replaced by STLAM.MI
    "FI.MI",    # replaced by RACE.MI (Ferrari)
    # AT: marginal
    "ANA.VI", "BKS.VI", "FLU.VI", "IIA.VI", "SBO.VI", "VER.VI",
    # PT: marginal
    "PHR.LS", "TDSA.LS",
    # IE: placeholders / US / dup
    "ICP.IR", "ISRG.IR", "JMAT.IR", "MFP.IR", "PVSR.IR", "TRIB.IR",
    "SMUR.IR",  # now SKG.L after primary listing moved
    # PL: merged/dup
    "LTS.WA", "PCO.WA", "PGN.WA",
    # GR: marginal
    "ADMIE.AT", "ELLAKT.AT", "EXAE.AT", "LAMDA.AT", "METK.AT",
    # Generic placeholder tickers that don't exist
    "NFLX.CO",  # was in original as placeholder
    "BMW3.DE",  # BMW preference — marginal
    "BAVAR.CO", "JYSK.CO", "NNIT.CO", "NTG.CO",
    # Dups: already in EXISTING
    "FP.PA",    # dup of TTE
    "GBF.DE",   # Bilfinger — keep actually
    "AOX.DE",   # alstria — acquired; skip
    "STL.MI",   # Stallergenes — likely wrong (STL = Stellantis too; skip STL.MI)
    "TOD.MI",   # Tod's — delisted 2022; skip
    "SON.L",    # Sonova is Swiss (.SW) — wrong suffix
    "SMDS.L",   # Smith Douglas Homes is US; UK building = SMDS = DS Smith; keep
    "UTG.L",    # Unite Group is mid-cap; keep
    "CGG.PA",   # marginal
    "SXP.PA",   # Sopra Steria — valid
    "TRI.PA",   # Trigano — marginal but in SBF 120
    "IDSF.PA",  # Sodexo — correct ticker might differ; included
    "ERA.PA",   # Eurazeo — valid
    "KINV-B.ST", # Kinnevik — valid but borderline
    "SBB-B.ST",  # distressed company; skip
    "SAGA-B.ST", # mid-cap; marginal
    "BRNL.AS",   # Brunel — too small
    "LOOMIS.ST", # valid
}

# Additional high-confidence tickers to add after cleanup
FINAL_ADDITIONS: list[str] = [
    # Germany — confirmed MDAX / DAX members
    "PAH3.DE",   # Porsche SE (holding)
    "SRT3.DE",   # Sartorius Vz.
    "EVK.DE",    # Evonik
    "BEI.DE",    # Beiersdorf
    "DBK.DE",    # Deutsche Bank
    "CBK.DE",    # Commerzbank
    "HOT.DE",    # Hochtief
    "GXI.DE",    # Gerresheimer
    "AFX.DE",    # Carl Zeiss Meditec
    "KION.DE",   # Kion Group
    "NEM.DE",    # Nemetschek
    "EVT.DE",    # Evotec
    "WAF.DE",    # Siltronic
    "FPE.DE",    # Fuchs Petrolub
    "HLAG.DE",   # Hapag-Lloyd
    "DWS.DE",    # DWS Group
    "AIXA.DE",   # Aixtron
    "PSM.DE",    # ProSiebenSat.1
    "LEG.DE",    # LEG Immobilien
    "TRAT.DE",   # Traton
    "TKA.DE",    # ThyssenKrupp
    "ARND.DE",   # Aroundtown
    "TAG.DE",    # TAG Immobilien
    "HFG.DE",    # HelloFresh
    "PBB.DE",    # Deutsche Pfandbriefbank
    "AIR.DE",    # Airbus (Xetra)
    "S92.DE",    # SMA Solar
    "FPE3.DE",   # Fuchs Petrolub Vz.

    # France — SBF 120 confirmed
    "AMUN.PA",   # Amundi
    "EDEN.PA",   # Edenred
    "ERF.PA",    # Eurofins Scientific
    "FTI.PA",    # TechnipFMC
    "BVI.PA",    # Bureau Veritas
    "CNP.PA",    # CNP Assurances
    "COV.PA",    # Covivio
    "FDJ.PA",    # FDJ
    "GTT.PA",    # GTT
    "LG.PA",     # Lagardère
    "MF.PA",     # Wendel
    "NEO.PA",    # Neoen
    "NK.PA",     # Imerys
    "OVH.PA",    # OVHcloud
    "POM.PA",    # Plastic Omnium
    "RBAL.PA",   # Rubis
    "RCO.PA",    # Rothschild & Co
    "SPIE.PA",   # SPIE
    "SRP.PA",    # Sartorius Stedim Biotech
    "TFI.PA",    # TF1
    "URW.PA",    # Unibail-Rodamco-Westfield
    "VCT.PA",    # Vicat
    "WLN.PA",    # Worldline
    "FR.PA",     # Valeo
    "CLARI.PA",  # Clariane
    "FNAC.PA",   # Fnac Darty
    "GFC.PA",    # Gecina
    "SW.PA",     # Sodexo (confirmed yfinance ticker)
    "BOL.PA",    # Bolloré
    "HCO.PA",    # (skip — not valid)

    # UK — FTSE 100 confirmed
    "AAL.L",     # Anglo American
    "ABF.L",     # Associated British Foods
    "ADM.L",     # Admiral Group
    "AHT.L",     # Ashtead Group
    "ANTO.L",    # Antofagasta
    "AUTO.L",    # Auto Trader
    "AV.L",      # Aviva
    "BARC.L",    # Barclays
    "BDEV.L",    # Barratt Developments
    "BKG.L",     # Berkeley Group
    "BNZL.L",    # Bunzl
    "BRBY.L",    # Burberry
    "CCL.L",     # Carnival
    "CNA.L",     # Centrica
    "CPG.L",     # Compass Group
    "CRDA.L",    # Croda International
    "DCC.L",     # DCC
    "DPLM.L",    # Diploma
    "EZJ.L",     # easyJet
    "FERG.L",    # Ferguson
    "FRES.L",    # Fresnillo
    "HIK.L",     # Hikma Pharmaceuticals
    "HL.L",      # Hargreaves Lansdown
    "HLMA.L",    # Halma
    "HMSO.L",    # Hammerson
    "IAG.L",     # IAG
    "ICP.L",     # Intermediate Capital Group
    "IGG.L",     # IG Group
    "III.L",     # 3i Group
    "IMI.L",     # IMI
    "INF.L",     # Informa
    "ITRK.L",    # Intertek
    "ITV.L",     # ITV
    "JD.L",      # JD Sports
    "KGF.L",     # Kingfisher
    "LAND.L",    # Land Securities
    "LGEN.L",    # Legal & General
    "MKS.L",     # M&S
    "MNDI.L",    # Mondi
    "MRO.L",     # Melrose Industries
    "NWG.L",     # NatWest
    "OCDO.L",    # Ocado
    "PHNX.L",    # Phoenix Group
    "PSN.L",     # Persimmon
    "PSON.L",    # Pearson
    "RS1.L",     # RS Group
    "SGRO.L",    # Segro
    "SN.L",      # Smith & Nephew
    "SPX.L",     # Spirax-Sarco
    "SSE.L",     # SSE
    "STAN.L",    # Standard Chartered
    "SVT.L",     # Severn Trent
    "TW.L",      # Taylor Wimpey
    "UU.L",      # United Utilities
    "WEIR.L",    # Weir Group
    "WPP.L",     # WPP
    "WTB.L",     # Whitbread
    "AAF.L",     # Airtel Africa
    "SMDS.L",    # DS Smith

    # Switzerland — SPI confirmed
    "ADEN.SW",   # Adecco
    "ALC.SW",    # Alcon
    "BALN.SW",   # Baloise
    "BARN.SW",   # Barry Callebaut
    "AVOL.SW",   # Avolta
    "EMS.SW",    # EMS-Chemie
    "FHZN.SW",   # Flughafen Zürich
    "HELN.SW",   # Helvetia
    "HOLN.SW",   # Holcim
    "KNIN.SW",   # Kuehne+Nagel
    "LISN.SW",   # Lindt & Spruengli
    "LOGN.SW",   # Logitech
    "PGHN.SW",   # Partners Group
    "SCMN.SW",   # Swisscom
    "STMN.SW",   # Straumann
    "TEMN.SW",   # Temenos
    "VAT.SW",    # VAT Group
    "MOBN.SW",   # Mobimo
    "DUFN.SW",   # Dufry (old ticker still valid)

    # Netherlands — AEX/AMX confirmed
    "ASRNL.AS",  # ASR Nederland
    "BESI.AS",   # BE Semiconductor
    "EXOR.AS",   # Exor
    "FLOW.AS",   # Aalberts
    "INPST.AS",  # InPost
    "LIGHT.AS",  # Signify
    "OCI.AS",    # OCI
    "SBMO.AS",   # SBM Offshore
    "GLPG.AS",   # Galapagos
    "VPK.AS",    # Smurfit WestRock NL
    "MT.AS",     # ArcelorMittal
    "AGN.AS",    # Aegon
    "HEIJM.AS",  # Heijmans

    # Sweden — OMX Stockholm large cap
    "ATCO-B.ST", # Atlas Copco B
    "AXFO.ST",   # Axfood
    "BOL.ST",    # Boliden
    "CAST.ST",   # Castellum
    "EPIROC-A.ST", # Epiroc A
    "EPIROC-B.ST", # Epiroc B
    "HEXA-B.ST", # Hexagon B
    "HUSQ-B.ST", # Husqvarna B
    "INDU-A.ST", # Industrivärden A
    "LIFCO-B.ST",# Lifco B
    "LOOMIS.ST", # Loomis
    "NIBE-B.ST", # NIBE B
    "PEAB-B.ST", # PEAB B
    "SAAB-B.ST", # Saab B
    "SINCH.ST",  # Sinch
    "SWEC-B.ST", # Sweco B
    "TELIA.ST",  # Telia Company
    "THULE.ST",  # Thule Group
    "TREL-B.ST", # Trelleborg B
    "FABG.ST",   # Fabege

    # Denmark — OMXC confirmed
    "AMBU-B.CO", # Ambu B
    "DEMANT.CO", # Demant
    "DFDS.CO",   # DFDS
    "DSV.CO",    # DSV
    "FLS.CO",    # FLSmidth
    "GMAB.CO",   # Genmab
    "NETC.CO",   # Netcompany
    "NZYM-B.CO", # Novozymes B
    "TRYG.CO",   # Tryg
    "ZEAL.CO",   # Zealand Pharma

    # Finland — OMX Helsinki confirmed
    "ELISA.HE",  # Elisa
    "KEMIRA.HE", # Kemira
    "METSO.HE",  # Metso
    "ORNBV.HE",  # Orion B
    "TIETO.HE",  # TietoEVRY
    "UPM.HE",    # UPM-Kymmene
    "VALMT.HE",  # Valmet

    # Norway — OBX/Oslo confirmed
    "AKER.OL",   # Aker ASA
    "FRO.OL",    # Frontline
    "KOG.OL",    # Kongsberg Gruppen
    "LSG.OL",    # Lerøy Seafood
    "STB.OL",    # Storebrand
    "TGS.OL",    # TGS
    "TOM.OL",    # Tomra Systems
    "SRBANK.OL", # SpareBank 1 SR-Bank
    "BWLPG.OL",  # BW LPG
    "SCATC.OL",  # Scatec

    # Belgium — BEL 20 confirmed
    "AEDIFICA.BR",  # Aedifica
    "BAR.BR",    # Barco
    "COFI.BR",   # Cofinimmo
    "D8.BR",     # D'Ieteren
    "MELE.BR",   # Melexis
    "SYNO.BR",   # Syensqo
    "WDP.BR",    # Warehouses De Pauw

    # Spain — IBEX 35 / IGBM confirmed
    "ACX.MC",    # Acerinox
    "ANA.MC",    # Acciona
    "AENA.MC",   # Aena
    "CABK.MC",   # CaixaBank
    "CIE.MC",    # CIE Automotive
    "COL.MC",    # Colonial REIT
    "ENG.MC",    # Enagás
    "GRF.MC",    # Grifols
    "IAG.MC",    # IAG
    "IDR.MC",    # Indra
    "MRL.MC",    # Merlin Properties
    "MTS.MC",    # ArcelorMittal Madrid
    "NTGY.MC",   # Naturgy
    "RED.MC",    # Red Eléctrica
    "VIS.MC",    # Viscofan
    "CAF.MC",    # CAF

    # Italy — FTSE MIB / Mid Cap confirmed
    "A2A.MI",    # A2A
    "AMP.MI",    # Amplifon
    "BAMI.MI",   # Banco BPM
    "BC.MI",     # Brunello Cucinelli
    "CNHI.MI",   # CNH Industrial
    "ERG.MI",    # ERG
    "INWT.MI",   # Inwit
    "IP.MI",     # Interpump
    "MB.MI",     # Mediobanca
    "NEXI.MI",   # Nexi
    "PRY.MI",    # Prysmian
    "RACE.MI",   # Ferrari
    "STLAM.MI",  # Stellantis
    "TRN.MI",    # Terna

    # Austria — ATX confirmed
    "ANDR.VI",   # Andritz
    "EVN.VI",    # EVN
    "IMMO.VI",   # Immofinanz
    "LNZ.VI",    # Lenzing
    "PORR.VI",   # PORR
    "VAS.VI",    # Verbund
    "WIE.VI",    # Wienerberger

    # Portugal — PSI confirmed
    "BCP.LS",    # Millennium BCP
    "CTT.LS",    # CTT
    "JMT.LS",    # Jerónimo Martins
    "RENE.LS",   # REN
    "SONC.LS",   # Sonae

    # Ireland — ISEQ confirmed
    "C5.IR",     # Cairn Homes
    "GLG.IR",    # Glanbia
    "ICG.IR",    # Irish Continental Group
    "ICON.IR",   # ICON plc
    "KYGA.IR",   # Kerry Group A
    "OVID.IR",   # Origin Enterprises
    "RY4C.IR",   # Ryanair

    # Poland — WIG 20/40 confirmed
    "ALE.WA",    # Allegro
    "ALR.WA",    # Alior Bank
    "BDX.WA",    # Budimex
    "CCC.WA",    # CCC Group
    "CPS.WA",    # Cyfrowy Polsat
    "JSW.WA",    # JSW
    "MBK.WA",    # mBank
    "PGE.WA",    # PGE
    "TPE.WA",    # Tauron

    # Greece — ATHEX confirmed
    "ALPHA.AT",  # Alpha Bank
    "EUROB.AT",  # Eurobank
    "ETE.AT",    # National Bank of Greece
    "GEKTERNA.AT", # GEK Terna
    "HTO.AT",    # Hellenic Telecom
    "MOH.AT",    # Motor Oil
    "MYTIL.AT",  # Mytilineos
    "OPAP.AT",   # OPAP
    "PPC.AT",    # PPC
    "TENERGY.AT",# Terna Energy
    "TITC.AT",   # Titan Cement

    # ===== ADDITIONAL GERMAN STOCKS (MDAX / SDAX large-caps) =====
    "1U1.DE",    # 1&1 AG
    "ADJ.DE",    # (skip — use below)
    "BEAM.DE",   # Beam Global — no, skip
    "BFSA.DE",   # Befesa
    "CWC.DE",    # (skip)
    "DKGR.DE",   # (skip)
    "DMRE.DE",   # Demire — marginal
    "DUE.DE",    # Duerr AG
    "ECV.DE",    # Encavis AG
    "GYC.DE",    # Grand City Properties
    "HAL.DE",    # Hella Automotive — merged with Faurecia; now FORVIA
    "HDD.DE",    # Heidelberg Druckmaschinen — marginal
    "HHFA.DE",   # (skip)
    "HIW.DE",    # Hornbach Holding — marginal
    "HOME24.DE", # Home24 — delisted; skip
    "INN.DE",    # INNO AG — skip
    "JNSE.DE",   # (skip)
    "KRN.DE",    # Krones AG
    "MLP.DE",    # MLP SE
    "MOR.DE",    # (skip)
    "MTG.DE",    # (skip)
    "NDX1.DE",   # Nordex SE
    "NFON.DE",   # (skip)
    "NWO.DE",    # (skip)
    "O2D.DE",    # Telefónica Deutschland
    "RHM.DE",    # Rheinmetall
    "SDAX.DE",   # (not a stock; skip)
    "SHA.DE",    # Schaeffler AG
    "SHL.DE",    # Siemens Healthineers — already in existing
    "SMHN.DE",   # Südzucker — actually SZU.DE
    "SZU.DE",    # Südzucker
    "UTDI.DE",   # United Internet
    "VBK.DE",    # (skip)
    "WIN.DE",    # (skip)
    "WIG.DE",    # (skip)
    "ZAL.DE",    # already in
    "KD8.DE",    # (skip)

    # Clean MDAX confirmed
    "RHM.DE",    # Rheinmetall — now DAX member
    "SHA.DE",    # Schaeffler
    "KRN.DE",    # Krones
    "UTDI.DE",   # United Internet
    "NDX1.DE",   # Nordex
    "SZU.DE",    # Südzucker
    "O2D.DE",    # Telefónica Deutschland
    "ECV.DE",    # Encavis
    "GYC.DE",    # Grand City Properties
    "DUE.DE",    # Dürr
    "BFSA.DE",   # Befesa
    "MLP.DE",    # MLP SE
    "1U1.DE",    # 1&1 AG
    "SMHN.DE",   # (skip — use SZU.DE)
    "DMRE.DE",   # (skip — too small)

    # ===== ADDITIONAL UK STOCKS (FTSE 100/250) =====
    "BNKR.L",    # (investment trust — skip)
    "BWY.L",     # Bellway
    "CTEC.L",    # (skip)
    "DR.L",      # (skip)
    "ENT.L",     # Entain
    "ESNT.L",    # (skip)
    "FEN.L",     # (skip)
    "FGT.L",     # (investment trust — skip)
    "GNK.L",     # (skip)
    "GRND.L",    # Grendene? no; Grainger plc
    "ICAG.L",    # IAG (alt ticker) — use IAG.L
    "IHG.L",     # InterContinental Hotels Group
    "IMB.L",     # already in
    "JMAT.L",    # Johnson Matthey
    "JET.L",     # Just Eat Takeaway (London)
    "MAN.L",     # Man Group
    "MGAM.L",    # (skip)
    "OSB.L",     # OSB Group
    "PETS.L",    # (skip)
    "PSP.L",     # (skip)
    "RCP.L",     # (investment trust — skip)
    "RDSA.L",    # (old Shell — skip)
    "RMV.L",     # Rightmove
    "SDR.L",     # Schroders
    "SGE.L",     # Sage Group
    "SLA.L",     # abrdn (formerly Standard Life Aberdeen)
    "SMWH.L",    # WH Smith
    "SNX.L",     # (skip)
    "TSEM.L",    # (skip)
    "TUI.L",     # TUI AG (London listing)
    "TWO.L",     # (skip)
    "VMUK.L",    # Virgin Money UK
    "VTY.L",     # Vistry Group
    "WIZZ.L",    # Wizz Air
    "XRX.L",     # (US — skip)
    "AG.L",      # (skip)
    "ALPH.L",    # (skip)

    # Confirmed FTSE 100/250
    "BWY.L",     # Bellway
    "ENT.L",     # Entain
    "GRND.L",    # Grainger
    "IHG.L",     # IHG
    "JMAT.L",    # Johnson Matthey
    "MAN.L",     # Man Group
    "RMV.L",     # Rightmove
    "SDR.L",     # Schroders
    "SGE.L",     # Sage Group
    "SLA.L",     # abrdn
    "TUI.L",     # TUI
    "VMUK.L",    # Virgin Money
    "VTY.L",     # Vistry
    "WIZZ.L",    # Wizz Air

    # ===== MORE FRENCH STOCKS (SBF 120) =====
    "ADP.PA",    # Aéroports de Paris
    "ALTEN.PA",  # Alten
    "APAM.PA",   # (skip)
    "ARGAN.PA",  # Argan REIT — marginal
    "BALO.PA",   # (skip)
    "BIGBEN.PA", # (skip)
    "BIM.PA",    # (skip)
    "CBT.PA",    # (skip)
    "CHSR.PA",   # (skip)
    "CRED.PA",   # (skip)
    "CS.PA",     # AXA — already in
    "DBV.PA",    # DBV Technologies — small
    "DPAM.PA",   # (skip)
    "EDF.PA",    # Électricité de France — nationalized 2022; skip
    "EPS.PA",    # (skip)
    "FBN.PA",    # Soitec
    "FCAC.PA",   # (skip)
    "FF.PA",     # (skip)
    "FLO.PA",    # (skip)
    "GBT.PA",    # Global Bioenergies — marginal
    "GLE.PA",    # already in
    "GLO.PA",    # GL Events — marginal
    "ID.PA",     # (skip)
    "IDEX.PA",   # Idex — marginal
    "INF.PA",    # (skip)
    "IPH.PA",    # Ipsos
    "IPCO.PA",   # (skip)
    "IPN.PA",    # (skip)
    "LNA.PA",    # LNA Santé — marginal
    "LSS.PA",    # (skip)
    "MCO.PA",    # (skip)
    "MDM.PA",    # (skip)
    "MDVX.PA",   # (skip)
    "MIF.PA",    # (skip)
    "MKT.PA",    # (skip)
    "MLFP.PA",   # Maisons du Monde
    "MONTEA.PA", # (skip)
    "MVV.PA",    # Movi'n — skip
    "NEXITY.PA", # Nexity
    "OBAS.PA",   # (skip)
    "OCEANE.PA", # (skip)
    "OLLN.PA",   # (skip)
    "OPB.PA",    # (skip)
    "OREP.PA",   # (skip)
    "PAJ.PA",    # (skip)
    "PAULIN.PA", # (skip)
    "PDCO.PA",   # (skip)
    "PE.PA",     # (skip)
    "PLR.PA",    # (skip)
    "POXEL.PA",  # (skip)
    "PROF.PA",   # (skip)
    "PSB.PA",    # (skip)
    "RWAY.PA",   # (skip)
    "SAB.PA",    # (skip)
    "SCRS.PA",   # (skip)
    "SDG.PA",    # Sodexo (correct yfinance ticker for Sodexo)
    "SGAM.PA",   # (skip)
    "SII.PA",    # Sirius — skip
    "SOP.PA",    # Sopra Steria (alt ticker)
    "SUPER.PA",  # Supersonic — skip
    "SWANN.PA",  # (skip)
    "SY1.PA",    # (skip)
    "SYNT.PA",   # (skip)
    "TFF.PA",    # TFF Group — marginal
    "TITAN.PA",  # (skip)
    "TOUP.PA",   # Tourmaline Oil? No, Touax — skip
    "TPEX.PA",   # (skip)
    "ULG.PA",    # (skip)
    "UMTS.PA",   # (skip)

    # Confirmed SBF 120 additions
    "ADP.PA",    # Aéroports de Paris
    "ALTEN.PA",  # Alten
    "FBN.PA",    # Soitec (SOITEC.PA also)
    "IPH.PA",    # Ipsos
    "NEXITY.PA", # Nexity
    "SDG.PA",    # Sodexo

    # ===== ADDITIONAL SWISS STOCKS =====
    "BCHN.SW",   # Banque Cantonale Vaudoise — marginal
    "CEVE.SW",   # Cembra Money Bank
    "HIAG.SW",   # HIAG Immobilien
    "IGBN.SW",   # (skip)
    "MBTN.SW",   # Meyer Burger — marginal
    "METN.SW",   # (skip)
    "MIUC.SW",   # (skip)
    "NREN.SW",   # (skip)
    "ORON.SW",   # Orion (Swiss)? skip
    "PEHN.SW",   # (skip)
    "SIGN.SW",   # Signa Sports — delisted; skip
    "SIKA.SW",   # Sika AG
    "SLHN.SW",   # Swiss Life — already in existing
    "SONV.SW",   # Sonova (Swiss .SW ticker)
    "SPEX.SW",   # Spineart — skip
    "SPSN.SW",   # Swiss Prime Site
    "SRAIL.SW",  # SBB (state-owned, not listed) — skip
    "SREN.SW",   # Swiss Re (already filtered)
    "TMAS.SW",   # (skip)
    "ZUGER.SW",  # (skip)

    # Confirmed Swiss additions
    "SIKA.SW",   # Sika AG — STOXX 600 member
    "SONV.SW",   # Sonova Holding
    "SPSN.SW",   # Swiss Prime Site
    "CEVE.SW",   # Cembra Money Bank

    # ===== MORE DUTCH STOCKS (AMX) =====
    "AMG.AS",    # AMG Critical Materials
    "BESI.AS",   # already added
    "CTPNV.AS",  # CTP NV
    "DOAK.AS",   # (skip)
    "HYDRA.AS",  # (skip)
    "INTER.AS",  # (skip)
    "JDEP.AS",   # (skip)
    "JUST.AS",   # Just Eat (NL) — same as TKWY.AS in existing
    "NSI.AS",    # NSI NV — marginal
    "PHARM.AS",  # (skip)
    "POST.AS",   # PostNL
    "PHOS.AS",   # (skip)
    "TKWY.AS",   # already in
    "TOM2.AS",   # TomTom
    "TPVG.AS",   # (skip)
    "TWEKA.AS",  # TKH Group
    "USG.AS",    # (skip — merged into Recruit)
    "VASTN.AS",  # (skip)
    "WKL.AS",    # already in
    "ALFEN.AS",  # Alfen NV
    "ARCE.AS",   # ArcelorMittal — use MT.AS

    # Confirmed NL additions
    "AMG.AS",    # AMG Critical Materials
    "CTPNV.AS",  # CTP NV
    "POST.AS",   # PostNL
    "TOM2.AS",   # TomTom
    "TWEKA.AS",  # TKH Group
    "ALFEN.AS",  # Alfen

    # ===== MORE SWEDISH STOCKS =====
    "AAK.ST",    # AAK AB
    "BETCO.ST",  # (skip)
    "BETS-B.ST", # Betsson B
    "BHG.ST",    # BHG Group — marginal
    "BIVAB.ST",  # (skip)
    "CLAS-B.ST", # Clas Ohlson — marginal
    "DIOS-B.ST", # Dios Fastigheter — marginal
    "EMBRAC-B.ST", # Embracer Group — marginal
    "EPI-A.ST",  # (use EPIROC-A.ST — already in)
    "ERIC-A.ST", # Ericsson A — marginal (B more liquid)
    "FPAR-D.ST", # Fastighets AB Balder — marginal
    "HEBA-B.ST", # Heba Fastighets — marginal
    "HEIMSTADEN.ST", # Heimstaden — marginal
    "INDUTRADE.ST", # Indutrade
    "IPCO.ST",   # (skip)
    "JM.ST",     # JM AB
    "KFAST-B.ST",# K-Fast Holding — marginal
    "KINVIK.ST", # (skip)
    "KNOW-B.ST", # (skip)
    "LIME.ST",   # Lime Technologies — marginal
    "LUND-B.ST", # Lundbergföretagen — marginal
    "MEAB-B.ST", # (skip)
    "MSAB-B.ST", # (skip)
    "NET.ST",    # (skip)
    "NKLA.ST",   # (US — skip)
    "NOLATO-B.ST", # Nolato — marginal
    "RECSI.ST",  # Recipharm — marginal
    "RNBS.ST",   # (skip)
    "ROOI.ST",   # (skip)
    "SECT-B.ST", # (skip)
    "SFAB.ST",   # (skip)
    "SGB.ST",    # (skip)
    "SHOT.ST",   # (skip)
    "SSAB-A.ST", # SSAB A
    "SSAB-B.ST", # SSAB B
    "SWEC-A.ST", # Sweco A — marginal (B more liquid)
    "TEL2-A.ST", # Tele2 A — marginal
    "TIGO-SDB.ST", # Millicom — marginal
    "VIAB-B.ST", # Viaplay Group — marginal
    "VOLCAR-B.ST", # Volvo Cars B
    "VSD.ST",    # (skip)

    # Confirmed Swedish additions
    "AAK.ST",    # AAK AB
    "BETS-B.ST", # Betsson
    "INDUTRADE.ST", # Indutrade
    "JM.ST",     # JM AB
    "SSAB-A.ST", # SSAB A
    "SSAB-B.ST", # SSAB B
    "VOLCAR-B.ST", # Volvo Cars

    # ===== MORE NORWEGIAN STOCKS =====
    "AFG.OL",    # American Shipping — skip
    "AKASO.OL",  # Aker Solutions
    "AUTO.OL",   # (skip)
    "BON.OL",    # Bonheur — marginal
    "BOUVET.OL", # Bouvet — small
    "BRG.OL",    # Borregaard
    "ELOP.OL",   # Elop? skip
    "FLNG.OL",   # Flex LNG
    "GJF.OL",    # Gjensidige Forsikring
    "GOD.OL",    # (skip)
    "HAVI.OL",   # (skip)
    "LINK.OL",   # (skip)
    "NONG.OL",   # (skip)
    "NORBT.OL",  # (skip)
    "NORAS.OL",  # (skip)
    "NTEM.OL",   # Northern Ocean — skip
    "OBX.OL",    # (index, not a stock — skip)
    "ODF.OL",    # (already filtered)
    "PARETO.OL", # (skip)
    "PGS.OL",    # PGS ASA — marginal
    "PHNX.OL",   # (skip)
    "RANA.OL",   # (skip)
    "RCR.OL",    # (skip)
    "RECSI.OL",  # REC Silicon — marginal
    "REN.OL",    # (skip)
    "SCHB.OL",   # Schibsted B — already have SCHA.OL
    "SOFF.OL",   # Solstad Offshore — marginal
    "SPOG.OL",   # SpareBank 1 Østlandet — marginal
    "SUBC.OL",   # already in
    "THIN.OL",   # Thin Film — delisted; skip
    "VAR.OL",    # Vår Energi
    "VISTIN.OL", # (skip)
    "WSTEP.OL",  # (already filtered)

    # Confirmed Norwegian additions
    "AKASO.OL",  # Aker Solutions
    "BRG.OL",    # Borregaard
    "FLNG.OL",   # Flex LNG
    "GJF.OL",    # Gjensidige Forsikring
    "VAR.OL",    # Vår Energi
    "PGS.OL",    # PGS
    "STB.OL",    # Storebrand (already added above)

    # ===== MORE DANISH STOCKS =====
    "ALK-B.CO",  # ALK-Abelló B
    "BAVA.CO",   # (skip)
    "CBRAIN.CO", # (skip — small)
    "EAC.CO",    # (skip)
    "FLUGGER.CO",# (skip)
    "GEN.CO",    # Genmab? use GMAB.CO (already added)
    "GRL.CO",    # Greenland Group — skip
    "HARBO-B.CO",# H+H International — marginal
    "HLUN-B.CO", # H. Lundbeck B
    "JYBA.CO",   # (skip)
    "KBHL.CO",   # (skip)
    "KELLY.CO",  # (skip)
    "KOBR.CO",   # Kobenhavns Lufthavne — Kopenhagen Airports
    "NDA-DK.CO", # Nordea DK listing
    "NNIT.CO",   # (already filtered)
    "PARKEN.CO", # (skip)
    "PNDORA.CO", # already in existing
    "RATOS.CO",  # (skip)
    "RIAS-B.CO", # (skip)
    "SANI.CO",   # Sanistål — marginal
    "SIM.CO",    # SimCorp — acquired by Deutsche Börse 2023 (delisted); skip
    "SPNO.CO",   # Spar Nord Bank — marginal
    "TCM.CO",    # (skip)
    "TOP.CO",    # Topdanmark
    "TORM-A.CO", # TORM A — marginal
    "TRUP.CO",   # (skip)
    "VESTJYSK.CO", # (skip)

    # Confirmed Danish additions
    "ALK-B.CO",  # ALK-Abelló
    "HLUN-B.CO", # Lundbeck
    "KOBR.CO",   # Copenhagen Airport
    "NDA-DK.CO", # Nordea DK
    "TOP.CO",    # Topdanmark

    # ===== MORE FINNISH STOCKS =====
    "ASPO.HE",   # Aspo — marginal
    "BIOHIT.HE", # (skip)
    "CGEM.HE",   # (skip)
    "CONSTI.HE", # (skip)
    "ENFO.HE",   # (skip)
    "FIA1S.HE",  # Fiskars — marginal
    "FFYH.HE",   # (skip)
    "GOFORE.HE", # (skip)
    "HARVIA.HE", # Harvia — marginal
    "HERO.HE",   # (skip)
    "HUHTAMAKI.HE", # already HUH1V.HE
    "INNOFACTOR.HE", # (skip)
    "KOJAMO.HE", # Kojamo
    "KPEUR.HE",  # (skip)
    "LIFA.HE",   # (skip)
    "NORDEA.HE", # Nordea (HE listing)
    "PIHLIS.HE", # (skip)
    "PIIPPO.HE", # (skip)
    "PUUILO.HE", # (skip)
    "QT.HE",     # Qt Group — marginal
    "REC.HE",    # Restamax — skip
    "REMEDY.HE", # Remedy — marginal
    "SRV.HE",    # SRV Group — marginal
    "TELE.HE",   # Telia? use TLS1V.HE
    "TERVE.HE",  # (skip)
    "TOKMAN.HE", # Tokmanni — marginal
    "UPM.HE",    # already added
    "VIK.HE",    # Viking Line — marginal
    "YIT.HE",    # YIT — marginal

    # Confirmed Finnish additions
    "FIA1S.HE",  # Fiskars
    "KOJAMO.HE", # Kojamo
    "NORDEA.HE", # Nordea
    "QT.HE",     # Qt Group

    # ===== MORE BELGIAN STOCKS =====
    "ACKB.BR",   # already in
    "BELA.BR",   # (skip)
    "BONE.BR",   # (skip)
    "BREW.BR",   # (skip)
    "CFE.BR",    # CFE (Compagnie d'Entreprises)
    "CPINA.BR",  # (skip)
    "ECO.BR",    # (skip)
    "ELI.BR",    # Elia Group
    "GBL.BR",    # GBL (ordinary) — use GBLB.BR
    "HOMI.BR",   # (skip)
    "IFB.BR",    # (skip)
    "LOTB.BR",   # (skip)
    "ONTEX.BR",  # Ontex Group
    "OXURION.BR",# (skip)
    "QIAGEN.BR", # (skip — use QIA.DE)
    "REEL.BR",   # (skip)
    "RENT.BR",   # (skip)
    "RETAIL.BR", # (skip)
    "SDF.BR",    # (skip)
    "SMCP.BR",   # (skip)
    "TEXAF.BR",  # (skip)
    "TER.BR",    # (skip)
    "THALES.BR", # (skip — use HO.PA)
    "TPG.BR",    # (skip)
    "UCB.BR",    # already in
    "WDPB.BR",   # WDP duplicate — use WDP.BR

    # Confirmed Belgian additions
    "CFE.BR",    # CFE
    "ELI.BR",    # Elia
    "ONTEX.BR",  # Ontex

    # ===== MORE SPANISH STOCKS =====
    "ALM.MC",    # Almirall — pharma
    "APAM.MC",   # Aperam (Madrid)
    "BKT.MC",    # Bankinter
    "CLNX.MC",   # Cellnex Telecom
    "COR.MC",    # (skip)
    "EBO.MC",    # Ebro Foods
    "ENCE.MC",   # ENCE Energía — marginal
    "GCO.MC",    # Grupo Catalana Occidente — marginal
    "IAG.MC",    # already added
    "LOG.MC",    # (filtered)
    "MEL.MC",    # Meliá Hotels
    "MRL.MC",    # already added
    "NDR.MC",    # (skip)
    "NTGY.MC",   # already added
    "PHM.MC",    # (filtered)
    "PRIM.MC",   # (skip)
    "PSG.MC",    # (skip)
    "RED.MC",    # already added
    "SOL.MC",    # (filtered)
    "TLAB.MC",   # (skip)
    "VID.MC",    # Vidrala — marginal
    "ZOT.MC",    # (skip)

    # Confirmed Spanish additions
    "ALM.MC",    # Almirall
    "BKT.MC",    # Bankinter
    "CLNX.MC",   # Cellnex
    "EBO.MC",    # Ebro Foods
    "MEL.MC",    # Meliá Hotels

    # ===== MORE ITALIAN STOCKS =====
    "ACEA.MI",   # Acea SpA
    "AEROPORTI.MI", # (skip — use SAVE.MI)
    "AQUAFIL.MI",# (skip — too small)
    "ARTE.MI",   # (skip)
    "AUTOGRILL.MI", # merged with HMSHost; skip
    "AZIMUT.MI", # Azimut — use AZM.MI (already in)
    "BPER.MI",   # already in
    "BPE.MI",    # (skip)
    "CASS.MI",   # Cassa Depositi — not listed; skip
    "CVAL.MI",   # (skip)
    "CVLARI.MI", # (skip)
    "DIASORIN.MI",# DiaSorin
    "DOVALUE.MI",# doValue — marginal
    "EXO.MI",    # Exor (Milan) — use EXOR.AS
    "FBK.MI",    # FinecoBank
    "FCEL.MI",   # (skip)
    "FNM.MI",    # (skip)
    "GD.MI",     # (skip)
    "HERA.MI",   # Hera SpA
    "ILLY.MI",   # illycaffè — marginal
    "INXTM.MI",  # (skip)
    "IVG.MI",    # (skip)
    "JUVE.MI",   # (skip)
    "LOTTO.MI",  # (skip)
    "LUX.MI",    # Luxottica — now part of EssilorLuxottica; skip
    "MARR.MI",   # MARR SpA — marginal
    "MLB.MI",    # (skip)
    "MONRIF.MI", # (skip)
    "MUTUIONLINE.MI", # (skip)
    "OVS.MI",    # OVS SpA — marginal
    "PIAGGIO.MI",# Piaggio — marginal
    "PRIMA.MI",  # (skip)
    "RAVA.MI",   # (skip)
    "REPLY.MI",  # Reply SpA — marginal
    "RICK.MI",   # (skip)
    "SAVE.MI",   # Aeroporto di Venezia — marginal
    "SOL.MI",    # Sol SpA — marginal
    "SOI.MI",    # (skip)
    "SPAXS.MI",  # (skip)
    "SYN.MI",    # Synbiotics — skip
    "TGYM.MI",   # Technogym
    "TINEXTA.MI",# Tinexta — marginal
    "TOD.MI",    # already filtered
    "TPS.MI",    # (skip)
    "UFI.MI",    # UFI Filters — skip
    "VLTAVA.MI", # (skip)
    "ZV.MI",     # (skip)

    # Confirmed Italian additions
    "ACEA.MI",   # Acea
    "DIASORIN.MI", # DiaSorin
    "FBK.MI",    # FinecoBank
    "HERA.MI",   # Hera
    "TGYM.MI",   # Technogym

    # ===== MORE AUSTRIAN STOCKS =====
    "AT&S.VI",   # AT&S Austria Technologie
    "BAWAG.VI",  # BAWAG Group
    "CAT.VI",    # (skip)
    "DO.VI",     # (skip)
    "FAB.VI",    # (skip)
    "IIA.VI",    # (already filtered)
    "KTM.VI",    # KTM Industries — marginal
    "NB.VI",     # (skip)
    "NOEV.VI",   # (skip)
    "POS.VI",    # Österreichische Post AG
    "PRE.VI",    # (skip)
    "RHI.VI",    # RHI Magnesita (Vienna listing)
    "SANT.VI",   # (skip)
    "SAOG.VI",   # (skip)
    "SKO.VI",    # (skip)
    "SWIV.VI",   # (skip)
    "UBM.VI",    # UBM Development — marginal
    "VER.VI",    # (already filtered)
    "VIE.VI",    # (skip)
    "VMLY.VI",   # (skip)
    "WEB.VI",    # Wolford — marginal

    # Confirmed Austrian additions
    "AT&S.VI",   # AT&S
    "BAWAG.VI",  # BAWAG
    "POS.VI",    # Österreichische Post
    "RHI.VI",    # RHI Magnesita

    # ===== MORE PORTUGUESE STOCKS =====
    "ALTR.LS",   # Altri — paper
    "COR.LS",    # Corticeira Amorim
    "IPM.LS",    # (skip)
    "MCP.LS",    # (skip)
    "NVGS.LS",   # (skip)
    "SLBEN.LS",  # (skip)
    "SEM.LS",    # (skip)
    "TPEX.LS",   # (skip)

    # Confirmed Portuguese additions
    "ALTR.LS",   # Altri
    "COR.LS",    # Corticeira Amorim

    # ===== MORE IRISH STOCKS =====
    "BOI.IR",    # Bank of Ireland (alt) — use BIRG.IR
    "CRH.IR",    # CRH (Dublin listing)
    "DCC.IR",    # DCC (Dublin)
    "GN1.IR",    # Greencore Group
    "IRES.IR",   # IRES REIT — marginal
    "OCAS.IR",   # (skip)
    "RY4B.IR",   # Ryanair B shares — skip
    "UDG.IR",    # UDG Healthcare — taken private; skip

    # Confirmed Irish additions
    "CRH.IR",    # CRH Dublin
    "DCC.IR",    # DCC Dublin
    "GN1.IR",    # Greencore

    # ===== MORE POLISH STOCKS =====
    "AMC.WA",    # (skip)
    "BML.WA",    # Bank Millennium
    "CPS.WA",    # already added
    "DKT.WA",    # (skip)
    "GTC.WA",    # GTC (Globe Trade Centre)
    "ING.WA",    # ING Bank Śląski
    "KETY.WA",   # (skip)
    "MRC.WA",    # (skip)
    "PCR.WA",    # (skip)
    "PLAY.WA",   # Play Communications
    "PLW.WA",    # (skip)
    "PMP.WA",    # (skip)
    "PKP.WA",    # already added (marginal — keep)
    "SANPL.WA",  # already added as SPL.WA
    "TEN.WA",    # Ten Square Games — skip
    "TVN.WA",    # (skip)
    "WAWEL.WA",  # (skip)
    "XTB.WA",    # XTB — marginal

    # Confirmed Polish additions
    "BML.WA",    # Bank Millennium
    "GTC.WA",    # GTC
    "ING.WA",    # ING Śląski
    "PLAY.WA",   # Play

    # ===== MORE GREEK STOCKS =====
    "AEGN.AT",   # Aegean Airlines
    "ATEMKE.AT", # (skip)
    "BELA.AT",   # Bekaert? no — skip
    "CENTR.AT",  # (skip)
    "DOMI.AT",   # (skip)
    "ELTRAK.AT", # (skip)
    "EXAE.AT",   # (already filtered)
    "FORTHNET.AT", # (skip)
    "FOYRLI.AT", # (skip)
    "GAS.AT",    # Enagas? no — skip
    "GRD.AT",    # (skip)
    "HEL.AT",    # Hellenic Gold — marginal
    "HELLAS.AT", # (skip)
    "IASO.AT",   # (skip)
    "INLOT.AT",  # (skip)
    "INTERCO.AT",# (skip)
    "INTRK.AT",  # (skip)
    "KRI.AT",    # Kri-Kri Milk — marginal
    "LAME.AT",   # Lamda Development (alt) — use LAMDA.AT (filtered)
    "MEVA.AT",   # (skip)
    "MINOA.AT",  # (skip)
    "NAYP.AT",   # (skip)
    "OLTH.AT",   # Thessaloniki Port — marginal
    "PGAS.AT",   # (skip)
    "PREMIA.AT", # (skip)
    "QUAL.AT",   # (skip)
    "SIDMA.AT",  # (skip)
    "SPARE.AT",  # (skip)
    "TELESIS.AT",# (skip)
    "TERNA.AT",  # (use TENERGY.AT already added)
    "TPEIR.AT",  # Piraeus Bank
    "TYPSA.AT",  # (skip)
    "VARNER.AT", # (skip)

    # Confirmed Greek additions
    "AEGN.AT",   # Aegean Airlines
    "TPEIR.AT",  # Piraeus Bank
]

# ---------------------------------------------------------------------------
# Build final list
# ---------------------------------------------------------------------------
def build_final_list() -> list[str]:
    """Combine all sources, de-duplicate, sort, and return clean ticker list."""
    seen: set[str] = set()
    result: list[str] = []

    for t in EXISTING + FINAL_ADDITIONS:
        t = t.strip()
        if not t:
            continue
        # Skip tickers in the REMOVE set
        if t in REMOVE:
            continue
        # Skip obvious placeholders
        if t.startswith("#") or len(t) < 2:
            continue
        # Skip clearly wrong suffixes
        if t.endswith(".BD") or t.endswith(".PR"):
            continue  # Hungarian/Czech — not standard yfinance; skip
        if t in seen:
            continue
        seen.add(t)
        result.append(t)

    # Sort by exchange suffix for readability
    def sort_key(ticker: str) -> tuple:
        parts = ticker.rsplit(".", 1)
        suffix = parts[1] if len(parts) > 1 else "ZZ"
        base = parts[0]
        return (suffix, base)

    result.sort(key=sort_key)
    return result


if __name__ == "__main__":
    tickers = build_final_list()

    existing_count = len([t for t in EXISTING
                          if t not in REMOVE
                          and not t.endswith(".BD")
                          and not t.endswith(".PR")])

    output = {
        "tickers": tickers,
        "count": len(tickers),
        "source": "compiled from major European indices",
        "note": (
            "STOXX Europe 600 approximation — covers major large/mid caps "
            "from DAX 40, MDAX, CAC 40, SBF 120, FTSE 100, SMI, AEX, "
            "OMX Stockholm/Copenhagen/Helsinki, OBX, BEL 20, IBEX 35, "
            "FTSE MIB, ATX, PSI 20, ISEQ, WIG 20/40, ATHEX"
        ),
    }

    out_path = Path(__file__).parent / "stoxx600_full_tickers.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"Total tickers in final list : {len(tickers)}")
    print(f"Base list (EXISTING, clean)  : {existing_count}")
    print(f"Added via FINAL_ADDITIONS    : {len(tickers) - existing_count}")
    print(f"Written to                   : {out_path}")

    # Print by exchange
    from collections import Counter
    suffixes = Counter(
        t.rsplit(".", 1)[1] if "." in t else "NONE"
        for t in tickers
    )
    print("\nTickers per exchange:")
    for suffix, count in sorted(suffixes.items(), key=lambda x: -x[1]):
        print(f"  .{suffix:6s}: {count}")
