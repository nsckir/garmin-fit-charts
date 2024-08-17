import io

import fitdecode
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide")


def format_column_name(col):
    return " ".join(word.capitalize() for word in col.split("_"))


def process_fit_file(file):
    records = []
    units = {}

    with fitdecode.FitReader(file) as fit:
        for frame in fit:
            if frame.frame_type == fitdecode.FIT_FRAME_DATA and frame.name == "record":
                record = {}
                for field in frame:
                    record[field.name] = field.value
                    units[field.name] = field.units
                records.append(record)

    df = pd.DataFrame(records)
    # Format column names
    df.columns = [format_column_name(col) for col in df.columns]

    # Update units dictionary keys
    units = {format_column_name(k): v for k, v in units.items()}
    return df, units


def create_plot(df, x_col, y_cols, shared_y_axis, smooth_data, ma_window):
    fig = go.Figure()

    for i, y_col in enumerate(y_cols):
        y_data = df[y_col]
        if smooth_data:
            y_data = y_data.rolling(window=ma_window, center=True).mean()

        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=y_data,
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


st.title("FIT File Data Analysis")

uploaded_file = st.file_uploader("Choose a FIT file", type="fit")

if uploaded_file is not None:
    # Process the uploaded file
    df, units = process_fit_file(io.BytesIO(uploaded_file.read()))

    # Get all available columns not starting with "Unknown"
    available_columns = [col for col in df.columns if not col.startswith("Unknown")]

    # Select x-axis
    x_col = st.selectbox(
        "Select X-axis",
        available_columns,
        index=(
            available_columns.index("Timestamp")
            if "Timestamp" in available_columns
            else 0
        ),
    )

    # Select up to 2 y-axes
    y_cols = st.multiselect(
        "Select up to 2 Y-axes",
        available_columns,
        default=["Heart Rate"] if "Heart Rate" in available_columns else [],
    )

    if len(y_cols) > 2:
        st.warning("Please select up to 2 Y-axes only. Using the first 2 selected.")
        y_cols = y_cols[:2]

    # Toggle for shared y-axis
    shared_y_axis = st.checkbox("Use shared Y-axis", value=True)

    # Add checkbox for data smoothing
    smooth_data = st.checkbox("Smooth data", value=False)

    # Add input field for moving average window size
    ma_window = 1
    if smooth_data:
        ma_window = st.number_input(
            "Moving average window size", min_value=1, max_value=100, value=5
        )

    if y_cols:
        # Get units for the selected columns
        x_unit = units.get(x_col, "")
        y_units = [units.get(col, "") for col in y_cols]

        # Create and display the plot
        fig = create_plot(df, x_col, y_cols, shared_y_axis, smooth_data, ma_window)

        # Update axis titles with units
        x_axis_title = f"{x_col} ({x_unit})" if x_unit else x_col
        fig.update_layout(
            xaxis_title=x_axis_title,
            yaxis_title=f"{y_cols[0]} ({y_units[0]})" if y_units[0] else y_cols[0],
        )

        if not shared_y_axis and len(y_cols) > 1:
            y2_axis_title = f"{y_cols[1]} ({y_units[1]})" if y_units[1] else y_cols[1]
            fig.update_layout(
                yaxis2=dict(
                    title=y2_axis_title,
                    side="right",
                    overlaying="y",
                )
            )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one Y-axis to plot.")
