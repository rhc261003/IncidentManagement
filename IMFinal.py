import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

def convert_sla_to_timedelta(sla):
    parts = sla.split(':')
    days = int(parts[0])
    hours = int(parts[1])
    minutes = int(parts[2])
    seconds = int(parts[3])
    return pd.Timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

def sample_sla_breached_data(im_df, sample_size):
    sample_df = im_df[im_df['SLA Breached(T/F)'] == True]
    sampled_df = sample_df.groupby('Creation Month').apply(lambda x: x.sample(n=min(len(x), sample_size)))
    return sampled_df.reset_index(drop=True)

# Streamlit App
st.title('Incident Management')

# Sidebar for file upload
st.sidebar.title('File Upload')
IM_file = st.sidebar.file_uploader('Upload Incident Dump Excel File', type='xlsx')
sla_file = st.sidebar.file_uploader('Upload SLA Excel File', type='xlsx')

# Sidebar for sample size input
st.sidebar.title('Sample Size for SLA Breaches')
sample_size = st.sidebar.number_input('Enter the sample size for each month:', min_value=1, value=1)

if IM_file is not None and sla_file is not None:
    # Load data
    im_df = pd.read_excel(IM_file)
    sla_df = pd.read_excel(sla_file)
    
    im_df = pd.merge(im_df, sla_df, on='Priority', how="left")
    im_df['Time taken for resolution (days)'] = (im_df['Resolution Date'] - im_df['Creation Date']).dt.days
    im_df['SLA'] = im_df['SLA'].apply(convert_sla_to_timedelta)
    im_df['SLA Breached By (days)'] = im_df['Time taken for resolution (days)'] - im_df['SLA'].dt.days
    im_df['Creation Month'] = im_df['Creation Date'].dt.to_period('M')
    im_df['Resolution Month'] = im_df['Resolution Date'].dt.to_period('M')
    im_df['SLA Breached(T/F)'] = im_df['SLA Breached By (days)'].apply(lambda x: True if x >= 1 else False)

    # Number of Incidents Created Each Month
    st.header('Number of Incidents Created Each Month')
    plt.figure(figsize=(10, 6))
    creation_monthly_counts = im_df['Creation Month'].value_counts().sort_index()
    plt.plot(creation_monthly_counts.index.astype(str), creation_monthly_counts.values, marker='o', linestyle='-', color="green")
    for i, count in enumerate(creation_monthly_counts.values):
        plt.text(i, count, str(count), ha='center', va='bottom', fontsize=10)
    plt.title('Number of Incidents Created Each Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Incidents')
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(plt)
    plt.clf()  # Clear the current figure

    # Number of Incidents Resolved Each Month
    st.header('Number of Incidents Resolved Each Month')
    plt.figure(figsize=(10, 6))
    resolution_monthly_counts = im_df['Resolution Month'].value_counts().sort_index()
    plt.plot(resolution_monthly_counts.index.astype(str), resolution_monthly_counts.values, marker='.', linestyle='-', color="green")
    for i, count in enumerate(resolution_monthly_counts.values):
        plt.text(i, count, str(count), ha='center', va='top', fontsize=10)
    plt.title('Number of Incidents Resolved Each Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Incidents')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(plt)
    plt.clf()  # Clear the current figure

    # Count of Incidents by Priority Each Month
    st.header('Count of Incidents by Priority')
    all_priorities = im_df['Priority'].unique()
    for priority in all_priorities:
        plt.figure(figsize=(10, 6))
        priority_monthly_counts = im_df.pivot_table(index='Creation Month', columns='Priority', aggfunc='size', fill_value=0)
        plt.plot(priority_monthly_counts.index.astype(str), priority_monthly_counts[priority], marker='o', linestyle='-', label=priority)
        for i, count in enumerate(priority_monthly_counts[priority]):
            plt.text(i, count, str(count), ha='center', va='bottom', fontsize=10)
        plt.title(f'Count of Incidents by Priority: {priority}')
        plt.xlabel('Month')
        plt.ylabel('Number of Incidents')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True)
        st.pyplot(plt)
        plt.clf()  # Clear the current figure

    # Distribution of Incidents by Application
    st.header('Distribution of Incidents by Application')
    plt.figure(figsize=(16, 8))
    application_counts = im_df['Application'].value_counts()
    bars = plt.bar(application_counts.index, application_counts.values, color='lightgreen', width=0.9, edgecolor='black')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.2, round(yval, 1), ha='center', va='bottom')
    plt.title('Distribution of Incidents by Application')
    plt.xlabel('Application')
    plt.ylabel('Number of Incidents')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()  # Clear the current figure

    # Distribution of Priorities
    st.header('Distribution of Priorities')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    priority_counts = im_df['Priority'].value_counts()
    ax1.pie(priority_counts, labels=priority_counts.index, autopct='%1.1f%%', startangle=60)
    ax1.set_title('Distribution of Priorities')
    ax1.axis('equal')

    bars = ax2.bar(priority_counts.index, priority_counts.values, color='lightgreen', width=0.5, edgecolor='black')
    for bar in bars:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', va='bottom', fontsize=12)
    ax2.set_title('Histogram of Priorities')
    ax2.set_xlabel('Priority')
    ax2.set_ylabel('Frequency')
    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()  # Clear the current figure

    # SLA Breached (T/F)
    st.header('SLA Breached (T/F)')
    plt.figure(figsize=(2, 1.5))
    sla_breached_counts = im_df['SLA Breached(T/F)'].value_counts()
    colors = ['gray', 'green']
    plt.pie(sla_breached_counts, labels=sla_breached_counts.index, colors=colors, autopct='%1.1f%%', startangle=0)
    plt.title('SLA Breached (T/F)')
    plt.axis('equal')
    st.pyplot(plt)
    plt.clf()  # Clear the current figure

    # Count of SLA Breaches by Priority
    st.header('Count of SLA Breaches by Priority')
    plt.figure(figsize=(12, 5))
    sla_breaches = im_df[im_df['SLA Breached(T/F)'] == True]
    sla_breaches_count = sla_breaches.groupby('Priority').size()
    bars = plt.bar(sla_breaches_count.index, sla_breaches_count.values, color='lightgreen', width=0.5, edgecolor='black')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', va='bottom', fontsize=12)
    plt.title('Count of SLA Breaches by Priority')
    plt.xlabel('Priority')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()  # Clear the current figure

    # Percentage of SLA Breaches by Priority
    st.header('Percentage of SLA Breaches by Priority')
    plt.figure(figsize=(12, 5))
    sla_breached_percentage = im_df.groupby('Priority').agg(
        total_incidents=('Incident ID', 'count'),
        breached_incidents=('SLA Breached(T/F)', 'sum')
    ).reset_index()
    sla_breached_percentage['breached_percentage'] = (
        sla_breached_percentage['breached_incidents'] / sla_breached_percentage['total_incidents'] * 100
    )
    bars = plt.bar(sla_breached_percentage['Priority'], sla_breached_percentage['breached_percentage'], color='lightgreen', width=0.5, edgecolor='black')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f'{yval:.1f}%', ha='center', va='bottom', fontsize=12)
    plt.title('Percentage of SLA Breaches by Priority')
    plt.xlabel('Priority')
    plt.ylabel('Percentage')
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()  # Clear the current figure

    # Download entire list of SLA breaches
    st.header('Download Entire List of SLA Breaches')
    sla_breached_df = im_df[im_df['SLA Breached(T/F)'] == True]
    sla_breached_csv = sla_breached_df.to_csv(index=False)
    st.download_button(label='Download Full SLA Breaches CSV', data=sla_breached_csv, file_name='full_sla_breaches.csv', mime='text/csv')

    # Download sampled list of SLA breaches
    st.header('Download Sampled List of SLA Breaches')
    sampled_sla_breached_df = sample_sla_breached_data(im_df, sample_size)
    sampled_sla_breached_csv = sampled_sla_breached_df.to_csv(index=False)
    st.download_button(label='Download Sampled SLA Breaches CSV', data=sampled_sla_breached_csv, file_name='sampled_sla_breaches.csv', mime='text/csv')
