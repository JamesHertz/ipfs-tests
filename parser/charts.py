#! /usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import math
import sys

from utils import Lookups as lk
from utils import Snapshots as sp 
from utils import Publishes as pb
from typing import cast, Callable
from igraph import Graph
from os import path, mkdir

type ExpGraphs = dict[str, list[list[Graph]]]

BARS_COLORS     = ['C10', 'C9', 'C1', 'C2']
CHARTS_SAVE_DIR = 'charts'
TIME_LIMIT_MINUTES = 30

def __init__():
    if not path.exists(CHARTS_SAVE_DIR):
        print(f"creating directory '{CHARTS_SAVE_DIR}/'")
        mkdir(CHARTS_SAVE_DIR)
    elif not path.isdir(CHARTS_SAVE_DIR):
        print(
            f"File '{CHARTS_SAVE_DIR}' is not a directory. Either change CHARTS_SAVE_DIR or remove it."
        )
        sys.exit(1)

def save_fig(filename: str, fig : plt.Figure = None): # type: ignore
    # TODO: check if directory charts exists, if not created it :)
    fig = fig if fig is not None else plt  # type: ignore
    filename = f'charts/{filename}'
    print(f"Saving '{filename}'")
    fig.savefig(filename,bbox_inches='tight')
    plt.clf()  # clear drawn charts for others :) # TODO: get rid of this thing c:


def plot_avg_success_resolve(data: pd.DataFrame):
    data = data[data[lk.PROVIDERS] > 0] # type: ignore

    data = data.groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.LOOKUP_TIME].agg(resolve_time='mean') # type: ignore

    # print(data)
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)
    pivot_data = data.pivot(columns=lk.CID_TYPE, values='resolve_time')

    ax = pivot_data.plot(
        kind='bar', color=BARS_COLORS[1:],
        figsize=(8, 6),
        width=2
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 1) if v > 0.0 else '' for v in cnt.datavalues], fontsize=15)

    plt.xticks(rotation=0, horizontalalignment="center",fontsize=20)
    plt.xlabel('Versão da DHT', fontweight='bold',fontsize=22)
    plt.ylabel('Tempo (ms)', fontweight='bold',fontsize=22)
    # plt.title('Average Resolve time (ms)', fontweight='bold')
    plt.legend(title='Tipo de CID',fontsize=22)

    # plt.show()
    save_fig('avg-resolve.pdf')


def plot_success_rate(data: pd.DataFrame):

    data = data.groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.PROVIDERS].aggregate(
        ['sum', 'count']
    ) # type: ignore
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    data['success rate'] = data['sum'] / data['count'] * 100

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='success rate')#.fillna(0)

    ax = pivot_data.plot(
        kind='bar',
        figsize=(8, 7),
        color=BARS_COLORS[1:],
        align='center',
        width=2,
        # linewidth=4,
        # edgecolor='white',
    )

    # print(pivot_data)

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 2) if v > 0.0 else '' for v in cnt.datavalues], fontsize=18)

    plt.xticks(rotation=0, horizontalalignment="center",fontsize=20)
    # plt.yticks([0,50,100])
    plt.xlabel('Versão da DHT', fontweight='bold',fontsize=26)
    plt.ylabel('Taxa de sucesso (%)', fontweight='bold',fontsize=26)
    # plt.title('Success rate of resolved CIDs', fontweight='bold')
    plt.legend(title='Tipo de CID', fontsize=26)
    # plt.tight_layout(pad=3)

    # # Display the histogram
    # plt.show()
    save_fig('success-rate.pdf')


# turn this into an average per node :) 
def plot_cids_lookups(data: pd.DataFrame):
    # TODO: think if it's worthed to set constants
    # TODO: think on a way to solve the colors incovinience
    # total_resolves = len(data)
    # print(total_resolves)
    # print('-----------------------')
    # print(data)
    data = data.groupby(lk.PEER_DHT)[lk.CID_TYPE].value_counts().to_frame()
    # print('-----------------------')
    # print(data)
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='count').fillna(0)
    # print(pivot_data)
    # for col in pivot_data:
    #     pivot_data[col] = (100 * pivot_data[col] / total_resolves) 

    # print('-----------------------')
    # print(pivot_data)
    __before = pivot_data['Normal']

    pivot_data['Normal'] = pivot_data['Secure'] + pivot_data['Normal']

    ax = None
    for col, color in zip(pivot_data, BARS_COLORS[1:]):
        tmp = pivot_data.plot(
            kind='bar',
            color=color,
            figsize=(12, 8),
            y=col,
            ax=ax
        )
        if ax is None:
            ax = tmp

    # fix what I did :)
    pivot_data['Normal'] = pivot_data['Normal'] - pivot_data['Secure']

    assert (__before == pivot_data['Normal']).all(
    ), 'Normal data not properly restored'

    for cont, col in zip(ax.containers, pivot_data):
        ax.bar_label(cont, labels=['{:,}'.format(
            int(x)) if x != 0.0 else '' for x in pivot_data[col]])
            # round(x, 2)) if x != 0.0 else '' for x in pivot_data[col]])

    ax.legend(title='Tipos de CID')
    plt.xticks(rotation=0, horizontalalignment="center")
    # plt.ylabel('Number of CIDs lookups', fontweight='bold')
    plt.ylabel('Número de pesquisas de CIDs', fontweight='bold')
    plt.xlabel('Versão da DHT', fontweight='bold')
    # plt.title('Number of CIDs lookups by DHT and CID type', fontweight='bold')

    # plt.show()
    save_fig('lookup-hist.pdf')

def calc_rt_evolution(snapshots: pd.DataFrame, fig : plt.Figure | None = None) -> pd.DataFrame:
    data = snapshots.groupby([sp.SRC_PID, sp.SNAPSHOT_NR, sp.SRC_DHT, sp.EXP_ID])[sp.DST_DHT].value_counts().to_frame()
    # print(data)

    # get each type as a row
    data.reset_index(level=(sp.DST_DHT), inplace=True)
    pivot_data = data.pivot(columns=sp.DST_DHT, values='count').fillna(0)
    # print(pivot_data)

    # turn each row number as  (axis=1 stands for apply to each row)
    pivot_data = pivot_data.apply(lambda x: round(x / x.sum() * 100, 2), axis=1)
    pivot_data.reset_index(inplace=True)
    
    pivot_data.drop(columns=[sp.SRC_DHT, sp.SRC_PID, sp.EXP_ID], inplace=True)
    pivot_data = pivot_data.groupby(sp.SNAPSHOT_NR).mean()
    # print(pivot_data)

    fig = fig if fig is not None else plt
    for dht_type in pivot_data.columns:
        aux = pivot_data[dht_type]
        if len(aux) > 0 :
            fig.plot(pivot_data.index, aux, label=dht_type)

    return pivot_data


def plot_rt_evolution(snapshots: pd.DataFrame):

    for node_type in ['Secure', 'Normal']:
        snaps    = snapshots[snapshots[sp.SRC_DHT] == node_type]
        # print(node_type)

        buckets = snaps[sp.BUCKET_NR].unique()

        cols = 3
        rows = int(math.ceil(
            (len(buckets) + 1)/ cols
        ))

        fig, axes = plt.subplots(
            nrows=rows, ncols=cols, figsize=(25,20), layout='constrained', sharey=True
        )

        over_all = axes[0, 0]
        dht_evol = calc_rt_evolution(snaps, over_all)

        over_all.set_title(f'Whole Routing Table', fontweight='bold')
        over_all.set_ylim(0, 100)
        over_all.set_xlim(0, dht_evol.index.max()) # 0 to max snapshot-number
        over_all.legend(fontsize=12)

        fig.suptitle(
            'Routing table evoluation for Secure Nodes', fontweight='bold', fontsize=20
        )

        fig.supxlabel(
            # 'Time (minutes) from the start of the experiment', fontweight='bold', fontsize=16
            'Tempo, em minutos, desde o início da expêriencia', fontweight='bold', fontsize=16
        )

        fig.supylabel(
            'Percentage (%) of nodes in the bucket', fontweight='bold', fontsize=16
        )

        for bucket in buckets:
            row = (bucket + 1) // cols
            col = (bucket + 1) % cols

            ax   = axes[row, col]
            data = calc_rt_evolution(snaps[ snaps[sp.BUCKET_NR] == bucket ], fig=ax)

            # ...
            ax.set_title(f'Bucket {bucket}', fontweight='bold')
            ax.set_ylim(0, 100)
            ax.set_xlim(0, data.index.max()) # 0 to max snapshot-number
            ax.legend(fontsize=12)

        # save_fig(f'{node_type}-rt-evol-bucket-{bucket}.pdf')
        save_fig(f'{node_type}-rt-buckets-evol.pdf', fig=fig)



def calc_rt_state(snapshots: pd.DataFrame) -> pd.DataFrame:
    data = snapshots.groupby([
        sp.SRC_PID, sp.SNAPSHOT_NR, sp.SRC_DHT, sp.EXP_ID
    ])[sp.DST_DHT].value_counts().to_frame('version-frequency')

    data.reset_index(level=(sp.DST_DHT), inplace=True)

    # get each type as a row turn each dht version type number into a row
    pivot_data = data.pivot(columns=sp.DST_DHT, values='version-frequency').fillna(0)

    # calculate the percentage of each freuqency
    pivot_data = pivot_data.apply(lambda x: round(x / x.sum() * 100, 2), axis=1)
    pivot_data.reset_index(inplace=True)
    
    # drop the collumns that doesn't matter more
    pivot_data.drop(columns=[sp.SRC_PID, sp.EXP_ID, sp.SNAPSHOT_NR], inplace=True)

    # get the average of each percentage by SRC_DHT
    pivot_data = pivot_data.groupby(sp.SRC_DHT).mean()

    
    return pivot_data

def plot_end_rt_state(snapshots: pd.DataFrame):
    last_snap = snapshots[sp.SNAPSHOT_NR].unique().max()
    snapshots = snapshots[ 
          (snapshots[sp.SNAPSHOT_NR] == last_snap - 1) 
        & (snapshots[sp.SRC_DHT].isin(['Secure', 'Normal']))
    ]

    def built_chart(data: pd.DataFrame, title: str, ax : plt.Figure):
        # sns.heatmap(
        #     data, annot=True, cmap='Blues', ax=ax, fmt='.2f', annot_kws={"fontsize": 10}
        # )
        ax = data.plot(
            kind='bar',
            color=[BARS_COLORS[2], BARS_COLORS[3]],
            ax=ax
        )

        for cnt in ax.containers:
            ax.bar_label(cnt, labels=[f"{round(v, 2)} %" if v > 0.0 else '' for v in cnt.datavalues])


        ax.set_xlabel(None)
        # ax.set_ylabel(None)
        # # ax.set_ylabel('percentage of the nodes in DHT', fontweight='bold')
        ax.legend(title="Versão da DHT")
        ax.set_title(title, fontweight='bold') # type: ignore

        labels = [item.get_text() for item in ax.get_xticklabels()] # type: ignore
        ticks  = range(len(labels))
        ax.set_xticks( # type: ignore
           ticks,
           labels=labels, 
           rotation=0, 
           horizontalalignment="center"
        ) 

    all_buckets = snapshots[sp.BUCKET_NR].unique()
    rows = 3
    cols = int(math.ceil( 
        # (len(all_buckets) + 1)/ 2
        ( len(all_buckets) + 1) / rows
    ))

    # data = calc_rt_state(snapshots)
    # built_chart(data, 'Percentage of nodes neibours in the Routing table', 'rt-end-state.pdf')
    fig, axes = plt.subplots(
        nrows=rows, ncols=cols, figsize=(25, 20), layout='constrained'
    )

    fig.suptitle(
        # 'Routing table end state for Secure and Normal Nodes', fontweight='bold', fontsize=20
        'Estado final da Routing Table para nós Secure e Normal', fontweight='bold', fontsize=20
    )

    fig.supxlabel(
        'DHT version', fontweight='bold', fontsize=16
    )

    fig.supylabel(
        'Percentage (%) of nodes in the routing table', fontweight='bold', fontsize=16
    )

    data = calc_rt_state(snapshots)
    built_chart(
        data, 
        'Whole Routing Table', 
        axes[0, 0]
    )

    # for bucket in snapshots[sp.BUCKET_NR].unique():
    for bucket in all_buckets:
        col = (bucket + 1) % cols
        row = (bucket + 1) // cols

        snaps = snapshots[snapshots[sp.BUCKET_NR] == bucket]
        data  = calc_rt_state(snaps) # type: ignore
        built_chart(
            data, 
            f'Bucket {bucket}', 
            ax=axes[row, col]
        )

    # TODO: uncomment when needed
    # blank_spots = cols * rows - len(all_buckets)
    # if blank_spots > 0:
    #     for i in range(blank_spots):
    #         axes[ rows - 1, cols - (1 + i)].axis('off')
    save_fig('rt-end-state.pdf', fig=fig)


def plot_avg_resolve_queries(data: pd.DataFrame):
    data = data[
        data[lk.PROVIDERS] > 0
    ].groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.QUERIES].mean().to_frame('avg-res-queries')

    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='avg-res-queries').fillna(0)

    ax = pivot_data.plot(
        kind='bar',
        figsize=(8, 6),
        color=BARS_COLORS[1:],
        width=2
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[f"{round(v, 1)}" if v > 0.0 else '' for v in cnt.datavalues],fontsize=17)

    # print(pivot_data)

    plt.xticks(rotation=0, horizontalalignment="center", fontsize=22)
    plt.xlabel('Versão da DHT', fontweight='bold', fontsize=22)
    plt.legend(title='Tipos de CID', loc='lower right', fontsize=22)
    plt.ylabel('Número de nós que\nse contatou', fontweight='bold', fontsize=22)
    # plt.title('Average number of queries per resolved CID type', fontweight='bold')
    # plt.show()
    save_fig('avg-res-queries.pdf')

def plot_puslish_time(data: pd.DataFrame):
    data = data[[
        pb.SRC_PID, pb.SRC_DHT, pb.EXP_ID, pb.CID, pb.DURATION
    ]].drop_duplicates() # type: ignore
    
    ax = data.groupby(pb.SRC_DHT)[pb.DURATION].mean().plot(
        kind='bar',
        figsize=(6,6),
        # figsize=(12, 8),
        color=BARS_COLORS[1:],
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 2) if v > 0.0 else '' for v in cnt.datavalues], fontsize=15)

    plt.xticks(rotation=0, horizontalalignment="center", fontsize=22)
    plt.xlabel('Versão da DHT', fontweight='bold', fontsize=22)
    plt.ylabel('Tempo (ms)', fontweight='bold', fontsize=22)
    # plt.title('Average publish time (ms)', fontweight='bold')
    # plt.show()
    save_fig('avg-publish-time.pdf')

def plot_publish_queries(data: pd.DataFrame):
    
    data = data[[
        pb.SRC_PID, pb.SRC_DHT, pb.EXP_ID, pb.CID, pb.QUERIES_NR
    ]].drop_duplicates() # type: ignore

    ax = data.groupby(pb.SRC_DHT)[pb.QUERIES_NR].mean().plot(
        kind='bar',
        figsize=(8, 6),
        color=BARS_COLORS[1:],
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 1) if v > 0.0 else '' for v in cnt.datavalues],fontsize=17.5)

    plt.xticks(rotation=0, horizontalalignment="center",fontsize=22)
    plt.xlabel('Versão da DHT', fontweight='bold',fontsize=22)
    # plt.ylabel('Average number of queries', fontweight='bold')
    plt.ylabel('Número de nós que\nse contatou', fontweight='bold',fontsize=22)
    # plt.title('Average number of queries per published CID', fontweight='bold')
    # plt.show()
    save_fig('avg-publish-queries.pdf')

def plot_publish_nodes(data: pd.DataFrame):
    data = data.groupby([
        pb.EXP_ID, pb.SRC_PID, pb.SRC_DHT, pb.CID
    ])[pb.STORAGE_DHT].value_counts().to_frame('count')

    data.reset_index(level=(pb.STORAGE_DHT), inplace=True)

    pivot = data.pivot(columns=pb.STORAGE_DHT, values='count').fillna(0)
    pivot.reset_index(inplace=True)
    pivot.drop(columns=[pb.SRC_PID, pb.EXP_ID, pb.CID], inplace=True)

    ax = pivot.groupby(pb.SRC_DHT).mean().plot(
        kind='bar',
        color=BARS_COLORS[1:],
        figsize=(8, 7),
        width=1
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 1) if v > 0.0 else '' for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center",fontsize=22)
    # plt.legend(title='Storage Nodes DHT')
    plt.legend(title='Nós que guardaram os PRs',loc='upper center', fontsize=22)
    # plt.title('Average number of nodes published per CID', fontweight='bold')
    plt.xlabel('Versão da DHT', fontweight='bold',fontsize=24)
    plt.ylabel('Número médio de nós', fontweight='bold',fontsize=24)
    # plt.show()
    save_fig('avg-published-nodes.pdf')

def plot_throughput(data: pd.DataFrame):
    lookups = data.copy()

    for name in ['Secure', 'Normal']:
        lookups.replace(name, 'Normal vs Secure', inplace=True)

    lookups[lk.TS]    = (lookups[lk.TS] / 60).round(0) # convert to minutes c:
    lookups['counts'] = 0

    for exp_id in lookups[lk.EXP_ID].unique():
        selector = lookups[lk.EXP_ID] == exp_id
        lookups.loc[
            selector, lk.TS
        ] -= lookups[selector][lk.TS].min()

    tp_per_exp = lookups.groupby(
        [lk.PEER_DHT, lk.TS, lk.EXP_ID]
    )['counts'].count().to_frame().reset_index()

    # print(tp_per_exp)
    # result.reset_index(inplace=True)

    throughput = tp_per_exp.groupby([lk.PEER_DHT, lk.TS])['counts'].mean().to_frame()
    # print(throughput)

    throughput.reset_index(level=(lk.PEER_DHT,), inplace=True)
    pivot_data = throughput.pivot(columns=lk.PEER_DHT, values='counts').fillna(0)
    # print(pivot_data)

    # plt.figure(figsize=(12, 8))
    plt.figure(figsize=(6, 6))

    for dht_type in pivot_data.columns:
        aux = pivot_data[dht_type]
        plt.plot(pivot_data.index, aux, label=dht_type)

    plt.legend(title='Experiências',fontsize=22)
    plt.xlabel('Tempo (em minutos)',fontsize=22)
    plt.ylabel('Throughput (operação/minuto)',fontsize=22)
    # plt.title('Evoluation of throughput over the experiment')

    save_fig('throughput.pdf')



class GraphMetric:
    data : dict[str, np.ndarray]
    time : np.ndarray
    def __init__(self, data, time):
        self.data = data
        self.time = time

def none_idx(values : list[list[Graph]]) -> list[list[int]]:
    return [ 
        [i for i, l in enumerate(list) if l is None] for list in values
    ]

def calc_graph_metric(
        graphs : ExpGraphs, 
        calc_metric : Callable[[Graph], float]
    ) -> GraphMetric:
    sample = graphs['Baseline'][0]

    min    = sample.count(None) # type: ignore
    max    = len(sample)
    assert min == 3

    data : dict[str, np.ndarray] = {}
    for label, graph_lists in graphs.items():
        assert [[0, 1, 2]] * len(graph_lists) == none_idx(graph_lists)
        metric_results = np.array( [
            [
                calc_metric(g) for g in list[min:max]
            ] for list in graph_lists
        ])

        data[label] = metric_results.mean(axis=0)

    time = np.arange(min, max)
    return GraphMetric(data, time)

def plot_clustering_coefficiency(graphs : ExpGraphs):

    metric = calc_graph_metric(
        graphs, lambda g : g.transitivity_undirected()
    )

    results = metric.data
    time    = metric.time

    # plt.figure(figsize=(12,8))
    plt.figure(figsize=(8,6))
    for label, values in results.items():
        plt.plot(
            time, values.round(2), label=label
        )

    plt.legend(title='Experiências',fontsize=22)
    plt.ylabel('Coeficiente de agrupamento \nmédio',fontsize=22)
    plt.xlabel('Tempo (em minutos)',fontsize=22)
    save_fig('clustering-coefficiency.pdf')

def plot_diameter(graphs : ExpGraphs):

    metric = calc_graph_metric(
        # graphs, lambda g : len(g.average_path_length())    
        graphs, lambda g : g.diameter()
    )

    results = metric.data
    time    = metric.time
    
    plt.figure(figsize=(8,6))
    for label, values in results.items():
        plt.plot(
            time, values.round(2), label=label
        )
    
    plt.legend(title='Experiências',fontsize=22)
    plt.ylabel('Diamétro do grafo',fontsize=22)
    plt.xlabel('Tempo (em minutos)',fontsize=22)
    save_fig('graph-diameter.pdf')

def plot_node_degree(graphs : ExpGraphs):
    metric = calc_graph_metric(
        graphs, lambda g : np.mean(g.degree())
    )

    results = metric.data
    time    = metric.time

    plt.figure(figsize=(8,6))
    for label, values in results.items():
        plt.plot(
            time, values.round(2), label=label
        )

    plt.legend(title='Experiments',fontsize=22)
    # plt.ylabel('Average node degree')
    plt.ylabel('Grau médio dos vértices',fontsize=22)
    plt.xlabel('Tempo (em minutos)',fontsize=22)
    # plt.xlabel('Time since the start of the experiment (minutes)')
    save_fig('avg-node-degree.pdf')


# import networkx as nx
# from pyvis.network import Network
# def draw_graphs(snapshots : pd.DataFrame):
#     nodes = cast(pd.DataFrame, snapshots[
#         (snapshots[sp.EXP_ID] == 0) & (snapshots[sp.SNAPSHOT_NR] == 30)
#     ])
#
#     mapping = build_pid_to_idx_mappping(nodes)
#     edges = [
#         (int(mapping[src]), int(mapping[dst])) for [src, dst] in nodes[[sp.SRC_PID, sp.DST_PID]].values
#     ]
#
#     G = nx.DiGraph()
#     G.add_edges_from(edges)
#
#     # Increase figure size
#     plt.figure(figsize=(30, 30))
#
#     # Use a layout algorithm
#     pos = nx.spring_layout(G, k=4)
#     nx.draw(
#         G, pos, node_color='skyblue', node_size=10, edge_color='gray',
#     )
#     plt.show()


def read_data(filename : str) -> pd.DataFrame:
    data = pd.read_csv(filename, low_memory=False)

    # NOTE: Akos said is not relevant at all having all here
    # aux = data[data[lk.PEER_DHT].isin(['SECURE', 'NORMAL'])].copy()
    # aux[lk.PEER_DHT] = 'All'
    # aux[lk.CID_TYPE] = 'All'

    for old, new in [
        ('DEFAULT', 'Baseline'),
        ('SECURE', 'Secure'),
        ('NORMAL', 'Normal')
    ]:
        data.replace(old, new, inplace=True)

    return data

def build_pid_to_idx_mappping(data : pd.DataFrame) -> dict[str, int]:
    nodes   = data[sp.SRC_PID].unique() # type: ignore
    indexes = np.arange(nodes.shape[0], dtype=int)
    return dict(zip(
        nodes, indexes
    ))

def build_graphs(data: pd.DataFrame) -> ExpGraphs:
    graphs = {
        'Baseline'         : [],
        'Normal vs Secure' : []
    }

    for exp_id in data[sp.EXP_ID].unique():
        rows = cast(pd.DataFrame, data[data[sp.EXP_ID] == exp_id])
        id   = rows[sp.SRC_DHT].iloc[0] # type: ignore
        graph_list = graphs[ 
            'Baseline' if id == 'Baseline' else 'Normal vs Secure'
        ]

        snaps_nrs : np.ndarray = rows[sp.SNAPSHOT_NR].unique() # type: ignore
        snaps_nrs.sort()

        snaps_graphs = [None] * (snaps_nrs.max() + 1)
        nodes_idx = build_pid_to_idx_mappping(rows)

        for nr in snaps_nrs:
            snaps_records = cast(pd.DataFrame, rows[rows[sp.SNAPSHOT_NR] == nr])
            edges = snaps_records[[sp.SRC_PID, sp.DST_PID]].values
            edges = [
                (nodes_idx[src], nodes_idx[dst]) for [src, dst] in edges
            ]

            snaps_graphs[nr] = Graph(edges=edges, directed=True)

        graph_list.append(snaps_graphs)

    return graphs

# TODO:
#   x Clustering coefficiency
#   x Average node path
#   x Average node degree
#   - Throughtput (reparse lookups and add time as one of the cols)
#   - some clean up of the code (someday)
#   - improve routing table end state readability
#   - max of the mininum paths (network diameter)
def main():
    plt.rcParams.update({
        'font.size' : 20,
        'axes.spines.top'   : False,
        'axes.spines.right' : False
    })
 
    lookups = read_data('lookups.csv')
    plot_success_rate(lookups)
    plot_avg_success_resolve(lookups)
    plot_avg_resolve_queries(lookups)
    plot_cids_lookups(lookups)
    plot_throughput(lookups)
    
    snapshots = read_data('snapshots.csv')
    graphs    = build_graphs(snapshots)
    plot_clustering_coefficiency(graphs)
    plot_node_degree(graphs)
    plot_diameter(graphs)

    ## plot_rt_evolution(snapshots)
    # TODO: needs to fix the one below c:
    # plot_end_rt_state(snapshots)
    
    publishes = read_data('publishes.csv')
    plot_publish_nodes(publishes)
    plot_puslish_time(publishes)
    plot_publish_queries(publishes)

if __name__ == '__main__':
    __init__()
    main()
