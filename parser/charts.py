#! /usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
# import utils as lk
import seaborn as sns
import math

from utils import Lookups as lk
from utils import Snapshots as sp 
from utils import Publishes as pb

BARS_COLORS = ['C10', 'C9', 'C1', 'C2']


def save_fig(filename: str, fig : plt.Figure = None):
    # TODO: check if directory charts exists, if not created it :)
    fig = fig if fig is not None else plt
    fig.savefig(f'charts/{filename}')
    plt.clf()  # clear drawn charts for others :)


def plot_avg_success_resolve(data: pd.DataFrame):
    data = data[data[lk.PROVIDERS] > 0]

    data = data.groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.LOOKUP_TIME].agg(resolve_time='mean')

    # print(data)
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)
    pivot_data = data.pivot(columns=lk.CID_TYPE, values='resolve_time').fillna(0)

    ax = pivot_data.plot(
        kind='bar', color=BARS_COLORS[1:],
        figsize=(14, 6),
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 2) if v > 0.0 else '' for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('time (ms)', fontweight='bold')
    plt.title('Average Resolve time (ms)', fontweight='bold')
    plt.legend(title='CID types')

    # plt.show()
    save_fig('avg-resolve.pdf')


def plot_success_rate(data: pd.DataFrame):

    data = data.groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.PROVIDERS].aggregate(
        ['sum', 'count']
    )
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    data['success rate'] = data['sum'] / data['count'] * 100

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='success rate').fillna(0)

    ax = pivot_data.plot(
        kind='bar',
        figsize=(14, 6),
        color=BARS_COLORS[1:],
    )

    # print(pivot_data)

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 2) if v > 0.0 else '' for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('success rate (%)', fontweight='bold')
    plt.title('Success rate of resolved CIDs', fontweight='bold')
    plt.legend(title='CID types', loc='lower right')

    # # Display the histogram
    # plt.show()
    save_fig('success-rate.pdf')


# turn this into an average per node :) 
def plot_cids_lookups(data: pd.DataFrame):
    # TODO: think if it's worthed to set constants
    # TODO: think on a way to solve the colors incovinience
    # total_resolves = len(data)
    # print(total_resolves)
    print('-----------------------')
    print(data)
    data = data.groupby(lk.PEER_DHT)[lk.CID_TYPE].value_counts().to_frame()
    print('-----------------------')
    print(data)
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='count').fillna(0)
    # print(pivot_data)
    # for col in pivot_data:
    #     pivot_data[col] = (100 * pivot_data[col] / total_resolves) 

    print('-----------------------')
    print(pivot_data)
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

    ax.legend(title='CID types')
    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('Number of CIDs lookups', fontweight='bold')
    plt.xlabel('DHT Types', fontweight='bold')
    plt.title('Number of CIDs lookups by DHT and CID type', fontweight='bold')

    # plt.show()
    save_fig('lookup-hist.pdf')

def calc_rt_evolution(snapshots: pd.DataFrame, fig : plt.Figure = None) -> pd.DataFrame:
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
        print(node_type)

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
            'Time (minutes) from the start of the experiment', fontweight='bold', fontsize=16
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
        ax.legend(title="DHT version")
        ax.set_title(title, fontweight='bold')

        labels = [item.get_text() for item in ax.get_xticklabels()]
        ticks  = range(len(labels))
        ax.set_xticks(
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
        'Routing table end state for Secure and Normal Nodes', fontweight='bold', fontsize=20
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
        data  = calc_rt_state(snaps)
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
        figsize=(12, 6),
        color=BARS_COLORS[1:],
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[f"{round(v, 1)}" if v > 0.0 else '' for v in cnt.datavalues])

    # print(pivot_data)

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.legend(title='CID Types', loc='lower right')
    plt.ylabel('Number of queries', fontweight='bold')
    plt.title('Average number of queries per resolved CID type', fontweight='bold')
    # plt.show()
    save_fig('avg-res-queries.pdf')



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


def plot_puslibh_time(data: pd.DataFrame):
    data = data[[pb.SRC_PID, pb.SRC_DHT, pb.EXP_ID, pb.CID, pb.DURATION]].drop_duplicates()
    
    ax = data.groupby(pb.SRC_DHT)[pb.DURATION].mean().plot(
        kind='bar',
        figsize=(12, 6),
        color=BARS_COLORS[1:],
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 2) if v > 0.0 else '' for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('time (ms)', fontweight='bold')
    plt.title('Average publish time (ms)', fontweight='bold')
    # plt.show()
    save_fig('avg-publish-time.pdf')

def plot_publish_queries(data: pd.DataFrame):
    data = data[[pb.SRC_PID, pb.SRC_DHT, pb.EXP_ID, pb.CID, pb.QUERIES_NR]].drop_duplicates()
    ax = data.groupby(pb.SRC_DHT)[pb.QUERIES_NR].mean().plot(
        kind='bar',
        figsize=(12, 6),
        color=BARS_COLORS[1:],
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 1) if v > 0.0 else '' for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('Average number of queries', fontweight='bold')
    plt.title('Average number of queries per published CID', fontweight='bold')
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
        figsize=(12, 6),
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[round(v, 1) if v > 0.0 else '' for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.legend(title='Storage Nodes DHT')
    plt.title('Average number of nodes published per CID', fontweight='bold')
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('Average number of nodes', fontweight='bold')
    # plt.show()
    save_fig('avg-published-nodes.pdf')


# TODO:
# remove all the duplication of the code
def main():
    # lookups = read_data('lookups.csv')
    # plot_avg_success_resolve(lookups)
    # plot_success_rate(lookups)
    # plot_avg_resolve_queries(lookups)
    # plot_cids_lookups(lookups)

    # TODO: do the number of queries in the publish and resolve
    snapshots = read_data('snapshots.csv')
    # plot_rt_evolution(snapshots)
    plot_end_rt_state(snapshots)

    # publishes = read_data('publishes.csv')
    # plot_publish_nodes(publishes)
    # plot_puslibh_time(publishes)
    # plot_publish_queries(publishes)

# TODO: charts by bucket and by experiment
# charts ideas:
#  - avg number of cid resolution by experiment
#  - experiment to check why normal nodes are more frequent than secure
#  x evolution of routing table peers overall and them by bucket 
if __name__ == '__main__':
    main()
