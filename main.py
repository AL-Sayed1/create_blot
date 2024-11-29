import streamlit as st
import base64
from utils import SVGToBlot


def main():
    st.set_page_config(
        page_title="SVG to Blot Converter", page_icon="✍️", layout="wide"
    )
    st.title("SVG to Blot Converter")
    st.subheader("Created by Sayed Hashim :)")
    uploaded_file = st.file_uploader("Upload SVG file", type=["svg"])

    if uploaded_file:
        svg_content = uploaded_file.read()
        uploaded_file.seek(0)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("SVG Preview")
            b64_svg = base64.b64encode(svg_content).decode()
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{b64_svg}" style="max-width: 100%; height: auto;">',
                unsafe_allow_html=True,
            )

        try:
            blot = SVGToBlot(uploaded_file)

            with col2:

                st.download_button(
                    label="Download JavaScript",
                    data=blot.blot_js.encode(),
                    file_name="blot_output.js",
                    mime="text/javascript",
                    use_container_width=True,
                )
                st.download_button(
                    label="Download polyline data only",
                    data=blot.polylines.encode(),
                    file_name="blot_output.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        except Exception as e:
            st.error(f"Error converting SVG: {str(e)}")

    with st.expander("Instructions"):
        st.markdown(
            """
        1. Upload an SVG file using the file uploader above
        2. Preview the SVG on the left
        3. The converted Blot JavaScript code will appear on the right
        4. Download the JavaScript code using the download button
        """
        )


if __name__ == "__main__":
    main()
