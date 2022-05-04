import os
import sys
import time

from IPython.display import Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb
sb.set_style("dark")


sa_weights  = {'yummy_score': 0, 'variety_score': 1}
mip_weights = {'yummy_score': .5, 'variety_score': .5}

def visualize_garden(bed_info):
    garden_layout = bed_info.sun.map({'Full sun':1,'Partial sun':2,'Partial shade':3}).to_numpy().reshape(14,3)
    palette = ["#ffa200","#fcbd53","#ffd58f"]
    f, ax = plt.subplots(figsize=(10, 6))
    ax = sb.heatmap(garden_layout,linewidths=5,linecolor='white',cmap=sb.color_palette(palette),cbar=False)
    ax.xaxis.set_ticklabels([])
    ax.yaxis.set_ticklabels([])
    plt.rcParams.update({'font.size': 13})
    return ax

def visualize_plan(bed_info,bed_index,years):
    for year in years:
        garden_viz = visualize_garden(bed_info)
        garden_viz.set_title(f'Year {year}')

        for bed in bed_index:
            x = bed_info.iloc[bed].x
            y = bed_info.iloc[bed].y
            plt.text(x + 0.5, y + 0.5, bed_info.loc[(bed_info.x==x)&(bed_info.y==y)][f'year_{year}'].iloc[0],
                            horizontalalignment='center',verticalalignment='center')

def annual_bed_plan(best_plan,bed_info,plant_info,bed_index,year_index):
    for t in year_index:
        bed_plan = []
        for b in bed_index:
            plant_idx = np.argmax(best_plan[:,b,t])
            plant = plant_info.iloc[plant_idx]['name']
            bed_plan.append(plant)
        bed_info[f'year_{t+1}'] = pd.Series(bed_plan)
    return bed_info

def visualize_obj_iters(current_plan_obj_values):
    objectives = []
    yummy_scores = []
    variety_scores = []
    for i in current_plan_obj_values:
        objectives.append(i[1]['objective'])
        yummy_scores.append(i[1]['yummy_score'])
        variety_scores.append(i[1]['variety_score'])
        
    df = pd.DataFrame([objectives,yummy_scores,variety_scores]).T#,yummy_scores,variety_scores]).T
    df.columns = ['obj_value','yummy_scores','variety_scores']#,'yummy_score','variety_score']
    df.reset_index(inplace=True)
    df = df.melt(id_vars=['index'],var_name='objective')

    fig, ax = plt.subplots(figsize=(20,8))
    sb.scatterplot(data=df,x='index',y='value',hue='objective',edgecolor=None,s=5)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)

    ax.set_title('Objective Values of Current Solution by Iteration')
    # ax2 = plt.twinx()
    # sb.scatterplot(data=df.drop_duplicates(['index','total_plants']),x='index',y='objective',edgecolor=None,ax=ax2,color='black',s=5)