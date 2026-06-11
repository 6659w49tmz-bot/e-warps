import webview


APP_TITLE = "E-WARPS"

# Normal mode keeps Streamlit sidebar controls visible.
APP_URL = "https://jqzjrhs7bjxjm58r3yd2kb.streamlit.app"


def main():
    webview.create_window(
        title=APP_TITLE,
        url=APP_URL,
        width=1280,
        height=800,
        resizable=True,
        fullscreen=False,
        text_select=True
    )

    webview.start(debug=False)


if __name__ == "__main__":
    main()