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
            font-size: 16px;
        }
        .title {
            font-size: 2.5em;
            color: #1e90ff;  /* Dodger Blue */
            text-align: center;
            margin-bottom: 15px;
        }
        .subheader {
            font-size: 1.8em;
            color: #ff6347;  /* Tomato */
            text-align: center;
            margin-top: 15px;
        }
        .dataframe {
            font-family: 'Courier New', Courier, monospace;
        }
        .stButton>button {
            background-color: #1e90ff;
            color: white;
            font-size: 1em;
            border-radius: 5px;
            padding: 8px 16px;
        }
        .stSelectbox {
            margin-bottom: 15px;
        }
        @media (max-width: 600px) {
            .title, .subheader {
                font-size: 1.5em;
            }
            .stButton>button {
                font-size: 0.9em;
                padding: 6px 12px;
            }
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data
def fetch_epl_data():
    url = "https://www.bbc.com/sport/football/premier-league/table"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching EPL data: {e}")
        st.error(f"🚨 Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    if table is None:
        st.error("🚫 Could not find the EPL table on the page.")
        return pd.DataFrame()

    headers = [header.text for header in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # Skip the header row

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        table_data.append(cols)

    df = pd.DataFrame(table_data, columns=headers)
    return df.iloc[:, :-1] if not df.empty else df  # Remove the last column if data exists

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

def display_team_stats(df):
    st.markdown('<div class="subheader">EPL Table</div>', unsafe_allow_html=True)
    search_term = st.text_input("🔍 Search the table", "")
    if search_term:
        search_term = search_term.lower()
        df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]
    st.dataframe(df, use_container_width=True)
    
    if 'Points' in df.columns:
        df['Points'] = pd.to_numeric(df['Points'], errors='coerce')
        top_5_teams = df.nlargest(5, 'Points')[['Team', 'Points']]
        st.markdown('<div class="subheader">🏅 Top 5 Teams </div>', unsafe_allow_html=True)
        st.table(top_5_teams)

        chart = alt.Chart(top_5_teams).mark_bar().encode(
            x='Team',
            y='Points',
            color='Team'
        ).properties(
            title='📊 Top 5 Teams by Points'
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

        if 'Goals For' in df.columns and 'Goals Against' in df.columns:
            performance = df[['Team', 'Goals For', 'Goals Against']]
            st.markdown('<div class="subheader">⚽ Goals Scored vs. Goals Conceded</div>', unsafe_allow_html=True)
            goals_scored_chart = alt.Chart(performance).mark_bar().encode(
                x='Team',
                y='Goals For',
                color='Team'
            ).properties(
                title='📊 Goals Scored'
            ).interactive()
            st.altair_chart(goals_scored_chart, use_container_width=True)

            goals_conceded_chart = alt.Chart(performance).mark_bar().encode(
                x='Team',
                y='Goals Against',
                color='Team'
            ).properties(
                title='📊 Goals Conceded'
            ).interactive()
            st.altair_chart(goals_conceded_chart, use_container_width=True)

def display_player_stats(player_df):
    st.markdown('<div class="subheader">👤 Player Stats </div>', unsafe_allow_html=True)
    st.dataframe(player_df, use_container_width=True)

    if 'Goals' in player_df.columns:
        player_df['Goals'] = pd.to_numeric(player_df['Goals'], errors='coerce')
        top_scorers = player_df.nlargest(5, 'Goals')[['Name', 'Goals']]
        st.markdown('<div class="subheader">🏆 Top 5 Scorers</div>', unsafe_allow_html=True)
        st.table(top_scorers)

        chart = alt.Chart(top_scorers).mark_bar().encode(
            x='Name',
            y='Goals',
            color='Name'
        ).properties(
            title='📊 Top 5 Scorers by Goals'
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

        if 'Assists' in player_df.columns:
            player_df['Assists'] = pd.to_numeric(player_df['Assists'], errors='coerce')
            comparison = player_df[['Name', 'Goals', 'Assists']]
            st.markdown('<div class="subheader">🎯 Goals vs Assists</div>', unsafe_allow_html=True)
            
            goals_chart = alt.Chart(comparison).mark_bar().encode(
                x='Name',
                y='Goals',
                color='Name'
            ).properties(
                title='📊 Goals'
            ).interactive()
            st.altair_chart(goals_chart, use_container_width=True)

            assists_chart = alt.Chart(comparison).mark_bar().encode(
                x='Name',
                y='Assists',
                color='Name'
            ).properties(
                title='📊 Assists'
            ).interactive()
            st.altair_chart(assists_chart, use_container_width=True)

def display_team_comparison(df):
    st.markdown('<div class="subheader">Team Comparison</div>', unsafe_allow_html=True)
    teams = df['Team'].unique().tolist()
    selected_teams = st.multiselect("Select teams to compare", teams)

    if selected_teams:
        comparison_df = df[df['Team'].isin(selected_teams)]
        st.dataframe(comparison_df, use_container_width=True)

        if 'Points' in comparison_df.columns:
            comparison_df['Points'] = pd.to_numeric(comparison_df['Points'], errors='coerce')
            comparison_chart = alt.Chart(comparison_df).mark_bar().encode(
                x='Team',
                y='Points',
                color='Team'
            ).properties(
                title='📊 Points Comparison'
            ).interactive()
            st.altair_chart(comparison_chart, use_container_width=True)

            if 'Goals For' in comparison_df.columns and 'Goals Against' in comparison_df.columns:
                goals_comparison = comparison_df[['Team', 'Goals For', 'Goals Against']]
                st.markdown('<div class="subheader">⚽ Goals Scored vs. Goals Conceded</div>', unsafe_allow_html=True)
                goals_for_chart = alt.Chart(goals_comparison).mark_bar().encode(
                    x='Team',
                    y='Goals For',
                    color='Team'
                ).properties(
                    title='📊 Goals Scored'
                ).interactive()
                st.altair_chart(goals_for_chart, use_container_width=True)

                goals_against_chart = alt.Chart(goals_comparison).mark_bar().encode(
                    x='Team',
                    y='Goals Against',
                    color='Team'
                ).properties(
                    title='📊 Goals Conceded'
                ).interactive()
                st.altair_chart(goals_against_chart, use_container_width=True)

def display_player_comparison(player_df):
    st.markdown('<div class="subheader">Player Comparison</div>', unsafe_allow_html=True)
    players = player_df['Name'].unique().tolist()
    selected_players = st.multiselect("Select players to compare", players)

    if selected_players:
        comparison_df = player_df[player_df['Name'].isin(selected_players)]
        st.dataframe(comparison_df, use_container_width=True)

        if 'Goals' in comparison_df.columns:
            comparison_df['Goals'] = pd.to_numeric(comparison_df['Goals'], errors='coerce')
            goals_chart = alt.Chart(comparison_df).mark_bar().encode(
                x='Name',
                y='Goals',
                color='Name'
            ).properties(
                title='📊 Goals Comparison'
            ).interactive()
            st.altair_chart(goals_chart, use_container_width=True)

        if 'Assists' in comparison_df.columns:
            comparison_df['Assists'] = pd.to_numeric(comparison_df['Assists'], errors='coerce')
            assists_chart = alt.Chart(comparison_df).mark_bar().encode(
                x='Name',
                y='Assists',
                color='Name'
            ).properties(
                title='📊 Assists Comparison'
            ).interactive()
            st.altair_chart(assists_chart, use_container_width=True)

def main():
    add_custom_css()

    st.markdown('<div class="title">⚽ EPL Team and Player Stats</div>', unsafe_allow_html=True)
    
    option = st.sidebar.selectbox(
        "Choose an option",
        ["📊 Team Stats", "👤 Player Stats", "⚖️ Team Comparison", "⚖️ Player Comparison"]
    )
    
    if option == "📊 Team Stats":
        df = fetch_epl_data()
        if not df.empty:
            display_team_stats(df)
    
    elif option == "👤 Player Stats":
        player_df = fetch_player_data()
        if not player_df.empty:
            display_player_stats(player_df)
    
    elif option == "⚖️ Team Comparison":
        df = fetch_epl_data()
        if not df.empty:
            display_team_comparison(df)
    
    elif option == "⚖️ Player Comparison":
        player_df = fetch_player_data()
        if not player_df.empty:
            display_player_comparison(player_df)

if __name__ == "__main__":
    main()
