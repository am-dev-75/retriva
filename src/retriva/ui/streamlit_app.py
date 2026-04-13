# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
import sys
from pathlib import Path

# Ensures 'src' is importable when running `streamlit run src/retriva/ui/streamlit_app.py`
src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from retriva.logger import setup_logging, get_logger
from retriva.qa.answerer import ask_question
from retriva.config import settings, VERSION

setup_logging()
logger = get_logger(__name__)
logger.info("Starting Streamlit UI...")

st.set_page_config(
    page_title="Retriva - Q&A PoC",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .citation-box {
        font-size: 0.85em;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-left: 3px solid #00f2fe;
        margin-top: 10px;
        margin-bottom: 20px;
        border-radius: 4px;
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

st.title(f"🔍 Retriva {VERSION}")
st.markdown("A grounded RAG chatbot answering exclusively from the custom knowledge base.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "debug_chunks" in msg and msg["debug_chunks"]:
            with st.expander("View Retrieval Context & Citations"):
                for idx, chunk in enumerate(msg["debug_chunks"]):
                    title = chunk.get("page_title", "Unknown")
                    url = chunk.get("canonical_doc_id", "Unknown")
                    lang = chunk.get("language", "en")
                    text = chunk.get("text", "")
                    st.markdown(f"**[{idx+1}] {title}** (`{lang}`)  \n`{url}`")
                    st.markdown(f"<div class='citation-box'>{text[:300]}...</div>", unsafe_allow_html=True)

if prompt := st.chat_input("Ask a question about the mirrored corpus (English or Italian)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Searching local mirror..."):
            try:
                response_data = ask_question(prompt, settings.retriever_top_k)
                answer = response_data["answer"]
                chunks = response_data["retrieved_chunks"]
                grounding = response_data.get("grounding", {})
                
                st.markdown(answer)
                
                # Grounding validation badge
                if grounding:
                    if grounding.get("grounded"):
                        st.success(
                            f"✅ Grounded — {len(grounding.get('citations_found', []))} citation(s), "
                            f"{grounding.get('overlap_score', 0):.0%} overlap"
                        )
                    elif grounding.get("is_refusal"):
                        st.info("ℹ️ The model declined to answer due to insufficient evidence.")
                    else:
                        st.warning("⚠️ Grounding check failed — answer may not be fully supported by the knowledge base.")
                        for w in grounding.get("warnings", []):
                            st.caption(f"• {w}")
                
                if chunks:
                    with st.expander("View Retrieval Context & Citations"):
                        for idx, chunk in enumerate(chunks):
                            title = chunk.get("page_title", "Unknown")
                            url = chunk.get("canonical_doc_id", "Unknown")
                            lang = chunk.get("language", "en")
                            text = chunk.get("text", "")
                            st.markdown(f"**[{idx+1}] {title}** (`{lang}`)  \n`{url}`")
                            st.markdown(f"<div class='citation-box'>{text[:300]}...</div>", unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "debug_chunks": chunks
                })
            except Exception as e:
                st.error(f"Error computing answer: {e}")
