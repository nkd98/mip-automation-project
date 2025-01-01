# -*- coding: utf-8 -*-
"""MIP_data_analysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1A3uUMCgg-CKXKbEnLbwto_eGLgPKEJK6
"""

# MIP Data Analysis
# Author: Niruj Deka
# Last Updated: 31-Dec-24

"""# Introduction and Setup"""

# prompt: install all the neccesary packages to run this notebook

!pip install pandas

# importing pacakges
import pandas as pd

# provide access to Google Drive. Authorise Google Drive when prompted
from google.colab import drive
drive.mount('/content/drive')

# check currect working directory
!pwd

## Please ensure that the folder you will be working with is in your Drive.
## If it is a shared folder, you need to move it to your Drive.

# list the files in the directory : change it your folder
!ls /content/drive/MyDrive/MIP

"""# Load Datasets.
Requirements: 1) MIP Data, 2) List of middle Schools.
Please ensure that both datasets is in the same folder.
"""

######## Read MIP data

# Assuming the file is named 'Status_Report_30Dec.csv' and is located in the folder.
# Replace 'Status_Report_30Dec.csv' and the folder path if necessary.

mip_file_path = '/content/drive/MyDrive/MIP/Status_Report_30Dec.csv'  # Update with the correct path

# read the data
mip_data = pd.read_csv(mip_file_path)

# check the columns
mip_data.columns

######### Read the School Data: List of all middle-schools

# Assuming the xlsx file is named 'School_List.xlsx' and is located in the same directory.
# Replace 'School_List.xlsx' with the actual file name.
sch_file_path = '/content/drive/MyDrive/MIP/school_list.xlsx'  # Update with the correct path

# Read data from
school_data = pd.read_excel(sch_file_path)

#print(school_data.head()) # print the first 5 rows to check

# Keep only necessary columns
school_data = school_data[['DISTRICT NAME', 'BLOCK NAME','UDISE+ SCHOOL CODE', 'SCHOOL NAME']]
#print(school_data.head()) # print the first 5 rows to check

# Rename the column from 'UDISE+ SCHOOL CODE' to 'School ID'
school_data = school_data.rename(columns={'UDISE+ SCHOOL CODE': 'School ID'})
print(school_data.head()) # print the first 5 rows to check

"""# Cleaning and Merging of Datasets"""

# Check for duplicates in the 'School ID' column of MIP Data
num_duplicates = mip_data['School ID'].duplicated(keep=False).sum()

if num_duplicates > 0:
    print(f"There are {num_duplicates} duplicates in the 'School ID' column.")
else:
    print("There are no duplicates in the 'School ID' column.")

# Create a new variable which takes value completed if value of projectstatus is completed, takes value started if not
mip_data['MIP_Status'] = mip_data['Project Status'].apply(lambda x: 'submitted' if x == 'submitted' else 'started')

# If a School ID has multiple MIP_Status values, it keeps the row with 'completed' if available;
# otherwise, it keeps the first available status for that school.

# Step 1: Sort the data by 'School ID' and 'MIP_Status' (alphabetical order)
mip_data_sorted = mip_data.sort_values(by=['School ID', 'MIP_Status'], ascending=[True, True])

# Step 2: Drop duplicates based on 'School ID', keeping the first row (which will be the 'completed' row if available)
mip_data_deduped = mip_data_sorted.drop_duplicates(subset='School ID', keep='last')

mip_data_sorted['MIP_Status'].value_counts()

# Convert school id to strings in both dataset. Merge the mip data with school data using School Id . Show how many mere merged and how many didnot merge. Replace mip status with notstarted for the unmerged observations

# Convert 'School ID' to string in both DataFrames
mip_data_deduped['School ID'] = mip_data_deduped['School ID'].astype(str)
school_data['School ID'] = school_data['School ID'].astype(str)

# Merge the two datasets
merged_data = pd.merge(school_data, mip_data_deduped,  on='School ID', how='left', indicator=True)

# Calculate the number of merged and unmerged observations
merged_count = len(merged_data[merged_data['_merge'] == 'both'])
unmerged_count = len(merged_data[merged_data['_merge'] == 'left_only'])

print(f"Number of observations merged: {merged_count}")
print(f"Number of observations not merged: {unmerged_count}")

# Replace 'MIP_Status' with 'notstarted' for unmerged observations
merged_data.loc[merged_data['_merge'] == 'left_only', 'MIP_Status'] = 'notstarted'

# Remove the '_merge' indicator column
merged_data = merged_data.drop('_merge', axis=1)

print(merged_data.head())

"""# Tables"""

#Show number of schools for mip status. Show Number of schools for each category of mip status  by district.

# Group by 'MIP_Status' and count the number of schools
mip_status_counts = merged_data.groupby('MIP_Status')['School ID'].count()
print("\nNumber of schools for each MIP status:")
print(mip_status_counts)

##### District wise Tables #####

# Calculate total number of schools per district
district_totals = merged_data.groupby('DISTRICT NAME')['School ID'].count().reset_index(name='Total Schools')

# Calculate the number of schools in each MIP status category by district
mip_by_district = merged_data.groupby(['DISTRICT NAME', 'MIP_Status'])['School ID'].count().reset_index(name='School Count')

# Merge the total schools and school counts
district_summary = pd.merge(district_totals, mip_by_district, on='DISTRICT NAME')

# Calculate the percentage of schools in each MIP status category
district_summary['Percentage'] = ((district_summary['School Count'] / district_summary['Total Schools']) * 100).round(2)  # Round to 2 decimal po

# Pivot the table to wide format
district_summary_wide = district_summary.pivot(index='DISTRICT NAME', columns='MIP_Status', values=['School Count', 'Percentage'])

# Add total schools as a column for clarity
district_summary_wide['Total Schools'] = district_totals.set_index('DISTRICT NAME')

# Flatten the MultiIndex columns
district_summary_wide.columns = [' '.join(col).strip() for col in district_summary_wide.columns.values]

# Reset the index to make the district names a column
district_summary_wide.reset_index(inplace=True)

# Display the wide-format table
print("\nWide-format Table: Number of schools (and percentage) in each MIP status category by district")
print(district_summary_wide)

# export to google sheet
from google.colab import sheets
sheet = sheets.InteractiveSheet(df=district_summary_wide)

#### Block-Wise Tables ####

# Calculate total number of schools per district and block
block_totals = merged_data.groupby(['DISTRICT NAME', 'BLOCK NAME'])['School ID'].count().reset_index(name='Total Schools')

# Calculate the number of schools in each MIP status category by district and block
mip_by_block = merged_data.groupby(['DISTRICT NAME', 'BLOCK NAME', 'MIP_Status'])['School ID'].count().reset_index(name='School Count')

# Merge the total schools and school counts
block_summary = pd.merge(block_totals, mip_by_block, on=['DISTRICT NAME', 'BLOCK NAME'])

# Calculate the percentage of schools in each MIP status category
block_summary['Percentage'] = ((block_summary['School Count'] / block_summary['Total Schools']) * 100).round(2)

# Pivot the table to wide format
block_summary_wide = block_summary.pivot(index=['DISTRICT NAME', 'BLOCK NAME'], columns='MIP_Status', values=['School Count', 'Percentage'])

# Add total schools as a column for clarity
block_summary_wide['Total Schools'] = block_totals.set_index(['DISTRICT NAME', 'BLOCK NAME'])

# Flatten the MultiIndex columns
block_summary_wide.columns = [' '.join(col).strip() for col in block_summary_wide.columns.values]

# Reset the index to make the district and block names columns
block_summary_wide.reset_index(inplace=True)

# Display the wide-format table
print("\nWide-format Table: Number of schools (and percentage) in each MIP status category by district and block")
print(block_summary_wide)

# export to google sheet
from google.colab import sheets
sheet = sheets.InteractiveSheet(df=block_summary_wide)

"""# Dashboard Creation"""

# Create a Dashboard showing the District data.

import pandas as pd
from google.colab import data_table
from google.colab import drive
from google.colab import sheets

# Assuming your data is in the 'merged_data' DataFrame from the previous code

# Display the DataFrame using data_table for interactive exploration
data_table.DataTable(merged_data)

# Example of creating a summary table (replace with your desired dashboard elements)
# This uses the district_summary_wide DataFrame that was already created
data_table.DataTable(district_summary_wide)


# Example of creating a chart (replace with your desired dashboard elements and chart type)
# Install plotly for creating interactive charts
!pip install plotly

import plotly.express as px

# Create a bar chart showing the number of schools by district and MIP status
fig = px.bar(district_summary, x='DISTRICT NAME', y='School Count', color='MIP_Status',
             title="Number of Schools by District and MIP Status",
             labels={'School Count': 'Number of Schools'})
fig.show()

# Add more charts or tables to create your dashboard as needed
# You can use other plotting libraries like matplotlib or seaborn if preferred