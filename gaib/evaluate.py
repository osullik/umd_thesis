import os
import json
import pandas as pd
from plotnine import ggplot, aes,  scale_x_log10, scale_y_log10, labs, scale_color_gradient, element_text, position_nudge
from plotnine import geom_boxplot, geom_point, geom_smooth, geom_text #Geoms
from plotnine import theme, theme_xkcd, theme_minimal, theme_void, theme_classic #Themes

def load_experiments_to_dict(data_source:os.path)->dict:
    experiment_results = {}
    for file in os.listdir(data_source):
        if file.endswith(".json"):
            with open(os.path.join(data_source,file),"r") as f:
                experiment_data = json.load(f)
        experiment_results[file.replace(".json","")] = experiment_data
    
    return experiment_results

def extract_experiments_to_dataframe(experiment_results:dict)->pd.DataFrame:
    experiments = []
    exp_no = []
    datasets = []
    sod = []
    vertices = []
    edges = []
    gt_comms = []
    results = []
    results_nmi = []
    results_nc = []
    ef_tx = []
    ef_etl = []
    ef_et = []
    ef_bl = []
    ef_br = []
    shapes = []
    alg_type = []
    for i, exp in enumerate(experiment_results.keys()):
        for res in experiment_results[exp]['effectiveness']:
            #Effectiveness:
            if 'final' in res: 
                results.append("termination")
            else:
                results.append(res)
            results_nmi.append(experiment_results[exp]['effectiveness'][res]['nmi'])
            results_nc.append(experiment_results[exp]['effectiveness'][res]['num_communities'])

            #Efficency:
            ef_tx.append(experiment_results[exp]['efficiency']['Transfer'])
            ef_etl.append(experiment_results[exp]['efficiency']['ETL'])
            ef_et.append(experiment_results[exp]['efficiency']['Processing'])
            ef_bl.append(experiment_results[exp]['efficiency']['Batch_Latency'])
            ef_br.append(experiment_results[exp]['efficiency']['Batch_Rate'])

            #Dataset Detail
            datasets.append(os.path.basename(experiment_results[exp]["datasets"]['dataset']).replace(".txt",""))
            sod.append(experiment_results[exp]["datasets"]['size_on_disk'])
            vertices.append(experiment_results[exp]["datasets"]['node_count'])
            edges.append(experiment_results[exp]["datasets"]['edge_count'])
            gt_comms.append(experiment_results[exp]["datasets"]['gt_community_count'])
            if 'city' in exp or 'county' in exp:
                shapes.append('mesh')
            else:
                shapes.append('scale-free')
            
            if 'INCREMENTAL' in exp:
                alg_type.append("incremental")
            else:
                alg_type.append('static')

            #Experiment Detail    
            experiments.append(exp.replace("_RESULTS",""))
            exp_no.append(i)

    flat_results_dict = {}
    flat_results_dict['exp_num'] = exp_no
    flat_results_dict['experiment'] = experiments
    flat_results_dict['alg_type'] = alg_type
    flat_results_dict['iteration'] = results
    flat_results_dict['datasets'] = datasets
    flat_results_dict['shape'] = shapes
    flat_results_dict['mb_on_disk'] = sod
    flat_results_dict['vertices'] = vertices
    flat_results_dict['edges'] = edges
    flat_results_dict['gt_comms'] = gt_comms
    flat_results_dict['results_nmi'] = results_nmi
    flat_results_dict['results_nc'] = results_nc
    flat_results_dict['ef_tx'] = ef_tx
    flat_results_dict['ef_etl'] = ef_etl
    flat_results_dict['ef_et'] = ef_et
    flat_results_dict['ef_bl'] = ef_bl
    flat_results_dict['ef_br'] = ef_br

    experiments_df = pd.DataFrame.from_dict(flat_results_dict)

    return experiments_df

def plot_et_against_vertices(experiment_df:pd.DataFrame):
    scatter_plot = (
        ggplot(experiments_df, aes(x='vertices', y='ef_et')) + 
        geom_point(aes(color='shape')) + 
        geom_smooth(se=False) +
        scale_x_log10() + 
        scale_y_log10() +
        labs(x='Vertex Count (log scale)', 
            y='Execution time in Seconds (log Scale)') + # Custom axis labels
        theme_classic()
    )

    return scatter_plot

def plot_et_against_edges(experiment_df:pd.DataFrame):
    scatter_plot = (
        ggplot(experiments_df, aes(x='edges', y='ef_et')) +  
        geom_point(aes(color='shape')) +  
        geom_smooth(se=False) +
        scale_x_log10() +  
        scale_y_log10() +
        labs(x='Edge Count (log scale)', 
            y='Execution time in Seconds (log Scale)') +
        theme_classic()
    )

    return(scatter_plot)

def plot_vertices_against_edges(experiment_df:pd.DataFrame):
    scatter_plot = (
        ggplot(experiments_df, aes(x='edges', y='vertices')) +  
        geom_point(aes(shape='shape')) +  
        scale_x_log10() + 
        scale_y_log10() +
        labs(x='Edge Count (log scale)', 
            y='Vertex Count (log Scale)') +
        theme_classic()
    )

    return(scatter_plot)

def plot_iterations_boxplot(experiment_df:pd.DataFrame):
    experiments_df_sorted = experiments_df.sort_values(by='results_nmi')

    box_plot = (
        ggplot(experiments_df_sorted, aes(x='iteration', y='results_nmi')) +  
        geom_boxplot(aes(color='exp_num')) +  
        scale_y_log10() +
        labs(x='Iteration', 
            y='NMI') + 
        theme_classic() +
        theme(axis_text_x=element_text(angle=45, ha='right'))
    )

    return(box_plot)

def plot_gt_against_predicted_communities(experiment_df:pd.DataFrame):
    filtered_df = experiments_df[experiments_df['iteration'] == 'termination']

    scatter_plot = (
        ggplot(filtered_df, aes(x='results_nc', y='gt_comms')) +  
        geom_point(aes(shape='shape',color='results_nmi')) +  
        scale_x_log10() +  
        scale_y_log10() +
        labs(x='Number of Communities Detected (Log Scale)', 
            y='Ground Truth number of Communities (Log Scale)') + 
        scale_color_gradient(low="red", high="blue") +
        theme_classic()
    )


    return(scatter_plot)

def plot_nmi_against_et(experiment_df:pd.DataFrame):
    # NMI against Total Execution Time
    filtered_df = experiments_df[experiments_df['iteration'] == 'termination']

    scatter_plot = (
        ggplot(filtered_df, aes(x='results_nmi', y='ef_et')) +  
        geom_point(aes(shape='shape')) +  
        scale_y_log10() +
        labs(x='NMI for experiments', 
            y='Total Execution Time (Log Scale)') + 
        theme_classic()
    )

    return(scatter_plot)

def plot_data_size_against_batch_latency(experiment_df:pd.DataFrame):
    # Type of Data Size vs Batch latency
    filtered_df = experiments_df[experiments_df['iteration'] == 'termination']

    scatter_plot = (
        ggplot(filtered_df, aes(x='mb_on_disk', y='ef_bl')) +  
        geom_point(aes(shape='alg_type')) + 
        scale_x_log10() +  
        scale_y_log10() +
        labs(x='Size of Data on Disk (Log Scale)', 
            y='Batch Latencies (Log Scale)') +
        theme_classic()
    )

    # Display the plot
    return(scatter_plot)

def save_plots_as_svg(plots:list, output_dir:os.path):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename, plot in plots:
        plot.save(os.path.join(output_dir,filename))

if __name__ == "__main__":

    DATA_SOURCE = os.path.join(".","experiment_results")
    OUTPUT_DIR = (os.path.join("..","dissertation","Figures","Experiment_Results"))

    experiment_results = load_experiments_to_dict(DATA_SOURCE)
    experiments_df = extract_experiments_to_dataframe(experiment_results)

    plots = []
    plots.append(('et_vs_vertex.svg', plot_et_against_vertices(experiments_df)))
    plots.append(('et_vs_edges.svg', plot_et_against_edges(experiments_df)))
    plots.append(('vertices_vs_edges.svg', plot_vertices_against_edges(experiments_df)))
    plots.append(('iterations_boxplot.svg', plot_iterations_boxplot(experiments_df)))
    plots.append(('gt_vs_predicted_communities.svg', plot_gt_against_predicted_communities(experiments_df)))
    plots.append(('nmi_vs_et.svg', plot_nmi_against_et(experiments_df)))
    plots.append(('bl_vs_sod.svg', plot_data_size_against_batch_latency(experiments_df)))

    save_plots_as_svg(plots=plots, output_dir=OUTPUT_DIR)


