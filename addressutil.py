"""
Contains various utilities for handling addresses in the United States. Requires Python 3.8 or newer.

### Quick start
To quickly get the cleaned-up version of an address, you can do
```
>>> import addressutil
>>> str(addressutil.Address.parse("123 MAIN ST.", "SPRINGFIELD IL 12345-6789"))
'123 MAIN ST\nSPRINGFIELD IL 12345-6789'
```
You can also work with Address objects directly, which are comparable. This is the preferred way to represent addresses.
```
>>> import addressutil
>>> addressutil.Address.parse("123 N.W. MAIN ST.", "SPRINGFIELD IL 12345-6789") == addressutil.Address.parse("123 NW MAIN STREET", "SPRINGFIELD IL 12345-6789")
True
```
The function `addressutil.Address.parse()` takes two arguments: the delivery address itself and the last line of the address (where the city, state, and ZIP
code are usually written). The outputted string separates the delivery address and the last line with a newline, just like how it would be written on an
envelope.
"""

from __future__ import annotations
import enum
import re
from typing import Optional

DIRECTIONS_LIST: tuple[str, ...] = ("N", "E", "S", "W", "NW", "NE", "SE", "SW", "NORTH", "EAST", "SOUTH", "WEST", "NORTHWEST", "NORTHEAST", "SOUTHEAST", "SOUTHWEST")
"""The 8 directions accepted by USPS, together with their spelled-out variants"""

DIRECTIONS_MAPPING: dict[str, str] = {"NORTH": "N", "EAST": "E", "SOUTH": "S", "WEST": "W", "NORTHWEST": "NW", "NORTHEAST": "NE", "SOUTHEAST": "SE", "SOUTHWEST": "SW"}
"""Dictionary to convert spelled-out directions to USPS-preferred directions"""

HIGHWAY_MAPPING: dict[str, str] = {"COUNTY HIGHWAY": "COUNTY HIGHWAY", "COUNTY HWY": "COUNTY HIGHWAY", "CNTY HWY": "COUNTY HIGHWAY", "COUNTY HWY": "COUNTY HIGHWAY", "COUNTY ROAD": "COUNTY ROAD", "COUNTY RD": "COUNTY ROAD", "CR": "COUNTY ROAD", "CNTY ROAD": "COUNTY ROAD", "CNTY RD": "COUNTY ROAD", "EXPRESSWAY": "EXPRESSWAY", "EXP": "EXPRESSWAY", "EXPR": "EXPRESSWAY", "EXPRESS": "EXPRESSWAY", "EXPW": "EXPRESSWAY", "EXPY": "EXPRESSWAY", "FARM TO MARKET": "FM", "FM": "FM", "HWY FM": "FM", "HWY": "HIGHWAY", "HIWAY": "HIGHWAY", "IH": "INTERSTATE", "INTERSTATE": "INTERSTATE", "INTERSTATE HWY": "INTERSTATE", "INTERSTATE HIGHWAY": "INTERSTATE", "LOOP": "LOOP", "RD": "ROAD", "RT": "ROUTE", "RTE": "ROUTE", "RANCH RD": "RANCH ROAD", "ST HIGHWAY": "STATE HIGHWAY", "STATE HWY": "STATE HIGHWAY", "STATE HIGHWAY": "STATE HIGHWAY", "ST HWY": "STATE HIGHWAY", "SH": "STATE HIGHWAY", "SR": "STATE ROAD", "ST RD": "STATE ROAD", "ST ROAD": "STATE ROAD", "STATE ROAD": "STATE ROAD", "ST RT": "STATE ROUTE", "STATE RT": "STATE ROUTE", "ST ROUTE": "STATE ROUTE", "ST RTE": " STATE ROUTE", "STATE RTE": "STATE ROUTE", "TOWNSHIP RD": "TOWNSHIP ROAD", "TSR": "TOWNSHIP ROAD", "US": "US HIGHWAY", "US HWY": "US HIGHWAY", "US HIGHWAY": "US HIGHWAY"}
"""Dictionary to standardize highway names"""

SECONDARY_UNIT_INDICATORS: tuple[str, ...] = ("APARTMENT", "APT", "BASEMENT", "BSMT", "BUILDING", "BLDG", "DEPARTMENT", "DEPT", "FLOOR", "FL", "FRONT", "FRNT", "HANGER", "HANGAR", "HNGR", "KEY", "LOBBY", "LBBY", "LOT", "LOWER", "LOWR", "OFFICE", "OFC", "PENTHOUSE", "PH", "PIER", "REAR", "ROOM", "RM", "SIDE", "SPACE", "SPC", "STOP", "SUITE", "STE", "TRAILER", "TRLR", "UNIT", "UPPER", "UPPR")
"""USPS Indicators for a secondary unit (address line 2)"""
# List formerly contained "SLIP", but this caused breakage.

STATE_NAME_MAPPING: dict[str, str] = {"ALABAMA": "AL", "ALASKA": "AK", "AMERICAN SAMOA": "AS", "ARIZONA": "AZ", "ARKANSAS": "AR", "BAKER ISLAND": "BI", "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE", "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL", "FEDERATED STATES OF MICRONESIA": "FM", "GEORGIA": "GA", "GUAM": "GU", "HAWAII": "HI", "HOWLAND ISLAND": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "JARVIS ISLAND": "JI", "JOHNSTON ATOLL": "JA", "KANSAS": "KS", "KENTUCKY": "KY", "KINGMAN REEF": "KR", "LOUISIANA": "LA", "MAINE": "ME", "MARSHALL ISLANDS": "MH", "MARYLAND": "MD", "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MIDWAY ISLANDS": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO", "MONTANA": "MT", "NAVASSA ISLAND": "NI", "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "NORTHERN MARIANA ISLANDS": "MP", "OHIO": "OH", "OKLAHOMA": "OK", "OREGON": "OR", "PALAU": "PW", "PALMYRA ATOLL": "PA", "PENNSYLVANIA": "PA", "PUERTO RICO": "PR", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "U.S. MINOR OUTLYING ISLANDS": "UM", "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "VIRGIN ISLANDS OF THE U.S.": "VI", "WAKE ISLAND": "WI", "WASHINGTON": "WA", "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",}
"""Mapping of state names to abbreviations"""

STREET_SUFFIXES: tuple[str, ...] = ("ALLEE", "ALLEY", "ALLY", "ALY", "ANEX", "ANNEX", "ANNX", "ANX", "ARC ", "ARCADE ", "AV", "AVE", "AVEN", "AVENU", "AVENUE", "AVN", "AVNUE", "BAYOO", "BAYOU", "BCH", "BEACH", "BEND", "BND", "BLF", "BLUF", "BLUFF", "BLUFFS ", "BOT", "BTM", "BOTTM", "BOTTOM", "BLVD", "BOUL", "BOULEVARD ", "BOULV", "BR", "BRNCH", "BRANCH", "BRDGE", "BRG", "BRIDGE", "BRK", "BROOK", "BROOKS ", "BURG", "BURGS", "BYP", "BYPA", "BYPAS", "BYPASS", "BYPS", "CAMP", "CP", "CMP", "CANYN", "CANYON", "CNYN", "CAPE", "CPE", "CAUSEWAY", "CAUSWA", "CSWY", "CEN", "CENT", "CENTER", "CENTR", "CENTRE", "CNTER", "CNTR", "CTR", "CENTERS ", "CIR", "CIRC", "CIRCL", "CIRCLE", "CRCL", "CRCLE", "CIRCLES", "CLF", "CLIFF", "CLFS", "CLIFFS", "CLB", "CLUB", "COMMON", "COMMONS", "COR", "CORNER", "CORNERS", "CORS", "COURSE", "CRSE", "COURT", "CT", "COURTS", "CTS", "COVE", "CV", "COVES", "CREEK", "CRK", "CRESCENT", "CRES", "CRSENT", "CRSNT", "CREST", "CROSSING ", "CRSSNG ", "XING ", "CROSSROAD", "CROSSROADS", "CURVE ", "DALE ", "DL ", "DAM ", "DM ", "DIV", "DIVIDE", "DV", "DVD", "DR", "DRIV", "DRIVE", "DRV", "DRIVES", "EST", "ESTATE", "ESTATES", "ESTS", "EXP", "EXPR", "EXPRESS", "EXPRESSWAY", "EXPW", "EXPY", "EXT", "EXTENSION", "EXTN", "EXTNSN", "EXTS", "FALL", "FALLS", "FLS", "FERRY", "FRRY", "FRY", "FIELD", "FLD", "FIELDS", "FLDS", "FLAT", "FLT", "FLATS", "FLTS", "FORD", "FRD", "FORDS", "FOREST", "FORESTS", "FRST", "FORG", "FORGE", "FRG", "FORGES", "FORK", "FRK", "FORKS", "FRKS", "FORT", "FRT", "FT", "FREEWAY", "FREEWY", "FRWAY", "FRWY", "FWY", "GARDEN", "GARDN", "GRDEN", "GRDN", "GARDENS", "GDNS", "GRDNS", "GATEWAY", "GATEWY", "GATWAY", "GTWAY", "GTWY", "GLEN", "GLN", "GLENS", "GREEN", "GRN", "GREENS", "GROV", "GROVE", "GRV", "GROVES", "HARB", "HARBOR", "HARBR", "HBR", "HRBOR", "HARBORS", "HAVEN", "HVN", "HT", "HTS", "HIGHWAY", "HIGHWY", "HIWAY", "HIWY", "HWAY", "HWY", "HILL", "HL", "HILLS", "HLS", "HLLW", "HOLLOW", "HOLLOWS", "HOLW", "HOLWS", "INLT", "IS", "ISLAND", "ISLND", "ISLANDS", "ISLNDS", "ISS", "ISLE", "ISLES", "JCT", "JCTION", "JCTN", "JUNCTION", "JUNCTN", "JUNCTON", "JCTNS", "JCTS", "JUNCTIONS", "KEY", "KY", "KEYS", "KYS", "KNL", "KNOL", "KNOLL", "KNLS", "KNOLLS", "LK", "LAKE", "LKS", "LAKES", "LAND", "LANDING", "LNDG", "LNDNG", "LANE", "LN", "LGT", "LIGHT", "LIGHTS", "LF", "LOAF", "LCK", "LOCK", "LCKS", "LOCKS", "LDG", "LDGE", "LODG", "LODGE", "LOOP", "LOOPS", "MALL", "MNR", "MANOR", "MANORS", "MNRS", "MEADOW", "MDW", "MDWS", "MEADOWS", "MEDOWS", "MEWS", "MILL", "MILLS", "MISSN", "MSSN", "MOTORWAY", "MNT", "MT", "MOUNT", "MNTAIN", "MNTN", "MOUNTAIN", "MOUNTIN", "MTIN", "MTN", "MNTNS", "MOUNTAINS", "NCK", "NECK", "ORCH", "ORCHARD", "ORCHRD", "OVAL", "OVL", "OVERPASS", "PARK", "PRK", "PARKS", "PARKWAY", "PARKWY", "PKWAY", "PKWY", "PKY", "PARKWAYS", "PKWYS", "PASS", "PASSAGE", "PATH", "PATHS", "PIKE", "PIKES", "PINE", "PINES", "PNES", "PL", "PLAIN", "PLN", "PLAINS", "PLNS", "PLAZA", "PLZ", "PLZA", "POINT", "PT", "POINTS", "PTS", "PORT", "PRT", "PORTS", "PRTS", "PR", "PRAIRIE", "PRR", "RAD", "RADIAL", "RADIEL", "RADL", "RAMP", "RANCH", "RANCHES", "RNCH", "RNCHS", "RAPID", "RPD", "RAPIDS", "RPDS", "REST", "RST", "RDG", "RDGE", "RIDGE", "RDGS", "RIDGES", "RIV", "RIVER", "RVR", "RIVR", "RD", "ROAD", "ROADS", "RDS", "ROUTE", "ROW", "RUE", "RUN", "SHL", "SHOAL", "SHLS", "SHOALS", "SHOAR", "SHORE", "SHR", "SHOARS", "SHORES", "SHRS", "SKYWAY", "SPG", "SPNG", "SPRING", "SPRNG", "SPGS", "SPNGS", "SPRINGS", "SPRNGS", "SPUR", "SPURS", "SQ", "SQR", "SQRE", "SQU", "SQUARE", "SQRS", "SQUARES", "STA", "STATION", "STATN", "STN", "STRA", "STRAV", "STRAVEN", "STRAVENUE", "STRAVN", "STRVN", "STRVNUE", "STREAM", "STREME", "STRM", "STREET", "STRT", "ST", "STR", "STREETS", "SMT", "SUMIT", "SUMITT", "SUMMIT", "TER", "TERR", "TERRACE", "THROUGHWAY", "TRACE", "TRACES", "TRCE", "TRACK", "TRACKS", "TRAK", "TRK", "TRKS", "TRAFFICWAY", "TRAIL", "TRAILS", "TRL", "TRLS", "TRAILER", "TRLR", "TRLRS", "TUNEL", "TUNL", "TUNLS", "TUNNEL", "TUNNELS", "TUNNL", "TRNPK", "TURNPIKE", "TURNPK", "UNDERPASS", "UN", "UNION", "UNIONS", "VALLEY", "VALLY", "VLLY", "VLY", "VALLEYS", "VLYS", "VDCT", "VIA", "VIADCT", "VIADUCT", "VIEW", "VW", "VIEWS", "VWS", "VILL", "VILLAG", "VILLAGE", "VILLG", "VILLIAGE", "VLG", "VILLAGES", "VLGS", "VILLE", "VL", "VIS", "VIST", "VISTA", "VST", "VSTA", "WALK", "WALKS", "WALL", "WY", "WAY", "WAYS", "WELL", "WELLS")
"""Tuple of street suffixes accepted by USPS"""

STREET_SUFFIX_MAPPING: dict[str, str] = {"ALLEE": "ALY", "ALLEY": "ALY", "ALLY": "ALY", "ALY": "ALY", "ANEX": "ANX", "ANNEX": "ANX", "ANNX": "ANX", "ANX": "ANX", "ARC": "ARC", "ARCADE": "ARC", "AV": "AVE", "AVE": "AVE", "AVEN": "AVE", "AVENU": "AVE", "AVENUE": "AVE", "AVN": "AVE", "AVNUE": "AVE", "BAYOO": "BYU", "BAYOU": "BYU", "BCH": "BCH", "BEACH": "BCH", "BEND": "BND", "BND": "BND", "BLF": "BLF", "BLUF": "BLF", "BLUFF": "BLF", "BLUFFS": "BLFS", "BOT": "BTM", "BTM": "BTM", "BOTTM": "BTM", "BOTTOM": "BTM", "BLVD": "BLVD", "BOUL": "BLVD", "BOULEVARD": "BLVD", "BOULV": "BLVD", "BR": "BR", "BRNCH": "BR", "BRANCH": "BR", "BRDGE": "BRG", "BRG": "BRG", "BRIDGE": "BRG", "BRK": "BRK", "BROOK": "BRK", "BROOKS": "BRKS", "BURG": "BG", "BURGS": "BGS", "BYP": "BYP", "BYPA": "BYP", "BYPAS": "BYP", "BYPASS": "BYP", "BYPS": "BYP", "CAMP": "CP", "CP": "CP", "CMP": "CP", "CANYN": "CYN", "CANYON": "CYN", "CNYN": "CYN", "CAPE": "CPE", "CPE": "CPE", "CAUSEWAY": "CSWY", "CAUSWA": "CSWY", "CSWY": "CSWY", "CEN": "CTR", "CENT": "CTR", "CENTER": "CTR", "CENTR": "CTR", "CENTRE": "CTR", "CNTER": "CTR", "CNTR": "CTR", "CTR": "CTR", "CENTERS": "CTRS", "CIR": "CIR", "CIRC": "CIR", "CIRCL": "CIR", "CIRCLE": "CIR", "CRCL": "CIR", "CRCLE": "CIR", "CIRCLES": "CIRS", "CLF": "CLF", "CLIFF": "CLF", "CLFS": "CLFS", "CLIFFS": "CLFS", "CLB": "CLB", "CLUB": "CLB", "COMMON": "CMN", "COMMONS": "CMNS", "COR": "COR", "CORNER": "COR", "CORNERS": "CORS", "CORS": "CORS", "COURSE": "CRSE", "CRSE": "CRSE", "COURT": "CT", "CT": "CT", "COURTS": "CTS", "CTS": "CTS", "COVE": "CV", "CV": "CV", "COVES": "CVS", "CREEK": "CRK", "CRK": "CRK", "CRESCENT": "CRES", "CRES": "CRES", "CRSENT": "CRES", "CRSNT": "CRES", "CREST": "CRST", "CROSSING": "XING", "CRSSNG": "XING", "XING": "XING", "CROSSROAD": "XRD", "CROSSROADS": "XRDS", "CURVE": "CURV", "DALE": "DL", "DL": "DL", "DAM": "DM", "DM": "DM", "DIV": "DV", "DIVIDE": "DV", "DV": "DV", "DVD": "DV", "DR": "DR", "DRIV": "DR", "DRIVE": "DR", "DRV": "DR", "DRIVES": "DRS", "EST": "EST", "ESTATE": "EST", "ESTATES": "ESTS", "ESTS": "ESTS", "EXP": "EXPY", "EXPR": "EXPY", "EXPRESS": "EXPY", "EXPRESSWAY": "EXPY", "EXPW": "EXPY", "EXPY": "EXPY", "EXT": "EXT", "EXTENSION": "EXT", "EXTN": "EXT", "EXTNSN": "EXT", "EXTS": "EXTS", "FALL": "FALL", "FALLS": "FLS", "FLS": "FLS", "FERRY": "FRY", "FRRY": "FRY", "FRY": "FRY", "FIELD": "FLD", "FLD": "FLD", "FIELDS": "FLDS", "FLDS": "FLDS", "FLAT": "FLT", "FLT": "FLT", "FLATS": "FLTS", "FLTS": "FLTS", "FORD": "FRD", "FRD": "FRD", "FORDS": "FRDS", "FOREST": "FRST", "FORESTS": "FRST", "FRST": "FRST", "FORG": "FRG", "FORGE": "FRG", "FRG": "FRG", "FORGES": "FRGS", "FORK": "FRK", "FRK": "FRK", "FORKS": "FRKS", "FRKS": "FRKS", "FORT": "FT", "FRT": "FT", "FT": "FT", "FREEWAY": "FWY", "FREEWY": "FWY", "FRWAY": "FWY", "FRWY": "FWY", "FWY": "FWY", "GARDEN": "GDN", "GARDN": "GDN", "GRDEN": "GDN", "GRDN": "GDN", "GARDENS": "GDNS", "GDNS": "GDNS", "GRDNS": "GDNS", "GATEWAY": "GTWY", "GATEWY": "GTWY", "GATWAY": "GTWY", "GTWAY": "GTWY", "GTWY": "GTWY", "GLEN": "GLN", "GLN": "GLN", "GLENS": "GLNS", "GREEN": "GRN", "GRN": "GRN", "GREENS": "GRNS", "GROV": "GRV", "GROVE": "GRV", "GRV": "GRV", "GROVES": "GRVS", "HARB": "HBR", "HARBOR": "HBR", "HARBR": "HBR", "HBR": "HBR", "HRBOR": "HBR", "HARBORS": "HBRS", "HAVEN": "HVN", "HVN": "HVN", "HT": "HTS", "HTS": "HTS", "HIGHWAY": "HWY", "HIGHWY": "HWY", "HIWAY": "HWY", "HIWY": "HWY", "HWAY": "HWY", "HWY": "HWY", "HILL": "HL", "HL": "HL", "HILLS": "HLS", "HLS": "HLS", "HLLW": "HOLW", "HOLLOW": "HOLW", "HOLLOWS": "HOLW", "HOLW": "HOLW", "HOLWS": "HOLW", "INLT": "INLT", "IS": "IS", "ISLAND": "IS", "ISLND": "IS", "ISLANDS": "ISS", "ISLNDS": "ISS", "ISS": "ISS", "ISLE": "ISLE", "ISLES": "ISLE", "JCT": "JCT", "JCTION": "JCT", "JCTN": "JCT", "JUNCTION": "JCT", "JUNCTN": "JCT", "JUNCTON": "JCT", "JCTNS": "JCTS", "JCTS": "JCTS", "JUNCTIONS": "JCTS", "KEY": "KY", "KY": "KY", "KEYS": "KYS", "KYS": "KYS", "KNL": "KNL", "KNOL": "KNL", "KNOLL": "KNL", "KNLS": "KNLS", "KNOLLS": "KNLS", "LK": "LK", "LAKE": "LK", "LKS": "LKS", "LAKES": "LKS", "LAND": "LAND", "LANDING": "LNDG", "LNDG": "LNDG", "LNDNG": "LNDG", "LANE": "LN", "LN": "LN", "LGT": "LGT", "LIGHT": "LGT", "LIGHTS": "LGTS", "LF": "LF", "LOAF": "LF", "LCK": "LCK", "LOCK": "LCK", "LCKS": "LCKS", "LOCKS": "LCKS", "LDG": "LDG", "LDGE": "LDG", "LODG": "LDG", "LODGE": "LDG", "LOOP": "LOOP", "LOOPS": "LOOP", "MALL": "MALL", "MNR": "MNR", "MANOR": "MNR", "MANORS": "MNRS", "MNRS": "MNRS", "MEADOW": "MDW", "MDW": "MDWS", "MDWS": "MDWS", "MEADOWS": "MDWS", "MEDOWS": "MDWS", "MEWS": "MEWS", "MILL": "ML", "MILLS": "MLS", "MISSN": "MSN", "MSSN": "MSN", "MOTORWAY": "MTWY", "MNT": "MT", "MT": "MT", "MOUNT": "MT", "MNTAIN": "MTN", "MNTN": "MTN", "MOUNTAIN": "MTN", "MOUNTIN": "MTN", "MTIN": "MTN", "MTN": "MTN", "MNTNS": "MTNS", "MOUNTAINS": "MTNS", "NCK": "NCK", "NECK": "NCK", "ORCH": "ORCH", "ORCHARD": "ORCH", "ORCHRD": "ORCH", "OVAL": "OVAL", "OVL": "OVAL", "OVERPASS": "OPAS", "PARK": "PARK", "PRK": "PARK", "PARKS": "PARK", "PARKWAY": "PKWY", "PARKWY": "PKWY", "PKWAY": "PKWY", "PKWY": "PKWY", "PKY": "PKWY", "PARKWAYS": "PKWY", "PKWYS": "PKWY", "PASS": "PASS", "PASSAGE": "PSGE", "PATH": "PATH", "PATHS": "PATH", "PIKE": "PIKE", "PIKES": "PIKE", "PINE": "PNE", "PINES": "PNES", "PNES": "PNES", "PL": "PL", "PLAIN": "PLN", "PLN": "PLN", "PLAINS": "PLNS", "PLNS": "PLNS", "PLAZA": "PLZ", "PLZ": "PLZ", "PLZA": "PLZ", "POINT": "PT", "PT": "PT", "POINTS": "PTS", "PTS": "PTS", "PORT": "PRT", "PRT": "PRT", "PORTS": "PRTS", "PRTS": "PRTS", "PR": "PR", "PRAIRIE": "PR", "PRR": "PR", "RAD": "RADL", "RADIAL": "RADL", "RADIEL": "RADL", "RADL": "RADL", "RAMP": "RAMP", "RANCH": "RNCH", "RANCHES": "RNCH", "RNCH": "RNCH", "RNCHS": "RNCH", "RAPID": "RPD", "RPD": "RPD", "RAPIDS": "RPDS", "RPDS": "RPDS", "REST": "RST", "RST": "RST", "RDG": "RDG", "RDGE": "RDG", "RIDGE": "RDG", "RDGS": "RDGS", "RIDGES": "RDGS", "RIV": "RIV", "RIVER": "RIV", "RVR": "RIV", "RIVR": "RIV", "RD": "RD", "ROAD": "RD", "ROADS": "RDS", "RDS": "RDS", "ROUTE": "RTE", "ROW": "ROW", "RUE": "RUE", "RUN": "RUN", "SHL": "SHL", "SHOAL": "SHL", "SHLS": "SHLS", "SHOALS": "SHLS", "SHOAR": "SHR", "SHORE": "SHR", "SHR": "SHR", "SHOARS": "SHRS", "SHORES": "SHRS", "SHRS": "SHRS", "SKYWAY": "SKWY", "SPG": "SPG", "SPNG": "SPG", "SPRING": "SPG", "SPRNG": "SPG", "SPGS": "SPGS", "SPNGS": "SPGS", "SPRINGS": "SPGS", "SPRNGS": "SPGS", "SPUR": "SPUR", "SPURS": "SPUR", "SQ": "SQ", "SQR": "SQ", "SQRE": "SQ", "SQU": "SQ", "SQUARE": "SQ", "SQRS": "SQS", "SQUARES": "SQS", "STA": "STA", "STATION": "STA", "STATN": "STA", "STN": "STA", "STRA": "STRA", "STRAV": "STRA", "STRAVEN": "STRA", "STRAVENUE": "STRA", "STRAVN": "STRA", "STRVN": "STRA", "STRVNUE": "STRA", "STREAM": "STRM", "STREME": "STRM", "STRM": "STRM", "STREET": "ST", "STRT": "ST", "ST": "ST", "STR": "ST", "STREETS": "STS", "SMT": "SMT", "SUMIT": "SMT", "SUMITT": "SMT", "SUMMIT": "SMT", "TER": "TER", "TERR": "TER", "TERRACE": "TER", "THROUGHWAY": "TRWY", "TRACE": "TRCE", "TRACES": "TRCE", "TRCE": "TRCE", "TRACK": "TRAK", "TRACKS": "TRAK", "TRAK": "TRAK", "TRK": "TRAK", "TRKS": "TRAK", "TRAFFICWAY": "TRFY", "TRAIL": "TRL", "TRAILS": "TRL", "TRL": "TRL", "TRLS": "TRL", "TRAILER": "TRLR", "TRLR": "TRLR", "TRLRS": "TRLR", "TUNEL": "TUNL", "TUNL": "TUNL", "TUNLS": "TUNL", "TUNNEL": "TUNL", "TUNNELS": "TUNL", "TUNNL": "TUNL", "TRNPK": "TPKE", "TURNPIKE": "TPKE", "TURNPK": "TPKE", "UNDERPASS": "UPAS", "UN": "UN", "UNION": "UN", "UNIONS": "UNS", "VALLEY": "VLY", "VALLY": "VLY", "VLLY": "VLY", "VLY": "VLY", "VALLEYS": "VLYS", "VLYS": "VLYS", "VDCT": "VIA", "VIA": "VIA", "VIADCT": "VIA", "VIADUCT": "VIA", "VIEW": "VW", "VW": "VW", "VIEWS": "VWS", "VWS": "VWS", "VILL": "VLG", "VILLAG": "VLG", "VILLAGE": "VLG", "VILLG": "VLG", "VILLIAGE": "VLG", "VLG": "VLG", "VILLAGES": "VLGS", "VLGS": "VLGS", "VILLE": "VL", "VL": "VL", "VIS": "VIS", "VIST": "VIS", "VISTA": "VIS", "VST": "VIS", "VSTA": "VIS", "WALK": "WALK", "WALKS": "WALK", "WALL": "WALL", "WY": "WAY", "WAY": "WAY", "WAYS": "WAYS", "WELL": "WL", "WELLS": "WLS", "WLS": "WLS"}
"""Mapping of street suffix variations to their preferred abbreviation"""

class AddressParseError(RuntimeError):
    """
    Raised when the parsing of an address string failed.
    """
    def __init__(self, description: str, address_string: str, index: int):
        """
        :param description: A brief description of the issue.
        :param address_string: Original address string, to provide a reference as to the location of the error.
        :param index: The index in the address string at which the parse error occured.
        """
        output_string = "Error parsing address at index " + str(index) + " (" + description + "), near:\n"
        output_string += address_string + '\n'
        output_string += (' ' * index) + "^\n"
        super().__init__(output_string)
        self.index = index
    
    def __reduce__(self):
        # Make the exception pickleable, just in case,
        return (AddressParseError, (self.message, self.index))


class _AddressToken:
    """
    Represents a token used during the parsing of an address. Should not be accessed outside
    of the addressutil module, unless you really know what you are doing.
    """
    TYPE_DECIMAL = "decimal"
    """Represents a decimal number"""
    TYPE_FRACTION = "fraction"
    """Represents a fractional number"""
    TYPE_NUMBER = "number"
    """Represents a nonnegative integer"""
    TYPE_NUMBERSUFFIXED = "numbersuffixed"
    """Represents a number suffixed with a non-numeric character"""
    TYPE_POUND = "pound"
    """Represents the pound sign (#)"""
    TYPE_SPECIAL = "special"
    """Represents a token that begins with a nonalphanumeric character"""
    TYPE_WORD = "word"
    """Represents a alphanumeric word beginning with a letter"""
    
    def __init__(self, literal: str, type_: str, index: int):
        """
        :param literal: The literal value of the token.
        :param type_: The type of the token.
        :param index: The index of the token in the original string. Should be an integer.
        """
        self.literal: str = literal
        self.type_: str = type_
        self.index: int = index
    
    def __repr__(self) -> str:
        return "addressutil._AddressToken(literal=" + self.literal + ", type_=" + self.type_ + ", index=" + repr(self.index) + ")"


class Address:
    """
    Represents an address in the United States. All subclasses of Address should be immutable and hashable.
    
    Some parameters in the constructor for Address and derived classes are optional. However, it is highly recommended to 
    explicitly specify them as None when they have been omitted, to make it clear that the omission was intentional.
    
    Designed based on the documentation at https://pe.usps.com/text/pub28/28c2_toc.htm.
    """
    
    # TODO Support private mailbox (PMB) designations in the base Address class.
    
    def __init__(self, city: str, state: str, zipcode: str, zipcode_ext: Optional[str]):
        """
        **Caution:** Do NOT initialize Address directly unless you know what you are doing! Initializing this class directly
        will result in a bare-bones object with no street information. The Address object will have type AddressType.BASE.
        Instead, you probably want to use Address.parse() to get a usable address.
        
        :param city: The city of the address
        :param state: The 2-letter state abbreviation of the address
        :param zipcode: The 5-digit ZIP code of the address
        :param zipcode_ext: The 4-digit extended ZIP code as a part of a 5+4 ZIP code (if present)
        :raises ValueError: If parameter "state" is not 2 characters long.
        """
        if len(state) != 2:
            raise ValueError("Invalid value \"" + str(state) + "\" for the state - Use the 2-letter FIPS abbreviation for the state, " + 
                    "not the full state name or any other abbreviation.")
        if len(zipcode) != 5:
            raise ValueError("Invalid value \"" + str(zipcode) + "\" for the zip code - Parameter \"zipcode\" should be 5 digits long. " + 
                    "Use the parameter \"zipcode_ext\" to store the extended zipcode.")
        if zipcode_ext is not None and len(zipcode_ext) != 4:
            raise ValueError("Parameter \"zipcode_ext\" should either be None or 4 digits long, not \"" + str(zipcode_ext) + "\"")
        self.__city: str = city.upper()
        self.__state: str = state.upper()
        self.__zipcode: str = zipcode.upper()
        self.__zipcode_ext: Optional[str] = None if zipcode_ext is None else zipcode_ext.upper()
    
    @property
    def city(self) -> str:
        """
        The city that the address is in
        """
        return self.__city
    
    @property
    def state(self) -> str:
        """
        The 2-letter USPS abbreviation for the state that the address is in
        """
        return self.__state
    
    @property
    def zipcode(self) -> str:
        """
        The 5-digit ZIP code of the address
        """
        return self.__zipcode
    
    @property
    def zipcode_full(self) -> str:
        """
        The full ZIP+4 ZIP code of the address. If the extended ZIP code is not specified, will return the 5-digit ZIP code.
        """
        if self.__zipcode_ext is None:
            return self.__zipcode
        return self.__zipcode + "-" + self.__zipcode_ext
    
    @staticmethod
    def _lex_delivery_address(delivery_address: str) -> list[_AddressToken]:
        """
        Internal function to process a string into a series of tokens.
        
        :return: List of Address tokens
        """
        output_tokens: list[_AddressToken] = []
        
        current_position: int = 0  # The character we are currently on within the delivery address
        current_token: Optional[_AddressToken] = None
        while current_position < len(delivery_address):
            if delivery_address[current_position] == "\n":
                raise AddressParseError("unexpected newline", delivery_address, current_position)
            if current_token is None:
                # No current token.
                if re.match(r"[^A-Za-z0-9#\-\.\/]", delivery_address[current_position]):
                    # We encountered another non-parsed character. Do nothing.
                    pass
                elif re.match(r"\d", delivery_address[current_position]):
                    # Begins with a number. Assume it is a number for now, although it could change.
                    current_token = _AddressToken(delivery_address[current_position], _AddressToken.TYPE_NUMBER, current_position)
                elif re.match(r"[A-Za-z]", delivery_address[current_position]):
                    # Begins with alphabetic character
                    current_token = _AddressToken(delivery_address[current_position], _AddressToken.TYPE_WORD, current_position)
                elif re.match(r"#", delivery_address[current_position]):
                    # The pound sign is a special token that will only ever consist of a single pound sign.
                    output_tokens.append(_AddressToken(delivery_address[current_position], _AddressToken.TYPE_POUND, current_position))
                else:
                    # Begins with hyphen, period, or forward slash,
                    current_token = _AddressToken(delivery_address[current_position], _AddressToken.TYPE_SPECIAL, current_position)
            else:
                if re.match(r"[^A-Za-z0-9\-\.\/]", delivery_address[current_position]):
                    # We encountered a non-parsed character. Terminate the current token.
                    output_tokens.append(current_token)
                    current_token = None
                    
                    # Also terminate the token if we encounter a pound (#) sign.
                    # However, we also want to add the pound sign in as a separate token.
                    if re.match(r"#", delivery_address[current_position]):
                        # Special pound sign token.
                        output_tokens.append(_AddressToken(delivery_address[current_position], _AddressToken.TYPE_POUND, current_position))
                else:
                    # Append whatever character we have on hand to the previous token.
                    if current_token.type_ == _AddressToken.TYPE_NUMBER:
                        if re.match(r"\.", delivery_address[current_position]):
                            # A dot indicates a decimal
                            current_token.type_ = _AddressToken.TYPE_DECIMAL
                        elif re.match(r"\/", delivery_address[current_position]):
                            # A slash indicates a fraction
                            current_token.type_ = _AddressToken.TYPE_FRACTION
                        elif re.match(r"[^0-9]", delivery_address[current_position]):
                            # This is no longer a number, but a suffixed number
                            current_token.type_ = _AddressToken.TYPE_NUMBERSUFFIXED
                    elif current_token.type_ == _AddressToken.TYPE_DECIMAL or current_token.type_ == _AddressToken.TYPE_FRACTION:
                        if re.match(r"[^0-9]", delivery_address[current_position]):
                            # This is not a decimal or a fraction, it is now a generic suffixed number.
                            current_token.type_ = _AddressToken.TYPE_NUMBERSUFFIXED
                    current_token.literal += delivery_address[current_position]
            current_position += 1
        # Append the last token in the string, if any.
        if current_token is not None:
            output_tokens.append(current_token)
        return output_tokens
    
    @staticmethod
    def parse(delivery_address: str, last_line: str) -> Address:
        """
        Parses an address from a string. Requires delivery_address and last_line to be separated. Usually, these
        are written as separate lines on an envelope. For example, consider the following written on an envelope:
        ```
        JOHN SMITH
        1003 S MAIN ST UNIT 603
        SPRINGFIELD IL 84785-9634
        ```
        The first line is discarded, as it is not part of the of the address but rather the recipient name. The
        second line, the delivery address, is 1003 S MAIN ST UNIT 603. Pass this in for the delivery_address
        parameter. The last line (SPRINGFIELD IL 84785) should be passed in for the last_time parameter. Note
        that this function only parses the address, it does **not** check if the address is valid or deliverable.
        
        With the exception of newlines, unknown characters are treated as spaces during parsing. There should
        not be any newlines in either parameter.
        
        :param delivery_address: The delivery address (line immediately under the recipient name).
        :param last_line: The last line of the address, usually containing city, state, and ZIP.
        :return: A subclass of Address.
        :raises AddressParseError: If there was an issue with parsing the delivery address.
        :raises ValueError: If there was an issue with parsing the address last line.
        """
        # Parse city, state, and zip first. Then, parse the delivery address itself.
        # All non-alphanumeric characters will be silently ignored.
        last_line = last_line.upper().strip()
        last_line = re.sub(r"\s", " ", last_line)
        last_line = re.sub(r"[^A-Za-z0-9\s\-]", "", last_line)
        
        last_line_tokens: list[str] = last_line.split(' ')
        city: str = ""
        state: str = ""
        zipcode: str = ""
        zipcode_ext: Optional[str] = ""
        if len(last_line_tokens) <= 1:
            raise ValueError("Missing 2-character state code in address last line \"" + last_line + "\"")
        if len(last_line_tokens) <= 2:
            raise ValueError("Missing city in address last line \"" + last_line + "\"")
        
        # Now parse the tokens
        if '-' in last_line_tokens[-1]:
            # ZIP+4
            zipcode = last_line_tokens[-1].split('-')[0]
            zipcode_ext = last_line_tokens[-1].split('-')[-1]
            if re.search(r"[^0-9]", zipcode) or re.search(r"[^0-9]", zipcode_ext):
                raise ValueError("Invalid characters in ZIP+4 code \"" + last_line_tokens[-1] + "\"")
            if len(zipcode) != 5 or len(zipcode_ext) != 4:
                raise ValueError("ZIP+4 code \"" + last_line_tokens[-1] + "\" has the wrong length. All ZIP codes must be zero-padded.")
        else:
            # ZIP
            zipcode = last_line_tokens[-1]
            zipcode_ext = None
            if re.search(r"[^0-9]", zipcode):
                raise ValueError("Invalid characters in ZIP code \"" + last_line_tokens[-1] + "\"")
            if len(zipcode) != 5:
                raise ValueError("ZIP code \"" + last_line_tokens[-1] + "\" has the wrong length. All ZIP codes must be zero-padded.")
        if len(last_line_tokens[-2]) != 2:
            raise ValueError("Invalid 2-character state code \"" + last_line_tokens[-2] + "\". The 2-character abbreviation should " + 
                    "be used instead of the full state name.")
        state = last_line_tokens[-2]
        city = " ".join(last_line_tokens[:-2])
        
        # At this point, the variables city, state, zipcode, and zipcode_ext should be populated. We now turn to parsing the delivery address.
        
        unparsed_tokens: list[_AddressToken] = Address._lex_delivery_address(delivery_address.upper().strip())
        """List of tokens not yet parsed."""
        
        
        # Make sure we have at least 1 token to work with.
        if len(unparsed_tokens) == 0:
            raise AddressParseError("no valid tokens found", delivery_address, 0)
        
        if len(unparsed_tokens) == 2 and unparsed_tokens[0].literal == "GENERAL" and unparsed_tokens[1].literal == "DELIVERY":
            # General delivery
            return GeneralDeliveryAddress(city, state, zipcode, zipcode_ext)
        elif re.sub(r"[^A-Za-z0-9]", "", unparsed_tokens[0].literal) in {"HC", "RR", "CPR", "OPC", "PSC", "UPR", "UNIT"} and (len(unparsed_tokens) >= 3 and unparsed_tokens[2].literal == "BOX"):
            # TODO Make sure "RR03 BOX 98D" is correctly recognized as a Rural Route address.
            route_address_type = "Highway Contract Route" if unparsed_tokens[0].literal == "HC" else "Rural Route"
            if unparsed_tokens[0].literal not in {"HC", "RR"}:
                route_address_type = "Overseas Military"
            if len(unparsed_tokens) < 4:
                raise AddressParseError("missing box number in " + route_address_type.lower() + " address", delivery_address, unparsed_tokens[-1].index + len(unparsed_tokens[-1].literal))
            if unparsed_tokens[1].type_ not in {_AddressToken.TYPE_NUMBER, _AddressToken.TYPE_NUMBERSUFFIXED}:
                raise AddressParseError("invalid " + route_address_type.lower() + " number, cannot begin with a letter or symbol", delivery_address, unparsed_tokens[1].index)
            route_number: str = unparsed_tokens[1].literal
            box_number: str = unparsed_tokens[3].literal
            if unparsed_tokens[0].literal == "HC":
                return HighwayContractRouteAddress(route_number, box_number, city, state, zipcode, zipcode_ext)
            elif unparsed_tokens[0].literal == "RR":
                return RuralRouteAddress(route_number, box_number, city, state, zipcode, zipcode_ext)
            else:
                # In the case of overseas military, the "route_number" is the address number.
                return OverseasMilitaryAddress(unparsed_tokens[0].literal, route_number, box_number, city, state, zipcode, zipcode_ext)
        elif len(unparsed_tokens) >= 2 and re.sub(r"[^A-Za-z0-9]", "", unparsed_tokens[0].literal) == "PO" and unparsed_tokens[1].literal == "BOX":
            if len(unparsed_tokens) < 3:
                raise AddressParseError("missing box number in post office box address", delivery_address, unparsed_tokens[-1].index + len(unparsed_tokens[-1].literal))
            po_box_number: str = unparsed_tokens[2].literal
            if po_box_number[0] == '-':
                po_box_number = "0" + po_box_number[1:]
            return PostOfficeBoxAddress(po_box_number, city, state, zipcode, zipcode_ext)
        elif len(unparsed_tokens) >= 3 and re.sub(r"[^A-Za-z0-9]", "", unparsed_tokens[0].literal) == "P" and \
                re.sub(r"[^A-Za-z0-9]", "", unparsed_tokens[1].literal) == "O" and unparsed_tokens[2].literal == "BOX":
            if len(unparsed_tokens) < 4:
                raise AddressParseError("missing box number in post office box address", delivery_address, unparsed_tokens[-1].index + len(unparsed_tokens[-1].literal))
            po_box_number = unparsed_tokens[3].literal
            if po_box_number[0] == '-':
                po_box_number = "0" + po_box_number[1:]
            return PostOfficeBoxAddress(po_box_number, city, state, zipcode, zipcode_ext)
        
        # Assuming standard address
        
        address_number: Optional[str] = None
        predirectional: Optional[str] = None
        street_name: Optional[str] = None
        street_suffix: Optional[str] = None
        postdirectional: Optional[str] = None
        address2_type: Optional[str] = None
        address2: Optional[str] = None
        
        # First, get the address number, if it exists.
        if len(unparsed_tokens) >= 2 and \
                unparsed_tokens[0].type_ in {_AddressToken.TYPE_NUMBER, _AddressToken.TYPE_FRACTION, _AddressToken.TYPE_DECIMAL} or \
                (_AddressToken.TYPE_NUMBERSUFFIXED and "-" in unparsed_tokens[0].literal):
            address_number = unparsed_tokens[0].literal
            if unparsed_tokens[0].type_ == _AddressToken.TYPE_NUMBER and unparsed_tokens[1].type_ == _AddressToken.TYPE_FRACTION:
                address_number += " " + unparsed_tokens[1].literal
                unparsed_tokens.pop(0)
            unparsed_tokens.pop(0)
        
        # At this point, the address number has been popped. No need to worry about it again.
        
        # Find where the suffix and secondary address identifier are.
        suffix_index: Optional[int] = None
        address2_index: Optional[int] = None
        already_seen_hashtag: bool = False  # Whether a hashtag has already been found.
        for i in range(len(unparsed_tokens)):
            current_token = unparsed_tokens[i]
            if current_token.literal.replace('.', "") in SECONDARY_UNIT_INDICATORS:
                address2_index = i
            if current_token.literal.replace('.', "") in STREET_SUFFIXES:
                suffix_index = i
            if current_token.type_ == _AddressToken.TYPE_POUND:
                if already_seen_hashtag:
                    raise AddressParseError("only at most one pound sign (#) is permitted in an address", delivery_address, current_token.index)
                if address2_index is not None and i == address2_index + 1:
                    raise AddressParseError("cannot have pound sign (#) if unit specifier is already present", delivery_address, current_token.index)
                address2_index = i
                already_seen_hashtag = True
            if current_token.type_ == _AddressToken.TYPE_SPECIAL:
                raise AddressParseError("unexpected token", delivery_address, current_token.index)
        
        # The secondary address must be after the street suffix.
        if suffix_index is not None and address2_index is not None and address2_index <= suffix_index:
            address2_index = None
        
        # Parse the secondary address and pop it from the list, if it exists
        if address2_index is not None:
            address2_type = unparsed_tokens[address2_index].literal
            if address2_index == len(unparsed_tokens) - 1:
                raise AddressParseError("missing number for secondary address", delivery_address, unparsed_tokens[-1].index + len(unparsed_tokens[-1].literal))
            address2 = " ".join((x.literal for x in unparsed_tokens[address2_index+1:]))
            
            # Keep removing unparsed tokens until we have reached the index of address2.
            while len(unparsed_tokens) > address2_index:
                unparsed_tokens.pop()
        
        # Now, we have the predirectional, street name, and street suffix, and postdirectional.
        
        # Check if we have a postdirectional.
        if len(unparsed_tokens) > 0 and unparsed_tokens[-1].literal.replace('.', "") in DIRECTIONS_LIST:
            # Yes, there is a postdirectional! Indicate its presence and pop it from the list.
            postdirectional = unparsed_tokens[-1].literal
            unparsed_tokens.pop()
        
        # At this point, only the predirectional, street name, and street suffix should be in the list, if they exist at all.
        
        # Now check the location of the suffix. If it's not at the end, the "suffix" we identified was actually not the true suffix.
        if suffix_index is not None and len(unparsed_tokens) - suffix_index > 1:
            # Okay, the "suffix" that we expected turned out not the be the suffix. That's okay, let's mark it as not a suffix.
            suffix_index = None
        
        # TODO Standardize highway names (like COUNTY ROAD 238A, INTERSTATE 75, etc.)
        
        if suffix_index is None:
            # The starting and ending index of the street name. If there is a postdirectional, don't count that here.
            if len(unparsed_tokens) > 1 and unparsed_tokens[0].literal.replace('.', "") in DIRECTIONS_LIST:
                predirectional = unparsed_tokens[0].literal
                unparsed_tokens.pop(0)
            street_name = " ".join((x.literal for x in unparsed_tokens))
        else:
            street_start_index = 0
            if suffix_index > 1:
                if unparsed_tokens[0].literal.replace('.', "") in DIRECTIONS_LIST:
                    predirectional = unparsed_tokens[0].literal
                    street_start_index = 1
            street_suffix = unparsed_tokens[suffix_index].literal
            street_name = " ".join((x.literal for x in unparsed_tokens[street_start_index:suffix_index]))
        
        # More standardization of the address.
        if predirectional is not None:
            predirectional = re.sub(r"[^A-Za-z]", "", predirectional)
        if postdirectional is not None:
            postdirectional = re.sub(r"[^A-Za-z]", "", postdirectional)
        if street_suffix is not None:
            street_suffix = re.sub(r"[^A-Za-z]", "", street_suffix)
        predirectional = DIRECTIONS_MAPPING[predirectional] if predirectional in DIRECTIONS_MAPPING else predirectional
        postdirectional = DIRECTIONS_MAPPING[postdirectional] if postdirectional in DIRECTIONS_MAPPING else postdirectional
        street_suffix = STREET_SUFFIX_MAPPING[street_suffix] if street_suffix in STREET_SUFFIX_MAPPING else street_suffix
        
        # Hyphens will be replaced with spaces by USPS as well.
        street_name = street_name.replace('-', ' ')
        
        return StandardAddress(address_number, predirectional, street_name, street_suffix, postdirectional, address2_type, address2,
                city, state, zipcode, zipcode_ext)
    
    @property
    def type_(self) -> str:
        """
        Gets the type of the address. Guaranteed to be a value from the addressutil.AddressType enum.
        """
        return AddressType.BASE.value
    
    def __eq__(self, other) -> bool:
        if self.type_ != other.type_:
            return False
        return self.city == other.city and self.state == other.state and self.zipcode_full == other.zipcode_full
    
    def __hash__(self) -> int:
        return hash(self.__repr__())
    
    def __repr__(self) -> str:
        return "addressutil.Address(city=" + repr(self.__city) + ", state=" + repr(self.__state) + ", zipcode=" + repr(self.zipcode) + \
                ", zipcode_ext=" + ("<uninitialized>" if self.__zipcode_ext is None else repr(self.__zipcode_ext)) + ")"
    
    def __str__(self) -> str:
        return "\n" + self.city + " " + self.state + " " + self.zipcode_full


class AddressType(enum.Enum):
    """
    Represents an address type.
    """
    BASE = "Base (uninitialized)"
    """Incomplete uninitialized address contaning only 2-letter state code and ZIP code."""
    GENERAL_DELIVERY = "General Delivery"
    """Objects of type GeneralDeliveryAddress"""
    HIGHWAY_CONTRACT_ROUTE = "Highway Contract Route"
    """Objects of type HighwayContractRouteAddress"""
    OVERSEAS_MILITARY = "Overseas Military"
    """Objects of type OverseasMilitaryAddress"""
    POST_OFFICE_BOX = "Post Office Box"
    """Objects of type PostOfficeBoxAddress"""
    RURAL_ROUTE = "Rural Route"
    """Objcets of type RuralRouteAddress"""
    STANDARD = "Standard Street"
    """Objecst of type StandardAddress"""


class GeneralDeliveryAddress(Address):
    """
    Represents general delivery, the practice of delivering mail straight to the post office.
    """
    
    # Note: There is no __init__ function because general delivery doesn't require additional parameters.
    
    @property
    def type_(self) -> str:
        return AddressType.GENERAL_DELIVERY.value
    
    def __repr__(self) -> str:
        return "addressutil.GeneralDeliveryAddress(" + super().__repr__() + ")"
    
    def __str__(self) -> str:
        return "GENERAL DELIVERY" + super().__str__()


class HighwayContractRouteAddress(Address):
    """
    Represents a highway contract route.
    """
    def __init__(self, route_number: str, box_number: str, city: str, state: str, zipcode: str, zipcode_ext: Optional[str]):
        """
        :param route_number: The route number of the highway contract route
        :param box_number: The box number of the highway contract route
        :param city: Refer to the documentation for Address.__init__()
        :param state: Refer to the documentation for Address.__init__()
        :param zipcode: Refer to the documentation for Address.__init__()
        :param zipcode_ext: Refer to the documentation for Address.__init__()
        """
        super().__init__(city, state, zipcode, zipcode_ext)
        self.__route_number: str = str(route_number).upper()
        self.__box_number: str = str(box_number).upper()
    
    @property
    def route_number(self) -> str:
        return self.__route_number
    
    @property
    def box_number(self) -> str:
        return self.__box_number
    
    @property
    def type_(self) -> str:
        return AddressType.HIGHWAY_CONTRACT_ROUTE.value
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.route_number == other.route_number and self.box_number == other.box_number
    
    def __repr__(self) -> str:
        return "addressutil.HighwayContractRouteAddress(route_number=" + repr(self.__route_number) + ", box_number=" + repr(self.__box_number) + ", " + super().__repr__() + ")"
    
    def __str__(self) -> str:
        return "HC " + self.__route_number + " BOX " + self.__box_number + super().__str__()


class OverseasMilitaryAddress(Address):
    """
    Represents an overseas military address. For such addresses, the 2-character "state" abbreviation is usually AA, AE, or AP.
    """
    def __init__(self, address_type: str, address_number: str, box_number: str, city: str, state: str, zipcode: str, zipcode_ext: Optional[str]):
        """
        :param address_type: One of "CPR", "OPC", "PSC", "UPR", or "UNIT"
        :param address_number: The address number for the overseas military address
        :param box_number: The box number for the overseas military address
        :param city: Refer to the documentation for Address.__init__()
        :param state: Refer to the documentation for Address.__init__()
        :param zipcode: Refer to the documentation for Address.__init__()
        :param zipcode_ext: Refer to the documentation for Address.__init__()
        :raises ValueError: If an invalid value is provided for address_type
        """
        super().__init__(city, state, zipcode, zipcode_ext)
        valid_address_types: tuple[str, ...] = ("CPR", "OPC", "PSC", "UPR", "UNIT")
        if address_type.upper() not in address_type:
            raise ValueError("Invalid value \"" + address_type.upper() + "\" for address_type, address_type must be one of: " + ", ".join(valid_address_types))
        self.__address_type: str = address_type
        self.__address_number: str = address_number
        self.__box_number: str = box_number
    
    @property
    def address_number(self) -> str:
        return self.__address_number
    
    @property
    def address_type(self) -> str:
        return self.__address_type
    
    @property
    def box_number(self) -> str:
        return self.__box_number
    
    @property
    def type_(self) -> str:
        return AddressType.OVERSEAS_MILITARY.value
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.address_type == other.address_type and self.address_number == other.address_number and self.box_number == other.box_number
    
    def __repr__(self) -> str:
        return "addressutil.OverseasMilitaryAddress(address_type=" + repr(self.__address_type) + ", address_number=" + repr(self.__address_number) + ", box_number=" + repr(self.__box_number) + \
                ", " + super().__repr__() + ")"
    
    def __str__(self) -> str:
        return self.__address_type + " " + self.__address_number + " BOX " + self.__box_number + super().__str__()


class PostOfficeBoxAddress(Address):
    """
    Represents a Post Office box address. Sample address:
    
    PO BOX 987 SPRINGFIELD IL 12345-6789
    """
    def __init__(self, box_number: str, city: str, state: str, zipcode: str, zipcode_ext: Optional[str]):
        """
        Sample PO Box address: PO BOX 987 SPRINGFIELD IL 12345-6789
        
        :param: The box number of the PO box. In the sample address above, the box number is 987.
        :param city: Refer to the documentation for Address.__init__()
        :param state: Refer to the documentation for Address.__init__()
        :param zipcode: Refer to the documentation for Address.__init__()
        :param zipcode_ext: Refer to the documentation for Address.__init__()
        """
        super().__init__(city, state, zipcode, zipcode_ext)
        self.__box_number: str = str(box_number).upper()
    
    @property
    def box_number(self) -> str:
        """
        Get the PO box number of this address. Some PO boxes are represented by letters rather than numbers.
        """
        return self.__box_number
    
    @property
    def type_(self) -> str:
        return AddressType.POST_OFFICE_BOX.value
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.box_number == other.box_number
    
    def __repr__(self) -> str:
        return "addressutil.PostOfficeBoxAddress(box_number=" + repr(self.__box_number) + ", " + super().__repr__() + ")"
    
    def __str__(self) -> str:
        return "PO BOX " + self.__box_number + super().__str__()


class RuralRouteAddress(Address):
    """
    Represents a rural route address.
    """
    def __init__(self, route_number: str, box_number: str, city: str, state: str, zipcode: str, zipcode_ext: Optional[str]):
        """
        :param route_number: The route number of the rural route
        :param box_number: The box number of the rural route
        :param city: Refer to the documentation for Address.__init__()
        :param state: Refer to the documentation for Address.__init__()
        :param zipcode: Refer to the documentation for Address.__init__()
        :param zipcode_ext: Refer to the documentation for Address.__init__()
        """
        super().__init__(city, state, zipcode, zipcode_ext)
        self.__route_number: str = str(route_number).upper()
        self.__box_number: str = str(box_number).upper()
    
    @property
    def route_number(self) -> str:
        return self.__route_number
    
    @property
    def box_number(self) -> str:
        return self.__box_number
    
    @property
    def type_(self) -> str:
        return AddressType.RURAL_ROUTE.value
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.route_number == other.route_number and self.box_number == other.box_number
    
    def __repr__(self) -> str:
        return "addressutil.RuralRouteAddress(route_number=" + repr(self.__route_number) + ", box_number=" + repr(self.__box_number) + ", " + super().__repr__() + ")"
    
    def __str__(self) -> str:
        return "RR " + self.__route_number + " BOX " + self.__box_number + super().__str__()


class StandardAddress(Address):
    """
    Represents a standard address, the most common type of address in the United States.
    """
    def __init__(self, address_number: Optional[str], predirectional: Optional[str], street_name: Optional[str], suffix: Optional[str], postdirectional: Optional[str], 
            address2_type: Optional[str], address2: Optional[str], city: str, state: str, zipcode: str, zipcode_ext: Optional[str]):
        """
        Most addresses will not contain values for all fields. Missing fields should be explicitly marked with None, NOT the empty string.
        
        Examples of standard addresses:
         - Example 1: 123 E MAIN ST
         - Example 2: 9262 COUNTY LINE RD NORTH APT 105
        
        :param address_number: In Example 1, this would be 123.
        :param predirectional: Optionally abbreviated predirectional. In Example 1, this would be E. Example 2 does not contain a predirectional.
        :param street_name: The street name. In Example 2, this would be COUNTY LINE.
        :param suffix: The suffix to the street name. In Example 2, this would be RD.
        :param postdirectional: Optionally abbreviated postdirectional. In Example 2, this would be NORTH.
        :param address2_type: In Example 2, this would be APT. Example 1 does not have a value for address2_type.
        :param address2: In Example 2, this would be 105.
        :param city: Refer to the documentation for Address.__init__()
        :param state: Refer to the documentation for Address.__init__()
        :param zipcode: Refer to the documentation for Address.__init__()
        :param zipcode_ext: Refer to the documentation for Address.__init__()
        """
        super().__init__(city, state, zipcode, zipcode_ext)
        self.__address_number: Optional[str] = address_number
        self.__predirectional: Optional[str] = predirectional
        self.__street_name: Optional[str] = street_name
        self.__suffix: Optional[str] = suffix
        self.__postdirectional: Optional[str] = postdirectional
        self.__address2_type: Optional[str] = address2_type
        self.__address2: Optional[str] = address2
    
    @property
    def address2_type(self) -> Optional[str]:
        """
        Get the type of address line 2 for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__address2_type
    
    @property
    def address2(self) -> Optional[str]:
        """
        Get the value for address line 2 for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__address2
    
    @property
    def address_number(self) -> Optional[str]:
        """
        Get the address number for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__address_number
    
    @property
    def postdirectional(self) -> Optional[str]:
        """
        Get the postdirectional for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__postdirectional
    
    @property
    def predirectional(self) -> Optional[str]:
        """
        Get the predirectional for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__predirectional
    
    @property
    def street_name(self) -> Optional[str]:
        """
        Get the street name for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__street_name
    
    @property
    def suffix(self) -> Optional[str]:
        """
        Get the street suffix for the address. See also the documentation for StandardAddress.__init__()
        """
        return self.__suffix
    
    @property
    def type_(self) -> str:
        return AddressType.STANDARD.value
    
    def as_tuple(self) -> tuple[Optional[str], ...]:
        """
        Get the fields of this address as a tuple.
        :return: Tuple containing every field in the address, in the order utilized by USPS.
        """
        standard_address_fields = []
        standard_address_fields.append(self.__address_number)
        standard_address_fields.append(self.__predirectional)
        standard_address_fields.append(self.__street_name)
        standard_address_fields.append(self.__suffix)
        standard_address_fields.append(self.__postdirectional)
        standard_address_fields.append(self.__address2_type)
        standard_address_fields.append(self.__address2)
        return tuple(standard_address_fields)
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.as_tuple() == other.as_tuple()
    
    def __repr__(self) -> str:
        return "addressutil.StandardAddress(" + ", ".join((("<unspecified>" if x is None else repr(x)) for x in self.as_tuple())) + ", " + super().__repr__() + ")"
    
    def __str__(self) -> str:
        return " ".join((x for x in self.as_tuple() if x is not None)) + super().__str__()


if __name__ == "__main__":
    print("Starting unit tests for addressutil.py...")
    test_addresses: tuple[str, ...] = ("123 N. MAIN ST.\nCHICAGO IL 12345", "4725 NORTHWEST 193RD COURT\nCHICAGO, IL, 29525-9186", 
    "1552 COUNTY ROAD 252\nCHICAGO IL 12345-6789", "1480 Inner Road\nGainesville, FL 32611", "General Delivery\nGainesville, FL, 32601", 
    "1234 S.E. BROADWAY AVE UNIT 5\nNEW YORK, NY, 10002", "PO BOX 15\nSPRINGFIELD IL 12345", "P.O. BOX C\nSPRINGFIELD IL 12345",
    "123 MAIN ST # 45\nSPRINGFIELD IL 12345", "123 MAIN ST #45\nSPRINGFIELD IL 12345", "51 1/2 362ND COURT SE\nCHICAGO, IL, 56124-7162",
    "201 FILBERT ST,STE 700\nSAN FRANCISCO CA 94133-3242", "P. O. BOX 123\nSPRINGFIELD IL 12345", "P. O. BOX 123B\nSPRINGFIELD IL 12345",)
    for address in test_addresses:
        print(address)
        address_object: Address = Address.parse(*address.split('\n'))
        print(repr(address_object))
        assert address_object == Address.parse(*str(address_object).split("\n")), "Parsing the output string for address \"" + str(address_object).replace("\n", " ") + \
                "\" is inconsistent, please check the code for Address.parse()"
    print("The above are unit tests for this module. If you want to use this module instead, you should read the documentation.")
    print("You can get started by typing \"import addressutil\" at the beginning of your code.")
    