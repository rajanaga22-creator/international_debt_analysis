import os
import re
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
import seaborn as sns

try:
    import streamlit as st
except ModuleNotFoundError:
    st = None

cache_data = st.cache_data if st is not None else lambda function: function
cache_resource = st.cache_resource if st is not None else lambda function: function

try:
    from sqlalchemy import create_engine, text
except ModuleNotFoundError:
    create_engine = None
    text = None

# Database connection configuration
host = 'localhost'
port = 5432
database = 'debt_db'
username = 'postgres'
password = 'nagarajan'
connection_string = f'postgresql://{username}:{password}@{host}:{port}/{database}'


@cache_resource
def get_connection():
    return create_engine(connection_string) if create_engine else None


connection = get_connection()

# Configure pandas to display full tables
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


@cache_data
def load_metadata():
    country_series = pd.read_csv(r'C:\Users\rajanaga22\mini_pro_two\Country-Series - Metadata.csv', encoding='latin-1')
    country_metadata = pd.read_csv(r'C:\Users\rajanaga22\mini_pro_two\IDS_CountryMetaData.csv', encoding='latin-1')
    country_metadata['Latest population census'] = pd.to_numeric(
        country_metadata['Latest population census'], errors='coerce'
    )
    country_metadata.loc[106, 'Latest population census'] = 1987
    country_metadata['Region'] = country_metadata['Region'].fillna(country_metadata['Long Name'])
    income_group_mode = country_metadata['Income Group'].mode(dropna=True)
    if not income_group_mode.empty:
        country_metadata['Income Group'] = country_metadata['Income Group'].fillna(income_group_mode.iloc[0])
    currency_unit_mode = country_metadata['Currency Unit'].mode(dropna=True)
    if not currency_unit_mode.empty:
        country_metadata['Currency Unit'] = country_metadata['Currency Unit'].fillna(currency_unit_mode.iloc[0])
    foot_note = pd.read_csv(r'C:\Users\rajanaga22\mini_pro_two\IDS_FootNoteMetaData.csv', encoding='latin-1')
    series_metadata = pd.read_csv(r'C:\Users\rajanaga22\mini_pro_two\IDS_SeriesMetaData.csv', encoding='latin-1')
    series_metadata = series_metadata.dropna(how='all').copy()
    series_metadata = series_metadata.drop(
        columns=[
            col for col in [
                'License Type',
                'Limitations and exceptions',
                'General comments'
            ]
            if col in series_metadata.columns
        ],
        errors='ignore'
    )
    for column in ['Short definition', 'Dataset']:
        if column in series_metadata.columns:
            mode = series_metadata[column].mode(dropna=True)
            if not mode.empty:
                series_metadata[column] = series_metadata[column].fillna(mode.iloc[0])
    return country_series, country_metadata, foot_note, series_metadata


@cache_data
def load_all_countries_data():
    source_df = pd.read_csv(r'C:\Users\rajanaga22\mini_pro_two\IDS_ALLCountries_Data.csv', encoding='latin-1')
    source_df['Country Name'] = source_df['Country Name'].astype('string').str.strip()
    source_df = source_df.loc[
        source_df['Country Name'].notna()
        & source_df['Country Name'].ne('')
        & source_df['Country Name'].ne('Unknown')
    ].copy()
    year_columns = [col for col in source_df.columns if str(col).isdigit()]
    id_columns = ['Country Name', 'Country Code', 'Series Code']
    all_countries_data = source_df.loc[:, id_columns + year_columns].melt(
        id_vars=id_columns,
        value_vars=year_columns,
        var_name='Year',
        value_name='Value'
    )
    all_countries_data['Year'] = pd.to_numeric(all_countries_data['Year'], errors='coerce')
    all_countries_data['Value'] = pd.to_numeric(all_countries_data['Value'], errors='coerce')
    all_countries_data['Country Code'] = all_countries_data['Country Code'].astype('string').str.strip()
    all_countries_data = all_countries_data.loc[
        ~(
            all_countries_data['Country Name'].astype(str).str.strip().eq('0')
            & all_countries_data['Country Code'].astype(str).str.strip().eq('0')
        )
    ].copy()
    all_countries_data = (
        all_countries_data.groupby(
            ['Country Name', 'Country Code', 'Series Code', 'Year'],
            as_index=False
        )['Value']
        .sum()
        .sort_values(['Country Name', 'Country Code', 'Series Code', 'Year'])
        .reset_index(drop=True)
    )
    all_countries_data = all_countries_data[
        ['Country Name', 'Country Code', 'Series Code', 'Year', 'Value']
    ]
    value_groups = all_countries_data.groupby(['Country Code', 'Series Code'])['Value']
    all_countries_data['Value'] = value_groups.transform(lambda values: values.ffill().bfill())
    all_countries_data = all_countries_data.dropna(subset=['Country Code'])
    return all_countries_data


country_series, country_metadata, foot_note, series_metadata = load_metadata()
all_countries_data = load_all_countries_data()

year_wise_totals = (
    all_countries_data.groupby(['Country Name', 'Year'], as_index=False)['Value']
    .sum()
    .sort_values(['Country Name', 'Year'])
    .reset_index(drop=True)
)
country_year_chart_data = (
    all_countries_data.groupby(
        ['Country Name', 'Country Code', 'Year'],
        as_index=False
    )['Value']
    .sum()
    .sort_values(['Country Name', 'Year'])
    .reset_index(drop=True)
)


def country_trend_figure(data):
    return px.line(
        data.sort_values(['Year', 'Country Name']),
        x='Year',
        y='Value',
        color='Country Name',
        hover_name='Country Name',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        markers=True,
        title='Debt Values by Country and Year',
        labels={'Value': 'Debt value', 'Year': 'Year'},
    ).update_layout(height=500)


def latest_country_map_figure(data):
    latest_year = data['Year'].max()
    latest_data = data[data['Year'] == latest_year]
    return px.choropleth(
        latest_data,
        locations='Country Code',
        color='Value',
        hover_name='Country Name',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        locationmode='ISO-3',
        color_continuous_scale='Blues',
        title=f'Debt Values by Country ({int(latest_year)})',
        labels={'Value': 'Debt value'},
    )


def country_totals_figure(data):
    totals = (
        data.groupby(['Country Code', 'Country Name'], as_index=False)['Value']
        .sum()
        .sort_values('Value', ascending=False)
    )
    return px.bar(
        totals,
        x='Value',
        y='Country Name',
        orientation='h',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        title='Total Debt Value by Country',
        labels={'Value': 'Total debt value ($)', 'Country Name': 'Country'},
    ).update_yaxes(categoryorder='total ascending').update_layout(height=800)

def indicator_count_vs_debt_figure(data):
    required_columns = {'Country Code', 'Country Name', 'Series Code', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.scatter(title='Number of Indicators vs Total Debt')

    country_summary = (
        data.groupby(['Country Code', 'Country Name'], as_index=False)
        .agg(
            total_debt=('Value', 'sum'),
            indicator_count=('Series Code', 'nunique'),
        )
    )

    return px.scatter(
        country_summary,
        x='indicator_count',
        y='total_debt',
        size='total_debt',
        hover_name='Country Name',
        hover_data={
            'Country Code': True,
            'indicator_count': True,
            'total_debt': '$,.2f',
        },
        title='Number of Indicators vs Total Debt by Country',
        labels={
            'indicator_count': 'Number of indicators',
            'total_debt': 'Total debt value ($)',
        },
    ).update_layout(height=600)

#Highest and lowest debt values for countries

def country_ranked_debt_figure(data, highest=True, count=10):
    totals = (
        data.groupby(['Country Code', 'Country Name'], as_index=False)['Value']
        .sum()
    )
    if highest:
        ranked = totals.nlargest(count, 'Value')
        title = f'Top {count} Countries by Total Debt'
    else:
        ranked = totals.nsmallest(count, 'Value')
        title = f'Bottom {count} Countries by Total Debt'

    ranked = ranked.sort_values('Value')
    return px.bar( 
        ranked,
        x='Value',
        y='Country Name',
        orientation='h',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        title=title,
        labels={'Value': 'Total debt value ($)', 'Country Name': 'Country'},
    ).update_layout(height=400)


def country_debt_pie_figure(data, top_n=10):
    totals = (
        data.groupby('Country Name', as_index=False)['Value']
        .sum()
        .sort_values('Value', ascending=False)
    )
    top_countries = totals.head(top_n).copy()
    other_total = totals.iloc[top_n:]['Value'].sum()
    if other_total > 0:
        top_countries.loc[len(top_countries)] = ['Other', other_total]

    return px.pie(
        top_countries,
        names='Country Name',
        values='Value',
        title='Overall Debt Distribution by Country',
        hole=0.35,
    ).update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Total debt: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
    )


def region_debt_pie_figure(data):
    required_columns = {'Country Code', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.pie(title='Debt Value by Region')

    region_lookup = country_metadata[['Code', 'Region']].copy()
    region_lookup['Code'] = region_lookup['Code'].map(normalize_country_code)
    region_lookup['Region'] = region_lookup['Region'].fillna('Unknown')

    region_totals = data.merge(
        region_lookup,
        left_on='Country Code',
        right_on='Code',
        how='left',
    )
    region_totals['Region'] = region_totals['Region'].fillna('Unknown')
    region_totals = (
        region_totals.groupby('Region', as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'Debt value'})
    )

    return px.pie(
        region_totals,
        names='Region',
        values='Debt value',
        title='Debt Value by Region',
        hole=0.35,
    ).update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Debt value: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
    ).update_layout(height=500)


def region_trend_figure(data):
    required_columns = {'Country Code', 'Year', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.line(title='Debt Trend by Region')

    region_lookup = country_metadata[['Code', 'Region']].copy()
    region_lookup['Code'] = region_lookup['Code'].map(normalize_country_code)
    region_lookup['Region'] = region_lookup['Region'].fillna('Unknown')

    regional_data = data.copy()
    regional_data['Country Code'] = regional_data['Country Code'].map(normalize_country_code)
    regional_data = regional_data.merge(
        region_lookup,
        left_on='Country Code',
        right_on='Code',
        how='left',
    )
    regional_data['Region'] = regional_data['Region'].fillna('Unknown')
    regional_totals = (
        regional_data.groupby(['Region', 'Year'], as_index=False)['Value']
        .sum()
    )

    return px.line(
        regional_totals,
        x='Year',
        y='Value',
        color='Region',
        markers=True,
        title='Debt Trend by Region',
        labels={'Value': 'Debt value', 'Year': 'Year'},
        hover_data={'Value': '$,.2f'},
    ).update_layout(height=550)


def region_country_treemap_figure(data):
    required_columns = {'Country Code', 'Country Name', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.treemap(title='Debt Contribution by Region and Country')

    region_lookup = country_metadata[['Code', 'Region']].copy()
    region_lookup['Code'] = region_lookup['Code'].map(normalize_country_code)
    region_lookup['Region'] = region_lookup['Region'].fillna('Unknown')

    treemap_data = data.copy()
    treemap_data['Country Code'] = treemap_data['Country Code'].map(normalize_country_code)
    treemap_data = treemap_data.merge(
        region_lookup,
        left_on='Country Code',
        right_on='Code',
        how='left',
    )
    treemap_data['Region'] = treemap_data['Region'].fillna('Unknown')
    treemap_data['Country Name'] = treemap_data['Country Name'].fillna(
        treemap_data['Country Code'].replace('', 'Unknown')
    )
    country_totals = (
        treemap_data.groupby(['Region', 'Country Name'], as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'Debt value'})
    )

    return px.treemap(
        country_totals,
        path=['Region', 'Country Name'],
        values='Debt value',
        color='Debt value',
        color_continuous_scale='Blues',
        title='Debt Contribution by Region and Country',
        hover_data={'Debt value': '$,.2f'},
    ).update_traces(
        hovertemplate='<b>%{label}</b><br>Debt value: $%{value:,.2f}<br>Share of parent: %{percentParent:.2%}<extra></extra>'
    ).update_layout(height=700)


def series_code_to_indicator_label(series_code, indicator_lookup=None):
    if pd.isna(series_code):
        return 'Unknown indicator'
    value = str(series_code).strip()
    if not value:
        return 'Unknown indicator'
    if indicator_lookup is not None and value in indicator_lookup:
        return indicator_lookup[value]
    match = re.search(r'(\d+)$', value)
    if match:
        return f'Indicator {match.group(1)}'
    return f'Indicator {value}'


def debt_indicator_figure(data, top_n=15):
    if data is None or data.empty or 'Series Code' not in data.columns or 'Value' not in data.columns:
        return px.bar(title='Debt by Indicator')

    indicator_lookup = {}
    if 'series_metadata' in globals() and series_metadata is not None and 'Code' in series_metadata.columns and 'Indicator Name' in series_metadata.columns:
        indicator_lookup = (
            series_metadata[['Code', 'Indicator Name']]
            .drop_duplicates()
            .set_index('Code')['Indicator Name']
            .to_dict()
        )

    indicator_totals = (
        data.groupby('Series Code', as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'Debt value'})
    )
    indicator_totals['Indicator'] = indicator_totals['Series Code'].map(
        lambda code: series_code_to_indicator_label(code, indicator_lookup)
    )
    indicator_totals = indicator_totals.sort_values('Debt value', ascending=False).head(top_n)

    return px.pie(
        indicator_totals,
        names='Indicator',
        values='Debt value',
        title='Debt Value by Indicator',
        hole=0.35,
    ).update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Debt value: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
    ).update_layout(height=500)


def country_series_figure(data):
    series_counts = (
        data.groupby('Country Code', as_index=False)['Series Code']
        .nunique()
        .rename(columns={'Series Code': 'Indicator count'})
        .sort_values('Indicator count', ascending=False)
    )
    return px.bar(
        series_counts,
        x='Indicator count',
        y='Country Code',
        orientation='h',
        hover_data={'Indicator count': True},
        title='Indicators Available by Country',
        labels={'Country Code': 'Country'},
    ).update_yaxes(categoryorder='total ascending').update_layout(height=800)


def country_metadata_figure(data):
    region_counts = (
        data['Region']
        .fillna('Unknown')
        .value_counts()
        .rename_axis('Region')
        .reset_index(name='Country count')
    )
    return px.bar(
        region_counts,
        x='Region',
        y='Country count',
        color='Region',
        title='Countries by Region',
        labels={'Country count': 'Number of countries'},
    )


def footnote_figure(data):
    footnote_counts = data.copy()
    footnote_counts['Year'] = footnote_counts['Time Code'].str.extract(r'(\d{4})')[0]
    footnote_counts = (
        footnote_counts.dropna(subset=['Year'])
        .groupby('Year', as_index=False)
        .size()
        .rename(columns={'size': 'Footnote count'})
    )
    return px.bar(
        footnote_counts,
        x='Year',
        y='Footnote count',
        title='Footnotes by Year',
        labels={'Footnote count': 'Number of footnotes'},
    )


def series_metadata_figure(data):
    topic_counts = (
        data['Topic']
        .fillna('Unknown')
        .value_counts()
        .head(15)
        .rename_axis('Topic')
        .reset_index(name='Series count')
    )
    return px.bar(
        topic_counts.sort_values('Series count'),
        x='Series count',
        y='Topic',
        orientation='h',
        title='Series by Topic',
        labels={'Series count': 'Number of series'},
    )


def normalize_country_code(value):
    if pd.isna(value):
        return ''
    cleaned = str(value).strip()
    if not cleaned:
        return ''
    match = re.search(r'\(([^)]+)\)$', cleaned)
    if match:
        return match.group(1).strip()
    return cleaned.replace(' ', '')


country_series_lookup = (
    country_series.assign(CountryCodeNorm=lambda df: df['Country Code'].map(normalize_country_code))
    .rename(columns={'Description': 'Country Series Description'})
    [['CountryCodeNorm', 'Series Code', 'Country Series Description']]
    .rename(columns={'CountryCodeNorm': 'Country Code'})
    .drop_duplicates()
)

footnote_lookup = (
    foot_note.assign(CountryCodeNorm=lambda df: df['Country Code'].map(normalize_country_code))
    .rename(columns={'Description': 'Footnote Description'})
    [['CountryCodeNorm', 'Series Code', 'Footnote Description']]
    .rename(columns={'CountryCodeNorm': 'Country Code'})
    .drop_duplicates()
    .groupby(['Country Code', 'Series Code'], as_index=False)['Footnote Description']
    .agg(lambda values: ' | '.join(str(v) for v in values if str(v).strip()))
)

country_metadata_lookup = country_metadata.rename(columns={'Code': 'Country Code'})
country_metadata_lookup['Country Code'] = country_metadata_lookup['Country Code'].map(normalize_country_code)
if connection is not None and os.getenv('LOAD_DATA_TO_DB', '').lower() == 'true':
    country_series.to_sql('country_series', connection, if_exists='replace', index=False)
    all_countries_data.to_sql('all_countries_data', connection, if_exists='replace', index=False)
    country_metadata.to_sql('country_metadata', connection, if_exists='replace', index=False)
    foot_note.to_sql('foot_note', connection, if_exists='replace', index=False)
    series_metadata.to_sql('series_metadata', connection, if_exists='replace', index=False)



# Debt data loading and reshaping
@cache_data
def load_all_countries_data():
    source_df = pd.read_csv(r'C:\Users\rajanaga22\mini_pro_two\IDS_ALLCountries_Data.csv', encoding='latin-1')
    source_df['Country Name'] = source_df['Country Name'].astype('string').str.strip()
    source_df = source_df.loc[
        source_df['Country Name'].notna()
        & source_df['Country Name'].ne('')
        & source_df['Country Name'].ne('Unknown')
    ].copy()
    year_columns = [col for col in source_df.columns if str(col).isdigit()]
    id_columns = ['Country Name', 'Country Code', 'Series Code']
    all_countries_data = source_df.loc[:, id_columns + year_columns].melt(
        id_vars=id_columns,
        value_vars=year_columns,
        var_name='Year',
        value_name='Value'
    )
    all_countries_data['Year'] = pd.to_numeric(all_countries_data['Year'], errors='coerce')
    all_countries_data['Value'] = pd.to_numeric(all_countries_data['Value'], errors='coerce')
    all_countries_data['Country Code'] = all_countries_data['Country Code'].astype('string').str.strip()
    all_countries_data = all_countries_data.loc[
        ~(
            all_countries_data['Country Name'].astype(str).str.strip().eq('0')
            & all_countries_data['Country Code'].astype(str).str.strip().eq('0')
        )
    ].copy()
    all_countries_data = (
        all_countries_data.groupby(
            ['Country Name', 'Country Code', 'Series Code', 'Year'],
            as_index=False
        )['Value']
        .sum()
        .sort_values(['Country Name', 'Country Code', 'Series Code', 'Year'])
        .reset_index(drop=True)
    )
    all_countries_data = all_countries_data[
        ['Country Name', 'Country Code', 'Series Code', 'Year', 'Value']
    ]
    value_groups = all_countries_data.groupby(['Country Code', 'Series Code'])['Value']
    all_countries_data['Value'] = value_groups.transform(lambda values: values.ffill().bfill())
    all_countries_data = all_countries_data.dropna(subset=['Country Code'])
    return all_countries_data


# Load datasets and prepare aggregated chart data
country_series, country_metadata, foot_note, series_metadata = load_metadata()
all_countries_data = load_all_countries_data()

year_wise_totals = (
    all_countries_data.groupby(['Country Name', 'Year'], as_index=False)['Value']
    .sum()
    .sort_values(['Country Name', 'Year'])
    .reset_index(drop=True)
)
country_year_chart_data = (
    all_countries_data.groupby(
        ['Country Name', 'Country Code', 'Year'],
        as_index=False
    )['Value']
    .sum()
    .sort_values(['Country Name', 'Year'])
    .reset_index(drop=True)
)


# Country-level visualizations
def country_trend_figure(data):
    return px.line(
        data.sort_values(['Year', 'Country Name']),
        x='Year',
        y='Value',
        color='Country Name',
        hover_name='Country Name',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        markers=True,
        title='Debt Values by Country and Year',
        labels={'Value': 'Debt value', 'Year': 'Year'},
    ).update_layout(height=500)


def latest_country_map_figure(data):
    latest_year = data['Year'].max()
    latest_data = data[data['Year'] == latest_year]
    return px.choropleth(
        latest_data,
        locations='Country Code',
        color='Value',
        hover_name='Country Name',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        locationmode='ISO-3',
        color_continuous_scale='Blues',
        title=f'Debt Values by Country ({int(latest_year)})',
        labels={'Value': 'Debt value'},
    )


def country_totals_figure(data):
    totals = (
        data.groupby(['Country Code', 'Country Name'], as_index=False)['Value']
        .sum()
        .sort_values('Value', ascending=False)
    )
    return px.bar(
        totals,
        x='Value',
        y='Country Name',
        orientation='h',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        title='Total Debt Value by Country',
        labels={'Value': 'Total debt value ($)', 'Country Name': 'Country'},
    ).update_yaxes(categoryorder='total ascending').update_layout(height=800)

def indicator_count_vs_debt_figure(data):
    required_columns = {'Country Code', 'Country Name', 'Series Code', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.scatter(title='Number of Indicators vs Total Debt')

    country_summary = (
        data.groupby(['Country Code', 'Country Name'], as_index=False)
        .agg(
            total_debt=('Value', 'sum'),
            indicator_count=('Series Code', 'nunique'),
        )
    )

    return px.scatter(
        country_summary,
        x='indicator_count',
        y='total_debt',
        size='total_debt',
        hover_name='Country Name',
        hover_data={
            'Country Code': True,
            'indicator_count': True,
            'total_debt': '$,.2f',
        },
        title='Number of Indicators vs Total Debt by Country',
        labels={
            'indicator_count': 'Number of indicators',
            'total_debt': 'Total debt value ($)',
        },
    ).update_layout(height=600)

#Highest and lowest debt values for countries

def country_ranked_debt_figure(data, highest=True, count=10):
    totals = (
        data.groupby(['Country Code', 'Country Name'], as_index=False)['Value']
        .sum()
    )
    if highest:
        ranked = totals.nlargest(count, 'Value')
        title = f'Top {count} Countries by Total Debt'
    else:
        ranked = totals.nsmallest(count, 'Value')
        title = f'Bottom {count} Countries by Total Debt'

    ranked = ranked.sort_values('Value')
    return px.bar( 
        ranked,
        x='Value',
        y='Country Name',
        orientation='h',
        hover_data={'Country Code': True, 'Value': '$,.2f'},
        title=title,
        labels={'Value': 'Total debt value ($)', 'Country Name': 'Country'},
    ).update_layout(height=400)


def country_debt_pie_figure(data, top_n=10):
    totals = (
        data.groupby('Country Name', as_index=False)['Value']
        .sum()
        .sort_values('Value', ascending=False)
    )
    top_countries = totals.head(top_n).copy()
    other_total = totals.iloc[top_n:]['Value'].sum()
    if other_total > 0:
        top_countries.loc[len(top_countries)] = ['Other', other_total]

    return px.pie(
        top_countries,
        names='Country Name',
        values='Value',
        title='Overall Debt Distribution by Country',
        hole=0.35,
    ).update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Total debt: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
    )


# Regional and indicator visualizations
def region_debt_pie_figure(data):
    required_columns = {'Country Code', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.pie(title='Debt Value by Region')

    region_lookup = country_metadata[['Code', 'Region']].copy()
    region_lookup['Code'] = region_lookup['Code'].map(normalize_country_code)
    region_lookup['Region'] = region_lookup['Region'].fillna('Unknown')

    region_totals = data.merge(
        region_lookup,
        left_on='Country Code',
        right_on='Code',
        how='left',
    )
    region_totals['Region'] = region_totals['Region'].fillna('Unknown')
    region_totals = (
        region_totals.groupby('Region', as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'Debt value'})
    )

    return px.pie(
        region_totals,
        names='Region',
        values='Debt value',
        title='Debt Value by Region',
        hole=0.35,
    ).update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Debt value: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
    ).update_layout(height=500)


def region_trend_figure(data):
    required_columns = {'Country Code', 'Year', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.line(title='Debt Trend by Region')

    region_lookup = country_metadata[['Code', 'Region']].copy()
    region_lookup['Code'] = region_lookup['Code'].map(normalize_country_code)
    region_lookup['Region'] = region_lookup['Region'].fillna('Unknown')

    regional_data = data.copy()
    regional_data['Country Code'] = regional_data['Country Code'].map(normalize_country_code)
    regional_data = regional_data.merge(
        region_lookup,
        left_on='Country Code',
        right_on='Code',
        how='left',
    )
    regional_data['Region'] = regional_data['Region'].fillna('Unknown')
    regional_totals = (
        regional_data.groupby(['Region', 'Year'], as_index=False)['Value']
        .sum()
    )

    return px.line(
        regional_totals,
        x='Year',
        y='Value',
        color='Region',
        markers=True,
        title='Debt Trend by Region',
        labels={'Value': 'Debt value', 'Year': 'Year'},
        hover_data={'Value': '$,.2f'},
    ).update_layout(height=550)


def region_country_treemap_figure(data):
    required_columns = {'Country Code', 'Country Name', 'Value'}
    if data is None or data.empty or not required_columns.issubset(data.columns):
        return px.treemap(title='Debt Contribution by Region and Country')

    region_lookup = country_metadata[['Code', 'Region']].copy()
    region_lookup['Code'] = region_lookup['Code'].map(normalize_country_code)
    region_lookup['Region'] = region_lookup['Region'].fillna('Unknown')

    treemap_data = data.copy()
    treemap_data['Country Code'] = treemap_data['Country Code'].map(normalize_country_code)
    treemap_data = treemap_data.merge(
        region_lookup,
        left_on='Country Code',
        right_on='Code',
        how='left',
    )
    treemap_data['Region'] = treemap_data['Region'].fillna('Unknown')
    treemap_data['Country Name'] = treemap_data['Country Name'].fillna(
        treemap_data['Country Code'].replace('', 'Unknown')
    )
    country_totals = (
        treemap_data.groupby(['Region', 'Country Name'], as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'Debt value'})
    )

    return px.treemap(
        country_totals,
        path=['Region', 'Country Name'],
        values='Debt value',
        color='Debt value',
        color_continuous_scale='Blues',
        title='Debt Contribution by Region and Country',
        hover_data={'Debt value': '$,.2f'},
    ).update_traces(
        hovertemplate='<b>%{label}</b><br>Debt value: $%{value:,.2f}<br>Share of parent: %{percentParent:.2%}<extra></extra>'
    ).update_layout(height=700)


def series_code_to_indicator_label(series_code, indicator_lookup=None):
    if pd.isna(series_code):
        return 'Unknown indicator'
    value = str(series_code).strip()
    if not value:
        return 'Unknown indicator'
    if indicator_lookup is not None and value in indicator_lookup:
        return indicator_lookup[value]
    match = re.search(r'(\d+)$', value)
    if match:
        return f'Indicator {match.group(1)}'
    return f'Indicator {value}'


def debt_indicator_figure(data, top_n=15):
    if data is None or data.empty or 'Series Code' not in data.columns or 'Value' not in data.columns:
        return px.bar(title='Debt by Indicator')

    indicator_lookup = {}
    if 'series_metadata' in globals() and series_metadata is not None and 'Code' in series_metadata.columns and 'Indicator Name' in series_metadata.columns:
        indicator_lookup = (
            series_metadata[['Code', 'Indicator Name']]
            .drop_duplicates()
            .set_index('Code')['Indicator Name']
            .to_dict()
        )

    indicator_totals = (
        data.groupby('Series Code', as_index=False)['Value']
        .sum()
        .rename(columns={'Value': 'Debt value'})
    )
    indicator_totals['Indicator'] = indicator_totals['Series Code'].map(
        lambda code: series_code_to_indicator_label(code, indicator_lookup)
    )
    indicator_totals = indicator_totals.sort_values('Debt value', ascending=False).head(top_n)

    return px.pie(
        indicator_totals,
        names='Indicator',
        values='Debt value',
        title='Debt Value by Indicator',
        hole=0.35,
    ).update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}<br>Debt value: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
    ).update_layout(height=500)


def country_series_figure(data):
    series_counts = (
        data.groupby('Country Code', as_index=False)['Series Code']
        .nunique()
        .rename(columns={'Series Code': 'Indicator count'})
        .sort_values('Indicator count', ascending=False)
    )
    return px.bar(
        series_counts,
        x='Indicator count',
        y='Country Code',
        orientation='h',
        hover_data={'Indicator count': True},
        title='Indicators Available by Country',
        labels={'Country Code': 'Country'},
    ).update_yaxes(categoryorder='total ascending').update_layout(height=800)


# Metadata visualizations
def country_metadata_figure(data):
    region_counts = (
        data['Region']
        .fillna('Unknown')
        .value_counts()
        .rename_axis('Region')
        .reset_index(name='Country count')
    )
    return px.bar(
        region_counts,
        x='Region',
        y='Country count',
        color='Region',
        title='Countries by Region',
        labels={'Country count': 'Number of countries'},
    )


def footnote_figure(data):
    footnote_counts = data.copy()
    footnote_counts['Year'] = footnote_counts['Time Code'].str.extract(r'(\d{4})')[0]
    footnote_counts = (
        footnote_counts.dropna(subset=['Year'])
        .groupby('Year', as_index=False)
        .size()
        .rename(columns={'size': 'Footnote count'})
    )
    return px.bar(
        footnote_counts,
        x='Year',
        y='Footnote count',
        title='Footnotes by Year',
        labels={'Footnote count': 'Number of footnotes'},
    )


def series_metadata_figure(data):
    topic_counts = (
        data['Topic']
        .fillna('Unknown')
        .value_counts()
        .head(15)
        .rename_axis('Topic')
        .reset_index(name='Series count')
    )
    return px.bar(
        topic_counts.sort_values('Series count'),
        x='Series count',
        y='Topic',
        orientation='h',
        title='Series by Topic',
        labels={'Series count': 'Number of series'},
    )


# Identifier normalization and lookup tables
def normalize_country_code(value):
    if pd.isna(value):
        return ''
    cleaned = str(value).strip()
    if not cleaned:
        return ''
    match = re.search(r'\(([^)]+)\)$', cleaned)
    if match:
        return match.group(1).strip()
    return cleaned.replace(' ', '')


# Build lookup tables
country_series_lookup = (
    country_series.assign(CountryCodeNorm=lambda df: df['Country Code'].map(normalize_country_code))
    .rename(columns={'Description': 'Country Series Description'})
    [['CountryCodeNorm', 'Series Code', 'Country Series Description']]
    .rename(columns={'CountryCodeNorm': 'Country Code'})
    .drop_duplicates()
)

footnote_lookup = (
    foot_note.assign(CountryCodeNorm=lambda df: df['Country Code'].map(normalize_country_code))
    .rename(columns={'Description': 'Footnote Description'})
    [['CountryCodeNorm', 'Series Code', 'Footnote Description']]
    .rename(columns={'CountryCodeNorm': 'Country Code'})
    .drop_duplicates()
    .groupby(['Country Code', 'Series Code'], as_index=False)['Footnote Description']
    .agg(lambda values: ' | '.join(str(v) for v in values if str(v).strip()))
)

country_metadata_lookup = country_metadata.rename(columns={'Code': 'Country Code'})
country_metadata_lookup['Country Code'] = country_metadata_lookup['Country Code'].map(normalize_country_code)
# Persist prepared data to the database when enabled
if connection is not None and os.getenv('LOAD_DATA_TO_DB', '').lower() == 'true':
    country_series.to_sql('country_series', connection, if_exists='replace', index=False)
    all_countries_data.to_sql('all_countries_data', connection, if_exists='replace', index=False)
    country_metadata.to_sql('country_metadata', connection, if_exists='replace', index=False)
    foot_note.to_sql('foot_note', connection, if_exists='replace', index=False)
    series_metadata.to_sql('series_metadata', connection, if_exists='replace', index=False)



    
# Streamlit app
if st is not None:
    st.set_page_config(layout='wide')
    st.markdown(
        """
        <style>
            .stApp h1 {
                color: #1f77b4;
                font-weight: 700;
            }
            .stApp h2 {
                color: #ff7f0e;
                font-weight: 700;
            }
            .stApp h3 {
                color: #2ca02c;
                font-weight: 700;
            }
            .stApp h4 {
                color: #d62728;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    page = st.sidebar.selectbox("Navigation", ["Dashboard", "Ask Me"], index=0, key="navigation_page")

    if page == "Ask Me":
        st.title("Ask Me")
        st.subheader("Database Queries")

        query_levels = ["basic", "medium", "advanced"]
        selected_query_level = st.selectbox("Choose query level", query_levels, key="query_level_ask")

        if selected_query_level == "basic":
            query_choices = [
                "Retrieve all distinct country names from the dataset.",
                "Count the total number of countries available.",
                "Find the total number of indicators present.",
                "Display the first 10 records of the dataset.",
                "Calculate the total global debt.",
                "List all unique indicator names.",
                "Find the number of records for each country.",
                "Display all records where debt is greater than 1 billion USD.",
                "Find the minimum, maximum, and average debt values.",
                "Count total number of records in the dataset."
            ]
        elif selected_query_level == "medium":
            query_choices = [
                "Find the total debt for each country.",
                "Display the top 10 countries with the highest total debt.",
                "Find the average debt per country.",
                "Calculate total debt for each indicator.",
                "Identify the indicator contributing the highest total debt.",
                "Find the country with the lowest total debt.",
                "Calculate total debt for each country and indicator combination.",
                "Count how many indicators each country has.",
                "Display countries whose total debt is above the global average.",
                "Rank countries based on total debt (highest to lowest)."
            ]
        else:
            query_choices = [
                "Find the top 5 indicators contributing most to global debt.",
                "Calculate percentage contribution of each country to total global debt.",
                "Identify the top 3 countries for each indicator based on debt.",
                "Find the difference between maximum and minimum debt for each country.",
                "Create a view for the top 10 countries with highest debt.",
                "Categorize countries into: High Debt, Medium Debt, Low Debt (based on thresholds)",
                "Use window functions to calculate cumulative debt per country.",
                "Find indicators where average debt is higher than overall average debt.",
                "Identify countries contributing more than 5% of global debt.",
                "Find the most dominant indicator (highest contribution) for each country."
            ]

        st.write(f"You selected the {selected_query_level} query group.")
        selected_query = st.selectbox("Choose a database query", query_choices, key="query_choice_ask")

        if selected_query_level == "basic":
            if selected_query == "Retrieve all distinct country names from the dataset.":
                result_df = all_countries_data[['Country Name']].drop_duplicates().reset_index(drop=True)
            elif selected_query == "Count the total number of countries available.":
                result_df = pd.DataFrame({"total_countries": [all_countries_data['Country Name'].nunique()]})
            elif selected_query == "Find the total number of indicators present.":
                result_df = pd.DataFrame({"total_indicators": [country_series['Series Code'].nunique()]})
            elif selected_query == "Display the first 10 records of the dataset.":
                result_df = all_countries_data.head(10)
            elif selected_query == "Calculate the total global debt.":
                result_df = pd.DataFrame({"total_global_debt": [all_countries_data['Value'].sum()]})
            elif selected_query == "List all unique indicator names.":
                result_df = pd.DataFrame({"Indicator Name": series_metadata['Indicator Name'].dropna().drop_duplicates().tolist()})
            elif selected_query == "Find the number of records for each country.":
                result_df = all_countries_data.groupby('Country Name').size().reset_index(name='Record count')
            elif selected_query == "Display all records where debt is greater than 1 billion USD.":
                result_df = all_countries_data[all_countries_data['Value'] > 1_000_000_000].reset_index(drop=True)
            elif selected_query == "Find the minimum, maximum, and average debt values.":
                result_df = pd.DataFrame({
                    "metric": ["min", "max", "avg"],
                    "value": [all_countries_data['Value'].min(), all_countries_data['Value'].max(), all_countries_data['Value'].mean()]
                })
            else:
                result_df = pd.DataFrame({"total_records": [len(all_countries_data)]})

        elif selected_query_level == "medium":
            if selected_query == "Find the total debt for each country.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum()
            elif selected_query == "Display the top 10 countries with the highest total debt.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum().nlargest(10, 'Value')
            elif selected_query == "Find the average debt per country.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].mean()
            elif selected_query == "Calculate total debt for each indicator.":
                result_df = all_countries_data.groupby('Series Code', as_index=False)['Value'].sum()
            elif selected_query == "Identify the indicator contributing the highest total debt.":
                result_df = all_countries_data.groupby('Series Code', as_index=False)['Value'].sum().nlargest(1, 'Value')
            elif selected_query == "Find the country with the lowest total debt.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum().nsmallest(1, 'Value')
            elif selected_query == "Calculate total debt for each country and indicator combination.":
                result_df = all_countries_data.groupby(['Country Name', 'Series Code'], as_index=False)['Value'].sum()
            elif selected_query == "Count how many indicators each country has.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Series Code'].nunique().rename(columns={'Series Code': 'indicator_count'})
            elif selected_query == "Display countries whose total debt is above the global average.":
                global_avg = all_countries_data['Value'].mean()
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum().query(f'Value > {global_avg}')
            else:
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum().sort_values('Value', ascending=False)
        else:
            if selected_query == "Find the top 5 indicators contributing most to global debt.":
                result_df = all_countries_data.groupby('Series Code', as_index=False)['Value'].sum().nlargest(5, 'Value')
            elif selected_query == "Calculate percentage contribution of each country to total global debt.":
                total_global_debt = all_countries_data['Value'].sum()
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum()
                result_df['percentage_contribution'] = (result_df['Value'] / total_global_debt) * 100
            elif selected_query == "Identify the top 3 countries for each indicator based on debt.":
                result_df = (
                    all_countries_data.groupby(['Series Code', 'Country Name'], as_index=False)['Value']
                    .sum()
                    .sort_values(['Series Code', 'Value'], ascending=[True, False])
                    .groupby('Series Code')
                    .head(3)
                )
            elif selected_query == "Find the difference between maximum and minimum debt for each country.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].agg(['max', 'min']).reset_index()
                result_df['debt_difference'] = result_df['max'] - result_df['min']
            elif selected_query == "Create a view for the top 10 countries with highest debt.":
                result_df = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum().nlargest(10, 'Value')
            elif selected_query == "Categorize countries into: High Debt, Medium Debt, Low Debt (based on thresholds)":
                total_debt_per_country = all_countries_data.groupby('Country Name', as_index=False)['Value'].sum()
                high_threshold = total_debt_per_country['Value'].quantile(0.75)
                low_threshold = total_debt_per_country['Value'].quantile(0.25)

                def categorize_debt(value):
                    if value >= high_threshold:
                        return 'High Debt'
                    elif value <= low_threshold:
                        return 'Low Debt'
                    return 'Medium Debt'

                total_debt_per_country['Debt Category'] = total_debt_per_country['Value'].apply(categorize_debt)
                result_df = total_debt_per_country
            elif selected_query == "Use window functions to calculate cumulative debt per country.":
                result_df = (
                    all_countries_data.sort_values(['Country Name', 'Year'])
                    .groupby('Country Name', as_index=False)
                    .apply(lambda x: x.assign(cumulative_debt=x['Value'].cumsum()))
                    .reset_index(drop=True)
                )
            elif selected_query == "Find indicators where average debt is higher than overall average debt.":
                overall_avg_debt = all_countries_data['Value'].mean()
                result_df = (
                    all_countries_data.groupby('Series Code', as_index=False)['Value']
                    .mean()
                    .query(f'Value > {overall_avg_debt}')
                )
            elif selected_query == "Identify countries contributing more than 5% of global debt.":
                total_global_debt = all_countries_data['Value'].sum()
                result_df = (
                    all_countries_data.groupby('Country Name', as_index=False)['Value']
                    .sum()
                    .query(f'Value > {0.05 * total_global_debt}')
                )
            else:
                result_df = (
                    all_countries_data.groupby(['Country Name', 'Series Code'], as_index=False)['Value']
                    .sum()
                    .sort_values(['Country Name', 'Value'], ascending=[True, False])
                    .groupby('Country Name')
                    .head(1)
                )

        st.subheader("Query Result")
        st.dataframe(result_df, use_container_width=True)
        st.stop()

    # Render the selected dashboard dataset
    st.title("Debt Data Analysis")
    dataset = st.selectbox("Select a dataset to view", ["all_countries_data", "country_series", "country_metadata", "foot_note", "series_metadata"], key="dashboard_dataset_ask")
    if dataset == "all_countries_data":
        st.header("All Countries Data")

        st.plotly_chart(country_debt_pie_figure(country_year_chart_data), use_container_width=True)
        st.plotly_chart(country_trend_figure(country_year_chart_data), width='stretch')
        st.plotly_chart(latest_country_map_figure(country_year_chart_data), use_container_width=True)
        st.plotly_chart(country_totals_figure(country_year_chart_data), use_container_width=True)
        st.plotly_chart(indicator_count_vs_debt_figure(all_countries_data), use_container_width=True)
        st.plotly_chart(country_ranked_debt_figure(country_year_chart_data, highest=True), use_container_width=True)
        st.plotly_chart(country_ranked_debt_figure(country_year_chart_data, highest=False), use_container_width=True)
        st.plotly_chart(region_trend_figure(all_countries_data), use_container_width=True)

        country_options = (
            all_countries_data[['Country Code', 'Country Name']]
            .drop_duplicates()
            .sort_values(['Country Name', 'Country Code'])
        )
        country_options['display_label'] = country_options['Country Name'].fillna(country_options['Country Code'])
        country_labels = country_options['display_label'].tolist()
        selected_country_label = st.selectbox("Select a country", country_labels, key="country_label_ask")

        selected_country_code = country_options.loc[country_options['display_label'] == selected_country_label, 'Country Code'].iloc[0]
        filtered_data = all_countries_data[all_countries_data['Country Code'] == selected_country_code]
        st.dataframe(filtered_data)

        if not filtered_data.empty:
            st.bar_chart(
                filtered_data.set_index('Year')['Value'],
                use_container_width=True
            )

        st.plotly_chart(debt_indicator_figure(all_countries_data), use_container_width=True)
        st.plotly_chart(region_debt_pie_figure(all_countries_data), use_container_width=True)
        st.plotly_chart(region_country_treemap_figure(all_countries_data), use_container_width=True)

    if dataset == "country_series":
        st.header("Country Series")
        st.plotly_chart(country_series_figure(country_series), use_container_width=True)
        st.dataframe(country_series)

    if dataset == "country_metadata":
        st.header("Country Metadata")
        st.plotly_chart(country_metadata_figure(country_metadata), use_container_width=True)
        st.dataframe(country_metadata)

    if dataset == "foot_note":
        st.header("Foot Note")
        st.plotly_chart(footnote_figure(foot_note), use_container_width=True)
        st.dataframe(foot_note)

    if dataset == "series_metadata":
        st.header("Series Metadata")
        st.plotly_chart(series_metadata_figure(series_metadata), use_container_width=True)
        st.dataframe(series_metadata)

    # Render the sidebar country total
    country_totals = (
        all_countries_data.groupby(['Country Code', 'Country Name'], as_index=False)['Value']
        .sum()
        .sort_values(['Country Name', 'Country Code'])
    )
    country_totals['display_label'] = (
        country_totals['Country Name'].fillna(country_totals['Country Code'])
        + ' (' + country_totals['Country Code'] + ')'
    )
    st.sidebar.header("Country Name")
    selected_country = st.sidebar.selectbox(
        "Select a country to view total debt",
        country_totals['display_label'].tolist(),
        key="country_total_sidebar_ask",
    )
    selected_total = country_totals.loc[
        country_totals['display_label'] == selected_country, 'Value'
    ].iloc[0]
    st.sidebar.metric("Total debt", f"${selected_total:,.2f}")

    # Query section is now kept only on the dedicated Ask Me page.

