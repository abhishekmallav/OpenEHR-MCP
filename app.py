# Streamlit frontend for EHRbase (openEHR)
# Single-file app: streamlit_ehrbase_frontend.py
# Requirements: streamlit, requests

import streamlit as st
from datetime import datetime
import requests
import json
from typing import Optional

st.set_page_config(page_title="EHRbase Streamlit UI", layout="wide")

st.title("EHRbase / openEHR — Streamlit Frontend")
st.markdown("A small admin/test UI to: list templates, fetch example flat JSON, create EHRs, post compositions (FLAT), fetch compositions and run AQL.")

# --- Sidebar settings ---
st.sidebar.header("Connection")
BASE_URL = st.sidebar.text_input("EHRbase base URL", value="http://localhost:8080/ehrbase/rest/openehr/v1")
API_HEADERS_RAW = st.sidebar.text_area("Extra headers (JSON)", value='{"openEHR-VERSION": "1.0.2", "openEHR-AUDIT_DETAILS": "hospital1"}')
try:
    EXTRA_HEADERS = json.loads(API_HEADERS_RAW)
except Exception:
    st.sidebar.error("Headers must be valid JSON")
    EXTRA_HEADERS = {}

DEFAULT_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
HEADERS = {**DEFAULT_HEADERS, **EXTRA_HEADERS}

# Small helper functions

def api_get(path: str, params: Optional[dict] = None):
    url = f"{BASE_URL}/{path.lstrip('/') }"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
        return resp
    except Exception as e:
        st.error(f"GET request failed: {e}")
        return None


def api_post(path: str, data=None, params: Optional[dict] = None, files=None, headers_override=None):
    url = f"{BASE_URL}/{path.lstrip('/')}"
    hdrs = headers_override if headers_override is not None else HEADERS
    try:
        if files:
            resp = requests.post(url, headers={k:v for k,v in hdrs.items() if k!='Content-Type'}, params=params, files=files, timeout=60)
        else:
            resp = requests.post(url, headers=hdrs, params=params, data=json.dumps(data) if (data is not None and not isinstance(data, str)) else data, timeout=60)
        return resp
    except Exception as e:
        st.error(f"POST request failed: {e}")
        return None

# --- Main UI ---

tabs = st.tabs(["Templates", "EHRs", "Compositions", "AQL","FORM"])

# --- Templates tab ---
with tabs[0]:
    st.header("Templates")
    col1, col2 = st.columns([1,2])
    with col1:
        if st.button("List templates"):
            r = api_get("definition/template/adl1.4")
            if r is not None:
                st.write(r.status_code, r.text)
                if r.ok:
                    try:
                        st.json(r.json())
                    except Exception:
                        st.text(r.text)
        template_id = st.text_input("Template id (exact)", value="patient_visit_template")
        if st.button("Get template example (FLAT)"):
            if template_id.strip():
                path = f"definition/template/adl1.4/{requests.utils.requote_uri(template_id)}/example?format=FLAT"
                r = api_get(path)
                if r is not None:
                    st.write(r.status_code)
                    if r.ok:
                        try:
                            st.json(r.json())
                        except Exception:
                            st.text(r.text)
                    else:
                        st.error(r.text)
    with col2:
        st.write("Upload template (.opt ADL1.4)")
        uploaded = st.file_uploader("Choose .opt file", type=["opt","xml","adl"]) 
        if uploaded is not None:
            # show filename and upload
            st.write(uploaded.name)
            if st.button("Upload template to EHRbase"):
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/xml")}
                r = api_post("definition/template/adl1.4", files=files)
                if r is not None:
                    st.write(r.status_code, r.text)
                    if r.ok:
                        st.success("Template uploaded")
                    else:
                        st.error(r.text)

# --- EHRs tab ---
with tabs[1]:
    st.header("EHRs")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Create new EHR"):
            r = api_post("ehr", data={})
            if r is not None:
                st.write(r.status_code)
                try:
                    st.json(r.json())
                except Exception:
                    st.text(r.text)
        st.write("Get EHR by id")
        ehr_id = st.text_input("EHR id", value="")
        if st.button("Fetch EHR"):
            if ehr_id.strip():
                r = api_get(f"ehr/{ehr_id}")
                if r is not None:
                    st.write(r.status_code)
                    try:
                        st.json(r.json())
                    except Exception:
                        st.text(r.text)
    with c2:
        st.write("List all EHRs (paged)")
        page = st.number_input("Page", min_value=0, max_value=1000, value=0)
        size = st.number_input("Size", min_value=1, max_value=100, value=20)
        if st.button("List EHRs"):
            r = api_get("ehr", params={"from": page*size, "size": size})
            if r is not None:
                st.write(r.status_code)
                try:
                    st.json(r.json())
                except Exception:
                    st.text(r.text)

# --- Compositions tab ---
with tabs[2]:
    st.header("Compositions (create / fetch)")
    colA, colB = st.columns([1,1])
    with colA:
        st.subheader("Create composition (FLAT)")
        ehr_id_post = st.text_input("EHR id for posting", value="")
        tpl_id = st.text_input("Template id", value="patient_visit_template")
        json_area = st.text_area("Flat JSON body (paste or get example)", height=300)
        if st.button("Create composition from JSON"):
            if not ehr_id_post.strip():
                st.error("Add EHR id")
            else:
                # post to composition
                path = f"ehr/{ehr_id_post}/composition?templateId={requests.utils.requote_uri(tpl_id)}&format=FLAT"
                try:
                    body = json.loads(json_area)
                except Exception:
                    st.error("Body must be valid JSON")
                    body = None
                if body is not None:
                    r = api_post(path, data=body)
                    if r is not None:
                        st.write(r.status_code)
                        try:
                            st.json(r.json())
                        except Exception:
                            st.text(r.text)
    with colB:
        st.subheader("Fetch composition")
        ehr_id_get = st.text_input("EHR id for get", value="")
        comp_uid = st.text_input("Composition UID (without ::version)", value="")
        if st.button("Get composition"):
            if ehr_id_get.strip() and comp_uid.strip():
                # full uid may need ::local.ehrbase.org::1; attempt to get with both
                full = comp_uid if '::' in comp_uid else f"{comp_uid}::local.ehrbase.org::1"
                r = api_get(f"ehr/{ehr_id_get}/composition/{requests.utils.requote_uri(full)}")
                if r is not None:
                    st.write(r.status_code)
                    try:
                        st.json(r.json())
                    except Exception:
                        st.text(r.text)
# ------------------------------------
# BLOOD PRESSURE FORM TAB
# ------------------------------------


with tabs[4]:
    # --- Blood Pressure Form ---
    st.header("🩺 Create Composition (Patient Visit Template)")

    with st.form("bp_form"):
        ehr_id = st.text_input("EHR ID", "")
        tpl_id = st.text_input("Template ID", "patient_visit_template")
        composer = st.text_input("Composer Name", "Dr. Max Mustermann")

        # --- Context Information ---
        st.subheader("🕒 Context Information")
        start_time = st.text_input("Start Time (ISO format)", datetime.now().isoformat())
        setting_value = st.selectbox("Setting", ["home"])
        setting_code = "225"
        setting_terminology = "openehr"

        # --- BP Readings ---
        st.subheader("💓 Blood Pressure Readings")
        systolic = st.number_input("Systolic Pressure (mmHg)", min_value=0.0, max_value=600.0, value=120.0)
        diastolic = st.number_input("Diastolic Pressure (mmHg)", min_value=0.0, max_value=600.0, value=80.0)
        mean_arterial = st.number_input("Mean Arterial Pressure (mmHg)", min_value=0.0, max_value=600.0, value=93.0)
        pulse_pressure = st.number_input("Pulse Pressure (mmHg)", min_value=0.0, max_value=600.0, value=40.0)
        tilt = st.number_input("Tilt (deg)", min_value=0.0, max_value=90.0, value=0.0)

        # --- Measurement Details ---
        st.subheader("🧩 Measurement Details")
        position = st.selectbox("Position", ["Standing", "Sitting", "Lying"])
        sleep_status = st.selectbox("Sleep Status", ["Awake", "Asleep"])
        cuff_size = st.selectbox("Cuff Size", ["Adult Thigh", "Adult"])
        location_measurement = st.selectbox("Location of Measurement", ["Right arm", "Left arm"])
        method = st.selectbox("Method", ["Auscultation"])
        diastolic_endpoint = st.selectbox("Diastolic Endpoint", ["Phase IV", "Phase V"])

        # --- Additional Info ---
        st.subheader("🧠 Additional Info")
        comment = st.text_area("Comment", "Lorem ipsum")
        clinical_interpretation = st.text_area("Clinical Interpretation", "Lorem ipsum")

        submit = st.form_submit_button("🚀 Submit to EHRbase")

    # ------------------------------------
    # SUBMIT HANDLER
    # ------------------------------------
    if submit:
        if not ehr_id.strip():
            st.error("EHR ID is required.")
        elif not tpl_id.strip():
            st.error("Template ID is required.")
        else:
            body = {
                # --- Category & Context ---
                f"{tpl_id}/category|code": "433",
                f"{tpl_id}/category|terminology": "openehr",
                f"{tpl_id}/category|value": "event",
                f"{tpl_id}/context/start_time": start_time,
                f"{tpl_id}/context/setting|value": setting_value,
                f"{tpl_id}/context/setting|code": setting_code,
                f"{tpl_id}/context/setting|terminology": setting_terminology,
                f"{tpl_id}/composer|name": composer,

                # --- Blood Pressure (any_event:0) ---
                f"{tpl_id}/blood_pressure/any_event:0/time": datetime.now().isoformat(),
                f"{tpl_id}/blood_pressure/any_event:0/math_function|value": "point in time",
                f"{tpl_id}/blood_pressure/any_event:0/width": "PT0S",

                f"{tpl_id}/blood_pressure/any_event:0/systolic|magnitude": systolic,
                f"{tpl_id}/blood_pressure/any_event:0/systolic|unit": "mm[Hg]",
                f"{tpl_id}/blood_pressure/any_event:0/diastolic|magnitude": diastolic,
                f"{tpl_id}/blood_pressure/any_event:0/diastolic|unit": "mm[Hg]",
                f"{tpl_id}/blood_pressure/any_event:0/mean_arterial_pressure|magnitude": mean_arterial,
                f"{tpl_id}/blood_pressure/any_event:0/mean_arterial_pressure|unit": "mm[Hg]",
                f"{tpl_id}/blood_pressure/any_event:0/pulse_pressure|magnitude": pulse_pressure,
                f"{tpl_id}/blood_pressure/any_event:0/pulse_pressure|unit": "mm[Hg]",
                f"{tpl_id}/blood_pressure/any_event:0/position|value": position,
                f"{tpl_id}/blood_pressure/any_event:0/position|terminology": "local",
                f"{tpl_id}/blood_pressure/any_event:0/sleep_status|value": sleep_status,
                f"{tpl_id}/blood_pressure/any_event:0/sleep_status|code": "at1044",
                f"{tpl_id}/blood_pressure/any_event:0/sleep_status|terminology": "local",
                f"{tpl_id}/blood_pressure/any_event:0/tilt|magnitude": tilt,
                f"{tpl_id}/blood_pressure/any_event:0/tilt|unit": "deg",
                f"{tpl_id}/blood_pressure/any_event:0/comment": comment,
                f"{tpl_id}/blood_pressure/any_event:0/clinical_interpretation": clinical_interpretation,

                # --- General BP Settings ---
                f"{tpl_id}/blood_pressure/cuff_size|value": cuff_size,
                f"{tpl_id}/blood_pressure/cuff_size|terminology": "local",
                f"{tpl_id}/blood_pressure/location_of_measurement|value": location_measurement,
                f"{tpl_id}/blood_pressure/location_of_measurement|terminology": "local",
                f"{tpl_id}/blood_pressure/method|value": method,
                f"{tpl_id}/blood_pressure/method|terminology": "local",
                f"{tpl_id}/blood_pressure/diastolic_endpoint|value": diastolic_endpoint,
                f"{tpl_id}/blood_pressure/diastolic_endpoint|code": "at1011",
                f"{tpl_id}/blood_pressure/diastolic_endpoint|terminology": "local",

                # --- Locale Info ---
                f"{tpl_id}/language|code": "en",
                f"{tpl_id}/language|terminology": "ISO_639-1",
                f"{tpl_id}/territory|code": "IN",
                f"{tpl_id}/territory|terminology": "ISO_3166-1"
            }

            path = f"{BASE_URL}/ehr/{ehr_id}/composition?templateId={tpl_id}&format=FLAT"
            st.write("📡 Sending data to:", path)
            st.json(body)

            try:
                r = requests.post(path, json=body)
                st.write("✅ Response status:", r.status_code)

                if r.status_code in [200, 201]:
                    st.success("Composition created successfully!")
                    data = r.json()
                    st.json(data)

                elif r.status_code == 204:
                    st.warning("✅ Composition created successfully (204: No Content). Fetching details via AQL...")

                    # --- AQL to get latest composition for that EHR ---
                    aql_query = {
                        "q": f"""
                            SELECT
                                c/uid/value AS composition_uid,
                                c/name/value AS composition_name,
                                c/context/start_time/value AS time_created
                            FROM EHR e
                                CONTAINS COMPOSITION c
                            WHERE e/ehr_id/value = '{ehr_id}'
                              AND c/archetype_details/template_id/value = '{tpl_id}'
                            ORDER BY c/context/start_time/value DESC
                            LIMIT 1
                        """
                    }

                    query_url = f"{BASE_URL}/query/aql"
                    resp = requests.post(query_url, json=aql_query)

                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("rows"):
                            latest = result["rows"][0]
                            st.success("🩸 Latest composition details:")
                            st.json({
                                "Composition UID": latest[0],
                                "Name": latest[1],
                                "Created": latest[2]
                            })
                        else:
                            st.warning("No compositions found for this EHR.")
                    else:
                        st.error(f"Failed to fetch via AQL (status: {resp.status_code})")
                        st.text(resp.text)

                else:
                    st.error(f"❌ Unexpected status code: {r.status_code}")
                    st.text(r.text)

            except Exception as e:
                st.error(f"Error posting to EHRbase: {e}")


# --- AQL tab ---
with tabs[3]:
    st.header("AQL Query Runner")
    aql = st.text_area("AQL query", height=200, value="SELECT c FROM EHR e CONTAINS COMPOSITION c LIMIT 10")
    if st.button("Run AQL"):
        r = api_post("query", data={"q": aql})
        if r is not None:
            st.write(r.status_code)
            try:
                st.json(r.json())
            except Exception:
                st.text(r.text)

st.info("Tip: Use 'Get template example (FLAT)' to obtain a valid JSON skeleton you can paste into 'Flat JSON body' and then create a composition.")


# EOF
