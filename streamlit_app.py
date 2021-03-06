import streamlit as st

# import suggests
# from suggests import suggests

from suggests import (
    add_parent_nodes,
    suggests,
    to_edgelist,
    get_suggests_tree,
    add_metanodes,
)

# from suggests import suggests,

# from suggests import get_google_url
import json
import pandas as pd
import time
import csv
import base64


import matplotlib as plt
import seaborn as sns

from pyecharts import options as opts
from pyecharts.charts import Tree
from streamlit_echarts import st_echarts


def _max_width_():
    max_width_str = f"max-width: 1400px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )


_max_width_()

# st.set_page_config(
#     page_title="StreamSuggest: Google & Bing Autocomplete suggestions at scale!",
#     page_icon="🧊",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )


# region Top area ############################################################

# endregion Top area ############################################################

st.title("StreamSuggest")
st.write("Google & Bing autocomplete suggestions at scale!")
st.write("https://github.com/gitronald/suggests")
st.header("")


def custom_get_google_url():
    # Retrieve language from session state, or set lang to 'en' by default
    lang = st.session_state.get("google_url_language", "fr")
    # return f"https://www.google.com/complete/search?sclient=psy-ab&hl={lang}&q="
    return f"https://www.google.com/complete/search?sclient=psy-ab&gl={lang}&q="


# Select your language, and store it in session state as 'google_url_language'
st.selectbox("Language", ["en", "fr", "es"], key="google_url_language")
#
# Here we replace suggests's function by our own
suggests.get_google_url = custom_get_google_url
#
# s = suggests.get_suggests("paris", source="google")
# s


c1, c2, c3 = st.columns(3)

with c1:
    keyword = st.text_input("Keyword", value="pain")
with c2:
    SearchEngine = st.selectbox("Search Engine", ("Google", "Bing"))

SearchEngineLowerCase = []

with c2:
    if SearchEngine == "Bing":
        SearchEngineLowerCase.append("bing")
    else:
        SearchEngineLowerCase.append("google")

with c3:
    maxDepth = st.number_input(
        "Crawl Depth (2 leafs max for now)",
        min_value=1,
        max_value=3,
        value=1,
        step=1,
        key=None,
    )


c10, c11, c12 = st.columns(3)

with c10:
    c = st.container()

button1 = st.button("Fetch suggestions")

if not keyword:
    c.success("🔼 Type a keyword")
    st.stop()

if keyword and not button1:
    c.success("🔽 'Fetch Suggestions'")
    st.stop()

# Patch suggests to support latin1 decoding
def suggests_tree(*args, **kwargs):
    try:
        old_loads = json.loads

        def new_loads(s, *args, **kwargs):
            if isinstance(s, bytes):
                s = s.decode("latin1")
            return old_loads(s, *args, **kwargs)

        json.loads = new_loads

        return get_suggests_tree(*args, **kwargs)

    finally:
        json.loads = old_loads


# tree = suggests_tree("français", source="google", max_depth=1)
tree = suggests_tree(keyword, source="google", max_depth=1)

edges = to_edgelist(tree)
edges = add_parent_nodes(edges)
edges = edges.apply(add_metanodes, axis=1)
show_restricted_colsFullDF = [
    "root",
    "edge",
    "rank",
    "depth",
    "search_engine",
    "datetime",
    "parent",
    "source_add",
    "target_add",
]
edges = edges[show_restricted_colsFullDF]
edges = edges.dropna()
show_restricted_cols1level = ["source_add", "target_add"]
show_restricted_cols2levels = ["parent", "source_add", "target_add"]

if maxDepth == 2:
    dflimitedcolumns = edges[show_restricted_cols2levels]
    dfNoneRemoved = dflimitedcolumns.dropna()
else:
    dflimitedcolumns = edges[show_restricted_cols1level]
    dfNoneRemoved = dflimitedcolumns.dropna()

edges["datetime"] = pd.to_datetime(edges["datetime"])

edges = edges.rename(
    {
        "root": "Root Keyword",
        "edge": "Full GSuggest String",
        "rank": "Rank (Lvl 03)",
        #'depth': 'Depth',
        "search_engine": "Search Engine",
        "datetime": "Date & Time scraped",
        "parent": "Level 01",
        "source_add": "Level 02",
        "target_add": "Level 03",
    },
    axis=1,
)

edges = edges[
    [
        "Root Keyword",
        "Level 01",
        "Level 02",
        "Level 03",
        "Rank (Lvl 03)",
        #'Depth',
        "Full GSuggest String",
        "Search Engine",
        "Date & Time scraped",
    ]
]


class Node(object):
    def __init__(self, name, size=None):
        self.name = name
        self.children = []
        self.size = size

    def child(self, cname, size=None):
        child_found = [c for c in self.children if c.name == cname]
        if not child_found:
            _child = Node(cname, size)
            self.children.append(_child)
        else:
            _child = child_found[0]
        return _child

    def as_dict(self):
        res = {"name": self.name}
        if self.size is None:
            res["children"] = [c.as_dict() for c in self.children]
        else:
            res["size"] = self.size
        return res


root = Node(keyword)

if maxDepth == 2:
    for index, row in dfNoneRemoved.iterrows():
        grp1, grp3, size = row
        root.child(grp1).child(grp3, size)
else:
    for index, row in dfNoneRemoved.iterrows():
        grp3, size = row
        root.child(grp3, size)

jsonString = json.dumps(root.as_dict(), indent=4)
jsonJSON = json.loads(jsonString)

opts = {
    "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
    "series": [
        {
            "type": "tree",
            "data": [jsonJSON],
            "top": "1%",
            "left": "7%",
            "bottom": "1%",
            "right": "20%",
            "symbolSize": 9,
            "label": {
                "position": "left",
                "verticalAlign": "middle",
                "align": "right",
                "fontSize": 12,
            },
            "toolbox": {
                "show": True,
                "feature": {
                    "dataZoom": {"yAxisIndex": "none"},
                    "restore": {},
                    "saveAsImage": {},
                },
            },
            "leaves": {
                "label": {
                    "position": "right",
                    "verticalAlign": "middle",
                    "align": "left",
                }
            },
            "expandAndCollapse": True,
            "animationDuration": 550,
            "animationDurationUpdate": 750,
        }
    ],
}

st.markdown("---")

st.markdown("## **🌳 Interactive Tree View**")

with st.expander("ℹ️ - How to use the Tree view ", expanded=True):

    st.write(
        """       
-  You can click on each node to nest or expand each leaf  
-  You can also save your preferred view as jpeg by right-clicking on the chart! 📷
        """
    )

st.markdown("")

st_echarts(opts, height=1000)
edges = edges.reset_index(drop=True)
cm = sns.light_palette("green", as_cmap=True)
edgescoloured = edges.style.background_gradient(cmap="Blues")

st.markdown("---")

try:
    csv = edges.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    st.markdown("## **🎁 Download all results to CSV **")
    st.subheader("")
    href = f'<a href="data:file/csv;base64,{b64}" download="filtered_table.csv">** ⯈ Download link **</a>'
    st.markdown(href, unsafe_allow_html=True)

except NameError:
    print("wait")

st.markdown("---")
st.markdown("## **👇 Or check results below**")
st.subheader("")
st.table(edgescoloured)

c.success("✅ Nice! Your suggestions have been retrieved!")