import streamlit as st
import base64
from utils import ConvertToBlot


def main():
    st.set_page_config(
        page_title="SVG/PNG to Blot Converter", page_icon="✍️", layout="wide"
    )
    st.title("SVG/PNG to Blot Converter")
    st.subheader("Created by Sayed Hashim :)")
    uploaded_file = st.file_uploader("Upload SVG or PNG file", type=["svg", "png"])

    if uploaded_file:
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1].lower()
        file_content = uploaded_file.read()
        uploaded_file.seek(0)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"{file_extension.upper()} Preview")
            if file_extension == "svg":
                b64_content = base64.b64encode(file_content).decode()
                st.markdown(
                    f'<img src="data:image/svg+xml;base64,{b64_content}" style="max-width: 100%; height: auto;">',
                    unsafe_allow_html=True,
                )
            elif file_extension == "png":
                st.image(uploaded_file, use_container_width=True)

        try:
            blot = ConvertToBlot(file=uploaded_file, file_type=file_extension)

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
                    data=str(blot.polylines).encode(),
                    file_name="blot_output.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        except Exception as e:
            st.error(f"Error converting {file_extension.upper()}: {str(e)}")

    with st.expander("Instructions"):
        st.markdown(
            """
        1. Upload an SVG or PNG file using the file uploader above
        2. Preview the file on the left
        3. The converted Blot JavaScript code will appear on the right
        4. Download the JavaScript code using the download button
        """
        )


if __name__ == "__main__":
    main()