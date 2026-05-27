"""Streamlit UI for the PDF financial statement extractor."""
import csv
import io
import tempfile
from pathlib import Path

import streamlit as st

from extractor import extract_from_pdf

st.set_page_config(page_title="Wisely Extractor", layout="centered")
st.title("Wisely — Statement Extractor")
st.caption("Upload a PDF statement to extract structured account data.")

uploaded = st.file_uploader("Drop a PDF statement here", type="pdf")

if uploaded:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = Path(tmp.name)

    with st.spinner("Extracting…"):
        try:
            result = extract_from_pdf(tmp_path)
        except RuntimeError as e:
            st.error(str(e))
            st.stop()
        finally:
            tmp_path.unlink(missing_ok=True)

    st.markdown(f"**Document type:** {result.document_type}")

    if result.unmatched:
        st.warning(f"Not a financial account statement — {result.unmatched_summary}")
    elif not result.accounts:
        st.warning("No accounts found in this document.")
    else:
        rows = [
            {
                "ASSET CLASS": a.asset_class,
                "BROKER": a.broker,
                "ACCOUNT HOLDER": a.account_holder,
                "AMOUNT": a.amount,
                "Notes": a.notes or "",
            }
            for a in result.accounts
        ]

        low_conf = [
            r for r in rows
            if "unmatched asset_class" in r["Notes"] or "normalized from" in r["Notes"]
        ]
        if low_conf:
            classes = ", ".join(r["ASSET CLASS"] for r in low_conf)
            st.warning(f"Low-confidence asset class normalization: {classes} — review Notes column.")

        st.dataframe(rows, use_container_width=True)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["ASSET CLASS", "BROKER", "ACCOUNT HOLDER", "AMOUNT", "Notes"])
        writer.writeheader()
        writer.writerows(rows)

        st.download_button(
            label="Download CSV",
            data=buf.getvalue(),
            file_name=f"{uploaded.name.removesuffix('.pdf')}_extracted.csv",
            mime="text/csv",
        )
