import streamlit as st
import fitdecode
import pandas as pd
import plotly.graph_objects as go
import io

# Add this line at the beginning of your script, right after the imports
st.set_page_config(layout="wide")


def process_fit_file(file):
    records = []

    with fitdecode.FitReader(file) as fit:
        for frame in fit:
            if frame.frame_type == fitdecode.FIT_FRAME_DATA and frame.name == "record":
                record = {}
                for field in frame:
                    record[f"{field.name}_value"] = field.value
                    record[f"{field.name}_units"] = field.units
                    record[f"{field.name}_raw_value"] = field.raw_value
                records.append(record)

    df = pd.DataFrame(records)
    return df


def create_plot(df, x_col, y_cols, shared_y_axis):
    fig = go.Figure()

    for i, y_col in enumerate(y_cols):
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines",
                name=y_col,
                line=dict(width=1),
                yaxis=f"y{i+1}" if not shared_y_axis and i == 1 else "y",
            )
        )

    # Customize the plot
    fig.update_layout(
        title=f"{' vs '.join(y_cols)} over Time",
        xaxis_title=x_col,
        yaxis_title=y_cols[0],
        legend_title="Measurement Type",
        hovermode="x unified",
    )

    if not shared_y_axis and len(y_cols) > 1:
        fig.update_layout(
            yaxis2=dict(
                title=y_cols[1],
                side="right",
                overlaying="y",
            )
        )

    # Update the axes to be white
    fig.update_xaxes(
        showline=True,
        linewidth=2,
        mirror=True,
    )
    fig.update_yaxes(
        showline=True,
        linewidth=2,
        mirror=True,
    )

    return fig


# Streamlit app
st.title("FIT File Data Analysis")

uploaded_file = st.file_uploader("Choose a FIT file", type="fit")

if uploaded_file is not None:
    # Process the uploaded file
    df = process_fit_file(io.BytesIO(uploaded_file.read()))

    # Get all available columns ending with "_value" and not starting with "unknown"
    available_columns = [
        col
        for col in df.columns
        if col.endswith("_value") and not col.startswith("unknown")
    ]

    # Select x-axis
    x_col = st.selectbox(
        "Select X-axis",
        available_columns,
        index=(
            available_columns.index("timestamp_value")
            if "timestamp_value" in available_columns
            else 0
        ),
    )

    # Select up to 2 y-axes
    y_cols = st.multiselect(
        "Select up to 2 Y-axes",
        available_columns,
        default=["heart_rate_value"] if "heart_rate_value" in available_columns else [],
    )

    if len(y_cols) > 2:
        st.warning("Please select up to 2 Y-axes only. Using the first 2 selected.")
        y_cols = y_cols[:2]

    # Toggle for shared y-axis
    shared_y_axis = st.checkbox("Use shared Y-axis", value=True)

    if y_cols:
        # Create and display the plot
        fig = create_plot(df, x_col, y_cols, shared_y_axis)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one Y-axis to plot.")
