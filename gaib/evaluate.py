import os
import json
import pandas as pd
from plotnine import ggplot, aes,  scale_x_log10, scale_y_log10, labs, scale_color_gradient, element_text, position_nudge, scale_fill_manual, guides, guide_legend
from plotnine import geom_boxplot, geom_point, geom_smooth, geom_text, geom_line, geom_bar #Geoms
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
    ef_total = []
    shapes = []
    alg_type = []
    hw_type = []
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
            ef_total.append(experiment_results[exp]['efficiency']['Experiment_Length'])

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

            if 'GPU' in exp:
                hw_type.append("GPU")
            elif 'CLUSTER'.casefold() in exp.casefold():
                hw_type.append("CLUSTER")
            else:
                hw_type.append("CPU")


    flat_results_dict = {}
    flat_results_dict['exp_num'] = exp_no
    flat_results_dict['experiment'] = experiments
    flat_results_dict['hw_type'] = hw_type
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
    flat_results_dict['ef_total'] = ef_total

    

    experiments_df = pd.DataFrame.from_dict(flat_results_dict)

    return experiments_df



#######################
### NEW EXPERIMENTS ###
#######################

def plot_exec_time_by_experiment(experiments_df:pd.DataFrame)->ggplot:

    custom_legend_labels = {
        'CPU': '12 Core M2 Max (Baseline)',
        'CLUSTER': '16 Core Intel Xeon Silver',
        'GPU': 'NVIDIA RTXA5000'
    }

    custom_dataset_labels = {
        "Delaware_adj_list":"OSM-DE",
        "District of Columbia_adj_list":"OSM-DC",
        "Maryland_adj_list":"OSM-MD",
        "Massapequa_adj_list":"OSM-M",
        "Rhode Island_adj_list":"OSM-RI",
        "Washington_adj_list":"OSM-WA",
        "wiki-topcats":"Wiki-Topcats",
        "email-Eu-core":"Email-EU-Core"
    }

    filtered_df = experiments_df[experiments_df['alg_type'] == 'static']
    filtered_df['custom_datasets'] = filtered_df['datasets'].map(custom_dataset_labels)


    # Define custom legend labels
    
    
    # Create the plot using plotnine with sorted DataFrame
    bar_chart = (
        ggplot(filtered_df, 
               aes(x='custom_datasets', 
                   y='ef_et', 
                   fill='hw_type')) +
        geom_bar(stat='identity', 
                 position='dodge') +
        # scale_y_log10() +
        labs(x='Dataset', 
             y='Execution Time (Seconds)') +
        theme_classic() +
        theme(axis_text_x=element_text(angle=45, ha='right'), 
              legend_position='bottom') +
        scale_fill_manual(values=['blue', 'orange', 'green'], 
                          labels=custom_legend_labels) +
        guides(fill=guide_legend(title="SUT", 
                                 nrow=2, 
                                 byrow=True))


    )
    return(bar_chart)

def plot_proportion_of_time_in_exp_phase(experiments_df:pd.DataFrame)->ggplot:

    custom_labels = {
        'CPU': '12 Core M2 Max (Baseline)',
        'CLUSTER': '16 Core Intel Xeon Silver',
        'GPU': 'NVIDIA RTXA5000'
    }

    #Generate the proportions
    experiments_df['prop_ef_tx'] = experiments_df['ef_tx'] / experiments_df['ef_total']
    experiments_df['prop_ef_etl'] = experiments_df['ef_etl'] / experiments_df['ef_total']
    experiments_df['prop_ef_et'] = experiments_df['ef_et'] / experiments_df['ef_total']

    #Transform dataframe
    filtered_df = experiments_df[experiments_df['alg_type'] == 'static']
    
    df_melted = filtered_df.melt(id_vars=['hw_type', 'ef_total'],
                        value_vars=['prop_ef_tx', 'prop_ef_etl', 'prop_ef_et'],
                        var_name='component', value_name='proportion')
    df_melted['custom_hw_type'] = df_melted['hw_type'].map(custom_labels)

    stacked_barchart= (
        ggplot(df_melted,
            aes(x='custom_hw_type',
                y='proportion',
                fill='component')) +
        geom_bar(stat='identity',
                position='fill',
                width=0.5) +
        labs(x='Hardware',
            y='Mean Proportion of\nTotal Experiment Time',
            color='Experiment Phase')+
        scale_fill_manual(values=['#90b9b3', '#eddba4', '#EA5f50'],
                        labels=['Execution', 'ETL', 'Transfer']) +
        theme_classic() +
        theme(axis_text_x=element_text(rotation=45, hjust=1), 
              legend_position='bottom') +
        guides(fill=guide_legend(title="Experiment Phase", 
                                 nrow=1, 
                                 byrow=True))
    ) 

    return stacked_barchart

def plot_proportion_of_time_in_exp_phase_by_dataset(experiments_df:pd.DataFrame, hardware:str=None)->ggplot:

    custom_dataset_labels = {
        "Delaware_adj_list":"OSM-DE",
        "District of Columbia_adj_list":"OSM-DC",
        "Maryland_adj_list":"OSM-MD",
        "Massapequa_adj_list":"OSM-M",
        "Rhode Island_adj_list":"OSM-RI",
        "Washington_adj_list":"OSM-WA",
        "wiki-topcats":"Wiki-Topcats",
        "email-Eu-core":"Email-EU-Core"
    }

    #Generate the proportions
    experiments_df['prop_ef_tx'] = experiments_df['ef_tx'] / experiments_df['ef_total']
    experiments_df['prop_ef_etl'] = experiments_df['ef_etl'] / experiments_df['ef_total']
    experiments_df['prop_ef_et'] = experiments_df['ef_et'] / experiments_df['ef_total']

    #Transform dataframe
    filtered_df = experiments_df[experiments_df['alg_type'] == 'static']
    filtered_df['custom_datasets'] = filtered_df['datasets'].map(custom_dataset_labels)

    if hardware:
        filtered_df = filtered_df[experiments_df['hw_type'] == hardware]

    
    df_melted = filtered_df.melt(id_vars=['custom_datasets', 'ef_total'],
                        value_vars=['prop_ef_tx', 'prop_ef_etl', 'prop_ef_et'],
                        var_name='Experiment Phase', value_name='proportion')

    # Plotting with plotnine
    stacked_barchart=(
        ggplot(df_melted,
            aes(x='custom_datasets',
                y='proportion',
                fill='Experiment Phase')) +
        geom_bar(stat='identity',
                position='fill',
                width=0.5) +
        labs(x='Dataset ',
            y='Proportion of Total\nExperiment Time')+
        scale_fill_manual(values=['#90b9b3', '#eddba4', '#EA5f50'],
                        labels=['Execution', 'ETL', 'Transfer']) +
        theme_classic() +
        theme(axis_text_x=element_text(rotation=45, hjust=1), legend_position='bottom')
    )

    return stacked_barchart

def plot_nmi_for_static_methods_by_dataset(experiment_df:pd.DataFrame)->ggplot:
    
    # Define custom legend labels
    custom_legend_labels = {
        'CPU': '1 x 12 Core M2 Max (Baseline)',
        'CLUSTER': '1 x 16 Core Intel Xeon Silver',
        'GPU': '1 x NVIDIA RTXA5000'
    }
    custom_dataset_labels = {
        "Delaware_adj_list":"OSM-DE",
        "District of Columbia_adj_list":"OSM-DC",
        "Maryland_adj_list":"OSM-MD",
        "Massapequa_adj_list":"OSM-M",
        "Rhode Island_adj_list":"OSM-RI",
        "Washington_adj_list":"OSM-WA",
        "wiki-topcats":"Wiki-Topcats",
        "email-Eu-core":"Email-EU-Core"
    }
    filtered_df = experiments_df[experiments_df['alg_type'] == 'static']
    filtered_df['custom_datasets'] = filtered_df['datasets'].map(custom_dataset_labels)

    #
    # Create the plot using plotnine with sorted DataFrame
    bar_chart = (
        ggplot(filtered_df, aes(x='custom_datasets', y='results_nmi', fill='hw_type')) +
        geom_bar(stat='identity', position='dodge') +
        # scale_y_log10() +
        labs(x='Dataset', y='NMI') +
        theme_classic() +
        theme(axis_text_x=element_text(angle=45, ha='right'), legend_position='bottom') +
        scale_fill_manual(values=['blue', 'orange', 'green'], labels=custom_legend_labels) +
        guides(fill=guide_legend(title="SUT", nrow=2, byrow=True))

    )
    return bar_chart

def plot_nmi_per_iteration_per_hardware(experiments_df:pd.DataFrame, hardware:str=None)->ggplot:

    custom_dataset_labels = {
        "Delaware_adj_list":"OSM-DE",
        "District of Columbia_adj_list":"OSM-DC",
        "Maryland_adj_list":"OSM-MD",
        "Massapequa_adj_list":"OSM-M",
        "Rhode Island_adj_list":"OSM-RI",
        "Washington_adj_list":"OSM-WA",
        "wiki-topcats":"Wiki-Topcats",
        "email-Eu-core":"Email-EU-Core"
    }

    # Experiment subset (only incremental algo's)
    filtered_df = experiments_df[experiments_df['alg_type'] == 'incremental']
    filtered_df['Dataset'] = filtered_df['datasets'].map(custom_dataset_labels)
    if hardware:
        filtered_df = filtered_df[filtered_df['hw_type'] == hardware]

    line_chart = (
        ggplot(filtered_df,
            mapping = aes(x='iteration',
                            y='results_nmi',
                            group="Dataset",
                            color="Dataset",
                            )) +
        geom_line(stat="identity") +
        labs(y="NMI",
            x="Iteration")+
        theme_classic()+
        theme(axis_text_x=element_text(angle=45, ha='right'), legend_position='right')+
        guides(fill=guide_legend(title="Dataset"))
    )

    return line_chart

def plot_number_of_predicted_communities_per_iteration(experiments_df:pd.DataFrame,hardware=None)->ggplot:
    
    custom_dataset_labels = {
        "Delaware_adj_list":"OSM-DE",
        "District of Columbia_adj_list":"OSM-DC",
        "Maryland_adj_list":"OSM-MD",
        "Massapequa_adj_list":"OSM-M",
        "Rhode Island_adj_list":"OSM-RI",
        "Washington_adj_list":"OSM-WA",
        "wiki-topcats":"Wiki-Topcats",
        "email-Eu-core":"Email-EU-Core"
    }

    # Experiment subset (only incremental algo's)
    filtered_df = experiments_df[experiments_df['alg_type'] == 'incremental']
    filtered_df['Dataset'] = filtered_df['datasets'].map(custom_dataset_labels)
    
    if hardware:
        filtered_df = filtered_df[filtered_df['hw_type'] == hardware]

    line_chart = (
        ggplot(filtered_df,
            mapping = aes(x='iteration',
                            y='results_nc',
                            group="Dataset",
                            color="Dataset",
                            )) +
        geom_line(stat="identity") +
        labs(y="Predicted Community Count",
            x="Iteration")+
        theme_classic()+
        theme(axis_text_x=element_text(angle=45, ha='right'), legend_position='right')+
        guides(fill=guide_legend(title="Dataset"))
    )

    return line_chart

#######################
### OLD EXPERIMENTS ###
#######################

def plot_et_against_vertices(experiment_df:pd.DataFrame):
    scatter_plot = (
        ggplot(experiments_df, aes(x='vertices', y='ef_et')) + 
        geom_point(aes(shape='shape')) + 
        geom_smooth(se=False) +
        scale_x_log10() + 
        #scale_y_log10() +
        labs(x='Vertex Count (log scale)', 
            y='Execution time in Seconds') + # Custom axis labels
        theme_classic()
    )

    return scatter_plot

def plot_et_against_edges(experiment_df:pd.DataFrame):
    scatter_plot = (
        ggplot(experiments_df, aes(x='edges', y='ef_et')) +  
        geom_point(aes(shape='shape')) +  
        geom_smooth(se=False) +
        scale_x_log10() +  
        #scale_y_log10() +
        labs(x='Edge Count (log scale)', 
            y='Execution time in Seconds') +
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

def plot_gt_against_predicted_communities_size_difference(experiment_df:pd.DataFrame):
    experiments_df['Size Delta'] = experiments_df['results_nc']-experiments_df['gt_comms']
    filtered_df = experiments_df[(experiments_df['gt_comms'] <= 1000000) & (experiments_df['iteration'] == 'termination')] #Exclude outlier

    scatter_plot = (
        ggplot(filtered_df, aes(x='results_nc', y='gt_comms')) +  
        geom_point(aes(shape='shape',color='Size Delta')) +  
        # scale_x_log10() +  
        # scale_y_log10() +
        labs(x='Number of Communities Detected', 
            y='Ground Truth number of Communities') + 
        scale_color_gradient(low="blue", high="red") +
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

def plot_nmi_against_iterations(experiment_df:pd.DataFrame):
    # Experiment subset (only incremental algo's)
    subset_df = experiments_df[experiments_df['alg_type'] == 'incremental']


    line_plot =(
        ggplot(subset_df, 
            mapping = aes(x='iteration', 
                            y='results_nmi', 
                            group="exp_num", 
                            color="exp_num")) + 
        geom_line(stat="identity") + 
        labs(y="NMI",
            x="Iteration")+
        theme_classic()+
        theme(axis_text_x=element_text(angle=45, ha='right'))
    )
    return(line_plot)

def plot_nc_against_iterations(experiment_df:pd.DataFrame):
    # Experiment subset (only incremental algo's)
    subset_df = experiments_df[experiments_df['alg_type'] == 'incremental']

    line_plot=(
        ggplot(subset_df, 
            mapping = aes(x='iteration', 
                            y='results_nc', 
                            group="exp_num", 
                            color="exp_num")) + 
        geom_line(stat="identity") + 
        scale_y_log10() +
        labs(y="Predicted Community Count (Log Scale)",
            x="Iteration")+
        theme_classic()+
        theme(axis_text_x=element_text(angle=45, ha='right'))
    )
    return(line_plot)

def plot_proportion_of_et(experiments_df:pd.DataFrame):
    # Proportion of time in experiment phase

    experiments_df['prop_ef_tx'] = experiments_df['ef_tx'] / experiments_df['ef_total']
    experiments_df['prop_ef_etl'] = experiments_df['ef_etl'] / experiments_df['ef_total']
    experiments_df['prop_ef_et'] = experiments_df['ef_et'] / experiments_df['ef_total']

    experiments_df.to_csv(os.path.join(".","experiment_results","summary_dataframe.csv"))

    df_melted = experiments_df.melt(id_vars=['exp_num', 'ef_total'],
                        value_vars=['prop_ef_tx', 'prop_ef_etl', 'prop_ef_et'],
                        var_name='component', value_name='proportion')

    prop_plot = (
        ggplot(df_melted, 
            aes(x='exp_num', 
                y='proportion', 
                fill='component')) +
        geom_bar(stat='identity', 
                position='fill', 
                width=0.5) +
        labs(x='Experiment Number', 
            y='Proportion of total experiment time')+ 
        scale_fill_manual(values=['#1f77b4', '#ff7f0e', '#2ca02c'], 
                        labels=['Execution Time', 'ETL Time', 'Transfer Time']) +
        theme_classic() +
        theme(axis_text_x=element_text(rotation=45, hjust=1))
    )

    return(prop_plot)

def plot_bl_against_exp_time(experiments_df:pd.DataFrame):
    # Proportion of time in experiment phase

    subset_df = experiments_df[experiments_df['alg_type'] == 'incremental']
    subset_df['exp_num'] = subset_df['exp_num'].astype(str)

    subset_df['prop_ef_bl'] = subset_df['ef_bl'] / subset_df['ef_total']
    subset_df['prop_ef_rest'] = 1-subset_df['prop_ef_bl']

    df_melted = subset_df.melt(id_vars=['exp_num', 'ef_total'],
                        value_vars=['prop_ef_rest','prop_ef_bl'],
                        var_name='component', value_name='proportion')

    df_melted['component'] = pd.Categorical(df_melted['component'], 
                                            categories=['prop_ef_rest','prop_ef_bl'], 
                                            ordered=True)

    # Plotting with plotnine
    prop_plot = (
        ggplot(df_melted, 
            aes(x='exp_num', 
                y='proportion', 
                fill='component')) +
        geom_bar(stat='identity', 
                position='fill', 
                width=0.5) +
        labs(x='Experiment Number', 
            y='Proportion of total experiment time')+ 
        scale_fill_manual(values=['#e0c013','#399a0b'], 
                        labels=['Remainder of ET', 'Batch Latency @1']) +
        theme_classic() +
        theme(axis_text_x=element_text(rotation=45, hjust=1))
    )
    return prop_plot

######################
## \OLD EXPERIMENTS ##
######################

def save_plots_as_svg(plots:list, output_dir:os.path):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename, plot in plots:
        try:
            plot.save(os.path.join(output_dir,filename))
        except IndexError:
            print(f"No Plot to output for {filename}")

if __name__ == "__main__":

    DATA_SOURCE = os.path.join(".","experiment_results","combined")
    OUTPUT_DIR = (os.path.join("..","dissertation","Figures","Experiment_Results"))
    # OUTPUT_DIR = (os.path.join(".","experiment_results","combined","figures"))

    experiment_results = load_experiments_to_dict(DATA_SOURCE)
    experiments_df = extract_experiments_to_dataframe(experiment_results)

    plots = []
    #NEW EXPERIMENTS:
    plots.append(('et_vs_exp_by_hardware.svg', 
                  plot_exec_time_by_experiment(experiments_df)))
    plots.append(('proportion_of_time_in_exp_phase.svg', 
                 plot_proportion_of_time_in_exp_phase(experiments_df)))
    plots.append(('GPU_proportion_of_time_in_exp_phase_by_dataset.svg', 
                 plot_proportion_of_time_in_exp_phase_by_dataset(experiments_df, 'GPU')))
    plots.append(('Xeon_proportion_of_time_in_exp_phase_by_dataset.svg', 
                 plot_proportion_of_time_in_exp_phase_by_dataset(experiments_df, 'CLUSTER')))
    plots.append(('Baseline_proportion_of_time_in_exp_phase_by_dataset.svg', 
                 plot_proportion_of_time_in_exp_phase_by_dataset(experiments_df, 'CPU')))
    plots.append(('Average_proportion_of_time_in_exp_phase_by_dataset.svg', 
                 plot_proportion_of_time_in_exp_phase_by_dataset(experiments_df)))
    plots.append(('plot_nmi_for_static_methods_by_dataset.svg',
                  plot_nmi_for_static_methods_by_dataset(experiments_df)))
    plots.append(('Baseline_nmi_per_iteration_per_hardware.svg',
                  plot_nmi_per_iteration_per_hardware(experiments_df,hardware='CPU')))
    plots.append(('Xeon_nmi_per_iteration_per_hardware.svg',
                  plot_nmi_per_iteration_per_hardware(experiments_df,hardware='CLUSTER')))
    plots.append(('Baseline_communities_per_iteration_per_hardware.svg',
                  plot_number_of_predicted_communities_per_iteration(experiments_df,hardware='CPU')))
    plots.append(('Xeon_communities_per_iteration_per_hardware.svg',
                  plot_number_of_predicted_communities_per_iteration(experiments_df,hardware='CLUSTER')))
    #OLD EXPERIMENTS:
    # plots.append(('et_vs_vertex.svg', plot_et_against_vertices(experiments_df)))
    # plots.append(('et_vs_edges.svg', plot_et_against_edges(experiments_df)))
    # plots.append(('vertices_vs_edges.svg', plot_vertices_against_edges(experiments_df)))
    # plots.append(('iterations_boxplot.svg', plot_iterations_boxplot(experiments_df)))
    # plots.append(('gt_vs_predicted_communities.svg', plot_gt_against_predicted_communities(experiments_df)))
    # plots.append(('gt_vs_predicted_communities_sizes.svg', plot_gt_against_predicted_communities_size_difference(experiments_df)))
    # plots.append(('nmi_vs_et.svg', plot_nmi_against_et(experiments_df)))
    # plots.append(('bl_vs_sod.svg', plot_data_size_against_batch_latency(experiments_df)))
    # plots.append(('nmi_vs_iter.svg', plot_nmi_against_iterations(experiments_df)))
    # plots.append(('communities_vs_iter.svg', plot_nc_against_iterations(experiments_df)))
    # plots.append(('et_vs_exp_total.svg', plot_proportion_of_et(experiments_df)))
    # plots.append(('bl_vs_exp_total.svg', plot_bl_against_exp_time(experiments_df)))

    save_plots_as_svg(plots=plots, output_dir=OUTPUT_DIR)


