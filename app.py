from datetime import datetime, timedelta
import json
import requests
import streamlit as st

st.set_page_config(
    page_title="National Rail Darwin Departure Board",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d0e12;
        color: #ffc400;
        font-family: 'Courier New', Courier, monospace;
    }
    .board-header {
        background-color: #161920;
        border: 2px solid #ffc400;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 15px;
        box-shadow: 0 0 8px rgba(255, 196, 0, 0.2);
    }
    .board-title {
        color: #ffc400;
        font-size: 16px;
        font-weight: 900;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 0;
        text-shadow: 0 0 5px #ffc400;
    }
    .stCaptionContainer p {
        font-size: 11px !important;
        color: #a0a0a0 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDialog"] > div {
        max-width: 520px !important;
        width: 90% !important;
        background-color: #161920 !important;
        border: 2px solid #ffc400 !important;
        color: #ffc400 !important;
    }
    div[data-testid="stDialog"] * {
        color: #ffc400 !important;
    }
    @keyframes flashRed {
        0% { background-color: #550000; color: #ffcccc; }
        50% { background-color: #ff0000; color: #ffffff; }
        100% { background-color: #550000; color: #ffcccc; }
    }
    .flash-status {
        animation: flashRed 1s infinite;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)

RDM_API_KEY = "J3yIpTIWUg7AHEVDpBGbJ2lg4nM3vatAD6S8eDt2XHPm5rUy"

OPERATOR_STATIONS = {
    "All Operators": {
        "Crystal Palace (CYP)": "CYP",
        "New Cross (NWX)": "NWX",
        "New Cross Gate (NXG)": "NXG",
        "Canada Water (ZCW)": "ZCW",
        "Brockley (BCY)": "BCY",
        "West Croydon (WCY)": "WCY",
        "London Victoria (VIC)": "VIC",
        "London Bridge (LBG)": "LBG",
        "Clapham Junction (CLJ)": "CLJ",
        "East Croydon (ECR)": "ECR",
        "Gatwick Airport (GTW)": "GTW",
        "Brighton (BTN)": "BTN",
        "St Pancras International (STP)": "STP",
        "London Waterloo (WAT)": "WAT",
        "London Liverpool Street (LST)": "LST",
        "Stratford (SRA)": "SRA",
    },
    "Southern": {
        "Crystal Palace (CYP)": "CYP",
        "New Cross Gate (NXG)": "NXG",
        "Brockley (BCY)": "BCY",
        "West Croydon (WCY)": "WCY",
        "London Victoria (VIC)": "VIC",
        "London Bridge (LBG)": "LBG",
        "Clapham Junction (CLJ)": "CLJ",
        "East Croydon (ECR)": "ECR",
        "Gatwick Airport (GTW)": "GTW",
        "Brighton (BTN)": "BTN",
        "Hove (HOV)": "HOV",
        "Eastbourne (EBN)": "EBN",
        "Hastings (HGS)": "HGS",
        "Southampton Central (SOU)": "SOU",
        "Portsmouth & Southsea (PMS)": "PMS",
        "Bognor Regis (BOG)": "BOG",
        "Littlehampton (LIT)": "LIT",
        "Horsham (HRH)": "HRH",
        "Redhill (RDH)": "RDH",
        "Uckfield (UCK)": "UCK",
        "Oxted (OXT)": "OXT",
        "Caterham (CAT)": "CAT",
        "Epsom (EPS)": "EPS",
        "Dorking (DKG)": "DKG",
        "Seaford (SEF)": "SEF",
        "Newhaven Harbour (NVH)": "NVH",
        "Ore (ORE)": "ORE",
        "Chichester (CCH)": "CCH",
        "Barnham (BAH)": "BAH",
    },
    "Thameslink": {
        "St Pancras International (STP)": "STP",
        "London Bridge (LBG)": "LBG",
        "London Blackfriars (BFR)": "BFR",
        "Farringdon (FAR)": "FAR",
        "City Thameslink (CTK)": "CTK",
        "Gatwick Airport (GTW)": "GTW",
        "Brighton (BTN)": "BTN",
        "Bedford (BDM)": "BDM",
        "Luton (LTN)": "LTN",
        "Luton Airport Parkway (LPA)": "LPA",
        "St Albans City (SAB)": "SAB",
        "Three Bridges (TBD)": "TBD",
        "Sevenoaks (SEV)": "SEV",
        "Sutton (SUO)": "SUO",
        "Wimbledon (WIM)": "WIM",
        "Harpenden (HPD)": "Harpenden",
        "Elstree & Borehamwood (ELB)": "ELB",
        "West Hampstead Thameslink (WHP)": "WHP",
        "Kentish Town (KTN)": "KTN",
        "East Croydon (ECR)": "ECR",
        "Horsham (HRH)": "HRH",
    },
    "Southeastern": {
        "London Charing Cross (CHX)": "CHX",
        "London Cannon Street (CST)": "CST",
        "London Bridge (LBG)": "LBG",
        "London Victoria (VIC)": "VIC",
        "St Pancras International (STP)": "STP",
        "New Cross (NWX)": "NWX",
        "Dartford (DFD)": "DFD",
        "Gravesend (GRV)": "GRV",
        "Sevenoaks (SEV)": "SEV",
        "Tunbridge Wells (TBW)": "TBW",
        "Hastings (HGS)": "HGS",
        "Dover Priory (DVP)": "DVP",
        "Folkestone Central (FKC)": "FKC",
        "Ashford International (AFK)": "AFK",
        "Ramsgate (RAM)": "RAM",
        "Margate (MAR)": "MAR",
        "Canterbury West (CBW)": "CBW",
        "Orpington (ORP)": "ORP",
        "Bromley South (BMS)": "BMS",
        "Faversham (FAV)": "FAV",
        "Sittingbourne (SIT)": "SIT",
        "Gillingham (GLM)": "GLM",
        "Rochester (RCH)": "RCH",
        "Tonbridge (TON)": "TON",
        "Paddock Wood (PDW)": "PDW",
    },
    "South Western Railway": {
        "London Waterloo (WAT)": "WAT",
        "Vauxhall (VXH)": "VXH",
        "Clapham Junction (CLJ)": "CLJ",
        "Wimbledon (WIM)": "WIM",
        "Surbiton (SUR)": "SUR",
        "Woking (WOK)": "WOK",
        "Guildford (GLD)": "GLD",
        "Basingstoke (BSK)": "BSK",
        "Southampton Central (SOU)": "SOU",
        "Bournemouth (BMH)": "BMH",
        "Weymouth (WEY)": "WEY",
        "Portsmouth Harbour (PMH)": "PMH",
        "Salisbury (SAL)": "SAL",
        "Exeter St Davids (EXD)": "EXD",
        "Reading (RDG)": "RDG",
        "Windsor & Eton Riverside (WNR)": "WNR",
        "Richmond (RMD)": "RMD",
        "Kingston (KNG)": "KNG",
        "Twickenham (TWC)": "TWC",
        "Staines (SNS)": "SNS",
        "Farnborough (FNB)": "FNB",
        "Winchester (WIN)": "WIN",
        "Poole (POO)": "POO",
    },
    "London Overground": {
        "Abbey Wood (ABW)": "ABW",
        "Acton Central (ACC)": "ACC",
        "Anerley (ANY)": "ANY",
        "Barking (BGK)": "BGK",
        "Barking Riverside (BKG)": "BKG",
        "Battersea Park (BAK)": "BAK",
        "Beckton Park (BPK)": "BPK",
        "Birkbeck (BIK)": "BIK",
        "Blackhorse Road (BHR)": "BHR",
        "Bond Street (BND)": "BND",
        "Brondesbury (BSY)": "BSY",
        "Brondesbury Park (BSP)": "BSP",
        "Brockley (BCY)": "BCY",
        "Bushey (BSH)": "BSH",
        "Caledonian Road & Barnsbury (CUB)": "CUB",
        "Cambridge Heath (CBH)": "CBH",
        "Camden Road (CDR)": "CDR",
        "Canada Water (ZCW)": "ZCW",
        "Canonbury (CNN)": "CNN",
        "Carpenders Park (CPK)": "CPK",
        "Cheshunt (CHN)": "CHN",
        "Chingford (CHI)": "CHI",
        "Clapham High Street (CLH)": "CLH",
        "Clapham Junction (CLJ)": "CLJ",
        "Clapton (CPT)": "CPT",
        "Crouch Hill (CRH)": "CRH",
        "Crystal Palace (CYP)": "CYP",
        "Dalston Junction (DLJ)": "DLJ",
        "Dalston Kingsland (DLK)": "DLK",
        "Denmark Hill (DNM)": "DNM",
        "Deptford Bridge (DPB)": "DPB",
        "Emerson Park (EMP)": "EMP",
        "Enfield Town (ENF)": "ENF",
        "Euston (EUS)": "EUS",
        "Finchley Road & Frognal (FNR)": "FNR",
        "Forest Hill (FOH)": "FOH",
        "Gospel Oak (GPO)": "GPO",
        "Hackney Downs (HAC)": "HAC",
        "Hackney Wick (HKW)": "HKW",
        "Haggerston (HGG)": "Haggerston",
        "Hampstead Heath (HMP)": "HMP",
        "Harringay Green Lanes (HRG)": "HRG",
        "Harrow & Wealdstone (HRW)": "HRW",
        "Headstone Lane (HDL)": "HDL",
        "Highams Park (HIP)": "HIP",
        "Highbury & Islington (HNB)": "HNB",
        "Homerton (HMR)": "HMR",
        "Honor Oak Park (HOP)": "HOP",
        "Hoxton (HOX)": "HOX",
        "Imperial Wharf (IMW)": "IMW",
        "Kensal Green (KNL)": "KNL",
        "Kensal Rise (KNR)": "KNR",
        "Kensington Olympia (KPA)": "KPA",
        "Kentish Town West (KTW)": "KTW",
        "Kilburn High Road (KLR)": "KLR",
        "New Cross (NWX)": "NWX",
        "New Cross Gate (NXG)": "NXG",
        "Penge West (PGW)": "PGW",
        "Queen's Park (QPS)": "QPS",
        "Queens Road Peckham (QRP)": "QRP",
        "Richmond (RMD)": "RMD",
        "Rotherhithe (ROE)": "ROE",
        "Shadwell (SHW)": "SHW",
        "Shepherd's Bush (SPS)": "SPS",
        "Shoreditch High Street (SDH)": "SDH",
        "Silver Street (SLV)": "SLV",
        "South Acton (SAT)": "SAT",
        "South Hampstead (SOH)": "SOH",
        "South Tottenham (STO)": "STO",
        "Stamford Hill (SMH)": "SMH",
        "Stoke Newington (STK)": "STK",
        "Stratford (SRA)": "SRA",
        "Surrey Quays (SQS)": "SQS",
        "Theobalds Grove (TEG)": "TEG",
        "Turkey Street (TKT)": "TKT",
        "Upper Holloway (UHL)": "UHL",
        "Wapping (WAP)": "Wapping",
        "Watford High Street (WFH)": "WFH",
        "Watford Junction (WFJ)": "WFJ",
        "Wembley Central (WMB)": "WMB",
        "West Brompton (WBP)": "WBP",
        "West Croydon (WCY)": "WCY",
        "White Hart Lane (WHL)": "WHL",
        "Whitechapel (WCL)": "WCL",
        "Willesden Junction (WIL)": "Willesden Junction",
        "Wood Street (WST)": "WST",
    },
    "Gatwick Express": {
        "London Victoria (VIC)": "VIC",
        "Gatwick Airport (GTW)": "GTW",
        "Brighton (BTN)": "BTN",
    },
    "Greater Anglia": {
        "London Liverpool Street (LST)": "LST",
        "Stratford (SRA)": "SRA",
        "Tottenham Hale (TTH)": "TTH",
        "Chelmsford (CHM)": "CHM",
        "Colchester (COL)": "COL",
        "Ipswich (IPS)": "IPS",
        "Norwich (NRW)": "NRW",
        "Southend Victoria (SOV)": "SOV",
        "Clacton-on-Sea (CLT)": "CLT",
        "Cambridge (CBG)": "CBG",
        "Bishop's Stortford (BHS)": "BHS",
        "Romford (RMF)": "RMF",
        "Shenfield (SNF)": "SNF",
    },
}

OPERATOR_ALIASES = {
    "Southern": ["sn", "southern"],
    "Thameslink": ["tl", "thameslink"],
    "Southeastern": ["se", "southeastern"],
    "South Western Railway": ["sw", "south western railway", "swr"],
    "London Overground": ["lo", "london overground", "arriva rail london", "tfl"],
    "Gatwick Express": ["gx", "gatwick express"],
    "Greater Anglia": ["ga", "greater anglia"],
}


@st.cache_data(ttl=15)
def fetch_live_darwin_board(crs_code, board_type="Departures"):
    endpoint = "GetDepBoardWithDetails" if board_type == "Departures" else "GetArrBoardWithDetails"
    url = f"https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120/{endpoint}/{crs_code}"
    headers = {
        "x-apikey": RDM_API_KEY,
        "User-Agent": "NationalRailStreamlitApp/1.0",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return 500, str(e)


def parse_darwin_services(raw_data, filter_operator, board_type="Departures"):
    services = []
    if not raw_data or not isinstance(raw_data, dict):
        return services

    board_result = raw_data.get("GetStationBoardResult", raw_data)

    services_key = "trainServices" if board_type == "Departures" else "trainServices"
    if services_key not in board_result and "arrTrainServices" in board_result:
        services_key = "arrTrainServices"

    train_services = board_result.get(services_key, {})
    if isinstance(train_services, dict):
        train_list = train_services.get("service", [])
    elif isinstance(train_services, list):
        train_list = train_services
    else:
        train_list = []

    for idx, item in enumerate(train_list):
        try:
            operators = item.get("operator", "Southern")
            if isinstance(operators, dict):
                operator_name = operators.get("content", "Southern")
            else:
                operator_name = str(operators)

            if filter_operator != "All Operators":
                allowed_tokens = OPERATOR_ALIASES.get(filter_operator, [filter_operator.lower()])
                matches = any(token in str(operator_name).lower() for token in allowed_tokens)
                if not matches:
                    continue

            location_key = "destination" if board_type == "Departures" else "origin"
            destinations = item.get(location_key, [])
            if isinstance(destinations, dict):
                dest_locs = destinations.get("location", [])
                dest_name = dest_locs[0].get("locationName", "TERMINUS") if dest_locs else "TERMINUS"
            elif isinstance(destinations, list) and len(destinations) > 0:
                dest_name = destinations[0].get("locationName", "TERMINUS")
            else:
                dest_name = "TERMINUS"

            time_key = "std" if board_type == "Departures" else "sta"
            time_val = item.get(time_key, "00:00")

            status_time_key = "etd" if board_type == "Departures" else "eta"
            status_time_val = item.get(status_time_key, "On Time")

            plat = item.get("platform", "1")

            # 1. Try official Darwin RSID first
            uid = None
            for key in ["rsid", "rsId"]:
                val = item.get(key)
                if val and str(val).strip():
                    uid = str(val).strip().upper()
                    break

            # 2. Fallback: Use Darwin trainUid if available, else formatted index
            train_uid_raw = item.get("trainUid", "")
            if not uid or uid == "----":
                if train_uid_raw and str(train_uid_raw).strip():
                    uid = str(train_uid_raw).strip().upper()
                else:
                    uid = f"UID-{idx + 1:02d}"

            status = "ON TIME"
            reason = "TRAIN RUNNING ON SCHEDULE."
            sort_time = 0

            status_lower = str(status_time_val).lower()
            if status_lower in ["cancelled", "cancel"] or item.get("isCancelled") == True:
                status = "CANCELLED"
                sort_time = 999999
                reason = item.get("cancelReason", "SERVICE CANCELLED DUE TO OPERATIONAL CONSTRAINTS.")
            elif status_lower not in ["on time", str(time_val).lower()]:
                status = f"DELAYED ({status_time_val})"
                sort_time = 300
                reason = item.get("delayReason", "TRAIN RUNNING LATE DUE TO NETWORK CONGESTION.")

            services.append({
                "UID": uid,
                "DUE": time_val,
                "DESTINATION": str(dest_name).upper(),
                "PLATFORM": str(plat),
                "OPERATOR": str(operator_name).upper(),
                "SERVICE STATUS": status,
                "REASON": reason,
                "_sort_time": sort_time,
            })
        except Exception:
            continue

    return services


@st.dialog("DARWIN CONTROL SERVICE REPORT")
def show_disruption_dialog(train_info):
    st.markdown(f"**SERVICE ID / HEADCODE:** {train_info['UID']}")
    st.markdown(f"**LOCATION:** {train_info['DESTINATION']}")
    st.markdown(f"**OPERATOR:** {train_info['OPERATOR']}")
    st.markdown(f"**PLATFORM:** {train_info['PLATFORM']}")
    st.markdown(f"**SCHEDULED TIME:** {train_info['DUE']}")
    st.markdown(f"**STATUS:** `{train_info['SERVICE STATUS']}`")
    st.divider()
    st.markdown(f"**CONTROL ADVISORY / REASON:**\n\n> {train_info['REASON']}")
    if st.button("CLOSE REPORT"):
        st.session_state.selected_train_idx = None
        st.rerun()


operators_list = list(OPERATOR_STATIONS.keys())

ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2.5, 2.5, 1.5, 1])

with ctrl_col1:
    selected_operator = st.selectbox("SELECT OPERATOR:", operators_list)

available_stations = OPERATOR_STATIONS[selected_operator]
station_display_names = list(available_stations.keys())

with ctrl_col2:
    selected_station_display = st.selectbox("SELECT STATION:", station_display_names)

with ctrl_col3:
    board_type = st.radio("BOARD TYPE:", ["Departures", "Arrivals"], horizontal=True)

with ctrl_col4:
    debug_mode = st.checkbox("DEBUG", value=False)

crs = available_stations[selected_station_display]
station_clean_name = selected_station_display.split(" (")[0]

st.markdown(
    f"""
    <div class="board-header">
        <div class="board-title">NATIONAL RAIL {board_type.upper()} — {station_clean_name.upper()} ({crs}) [{selected_operator.upper()}]</div>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.fragment(run_every=30)
def render_live_board():
    status_code, raw_data = fetch_live_darwin_board(crs, board_type)

    if debug_mode:
        st.write(f"**API Status Code:** {status_code}")
        st.json(raw_data if isinstance(raw_data, dict) else {"error": raw_data})

    parsed_services = parse_darwin_services(
        raw_data if status_code == 200 else None, selected_operator, board_type
    )

    if not parsed_services:
        st.warning(
            f"⚠️ Live API feed unavailable or returning no {board_type.lower()} for this station/operator combination.")
        return

    parsed_services.sort(key=lambda x: x["_sort_time"])

    st.caption(
        "💡 Click INFO on any service row to inspect detailed Darwin log reasons."
    )

    for idx, train in enumerate(parsed_services):
        cols = st.columns([1.0, 1.2, 3.2, 1.2, 2.0, 2.0, 1.0])
        with cols[0]:
            st.markdown(f"`{train['UID']}`")
        with cols[1]:
            st.markdown(f"**{train['DUE']}**")
        with cols[2]:
            st.markdown(train["DESTINATION"])
        with cols[3]:
            st.markdown(train["PLATFORM"])
        with cols[4]:
            st.markdown(train["OPERATOR"])
        with cols[5]:
            if train["SERVICE STATUS"] == "CANCELLED":
                st.markdown(f'<div class="flash-status">{train["SERVICE STATUS"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(train["SERVICE STATUS"])
        with cols[6]:
            if st.button("INFO", key=f"btn_{idx}"):
                st.session_state.selected_train_idx = idx
                st.rerun()

        st.markdown(
            "<hr style='margin: 4px 0; border-color: #22222a;'>",
            unsafe_allow_html=True,
        )

    if "selected_train_idx" in st.session_state and st.session_state.selected_train_idx is not None:
        sel_idx = st.session_state.selected_train_idx
        if 0 <= sel_idx < len(parsed_services):
            show_disruption_dialog(parsed_services[sel_idx])


render_live_board()