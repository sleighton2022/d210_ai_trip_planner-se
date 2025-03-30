#################################################################################
### Define helper function 
#################################################################################

ef get_id(length: int = 8) -> str:
    """Generate a uuid of a specified length (default=8)."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def parse_crewai_output_to_dictionary(crew, crew_output):
    """
    Parse CrewAI output into a structured dictionary format.
    """
    final_output = {"response": str(crew_output), "predicted_trajectory": []}

    try:
        # Access tools_results directly from each agent
        for agent in crew.agents:
            if hasattr(agent, "tools_results"):
                for tool_result in agent.tools_results:
                    tool_info = {
                        "tool_name": tool_result.get("tool_name", ""),
                        "tool_input": tool_result.get("tool_args", {}),
                    }
                    final_output["predicted_trajectory"].append(tool_info)

    except Exception as e:
        final_output["error"] = f"Error parsing tools results: {str(e)}"

    return final_output


def format_output_as_markdown(output: dict) -> str:
    """Convert the output dictionary to a formatted markdown string."""
    markdown = "### AI Response\n"
    markdown += f"{output['response']}\n\n"

    if output["predicted_trajectory"]:
        markdown += "### Function Calls\n"
        for call in output["predicted_trajectory"]:
            markdown += f"- **Function**: `{call['tool_name']}`\n"
            markdown += "  - **Arguments**:\n"
            for key, value in call["tool_input"].items():
                markdown += f"    - `{key}`: `{value}`\n"

    return markdown


def display_eval_report(eval_result: pd.DataFrame) -> None:
    """Display the evaluation results."""
    metrics_df = pd.DataFrame.from_dict(eval_result.summary_metrics, orient="index").T
    display(Markdown("### Summary Metrics"))
    display(metrics_df)

    display(Markdown(f"### Row-wise Metrics"))
    display(eval_result.metrics_table)


def display_drilldown(row: pd.Series) -> None:
    """Displays a drill-down view for trajectory data within a row."""

    style = "white-space: pre-wrap; width: 800px; overflow-x: auto;"

    if not (
        isinstance(row["predicted_trajectory"], list)
        and isinstance(row["reference_trajectory"], list)
    ):
        return

    for predicted_trajectory, reference_trajectory in zip(
        row["predicted_trajectory"], row["reference_trajectory"]
    ):
        display(
            HTML(
                f"Tool Names:{predicted_trajectory['tool_name'], reference_trajectory['tool_name']}"
            )
        )

        if not (
            isinstance(predicted_trajectory.get("tool_input"), dict)
            and isinstance(reference_trajectory.get("tool_input"), dict)
        ):
            continue

        for tool_input_key in predicted_trajectory["tool_input"]:
            print("Tool Input Key: ", tool_input_key)

            if tool_input_key in reference_trajectory["tool_input"]:
                print(
                    "Tool Values: ",
                    predicted_trajectory["tool_input"][tool_input_key],
                    reference_trajectory["tool_input"][tool_input_key],
                )
            else:
                print(
                    "Tool Values: ",
                    predicted_trajectory["tool_input"][tool_input_key],
                    "N/A",
                )
        print("\n")
    display(HTML(""))


def display_dataframe_rows(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    num_rows: int = 3,
    display_drilldown: bool = False,
) -> None:
    """Displays a subset of rows from a DataFrame, optionally including a drill-down view."""

    if columns:
        df = df[columns]

    base_style = "font-family: monospace; font-size: 14px; white-space: pre-wrap; width: auto; overflow-x: auto;"
    header_style = base_style + "font-weight: bold;"

    for _, row in df.head(num_rows).iterrows():
        for column in df.columns:
            display(
                HTML(
                    f"{column.replace('_', ' ').title()}: "
                )
            )
            display(HTML(f"{row[column]}"))

        display(HTML(""))

        if (
            display_drilldown
            and "predicted_trajectory" in df.columns
            and "reference_trajectory" in df.columns
        ):
            display_drilldown(row)


def plot_bar_plot(
    eval_result: pd.DataFrame, title: str, metrics: list[str] = None
) -> None:
    fig = go.Figure()
    data = []

    summary_metrics = eval_result.summary_metrics
    if metrics:
        summary_metrics = {
            k: summary_metrics[k]
            for k, v in summary_metrics.items()
            if any(selected_metric in k for selected_metric in metrics)
        }

    data.append(
        go.Bar(
            x=list(summary_metrics.keys()),
            y=list(summary_metrics.values()),
            name=title,
        )
    )

    fig = go.Figure(data=data)

    # Change the bar mode
    fig.update_layout(barmode="group")
    fig.show()


def display_radar_plot(eval_results, title: str, metrics=None):
    """Plot the radar plot."""
    fig = go.Figure()
    summary_metrics = eval_results.summary_metrics
    if metrics:
        summary_metrics = {
            k: summary_metrics[k]
            for k, v in summary_metrics.items()
            if any(selected_metric in k for selected_metric in metrics)
        }

    min_val = min(summary_metrics.values())
    max_val = max(summary_metrics.values())

    fig.add_trace(
        go.Scatterpolar(
            r=list(summary_metrics.values()),
            theta=list(summary_metrics.keys()),
            fill="toself",
            name=title,
        )
    )
    fig.update_layout(
        title=title,
        polar=dict(radialaxis=dict(visible=True, range=[min_val, max_val])),
        showlegend=True,
    )
    fig.show()

#################################################################################
### Call the agent 
#################################################################################


#################################################################################
### Prepare agent evaluation dataset 
#################################################################################


#################################################################################
### Prepare agent function
#################################################################################

#################################################################################
### Run and agent evaluation task
#################################################################################

single_tool_usage_metrics = [TrajectorySingleToolUse(tool_name="get_product_price")]

EXPERIMENT_RUN = f"single-metric-eval-{get_id()}"

single_tool_call_eval_task = EvalTask(
    dataset=eval_sample_dataset,
    metrics=single_tool_usage_metrics,
    experiment=EXPERIMENT_NAME,
)

single_tool_call_eval_result = single_tool_call_eval_task.evaluate(
    runnable=agent_parsed_response, experiment_run_name=EXPERIMENT_RUN
)

display_eval_report(single_tool_call_eval_result)

#################################################################################
### Visualize evaluation results 
#################################################################################

display_dataframe_rows(single_tool_call_eval_result.metrics_table, num_rows=3)

#################################################################################
### Tragectory evaluation
#################################################################################

trajectory_metrics = [
    "trajectory_exact_match",
    "trajectory_in_order_match",
    "trajectory_any_order_match",
    "trajectory_precision",
    "trajectory_recall",
]

EXPERIMENT_NAME = "evaluate-re-agent-trajectory"  # @param {type:"string"}

trajectory_eval_task = EvalTask(
    dataset=eval_sample_dataset, metrics=trajectory_metrics, experiment=EXPERIMENT_NAME
)

trajectory_eval_result = trajectory_eval_task.evaluate(runnable=agent_parsed_response)

display_eval_report(trajectory_eval_result)

#################################################################################
### Visualize evaluation results 
#################################################################################

display_dataframe_rows(trajectory_eval_result.metrics_table, num_rows=3)

plot_bar_plot(
    trajectory_eval_result,
    title="Trajectory Metrics",
    metrics=[f"{metric}/mean" for metric in trajectory_metrics],
)

#################################################################################
### Final response evaluation
#################################################################################

response_metrics = ["safety", "coherence"]

EXPERIMENT_NAME = "evaluate-re-agent-response"  # @param {type:"string"}

response_eval_task = EvalTask(
    dataset=eval_sample_dataset, metrics=response_metrics, experiment=EXPERIMENT_NAME
)

response_eval_result = response_eval_task.evaluate(runnable=agent_parsed_response)

display_eval_report(response_eval_result)

display_dataframe_rows(response_eval_result.metrics_table, num_rows=3)


