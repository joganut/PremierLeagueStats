import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Custom CSS for enhanced styling
def add_custom_css():
    st.markdown("""
        <style>
        body {
            background-color: #f7f9fc;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
        .title {
            font-size: 3em;
            color: #1e90ff;  /* Dodger Blue */
            text-align: center;
            margin-bottom: 20px;
        }
        .subheader {
            font-size: 2em;
            color: #ff6347;  /* Tomato */
            text-align: center;
            margin-top: 20px;
        }
        .dataframe {
            font-family: 'Courier New', Courier, monospace;
        }
        .stButton>button {
            background-color: #1e90ff;
            color: white;
            font-size: 1.2em;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stSelectbox {
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data
def fetch_english_premier_league_data():
    url = "https://www.bbc.com/sport/football/premier-league/table"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching English Premier League data: {e}")
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    if table is None:
        st.error("🚫 Could not find the English Premier League table on the page.")
        return pd.DataFrame()

    headers = [header.text for header in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # Skip the header row

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        table_data.append(cols)

    df = pd.DataFrame(table_data, columns=headers)
    if not df.empty:
        df = df.iloc[:, :-1]  # Remove the last column
    return df

@st.cache_data
def fetch_player_data():
    url = "https://www.bbc.com/sport/football/premier-league/top-scorers"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching player data: {e}")
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    if table is None:
        st.error("🚫 Could not find the player stats table on the page.")
        return pd.DataFrame()

    headers = [header.text for header in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # Skip the header row

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        table_data.append(cols)

    df = pd.DataFrame(table_data, columns=headers)
    
    # Clean player names and separate them from teams
    def clean_column(value):
        return value[:len(value)//2]

    df['Name'] = df['Name'].apply(clean_column)
    df.drop_duplicates(inplace=True)  # Remove duplicate rows
    return df

def plot_team_performance(df):
    chart = alt.Chart(df).mark_bar().encode(
        x='Team',
        y='Points',
        color='Team'
    ).properties(
        title='📊 Predicted Team Performance'
    ).interactive()
    return chart

def plot_player_scoring(df):
    chart = alt.Chart(df).mark_bar().encode(
        x='Name',
        y='Goals',
        color='Name'
    ).properties(
        title='📊 Predicted Player Scoring'
    ).interactive()
    return chart

def main():
    add_custom_css()
    st.markdown('<div class="title">⚽ English Premier League Stats - 2024</div>', unsafe_allow_html=True)

    # Sidebar for navigation
    option = st.sidebar.selectbox("Choose a view", ["🏆 Team Stats", "🎯 Player Stats"])

    if option == "🏆 Team Stats":
        df = fetch_english_premier_league_data()
        if not df.empty:
            st.markdown('<div class="subheader">English Premier League Table - 2024</div>', unsafe_allow_html=True)
            search_term = st.text_input("🔍 Search the table", "")
            if search_term:
                search_term = search_term.lower()
                df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]
            st.dataframe(df, use_container_width=True)
            
            if 'Points' in df.columns:
                df['Points'] = pd.to_numeric(df['Points'], errors='coerce')
                top_5_teams = df.nlargest(5, 'Points')[['Team', 'Points']]
                st.markdown('<div class="subheader">🏅 Top 5 Teams - 2024</div>', unsafe_allow_html=True)
                st.table(top_5_teams)

                chart = alt.Chart(top_5_teams).mark_bar().encode(
                    x='Team',
                    y='Points',
                    color='Team'
                ).properties(
                    title='📊 Top 5 Teams by Points - 2024'
                ).interactive()
                st.altair_chart(chart, use_container_width=True)

                if 'Goals For' in df.columns and 'Goals Against' in df.columns:
                    performance = df[['Team', 'Goals For', 'Goals Against']]
                    st.markdown('<div class="subheader">⚽ Goals Scored vs. Goals Conceded - 2024</div>', unsafe_allow_html=True)
                    goals_scored_chart = alt.Chart(performance).mark_bar().encode(
                        x='Team',
                        y='Goals For',
                        color='Team'
                    ).properties(
                        title='📊 Goals Scored - 2024'
                    ).interactive()
                    st.altair_chart(goals_scored_chart, use_container_width=True)

                    goals_conceded_chart = alt.Chart(performance).mark_bar().encode(
                        x='Team',
                        y='Goals Against',
                        color='Team'
                    ).properties(
                        title='📊 Goals Conceded - 2024'
                    ).interactive()
                    st.altair_chart(goals_conceded_chart, use_container_width=True)

    elif option == "🎯 Player Stats":
        player_df = fetch_player_data()
        if not player_df.empty:
            st.markdown('<div class="subheader">👤 Player Stats - 2024</div>', unsafe_allow_html=True)
            st.dataframe(player_df, use_container_width=True)

            if 'Goals' in player_df.columns:
                player_df['Goals'] = pd.to_numeric(player_df['Goals'], errors='coerce')
                top_scorers = player_df.nlargest(5, 'Goals')[['Name', 'Goals']]
                st.markdown('<div class="subheader">🏆 Top 5 Scorers - 2024</div>', unsafe_allow_html=True)
                st.table(top_scorers)

                chart = alt.Chart(top_scorers).mark_bar().encode(
                    x='Name',
                    y='Goals',
                    color='Name'
                ).properties(
                    title='📊 Top 5 Scorers by Goals - 2024'
                ).interactive()
                st.altair_chart(chart, use_container_width=True)

                if 'Assists' in player_df.columns:
                    player_df['Assists'] = pd.to_numeric(player_df['Assists'], errors='coerce')
                    comparison = player_df[['Name', 'Goals', 'Assists']]
                    st.markdown('<div class="subheader">🎯 Goals vs Assists - 2024</div>', unsafe_allow_html=True)
                    
                    goals_chart = alt.Chart(comparison).mark_bar().encode(
                        x='Name',
                        y='Goals',
                        color='Name'
                    ).properties(
                        title='📊 Goals - 2024'
                    ).interactive()
                    st.altair_chart(goals_chart, use_container_width=True)

                    assists_chart = alt.Chart(comparison).mark_bar().encode(
                        x='Name',
                        y='Assists',
                        color='Name'
                    ).properties(
                        title='📊 Assists - 2024'
                    ).interactive()
                    st.altair_chart(assists_chart, use_container_width=True)

if __name__ == "__main__":
    main()
