import streamlit as st
import requests
import pandas as pd
import urllib.parse

# ─── API Key ──────────────────────────────────────────────
SERPAPI_KEY = "392e7bff178ec41e7ae534a82a44ebc6bc10f66bfa1b054cf84028824fffee2d"

# ─── Session State Init ───────────────────────────────────
for key, val in {
    "page": 0, "last_query": "", "num_results": 10,
    "search_meta": {}, "results": [], "searched": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─── Page Setup ───────────────────────────────────────────
st.set_page_config(page_title="LinkedIn Finder", page_icon="", layout="centered")

# ─── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
  .main { background-color: #f8f7f4; }
  .title    { font-size: 36px; font-weight: 800; color: #0C447C; }
  .subtitle { color: #5F5E5A; font-size: 16px; margin-bottom: 20px; }
  .tag { display:inline-block; border-radius:20px; padding:3px 10px;
         font-size:12px; margin-right:5px; margin-top:3px; font-weight:500; }
  .tag-blue   { background:#E6F1FB; color:#0C447C; }
  .tag-teal   { background:#E1F5EE; color:#0F6E56; }
  .tag-coral  { background:#FAECE7; color:#993C1D; }
  .tag-gray   { background:#F1EFE8; color:#5F5E5A; }
  .tag-purple { background:#F0E8FA; color:#6C3483; }
  .stats-row  { display:flex; gap:10px; margin:12px 0; flex-wrap:wrap; }
  .stat-chip  { background:white; border:1px solid #e0e0e0; border-radius:20px;
                padding:5px 14px; font-size:13px; font-weight:600; color:#0C447C; }
  .page-indicator { text-align:center; padding:8px 20px; background:white;
                    border:1px solid #E6F1FB; border-radius:20px;
                    font-weight:700; color:#0C447C; font-size:14px; }
  #MainMenu{visibility:hidden;} footer{visibility:hidden;} header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ─── Avatar ───────────────────────────────────────────────
AVATAR_COLORS = ["0C447C","0F6E56","993C1D","7B3F9E",
                 "185FA5","16A085","D35400","C0392B",
                 "2471A3","1E8449","6C3483","5F5E5A"]

def avatar_url(name):
    encoded = urllib.parse.quote(name)
    idx = ord(name[0].upper()) % len(AVATAR_COLORS) if name else 0
    return (f"https://ui-avatars.com/api/?name={encoded}"
            f"&background={AVATAR_COLORS[idx]}&color=fff"
            f"&size=80&rounded=true&bold=true&font-size=0.38&length=2")

# ─── Filter Maps ──────────────────────────────────────────
EXP_KEYWORDS  = {
    "Fresher (0-1 yrs)":    "fresher",
    "Junior (1-3 yrs)":     "junior",
    "Mid Level (3-6 yrs)":  "mid level",
    "Senior (6-10 yrs)":    "senior",
    "Director":             "director",
    "VP / Vice President":  "vice president",
    "C-Suite / Executive":  "CEO OR CTO OR CFO",
}
SIZE_KEYWORDS = {
    "Startup (1-50)":            "startup",
    "Small (50-200)":            "small company",
    "Enterprise (1000-10000)":   "enterprise",
    "Large Enterprise (10000+)": "large enterprise",
}

# ─── Helpers ──────────────────────────────────────────────
def build_query(designation, location, domain, company,
                keywords, exclude, exp_level, comp_size):
    parts = ["site:linkedin.com/in"]
    if designation: parts.append(f'"{designation}"')
    if location:    parts.append(location)
    if domain:      parts.append(f'"{domain}"')
    if company:     parts.append(f'"{company}"')
    if keywords:    parts.append(keywords)
    if EXP_KEYWORDS.get(exp_level):  parts.append(f'"{EXP_KEYWORDS[exp_level]}"')
    if SIZE_KEYWORDS.get(comp_size): parts.append(f'"{SIZE_KEYWORDS[comp_size]}"')
    if exclude:
        for w in exclude.split(","):
            w = w.strip()
            if w: parts.append(f'-"{w}"')
    return " ".join(parts)

def extract_name(title):
    for sep in [" - ", " | ", " – "]:
        if sep in title:
            return title.split(sep)[0].strip()
    return title.strip() or "Unknown"

def search_linkedin(query, num, start):
    try:
        resp = requests.get("https://serpapi.com/search", timeout=15, params={
            "q": query, "api_key": SERPAPI_KEY,
            "engine": "google", "num": num, "start": start
        })
        data = resp.json()
        if "error" in data:
            return None, data["error"]
        results = []
        for item in data.get("organic_results", []):
            link = item.get("link", "")
            if "linkedin.com/in/" in link or "/in/" in link:
                results.append({
                    "Name":         extract_name(item.get("title", "")),
                    "LinkedIn URL": link,
                    "About":        item.get("snippet", ""),
                })
        return results, None
    except Exception as e:
        return None, str(e)

def render_results(results, meta, page, num):
    start     = page * num
    show_from = start + 1
    show_to   = start + len(results)

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-chip"> {len(results)} Profiles</div>
      <div class="stat-chip"> Page {page + 1}</div>
      <div class="stat-chip">#{show_from}–{show_to}</div>
      {"<div class='stat-chip'> " + meta.get('designation','') + "</div>" if meta.get('designation') else ""}
      {"<div class='stat-chip'> " + meta.get('location','') + "</div>" if meta.get('location') else ""}
    </div>
    """, unsafe_allow_html=True)

    for r in results:
        col_img, col_info = st.columns([1, 6])
        with col_img:
            st.markdown(
                f'<div style="margin-top:8px;">'
                f'<img src="{avatar_url(r["Name"])}" '
                f'style="width:62px;height:62px;border-radius:50%;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.12);" /></div>',
                unsafe_allow_html=True
            )
        with col_info:
            tags = ""
            if meta.get("designation"): tags += f'<span class="tag tag-blue"> {meta["designation"]}</span>'
            if meta.get("location"):    tags += f'<span class="tag tag-teal"> {meta["location"]}</span>'
            if meta.get("domain"):      tags += f'<span class="tag tag-coral"> {meta["domain"]}</span>'
            if meta.get("exp_level"):   tags += f'<span class="tag tag-purple"> {meta["exp_level"]}</span>'
            if meta.get("comp_size"):   tags += f'<span class="tag tag-gray">🏗 {meta["comp_size"]}</span>'
            st.markdown(f"**{r['Name']}**")
            st.markdown(f"<small style='color:#5F5E5A'>{r['About'][:180]}...</small>", unsafe_allow_html=True)
            st.markdown(f"{tags}&nbsp;&nbsp;<a href='{r['LinkedIn URL']}' target='_blank'>Open Profile ↗</a>", unsafe_allow_html=True)
        st.divider()

    df  = pd.DataFrame([{"Name": r["Name"], "LinkedIn URL": r["LinkedIn URL"],
                          "About": r["About"]} for r in results])
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", data=csv,
                       file_name="linkedin_results.csv",
                       mime="text/csv", use_container_width=True)

    st.markdown("---")
    p1, p2, p3 = st.columns([2, 3, 2])
    with p1:
        if page > 0:
            if st.button("← Previous", use_container_width=True, key="prev_btn"):
                st.session_state.page -= 1
                res, err = search_linkedin(
                    st.session_state.last_query,
                    st.session_state.num_results,
                    st.session_state.page * st.session_state.num_results
                )
                if not err and res:
                    st.session_state.results = res[:st.session_state.num_results]
                st.rerun()
    with p2:
        st.markdown(
            f'<div class="page-indicator">Page {page + 1} &nbsp;·&nbsp; {show_from}–{show_to}</div>',
            unsafe_allow_html=True
        )
    with p3:
        if len(results) > 0:
            if st.button("Next →", use_container_width=True, key="next_btn"):
                st.session_state.page += 1
                res, err = search_linkedin(
                    st.session_state.last_query,
                    st.session_state.num_results,
                    st.session_state.page * st.session_state.num_results
                )
                if not err and res:
                    st.session_state.results = res[:st.session_state.num_results]
                st.rerun()

# ══════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════
st.markdown('<div class="title">LinkedIn Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Find LinkedIn profiles by Designation, Location & Domain</div>', unsafe_allow_html=True)
st.divider()

if not st.session_state.searched or st.session_state.page == 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        designation = st.text_input(" Designation / Role", placeholder="e.g. CEO")
    with col2:
        location = st.text_input(" Location", placeholder="e.g. New Delhi")
    with col3:
        domain = st.text_input(" Domain / Industry", placeholder="e.g. fintech")

    with st.expander("Advanced Filters"):
        acol1, acol2 = st.columns(2)
        with acol1:
            company   = st.text_input(" Company Name", placeholder="e.g. Google")
            exp_level = st.selectbox(" Experience Level", [
                "", "Fresher (0-1 yrs)", "Junior (1-3 yrs)", "Mid Level (3-6 yrs)",
                "Senior (6-10 yrs)", "Director", "VP / Vice President", "C-Suite / Executive"
            ])
        with acol2:
            keywords  = st.text_input(" Extra Keywords", placeholder="e.g. IIT founder")
            comp_size = st.selectbox("Company Size", [
                "", "Startup (1-50)", "Small (50-200)",
                "Enterprise (1000-10000)", "Large Enterprise (10000+)"
            ])
            exclude = st.text_input("Exclude Words", placeholder="e.g. intern, student")

    num_results = st.selectbox("Number of Results", [5, 10, 15, 20], index=1)

    if designation or location or domain:
        st.code(build_query(designation, location, domain, company,
                            keywords, exclude, exp_level, comp_size), language=None)

    st.divider()

    if st.button("Search LinkedIn", type="primary", use_container_width=True):
        if not designation and not location and not domain:
            st.error("Please fill in at least one field!")
        else:
            st.session_state.page        = 0
            st.session_state.num_results = num_results
            st.session_state.last_query  = build_query(
                designation, location, domain, company,
                keywords, exclude, exp_level, comp_size
            )
            st.session_state.search_meta = {
                "designation": designation, "location": location,
                "domain": domain, "exp_level": exp_level, "comp_size": comp_size
            }
            st.session_state.searched = True

            with st.spinner("Searching LinkedIn profiles..."):
                results, error = search_linkedin(
                    st.session_state.last_query, num_results, start=0
                )

            if error:
                st.error(f"Error: {error}")
            elif not results:
                st.warning("No profiles found. Try broader search terms.")
            else:
                st.session_state.results = results[:num_results]
                st.rerun()

if st.session_state.searched and st.session_state.results:
    if st.button("New Search", use_container_width=False):
        st.session_state.searched   = False
        st.session_state.page       = 0
        st.session_state.results    = []
        st.session_state.last_query = ""
        st.rerun()

    render_results(
        st.session_state.results,
        st.session_state.search_meta,
        st.session_state.page,
        st.session_state.num_results
    )