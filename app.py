import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import random


# table for input data
if "jobs_df" not in st.session_state:
    st.session_state["jobs_df"] = pd.DataFrame(columns=["ID", "Name", "Dependencies"])
# flag for job update
if "jobs_updated" not in st.session_state:
    st.session_state["jobs_updated"] = False

def process_jobs_from_input(jobs_df):
    jobs = []
    for _, row in jobs_df.iterrows():
        job_id = row["ID"]
        job_name = row["Name"]
        dependencies = row["Dependencies"].split(',') if row["Dependencies"] else []
        jobs.append((job_id, job_name, dependencies))
    return jobs

def validate_dependencies(jobs_df):
    job_ids = set(jobs_df["ID"])  # Set of all job IDs for quick lookup
    invalid_dependencies = {}  # Dictionary to store invalid dependencies for each job

    for _, row in jobs_df.iterrows():
        job_id = row["ID"]
        dependencies = row["Dependencies"].split(',') if row["Dependencies"] else []
        # Find dependencies that are not in the job IDs
        invalid_deps = [dep.strip() for dep in dependencies if dep.strip() not in job_ids]
        if invalid_deps:
            invalid_dependencies[job_id] = invalid_deps

    return invalid_dependencies

def build_dependency_graph(jobs):
    G = nx.DiGraph()
    job_id_to_name = {}  

    for job_id, job_name, dependencies in jobs:
        job_id_to_name[job_id] = job_name  
        G.add_node(job_id, label=job_name)

        for dep in dependencies:
            if dep:
                G.add_edge(dep, job_id)  
    return G, job_id_to_name

def assign_layers(G):
    layers = {}
    for node in nx.topological_sort(G):
        if G.in_degree(node) == 0:
            layers[node] = 0
        else:
            layers[node] = max(layers[pred] for pred in G.predecessors(node)) + 1
    return layers   

def draw_layered_graph(G, layers, job_id_to_name, orientation):
    layer_colors = ['lightblue', 'lightgreen', 'salmon', 'grey', 'cyan', 'yellow']
    random.shuffle(layer_colors)

    # Define position mapping based on orientation
    if orientation == "Top to Bottom":
        pos = {node: (i, -layers[node]) for i, node in enumerate(G.nodes())}
    elif orientation == "Bottom to Top":
        pos = {node: (i, layers[node]) for i, node in enumerate(G.nodes())}
    elif orientation == "Left to Right":
        pos = {node: (layers[node], -i) for i, node in enumerate(G.nodes())}
    elif orientation == "Right to Left":
        pos = {node: (-layers[node], -i) for i, node in enumerate(G.nodes())}

    node_colors = [layer_colors[layers[node] % len(layer_colors)] for node in G.nodes()]

    labels = {node: job_id_to_name.get(node, node) for node in G.nodes()}
    plt.figure(figsize=(10, 7))
    nx.draw(G, pos, labels=labels, with_labels=True, node_color=node_colors, node_size=2000, font_size=10, font_weight='bold', arrows=True)
    plt.title('Job Dependency Layered Graph')
    plt.show()

def visualize_jobs(jobs_df, orientation):    
    jobs = process_jobs_from_input(jobs_df)
    G, job_id_to_name = build_dependency_graph(jobs)
    layers = assign_layers(G)

    # Adjust layers to start from 1
    layers = {node: layer + 1 for node, layer in layers.items()}

    # Create a DataFrame with the specified column order
    ordered_jobs = sorted(layers.items(), key=lambda x: x[1])  # Sort by layers
    ordered_jobs_df = pd.DataFrame(ordered_jobs, columns=['Job ID', 'Layer'])
    ordered_jobs_df['Name'] = ordered_jobs_df['Job ID'].map(job_id_to_name)  # Add Name column
    ordered_jobs_df = ordered_jobs_df[['Layer', 'Job ID', "Name"]]  # Change column order

    # Draw the graph
    draw_layered_graph(G, layers, job_id_to_name, orientation)

    return ordered_jobs_df  # Return the ordered DataFrame

def main():
    st.title("Job Dependency Visualizer")
    st.write("Enter job details and dependencies.")
    
    edited_jobs_df = st.data_editor(st.session_state["jobs_df"], num_rows="dynamic",hide_index=True)

    if st.button("Generate Graph"):
        edited_jobs_df.dropna(subset=['ID', 'Name'], inplace=True)
        edited_jobs_df = edited_jobs_df.reset_index(drop=True)
        invalid_dependencies = validate_dependencies(edited_jobs_df)

        if edited_jobs_df.empty or edited_jobs_df.isnull().all().all():
            st.error("Please enter job details and dependencies.")
        elif invalid_dependencies:
            error_message = "Invalid dependencies found:\n"
            for job_id, deps in invalid_dependencies.items():
                error_message += f"Job ID {job_id} has invalid dependencies: {', '.join(deps)}\n"
            st.error(error_message)
            st.session_state["jobs_updated"] = False
        else:
            st.session_state["jobs_df"] = edited_jobs_df
            st.session_state["jobs_updated"] = True
            st.success("Jobs updated successfully.")


    if st.session_state.get("jobs_updated"):
            ordered_jobs_df = visualize_jobs(st.session_state["jobs_df"], "Top to Bottom")
            st.subheader("Ordered Jobs for Execution")
            st.dataframe(ordered_jobs_df)

            orientation = st.selectbox("Select Graph Orientation", ["Top to Bottom", "Bottom to Top", "Left to Right", "Right to Left"])

            ordered_jobs_df = visualize_jobs(st.session_state["jobs_df"], orientation)
            st.pyplot(plt)

if __name__ == "__main__":
    main()
