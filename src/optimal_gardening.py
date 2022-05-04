import os
import sys
import time

from IPython.display import Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb
sb.set_style("dark")

#### Initial Setup ####

#plant info
plant_info = pd.read_csv('../data/plant_data.csv')
plant_info.index.name = 'plant_index'
plants = plant_info.name.to_numpy()
plant_index = plant_info.index.to_numpy()
num_plants = len(plants)
plant_sun_req = plant_info.sun.to_numpy()
perennials = plant_info[plant_info.perennial==1].index.to_list()
problem_plants = plant_info[plant_info.problem_plant==1].index.to_list()

#calculate weighted average preference for each plant
family = ['evan','gina','liesse','lizzie','jack']
plant_info['avg_pref'] = np.average(plant_info[family],axis=1,weights=[.5,.5,0,0,0])
plant_info.drop(family,axis=1,inplace=True)
preferences = plant_info.avg_pref.to_numpy()

#bed info
bed_info = pd.read_csv('../data/bed_data.csv')
bed_info.index.name = 'bed_index'
beds = bed_info.bed.to_numpy()
bed_index = bed_info.index.to_numpy()
bed_sun_req = bed_info.sun.to_numpy()
num_beds = len(beds)

#time dimension
num_years = 3
years = np.array(range(1,num_years+1))
year_index = np.array(range(num_years))

#for keeping track of what axis is which
plant_axis = 0
bed_axis = 1
year_axis = 2

##### Constraints #####

#initialize sun constraint. 1 where plant can feasibly be planted in bed. 0 where sun requirements do not match. 
sun_constraint = np.ones(shape=(num_plants,num_beds,num_years))
for p in plant_index:
    for b in bed_index:
        p_sun = plant_sun_req[p]
        b_sun = bed_sun_req[b]
        if p_sun != b_sun:
            sun_constraint[p,b,:] = 0
            
def enforce_sun_constraint(plan,sun_constraint):
    """
    Force plan to be 0 where sun requirements for plant and bed do not match. 
    """
    return plan*sun_constraint

def enforce_perennial_constraint(plan,plant,bed,year,perennials):
    """Forward fill plan for perennial plants. If 1 in a given bed/year, it will be 1 in same bed thereafter."""

    perennial_plan = plan.copy()

    #what was planted the year before
    plant_last_year = perennial_plan[:,bed,year-1].argmax() 

    #if the plant is a perennial, plant it this year and every year thereafter
    if plant in perennials:
        perennial_plan[:,bed,year:] = 0 # zeros out anything else that may have been planted in bed in current and subsequent years during a previous make_neighbor call
        perennial_plan[plant,bed,year:] = 1 #sets plant to 1 in bed every year after the current year
   
    #if what was planted already in this bed was a perennial, remove it from previous years
    elif plant_last_year in perennials:
        perennial_plan[plant_last_year,bed,:year] = 0

    return perennial_plan

def enforce_disease_constraint(plan,problem_plants):
    """Creates a mask to determine if the same veg was planted in the same bed over multiple years.
       Multiplies the plan for problem plants by 0 in subsequent years where we planned to put them in the same bed
    """

    disease_plan = plan.copy()

    #mask to determine cases where same thing was planted in the same bed yoy
    same_veg_in_bed_yoy = disease_plan.cumsum(axis=year_axis)>1 

    #multiply plan for specific problem plants by 0 
    disease_plan[problem_plants] = disease_plan[problem_plants]*(abs(1-same_veg_in_bed_yoy)[problem_plants])
    return disease_plan


##### Objectives #####

#the most satisfied you could be (planting fruit or vegetable with highest preference in all beds every year)
max_yums = num_beds*num_years*np.max(preferences)

def compute_yummy_score(plan,preferences,max_yums):
    """Takes the weighted average of the preferences of each plant, weighted by the total qty of plants 
    in the current plan for each plant. Maximization encourages plants with higher preferences to be planted in higher quantities."""
    plan_yummy = plan.copy()
    plan_by_plant = plan_yummy.sum(axis=(bed_axis,year_axis))
    yums = round(np.dot(preferences,plan_by_plant)/max_yums*100,1)
    return yums

def compute_variety_score(plan,num_plants):
    """Sums the number of unique plants that are actually planted in the garden. Counts the number of plants that are being planted across all beds.
       Then counts the number of plants with non-zero planting plan. 
       Maximization encourages more unique plants to be planted."""
    plan_variety = plan.copy()
    num_plants_in_plan = (plan_variety.sum(axis=(bed_axis,year_axis)) > 0).sum()
    variety_score = round(num_plants_in_plan/num_plants*100,1)
    return variety_score


#### Analysis & Visualization ####

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